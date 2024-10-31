import sqlite3
import pandas as pd
import numpy as np
import os
from apps.analyze.USB.table_info import *
from apps.analyze.USB.windows_event_log import *

def generate_to_timestamp(column, table, attribute, conn, table_info, time_dict) :
    query = f"SELECT hit_id, [{column}], [{table_info[table]['root_col']}] FROM '{table}'"
    try:
        # 데이터프레임으로 변환하여 리스트에 추가
        df = pd.read_sql_query(query, conn).dropna()
        if not df.empty:
            # 시간 컬럼 기준이 아닌 다른 조건을 통해 type을 매겨야 할 때
            if isinstance(attribute['type'], dict) :
                key, value = None, None
                for i, ii in attribute['type'].items() :
                    key = i
                    value = ii
                for index, row in df.iterrows() :
                    tmp_df = pd.read_sql(f"SELECT [{key}] FROM '{table}' WHERE hit_id = {row['hit_id']}", conn)
                    df.at[index, 'type'] = value[tmp_df[key].iloc[0]]
                print(df)
            # 시간 컬럼이 type자체를 의미할 때
            else :
                df['type'] = attribute['type']  # 설명 추가
            
            df['table'] = table  # 데이터 출처 테이블 정보 추가
            
            # 특정 데이터는 추가적인 정보를 포함할 수 있음
            if len(attribute.keys()) > 1 and 'what' not in attribute.keys() :
                additional_data = [key for key in attribute.keys() if key != 'type']
                df['additional_data'] = ', '.join(additional_data)
            else :
                df['additional_data'] = np.nan
            
            df['column'] = column
            df.rename(columns={table_info[table]['root_col']: 'main_data'}, inplace=True)
            df.rename(columns={f"{column}": 'timestamp'}, inplace=True)  # 컬럼 이름을 'timestamp'로 변경
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            # 결측값 제외
            df.dropna(subset=['timestamp'], inplace=True)
            return df
    except Exception as e:
        if 'no such column' not in str(e) :
            print(f"Error processing table {table}, column {column}: {e}")
        return None

def time_parsing(db_path, new_db_path) :
    
    # 파일이 존재하는지 확인
    if os.path.exists(new_db_path):
        # 파일 삭제
        os.remove(new_db_path)
        print(f"{new_db_path} has been deleted.")
    else:
        print(f"{new_db_path} does not exist.")
    
    time_dict = table_info_class.get_time_dict()
    table_info = table_info_class.get_info()
    
    conn = sqlite3.connect(db_path)

    # 결과를 저장할 데이터프레임 리스트
    dataframes = []

    # 각 테이블에 대해 데이터 추출
    for table, columns in time_dict.items():
        # 테이블 존재 여부 확인
        table_exists_query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
        table_exists = pd.read_sql_query(table_exists_query, conn)
        
        if not table_exists.empty:
            for column, attribute in columns.items():
                if column == 'include' :
                    query = f"PRAGMA table_info('{table}')"
                    column_list = pd.read_sql_query(query, conn)
                    date_cols = [col['name'] for _, col in column_list.iterrows() if attribute['what'] in col['name']]
                    for col in date_cols :
                        df = generate_to_timestamp(col, table, attribute, conn, table_info, time_dict)
                        if df is not None:
                            dataframes.append(df)
                else :
                    df = generate_to_timestamp(column, table, attribute, conn, table_info, time_dict)
                    if df is None:
                        continue
                    dataframes.append(df)


    # 모든 데이터프레임을 하나로 합치기 & 그룹화
    if dataframes:
        combined_df = pd.concat(dataframes, ignore_index=True)

        # 시간 순서로 정렬
        combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'], errors='coerce')
        sorted_df = combined_df.sort_values(by=['timestamp', 'type', 'main_data'])
        sorted_df = sorted_df.dropna(subset=['main_data']).reset_index()
        sorted_df = sorted_df.drop(columns=['index'])

        new_df = pd.DataFrame(columns=sorted_df.columns.to_list())
        hit_id_tmp = set()
        for index, row in sorted_df.iterrows() :
            #row['timestamp'] = pd.to_datetime(row['timestamp'], errors='coerce')
            if index != 0:
                if  (row['timestamp'] < new_df.iloc[-1]['timestamp'] + pd.Timedelta(seconds=1) and
                    new_df.iloc[-1]['type'] == row['type'] and
                    new_df.iloc[-1]['main_data'] == row['main_data']) :
                    if not hit_id_tmp :
                        hit_id_tmp.add(str(new_df.iloc[-1]['hit_id']))
                    hit_id_tmp.add(str(row['hit_id']))
                    continue
                elif hit_id_tmp:
                    # 마지막 행의 'hit_id'와 'table'을 업데이트
                    new_df.loc[new_df.index[-1], 'hit_id'] = ', '.join(list(hit_id_tmp))
                    table_tmp = [str(sorted_df.loc[sorted_df['hit_id'] == hit_id, 'table'].values[0]) for hit_id in hit_id_tmp]
                    new_df.loc[new_df.index[-1], 'table'] = ', '.join(table_tmp)
                    hit_id_tmp = set()
            new_df = pd.concat([new_df, pd.DataFrame([row])], ignore_index=True)

        # 시간 순서로 정렬
        new_df['timestamp'] = pd.to_datetime(new_df['timestamp'], errors='coerce')
        sorted_df = new_df.sort_values(by='timestamp')
        sorted_df = sorted_df.dropna(subset=['main_data']).reset_index()
        sorted_df = sorted_df.drop(columns=['index'])
        sorted_df.reset_index(inplace=True)

        # 새로운 데이터베이스 파일에 연결
        new_conn = sqlite3.connect(new_db_path)

        # 정렬된 결과를 새로운 데이터베이스 테이블에 저장
        sorted_df.to_sql('data', new_conn, if_exists='replace', index=False)

        # 새로운 데이터베이스 연결 종료
        new_conn.close()

        # 결과 출력
        return True
    else:
        print("No data to process.")
        return False