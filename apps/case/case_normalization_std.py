import os, pandas, sqlite3
from datetime import datetime
import json
import glob

from apps.case.case_normalization_std_util import *
from apps.manager.progress_bar import *

def remove_system_files(db_path, progress) :
    progressBar = ProgressBar.get_instance()
    removes_json_path = os.path.join(os.getcwd(), "apps", "case", "STD_Exclude", "system_files.json")
    with open(removes_json_path, "r", encoding='utf8') as f:
        f = f.read()
        json_data = json.loads(f)
    # removal_target 딕셔너리 선언
    removal_target = json_data['removal_target']
    file_paths = [
        "dll.txt",
        "exe.txt",
        "msc.txt"
    ]
    removes = []
    for file_path in file_paths:
        file_path = os.path.join(os.getcwd(), "apps", "case", "STD_Exclude", file_path)
        removes.extend(load_file(file_path))
    
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
        progress['message'] += f"{table} 테이블 삭제 전: {before_remove} / 삭제 후: {after_remove} 개의 행으로 감소하였습니다.\n"
        progressBar.append_log(f"{table} 테이블 삭제 전: {before_remove} / 삭제 후: {after_remove} 개의 행으로 감소하였습니다.\n")
        # print(f"{table} 테이블 삭제 전: {before_remove} / 삭제 후: {after_remove} 개의 행으로 감소하였습니다.")

    # print(f"전체 행 {before_total} 중에서 {before_total - after_taotal} 개의 행이 삭제되었습니다.\n현재 {after_taotal} 개의 행이 존재합니다.")
    progress['message'] += f"전체 행 {before_total} 중에서 {before_total - after_taotal} 개의 행이 삭제되었습니다.\n현재 {after_taotal} 개의 행이 존재합니다.\n"
    progressBar.append_log(f"전체 행 {before_total} 중에서 {before_total - after_taotal} 개의 행이 삭제되었습니다.\n현재 {after_taotal} 개의 행이 존재합니다.\n")
    conn.commit()
    conn.close()

def remove_keywords(new_db_path, progress) :
    progressBar = ProgressBar.get_instance()
    
    exclude_apps  = ['hwp', 'acrobat', 'office']
    app_template_path = os.path.join(os.getcwd(), 'apps', 'case', 'STD_Exclude', 'Apps_Templates')
    load_app_list = []
    for exclude_app in exclude_apps :
        load_app_list.extend(glob.glob(f'{app_template_path}{exclude_app}*.txt'))
    
    removes = []
    for file_path in load_app_list :
        removes.extend(load_file(file_path))
    
    # keywords.json 로드
    # 테이블명, 컬럼, 키워드 정보가 저장되어 있음
    removes_json_path = os.path.join(os.getcwd(), "apps", "case", "STD_Exclude", "keywords_v2.json")

    with open(removes_json_path, "r", encoding='utf8') as f:
        f = f.read()
        json_data = json.loads(f)

    # removal_target 딕셔너리 선언
    removal_target = json_data['removal_target']

    # 첫 번째 딕셔너리: 'table'이 key, 'column'이 value
    table_column_dict = {item['table']: item['column'] for item in removal_target}
    # 두 번째 딕셔너리: 'table'이 key, 'values'가 value
    #table_values_dict = {item['table']: item['values'] for item in removal_target}

    # removal_target에 저장된 테이블 명 저장
    remove_table_list = list(table_column_dict.keys())

    conn = sqlite3.connect(new_db_path)

    # 현재 케이스 파일의 테이블명 추출
    db_cursor = conn.cursor()
    db_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

    db_table_list = []
    for row in db_cursor:
        db_table_list.append(row[0])

    # 제거 파일 수 기록용
    before_total = 0
    after_taotal = 0
    total = 0

    # 현재 케이스 파일의 각 테이블 별 필요 없는 row 제거
    for table in db_table_list:
        # 삭제를 진행하지 않더라도 total을 위해 해당 테이블 row 수 저장
        db_cursor.execute(f'SELECT * FROM "{table}"')
        res = db_cursor.fetchall()
        total += len(res)

        # json에 없는 테이블이라면 pass
        if table not in remove_table_list:
            continue

        # 딕셔너리로부터 target 컬럼 가져옴
        target_column = table_column_dict[table]
        if target_column == '':
            continue

        # 삭제 전후 비교 위해 삭제 전 row 수 저장
        db_cursor.execute(f'SELECT "{target_column}" FROM "{table}"')
        res = db_cursor.fetchall()
        before_remove = len(res)

        # 삭제 진행
        delete_in_chunks(db_cursor, conn, removes, table, target_column)

        # 삭제 전후 비교 위해 삭제 전 row 수 저장
        db_cursor.execute(f'SELECT "{target_column}" FROM "{table}"')
        res = db_cursor.fetchall()
        after_remove = len(res)

        before_total += before_remove
        after_taotal += after_remove

        # 변경 사항 출력
        # print(f"{table} 테이블 삭제 전: {before_remove} / 삭제 후: {after_remove} 개의 행으로 감소하였습니다.")
        progress['message'] += f"{table} 테이블 삭제 전: {before_remove} / 삭제 후: {after_remove} 개의 행으로 감소하였습니다.\n"
        progressBar.append_log(f"{table} 테이블 삭제 전: {before_remove} / 삭제 후: {after_remove} 개의 행으로 감소하였습니다.\n")
        
    # print(f"전체 행 {total} 중에서 {before_total - after_taotal} 개의 행이 삭제되었습니다.\n현재 {total - before_total + after_taotal} 개의 행이 존재합니다.")
    progress['message'] += f"전체 행 {before_total} 중에서 {before_total - after_taotal} 개의 행이 삭제되었습니다.\n현재 {after_taotal} 개의 행이 존재합니다.\n"
    progressBar.append_log(f"전체 행 {before_total} 중에서 {before_total - after_taotal} 개의 행이 삭제되었습니다.\n현재 {after_taotal} 개의 행이 존재합니다.\n")
    
def process_json_file(json_file_path, cursor, progress):
    progressBar = ProgressBar.get_instance()
    max_sql_variables=999
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
            # print(f'Table "{table}": {deleted_rows} rows deleted, {final_row_count} rows remaining.')
            progress['message'] += f'Table "{table}": {deleted_rows} rows deleted, {final_row_count} rows remaining.\n'
            progressBar.append_log(f'Table "{table}": {deleted_rows} rows deleted, {final_row_count} rows remaining.\n')
        except sqlite3.OperationalError as e:
            print(f'Skipping table "{table}" due to error: {e}')
        except sqlite3.DatabaseError as e:
            print(f"Error with data in table '{table}': {e}")
    return deleted_rows_total

def remove_win10_11_basic_artifacts(db_path, progress) :
    progressBar = ProgressBar.get_instance()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try :
        win11_json_file_path = os.path.join(os.getcwd(), "apps", "case", "STD_Exclude", "win11_output.json")
        deleted_rows_win11 = process_json_file(win11_json_file_path, cursor, progress)
        print(f"Window11 기본 데이터가 {deleted_rows_win11}개 삭제되었습니다.")
    except Exception as e :
        print("Windows 11 Error / " + str(e))
    
    try :
        win10_json_file_path = os.path.join(os.getcwd(), "apps", "case", "STD_Exclude", "win10_output.json")
        deleted_rows_win10 = process_json_file(win10_json_file_path, cursor, progress)
        print(f"Window10 기본 데이터가 {deleted_rows_win10}개 삭제되었습니다.")
    except Exception as e :
        print("Windows 10 Error / " + str(e))
    conn.commit()
    conn.close()
    