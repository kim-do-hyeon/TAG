import os, sqlite3, re
import numpy as np
import pandas as pd
from apps.authentication.models import Upload_Case
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from pyvis.network import Network

def usb_connection(db_path, case_id, username, progress):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    case_number = Upload_Case.query.filter_by(id = case_id).first().case_number
    case_folder = os.path.join(os.getcwd(), "uploads", username, case_number)
    data_dict = {'USB_Devices': 'USB 연결 흔적에서 연결된 USB 장치 정보를 분석하여 시스템에 연결된 외부 장치의 이력을 파악할 수 있습니다.'}
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
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
        times = []
        for idx_, (row_number, result) in enumerate(top_results):
            match = re.search(r'hit_id: (\d+)', result)
            if match:
                conn = sqlite3.connect(db_path)
                query = f"SELECT * FROM '{key}';"
                result_df = pd.read_sql_query(query, conn)
                result_df['Last_Connected_Date/Time_-_UTC_(yyyy-mm-dd)'] = pd.to_datetime(result_df['Last_Connected_Date/Time_-_UTC_(yyyy-mm-dd)'], errors='coerce')
                result_df['Last_Removal_Date/Time_-_UTC_(yyyy-mm-dd)'] = pd.to_datetime(result_df['Last_Removal_Date/Time_-_UTC_(yyyy-mm-dd)'], errors='coerce')
                result = result_df.groupby('Serial_Number').agg({
                    'Last_Connected_Date/Time_-_UTC_(yyyy-mm-dd)': 'min',
                    'Last_Removal_Date/Time_-_UTC_(yyyy-mm-dd)': 'max'
                }).reset_index()
                filtered_result = result[(result['Last_Connected_Date/Time_-_UTC_(yyyy-mm-dd)'].notna()) & 
                         (result['Last_Removal_Date/Time_-_UTC_(yyyy-mm-dd)'].notna())]
                for index, row in filtered_result.iterrows():
                    times.append([str(row['Last_Connected_Date/Time_-_UTC_(yyyy-mm-dd)']), str(row['Last_Removal_Date/Time_-_UTC_(yyyy-mm-dd)'])])
        times_data = (list(set(tuple(time) for time in times)))

        tables_query = "SELECT name FROM sqlite_master WHERE type='table';"
        tables = pd.read_sql_query(tables_query, conn)['name'].tolist()
        related_data = []
        for table in tables:
            if "Document" in table:
                columns = pd.read_sql_query(f"PRAGMA table_info('{table}');", conn)['name'].tolist()
                
                # "Date"가 칼럼 이름에 포함된 칼럼을 찾음
                date_columns = [col for col in columns if 'Date' in col]

                if date_columns:  # 'Date'가 포함된 칼럼이 있는 경우만 처리
                    for start, end in times_data:
                        for date_col in date_columns:
                            # 테이블에서 데이터를 읽어옴
                            query = f"SELECT * FROM '{table}';"
                            result_df = pd.read_sql_query(query, conn)
                            print(query, table)
                            # 날짜 컬럼을 datetime 형식으로 변환
                            if date_col in result_df.columns:
                                try:
                                    result_df[date_col] = pd.to_datetime(result_df[date_col], errors='coerce')
                                    
                                    # start와 end 사이의 값 필터링
                                    filtered_df = result_df[(result_df[date_col] >= pd.to_datetime(start)) & 
                                                            (result_df[date_col] <= pd.to_datetime(end))]
                                    
                                    if not filtered_df.empty:
                                        for col in filtered_df.columns:
                                            values = filtered_df[col].dropna().unique()
                                            for value in values:
                                                # related_data 리스트에 추가
                                                related_data.append({
                                                    'Table': table, 
                                                    'Column': col, 
                                                    'Value': value, 
                                                    'Data': filtered_df.to_dict()
                                                })
                                except Exception as e:
                                    print(f"테이블 '{table}'에서 열 '{col}'로 검색 중 오류 발생: {e}")

        # PyVis 네트워크 그래프 생성
        net = Network(height="750px", width="100%", notebook=True)

        # 각 테이블, 컬럼, 값들을 노드와 엣지로 추가
        for record in related_data:
            table = record['Table']
            data = record['Data']

            # 최상위 부모 노드는 테이블 이름
            net.add_node(table, label=f"Table: {table}", color="red", shape="ellipse", size=50)  # 테이블 이름을 최상위 부모로 설정
            
            # Data의 각 인덱스(예: 322)를 중간 부모 노드로 설정
            for index in data['Filename'].keys():
                index_node = f"{table}_index_{index}"
                net.add_node(index_node, label=f"Index: {data['Filename'][index]}", color="orange", shape="ellipse", size=40)  # 중간 부모 노드 (각 인덱스)
                net.add_edge(table, index_node)  # 테이블 노드와 인덱스 노드 연결
                
                # 해당 인덱스 아래에 있는 각 열을 중간 부모 노드로 추가
                for col in data.keys():
                    column_node = f"{col}_{index}"
                    net.add_node(column_node, label=f"{col}", color="blue", shape="box", size=30)  # 중간 부모 노드 (각 컬럼)
                    net.add_edge(index_node, column_node)  # 인덱스 노드와 컬럼 노드를 연결
                    
                    # 각 열의 값을 자식 노드로 추가
                    value = data[col][index]
                    child_node = f"value_{col}_{index}"
                    net.add_node(child_node, label=f"{str(value)}", color="green", shape="box", size=50)  # 자식 노드
                    net.add_edge(column_node, child_node)  # 컬럼 노드와 값 노드를 연결

        # 네트워크 그래프를 HTML 파일로 저장
        output_file = os.path.join(case_folder, "usb_network.html")
        net.show(output_file)
        print(f"Saved graph to {output_file}")
        # 데이터베이스 연결 종료
        conn.close()       
        # progress
        progress[case_id] = min(99, int((idx_/len(top_results))*progress_unit + progress_unit * idx))
    cursor.close()
    conn.close()
    return output_file