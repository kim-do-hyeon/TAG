import sqlite3
import json
import pandas as pd
import os

def delete_in_chunks(cursor, conn, removes, table, target_column, chunk_size=999):
    # 리스트를 chunk_size로 나누기
    for i in range(0, len(removes), chunk_size):
        chunk = removes[i:i + chunk_size]
        # 각 아이템에 대해 LIKE 조건을 만듦
        like_conditions = ' OR '.join([f'"{target_column}" LIKE ?' for _ in chunk])
        sql_query = f'DELETE FROM "{table}" WHERE {like_conditions}'
        # %를 사용하여 부분 일치를 찾기 위해 각 항목에 %를 추가
        like_values = [f'%{value}%' for value in chunk]
        cursor.execute(sql_query, like_values)
        conn.commit()  # 각 청크 처리 후 커밋

def load_file(file_path):
    with open(file_path, "r") as file:
        return [line.strip() for line in file]