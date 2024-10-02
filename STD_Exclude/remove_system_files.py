import sqlite3
import json
import pandas as pd
import os

# 청크로 나눠서 실행할 함수
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

# system_files.json 로드
# 각 아티팩트 테이블 별 참고할 컬럼 리스트가 저장되어 있음
removes_json_path = os.path.join(os.path.dirname(__file__), "system_files.json")

with open(removes_json_path, "r", encoding='utf8') as f:
    f = f.read()
    json_data = json.loads(f)

# removal_target 딕셔너리 선언
removal_target = json_data['removal_target']

# .db 파일 경로
db_path = input(f"제거를 진행할 정규화 파일 경로를 입력하세요:\n")  # 현재 사건 케이스 파일 normalization 경로

# 만약 이스케이프 문자가 있는 경우 처리 (백슬래시를 두 번으로 변경)
db_path = db_path.replace('\\', '\\\\')

# 데이터베이스 연결
conn = sqlite3.connect(db_path)

# 현재 케이스 파일의 테이블명 추출
db_cursor = conn.cursor()
db_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

db_table_list = []
for row in db_cursor:
    db_table_list.append(row[0])

# 제거 파일 수 기록용
before_total = 0
after_taotal = 0

# 파일 목록을 읽어 리스트에 추가하는 함수
def load_file(file_path):
    with open(file_path, "r") as file:
        return [line.strip() for line in file]

# 여러 파일 목록을 하나의 리스트로 병합
file_paths = [
    "dll.txt",
    "exe.txt",
    "msc.txt"
]

# 각 파일의 데이터를 병합하여 removes 리스트에 저장
removes = []
for file_path in file_paths:
    file_path = os.path.join(os.path.dirname(__file__), file_path)
    removes.extend(load_file(file_path))

# 현재 케이스 파일의 각 테이블 별 필요 없는 row 제거
for table in db_table_list:
    # json이나 삭제 대상에 없는 테이블이 존재한다면 pass
    if table not in removal_target.keys():
        continue

    # 딕셔너리로부터 target 컬럼 가져옴
    target_column = removal_target[table][0]
    if target_column == '':
        continue
    
    # 삭제 전후 비교 위해 삭제 전 row 수 저장
    db_cursor.execute(f'SELECT "{target_column}" FROM "{table}"')
    res = db_cursor.fetchall()
    before_remove = len(res)

    delete_in_chunks(db_cursor, conn, removes, table, target_column)

    # 삭제 전후 비교 위해 삭제 전 row 수 저장
    db_cursor.execute(f'SELECT "{target_column}" FROM "{table}"')
    res = db_cursor.fetchall()
    after_remove = len(res)

    before_total += before_remove
    after_taotal += after_remove

    # 변경 사항 출력
    print(f"{table} 테이블 삭제 전: {before_remove} / 삭제 후: {after_remove} 개의 행으로 감소하였습니다.")

print(f"전체 행 {before_total} 중에서 {before_total - after_taotal} 개의 행이 삭제되었습니다.\n현재 {after_taotal} 개의 행이 존재합니다.")

# 변경 사항 저장 및 연결 종료
conn.commit()
conn.close()