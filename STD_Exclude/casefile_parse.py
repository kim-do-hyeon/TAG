import sqlite3
import json
import os

# 데이터베이스 파일 경로
db_path = r"DB파일 경로"

# JSON 파일 경로
json_file_path = r"JSON파일 경로"

# 데이터베이스 연결
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 테이블과 컬럼 이름 지정
table_name = '추출 테이블'  # 테이블 이름 입력
column_name = '추출 컬럼'  # 컬럼 이름 입력

# 특정 테이블의 특정 컬럼에 해당하는 값들을 가져오는데, NULL 값을 제외하는 쿼리 실행
cursor.execute(f"SELECT {column_name} FROM '{table_name}' WHERE {column_name} IS NOT NULL")

# 결과를 리스트로 변환
rows = cursor.fetchall()
values = [row[0] for row in rows]

# 기존 JSON 파일 읽기 (파일이 존재하는지 확인)
if os.path.exists(json_file_path):
    with open(json_file_path, 'r', encoding='utf-8') as json_file:
        try:
            data = json.load(json_file)
            # 만약 파일이 딕셔너리라면 리스트로 변환
            if isinstance(data, dict):
                data = [data]
        except json.JSONDecodeError:
            data = []  # 파일이 비어 있거나 잘못된 경우 빈 리스트로 시작
else:
    data = []  # 파일이 없으면 빈 리스트로 시작

# 새로운 데이터 형식에 맞추기
new_entry = {
    "table": table_name,
    "column": column_name,
    "values": values
}

# 기존 데이터에 새로운 데이터를 추가
data.append(new_entry)

# JSON 파일로 저장 (덮어쓰기)
with open(json_file_path, 'w', encoding='utf-8') as json_file:
    json.dump(data, json_file, ensure_ascii=False, indent=4)

# 데이터베이스 연결 종료
conn.close()

print(f"JSON 파일에 데이터가 추가되었음: {json_file_path}")
