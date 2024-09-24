import sqlite3
import json
from hashlib import sha1

# removal_target_list.json 로드
# 각 아티팩트 테이블 별 참고할 컬럼 리스트가 저장되어 있음
removes_json_path = './removal_target_list.json'

with open(removes_json_path, "r", encoding='utf8') as f:
    f = f.read()
    json_data = json.loads(f)

# removal_target 딕셔너리 선언
removal_target = json_data['removal_target']

# .db 파일 경로
db_path = '' # 현재 사건 케이스 파일 normalization 경로
removal_db_dpath = '' # 윈도우 초기 케이스 파일 normalization 경로

# 데이터베이스 연결
conn = sqlite3.connect(db_path)
conn_remove = sqlite3.connect(removal_db_dpath)

# 현재 케이스 파일의 테이블명 추출
db_cursor = conn.cursor()
db_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

db_table_list = []
for row in db_cursor:
    db_table_list.append(row[0])

# 삭제 대상 파일의 테이블명 추출
remove_cursor = conn_remove.cursor()
remove_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

remove_table_list = []
for row in remove_cursor:
    remove_table_list.append(row[0])

# 현재 케이스 파일의 각 테이블 별 필요 없는 row 제거
for table in db_table_list:
    # json이나 삭제 대상에 없는 테이블이 존재한다면 pass
    if table not in removal_target.keys() or table not in remove_table_list:
        continue

    # 딕셔너리로부터 target 컬럼 가져옴
    target_column = removal_target[table][0]
    if target_column == '':
        continue

    remove_cursor.execute(f'SELECT "{target_column}" FROM "{table}" WHERE "{target_column}" IS NOT NULL')
    
    # 지워야 할 파일명들
    removes = []
    for row in remove_cursor:
        removes.append(row[0])
    removes = list(set(removes)) # 중복 제거

    # # Scheduled_Tasks 테이블의 경우 예외 처리
    # -> 굳이 해싱 안해도 돼서 주석 처리
    # if table == "Scheduled_Tasks":

    #     # 원본 removes들을 해싱
    #     removes = [sha1(item.encode()).hexdigest() for item in removes]

    #     # 현재 케이스 해싱하기 위해 데이터 로드
    #     db_cursor.execute(f'SELECT "{target_column}" FROM "{table}" WHERE "{target_column}" IS NOT NULL')
    #     rows = db_cursor.fetchall()

    #     # 현재 케이스 해싱: 현재 케이스 원본 데이터
    #     # 형태로 딕셔너리 선언
    #     original_hash_dict = {sha1(row[0].encode()).hexdigest() : row[0] for row in rows}

    #     # removes 에 있는 해시값과 일치할 경우, original_value만 removes에 저장
    #     removes = [original_hash_dict[hash_value] for hash_value in removes if hash_value in original_hash_dict]

    # 삭제 전후 비교 위해 삭제 전 row 수 저장
    db_cursor.execute(f'SELECT "{target_column}" FROM "{table}"')
    res = db_cursor.fetchall()
    before_remove = len(res)

    # 쿼리 작성
    # '?' 플레이스 홀더를 사용하여 여러 값을 대입
    placeholders = ', '.join(['?'] * len(removes))
    sql_query = f'DELETE FROM "{table}" WHERE "{target_column}" IN ({placeholders})'

    # 쿼리 실행
    db_cursor.execute(sql_query, removes)

    # 삭제 전후 비교 위해 삭제 전 row 수 저장
    db_cursor.execute(f'SELECT "{target_column}" FROM "{table}"')
    res = db_cursor.fetchall()
    after_remove = len(res)

    # 변경 사항 출력
    print(f"{table} 테이블 삭제 전: {before_remove} / 삭제 후: {after_remove} 개의 행으로 감소하였습니다.")

# 변경 사항 저장 및 연결 종료
conn.commit()
conn.close()
conn_remove.close()
