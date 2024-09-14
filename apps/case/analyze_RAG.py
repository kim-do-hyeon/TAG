from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import sqlite3
import openai
import re, os
import pandas as pd

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
    
def search_query(scenario, db_path):
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
    for key, value in data_dict.items():
        cursor.execute(f"SELECT * FROM {key}")
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
            print(f"Row {row_number}: {result.strip()}")
            # print(f"Row {row_number}")

    cursor.close()
    conn.close()