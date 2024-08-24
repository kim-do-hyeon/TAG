import sqlite3
import json

# 함수 정의: JSON 데이터를 처리하여 DB에서 행을 삭제하고, 삭제된 행의 수를 반환하는 함수
def process_json_file(json_file_path, cursor, max_sql_variables=999):
    # JSON 파일을 읽어옴
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # 각 파일에서 삭제된 행의 수를 추적
    deleted_rows_total = 0

    # 데이터를 기반으로 삭제 작업 수행
    for entry in data:
        table = entry['table']
        column = entry['column']
        values = entry['values']

        # NULL 값을 제외하고 유효한 값들만 리스트로 추출
        filtered_values = [value for value in values if value is not None]

        try:
            # 삭제 작업 전 테이블의 총 행 수를 확인
            cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
            initial_row_count = cursor.fetchone()[0]

            if filtered_values:
                # 데이터를 최대 999개씩 처리하도록 분할
                for i in range(0, len(filtered_values), max_sql_variables):
                    chunk = filtered_values[i:i + max_sql_variables]
                    placeholders = ', '.join('?' for _ in chunk)
                    query = f'DELETE FROM "{table}" WHERE "{column}" IN ({placeholders})'
                    cursor.execute(query, chunk)

            # 삭제 작업 후 테이블의 총 행 수를 확인
            cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
            final_row_count = cursor.fetchone()[0]

            # 삭제된 행의 수 계산
            deleted_rows = initial_row_count - final_row_count
            deleted_rows_total += deleted_rows

            # 각 테이블별로 삭제된 행과 남아있는 행 출력
            print(f'Table "{table}": {deleted_rows} rows deleted, {final_row_count} rows remaining.')

        except sqlite3.OperationalError as e:
            # 테이블이 없을 경우 에러 메시지를 출력하고 넘어감
            print(f'Skipping table "{table}" due to error: {e}')
        except sqlite3.DatabaseError as e:
            # 데이터 값에 문제가 발생한 경우 예외 처리
            print(f"Error with data in table '{table}': {e}")

    return deleted_rows_total

# SQLite DB에 연결 (DB 파일 경로를 지정)
db_path = input(r"DB파일 경로를 지정해주세요 : ")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Windows 11 버전 데이터를 처리
win11_json_file_path = r"win11_output.json"
deleted_rows_win11 = process_json_file(win11_json_file_path, cursor)
print("-"*100)
print(f"Window11 기본 데이터가 {deleted_rows_win11}개 삭제되었습니다.\n")

# Windows 10 버전 데이터를 처리
win10_json_file_path = r"win10_output.json"
deleted_rows_win10 = process_json_file(win10_json_file_path, cursor)
print("-"*100)
print(f"Window10 기본 데이터가 {deleted_rows_win10}개 삭제되었습니다.\n")

# 전체 삭제된 행의 총 수 출력
total_deleted_rows = deleted_rows_win11 + deleted_rows_win10
print("="*100)
print(f"전체 삭제 갯수 : {total_deleted_rows}")
print("="*100)
# 변경 사항을 커밋하고 DB 연결을 종료
conn.commit()
conn.close()
