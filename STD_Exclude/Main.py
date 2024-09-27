import sqlite3
from datetime import datetime
import json
import os

def process_json_file(json_file_path, cursor, max_sql_variables=999):
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    deleted_rows_total = 0
    for entry in data:
        table = entry['table']
        column = entry['column']
        values = entry['values']
        filtered_values = [value for value in values if value is not None]
        try:
            cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
            initial_row_count = cursor.fetchone()[0]
            if filtered_values:
                for i in range(0, len(filtered_values), max_sql_variables):
                    chunk = filtered_values[i:i + max_sql_variables]
                    placeholders = ', '.join('?' for _ in chunk)
                    query = f'DELETE FROM "{table}" WHERE "{column}" IN ({placeholders})'
                    cursor.execute(query, chunk)
            cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
            final_row_count = cursor.fetchone()[0]
            deleted_rows = initial_row_count - final_row_count
            deleted_rows_total += deleted_rows
            print(f'Table "{table}": {deleted_rows} rows deleted, {final_row_count} rows remaining.')
        except sqlite3.OperationalError as e:
            print(f'Skipping table "{table}" due to error: {e}')
        except sqlite3.DatabaseError as e:
            print(f"Error with data in table '{table}': {e}")
    return deleted_rows_total

def filter_and_save_db(cursor):
    timestamp_input = input("사건 시작시간을 입력해주세요 (예: 2024-09-29 07:24:22.252): ")
    timestamp = datetime.strptime(timestamp_input, '%Y-%m-%d %H:%M:%S.%f')

    # 모든 Displayed_Computer_Name 가져오기
    cursor.execute("SELECT DISTINCT Displayed_Computer_Name FROM Operating_System_Information")
    computers = cursor.fetchall()

    if len(computers) == 1:
        computer_name = computers[0][0]
    else:
        # 사용자에게 선택지 제공
        print("선택 가능한 컴퓨터 이름:")
        for idx, (name,) in enumerate(computers):
            print(f"{idx + 1}. {name}")
        choice = int(input("컴퓨터를 선택해주세요 (번호 입력): "))
        computer_name = computers[choice - 1][0]

    # 데이터 필터링 및 삭제
    cursor.execute('DELETE FROM Windows_Event_Logs WHERE "Created_Date/Time_-_UTC_(yyyy-mm-dd)" < ? OR Computer != ?', (timestamp, computer_name))

    print(f"데이터가 {timestamp_input} 이후로 컴퓨터 이름 '{computer_name}'에 해당하는 데이터만 남았습니다.")

def save_database_as(file_name, conn, original_path):
    # 입력받은 파일 이름으로 새 경로 생성
    new_db_path = os.path.join(os.path.dirname(original_path), file_name)

    new_conn = sqlite3.connect(new_db_path)
    for line in conn.iterdump():
        if 'CREATE TABLE' in line:
            new_conn.execute(line)
        elif 'INSERT INTO' in line:
            new_conn.execute(line)
    
    new_conn.commit()
    new_conn.close()
    print(f"변경된 데이터가 '{new_db_path}'에 저장되었습니다.")

def main_menu():
    # 한 번만 DB 경로 입력받기
    db_path = input("DB 파일 경로를 지정해주세요: ")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    while True:
        print("\n메뉴:")
        print("1. 시간 지정 필터링")
        print("2. Windows 11 JSON 데이터 처리")
        print("3. Windows 10 JSON 데이터 처리")
        print("4. 다른 이름으로 저장하고 종료")
        choice = input("원하는 작업을 선택하세요 (1-4): ")
        if choice == '1':
            filter_and_save_db(cursor)
        elif choice == '2':
            win11_json_file_path = r"win11_output.json"
            deleted_rows_win11 = process_json_file(win11_json_file_path, cursor)
            print(f"Window11 기본 데이터가 {deleted_rows_win11}개 삭제되었습니다.")
        elif choice == '3':
            win10_json_file_path = r"win10_output.json"
            deleted_rows_win10 = process_json_file(win10_json_file_path, cursor)
            print(f"Window10 기본 데이터가 {deleted_rows_win10}개 삭제되었습니다.")
        elif choice == '4':
            file_name = input("저장할 새 파일 이름을 입력해주세요 (확장자 .db 포함): ")
            save_database_as(file_name, conn, db_path)
            break
        else:
            print("잘못된 입력입니다. 다시 선택해주세요.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    main_menu()
