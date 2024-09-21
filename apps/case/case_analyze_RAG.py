from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import sqlite3
import openai
import re, os
import pandas as pd
import os
import json
from flask import current_app
from py2neo import Graph, Node, Relationship
from apps import db
from apps.authentication.models import PromptQuries, Upload_Case, GraphData

neo4j_url = os.getenv('neo4j_server')
neo4j_username = os.getenv('neo4j_id')
neo4j_password = os.getenv('neo4j_password')
graph = Graph(neo4j_url, auth=(neo4j_username, neo4j_password))

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

def search_query(scenario, db_path, case_id, username, progress):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    case_number = Upload_Case.query.filter_by(id = case_id).first().case_number
    case_folder = os.path.join(os.getcwd(), "uploads", username, case_number)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    openai.api_key = os.getenv('API_KEY')

    prompt = str(scenario) + "에서 포렌식 관점에서 필요한 아티팩트를 너가 선정해서 아래에서 골라줘," + str(tables) + " // 단 아티팩트 이름만 나열해. 그리고 각 아티팩트와 시나리오를 합쳐서 한문장으로 쿼리를 만들어줘(아티팩트당 하나의 쿼리)" + """
    형식은 아래와 같이 3개 나오게 해줘. 순서를 정하지마, 단순히 아래와 같은 형식으로.
    - Internet:인터넷에서 어떤걸 검색했나요?
    """
    prompt_response = generate_response(prompt)
    text = prompt_response.replace("- ", "").replace("'", "")
    result1 = re.split(r'[:\n]+', text)

    data_dict = {result1[i]: result1[i + 1].strip() for i in range(0, len(result1), 2)}

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    response = ''
    graph_datas = []
    query_datas = []
    
    progress_unit = 100 / len(data_dict)
    
    for idx, (key, value) in enumerate(data_dict.items()):
        cursor.execute(f"SELECT * FROM '{key}'")
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()

        texts = [" ".join([f"{col}: {val}" for col, val in zip(columns, row) if val is not None]) for row in rows]
        embeddings = model.encode(texts)

        np.save(os.path.join(case_folder, 'embeddings.npy'), embeddings)
        with open(os.path.join(case_folder, 'original_texts.txt'), 'w', encoding='utf-8') as f:
            for text in texts:
                f.write(text + "\n")

        query = value
        query_embedding = model.encode([query])

        embeddings = np.load(os.path.join(case_folder, 'embeddings.npy'))
        similarities = cosine_similarity(query_embedding, embeddings).flatten()

        top_indices = similarities.argsort()[-10:][::-1]
        with open(os.path.join(case_folder, 'original_texts.txt'), 'r', encoding='utf-8') as f:
            original_texts = f.readlines()

        top_results = [(idx, original_texts[idx]) for idx in top_indices]  # Store row numbers with results
        # print()
        # print()
        # print("=" * 100)
        # print(f"[{key}] Query : {query}")
        
        # Print results with row numbers
        for idx_, (row_number, result) in enumerate(top_results):
            match = re.search(r'hit_id: (\d+)', result)
            if match:
                # print(f"Row {row_number}: hit_id: {match.group(1)}")
                graph_value, query_value = connection_to_case(db_path, str(match.group(1)))
                graph_datas.append(graph_value)
                query_datas.append(query_value)
                
            #progress
            progress[case_id] = min(99, int((idx_/len(top_results))*progress_unit + progress_unit * idx))

    
    
    cursor.close()
    conn.close()
    
    graph_record = GraphData(case_id=case_id, graph_data=graph_datas, query_data=query_datas)
    db.session.add(graph_record)
    db.session.commit()
    
    prompt_data = PromptQuries(username = username,
                        case_id = case_id,
                        query = str(scenario),
                        tables = str(tables),
                        response = str(prompt_response),
                        graph_index = graph_record.id)
    db.session.add(prompt_data)

    db.session.commit()
    return True

def connection_to_case(db_path, hit_id) :
    
    def is_not_in_exclude_columns(table, col) :
        with open(current_app.root_path + '/case/exclude_column_list.json', 'r', encoding='utf-8') as f:
            exclude_columns = json.load(f)
        if col in exclude_columns['common']:
            return False
        if table in exclude_columns and col in exclude_columns[table]:
            return False
        return True
    
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
                    if is_not_in_exclude_columns(table, col):
                        if col not in related_values:
                            related_values[col] = set()
                        related_values[col].update(result_df[col].dropna().unique())

    # print("추출된 연관된 값들:", related_values)
    related_data = []

    for table in tables:
        columns = pd.read_sql_query(f"PRAGMA table_info('{table}');", conn)['name'].tolist()
        for col, values in related_values.items():
            if col in columns:
                for value in values:
                    if len(value) > 5 :
                        try:
                            if is_not_in_exclude_columns(table, col) :
                                value = value.replace("'", "").replace('"', "")
                                query = f"SELECT * FROM '{table}' WHERE \"{col}\" = '{value}';"
                                result_df = pd.read_sql_query(query, conn)
                                if len(result_df) < 1000 :
                                    if not result_df.empty:
                                        related_data.append({'Table': table, 'Column': col, 'Value': value, 'Data': result_df})
                        except Exception as e:
                            print(f"테이블 '{table}'에서 열 '{col}'로 검색 중 오류 발생: {e}")
    query_value = {}
    for data in related_data:
        # print(f"테이블: {data['Table']}, 열: {data['Column']}, 값: {data['Value']}")
        # print(data['Data'])
        if data['Table'] in query_value :
            query_value[data['Table']].append({data['Column']:data['Value']})
        else :
            query_value[data['Table']] = [{data['Column']:data['Value']}]
        # print('-' * 50)

    conn.close()
    data, query = create_graph(related_data), query_value
    return data, query

def create_graph(related_data):
    # 기존 데이터를 삭제 (필요 시)
    graph.run("MATCH (n) DETACH DELETE n")

    # 관련된 데이터를 그래프로 생성
    for data in related_data:
        table = data['Table']
        column = data['Column']
        value = data['Value']
        result_df = data['Data']

        # 테이블 노드 생성, 라벨은 "Table", 기본 키는 "name"
        table_node = Node("Table", name=table)
        graph.merge(table_node, "Table", "name")

        # 열 노드 생성, 라벨은 "Column", 기본 키는 "name"
        column_node = Node("Column", name=column, table=table)
        graph.merge(column_node, "Column", "name")

        # 테이블과 열 노드를 연결
        relationship = Relationship(table_node, "HAS_COLUMN", column_node)
        graph.merge(relationship)

        # 데이터 노드 생성, 라벨은 "Data", 기본 키는 데이터의 고유한 키 (예: ID, 이름 등)
        for index, row in result_df.iterrows():
            row_node = Node("Data", id=index, **row.to_dict())  # 'id' 또는 다른 고유 키를 사용
            graph.merge(row_node, "Data", "id")

            # 열과 데이터 노드를 연결
            col_data_relationship = Relationship(column_node, "HAS_DATA", row_node)
            graph.merge(col_data_relationship)

            # 특정 열과 값이 연관된 다른 데이터 노드 연결 예시
            if 'related_column' in row:
                related_node = Node("Data", name=row['related_column'])
                graph.merge(related_node, "Data", "name")
                related_relationship = Relationship(row_node, "RELATED_TO", related_node)
                graph.merge(related_relationship)
    
    # Neo4j에서 데이터 가져오기 (노드와 관계 모두 포함)
    query = "MATCH (n)-[r]->(m) RETURN n, r, m"
    results = graph.run(query).data()
    # print(results)
    nodes = {}
    links = []

    for record in results:
        for node in [record['n'], record['m']]:
            if node.identity not in nodes:
                if "chrom" in str(node).lower() or "edge" in str(node) :
                    node_name = node.get('Title', str(node.__name__)) + str(node.get('URL', str(node.__name__)))
                else :
                    node_name = node.get('URL', str(node.__name__))
                nodes[node.identity] = {
                    "id": node.identity,
                    "label": list(node.labels)[0] if node.labels else "Node",
                    "name": node_name
                }
        
        links.append({
            "source": record['n'].identity,
            "target": record['m'].identity,
            "type": type(record['r']).__name__
        })
    return {"nodes": list(nodes.values()), "links": links}
