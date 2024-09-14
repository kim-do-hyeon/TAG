from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import sqlite3
import openai
import re, os
import pandas as pd
import os
import json
from werkzeug.utils import secure_filename
from flask import current_app

def generate_response(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            n=1,
            temperature=0
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        return f"Error: {str(e)}"

def save_query_data_to_user_folder(query, tables, response, case_id, username):
    user_folder = os.path.join(current_app.root_path, 'user_folder', username, str(case_id))
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    file_path = os.path.join(user_folder, 'queries.json')
    
    # 기존 JSON 파일 읽기
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = []

    # 새로운 데이터 추가
    data.append({
        "query": query,
        "tables": tables,
        "response": response
    })

    # JSON 파일에 저장
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def search_query(scenario, db_path, case_id, username):
    model = SentenceTransformer('all-MiniLM-L6-v2')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print(tables)
    openai.api_key = os.getenv('API_KEY')

    prompt = str(scenario) + "에서 포렌식 관점에서 필요한 아티팩트를 너가 선정해서 아래에서 골라줘," + str(tables) + " // 단 아티팩트 이름만 나열해. 그리고 각 아티팩트와 시나리오를 합쳐서 한문장으로 쿼리를 만들어줘(아티팩트당 하나의 쿼리)" + """
    형식은 아래와 같이 5개 이상 나오게 해줘.
    - Internet : 인터넷에서 어떤걸 검색했나요?
    """
    print(prompt)
    result = generate_response(prompt)
    print(result)
    text = result.replace("- ", "").replace("'", "")
    result1 = re.split(r'[:\n]+', text)

    data_dict = {result1[i]: result1[i + 1].strip() for i in range(0, len(result1), 2)}

    print(data_dict)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    response = ''
    for key, value in data_dict.items():
        cursor.execute(f"SELECT * FROM '{key}'")
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()

        texts = [" ".join([f"{col}: {val}" for col, val in zip(columns, row) if val is not None]) for row in rows]
        embeddings = model.encode(texts)

        np.save('embeddings.npy', embeddings)
        with open('original_texts.txt', 'w', encoding='utf-8') as f:
            for text in texts:
                f.write(text + "\n")

        query = value
        query_embedding = model.encode([query])

        embeddings = np.load('embeddings.npy')
        similarities = cosine_similarity(query_embedding, embeddings).flatten()

        top_indices = similarities.argsort()[-10:][::-1]
        with open('original_texts.txt', 'r', encoding='utf-8') as f:
            original_texts = f.readlines()

        top_results = [(idx, original_texts[idx]) for idx in top_indices]  # Store row numbers with results
        print()
        print()
        print("=" * 100)
        print(f"[{key}] Query : {query}")
        
        # Print results with row numbers
        for row_number, result in top_results:
            match = re.search(r'hit_id: (\d+)', result)
            if match:
                print(f"Row {row_number}: hit_id: {match.group(1)}")
                connection_to_case(db_path, str(match.group(1)))

    save_query_data_to_user_folder(prompt, str(result1), response, case_id, secure_filename(username))
    
    cursor.close()
    conn.close()

def connection_to_case(db_path, hit_id) :
    conn = sqlite3.connect(db_path)
    tables_query = "SELECT name FROM sqlite_master WHERE type='table';"
    tables = pd.read_sql_query(tables_query, conn)['name'].tolist()
    related_values = {}

    for table in tables:
        columns = pd.read_sql_query(f"PRAGMA table_info('{table}');", conn)['name'].tolist()
        if 'hit_id' in columns:
            query = f"SELECT * FROM '{table}' WHERE hit_id = '{hit_id}';"
            result_df = pd.read_sql_query(query, conn)
            if not result_df.empty:
                for col in result_df.columns:
                    if col not in ['artifact_version_id', 'hit_id', 'artifact_id', 'artifact_name']:
                        if col not in related_values:
                            related_values[col] = set()
                        related_values[col].update(result_df[col].dropna().unique())

    print("추출된 연관된 값들:", related_values)
    related_data = []

    for table in tables:
        columns = pd.read_sql_query(f"PRAGMA table_info('{table}');", conn)['name'].tolist()
        for col, values in related_values.items():
            if col in columns:
                for value in values:
                    if len(value) > 5 :
                        try:
                            query = f"SELECT * FROM '{table}' WHERE \"{col}\" = '{value}';"
                            result_df = pd.read_sql_query(query, conn)
                            if len(result_df) < 1000 :
                                if not result_df.empty:
                                    related_data.append({'Table': table, 'Column': col, 'Value': value, 'Data': result_df})
                        except Exception as e:
                            print(f"테이블 '{table}'에서 열 '{col}'로 검색 중 오류 발생: {e}")

    for data in related_data:
        print(f"테이블: {data['Table']}, 열: {data['Column']}, 값: {data['Value']}")
        print(data['Data'])
        print('-' * 50)

    conn.close()