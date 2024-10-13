import os, pandas, sqlite3
from apps.case.case_normalization_std_util import *

def remove_system_files(db_path) :
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

        print(f"{table} 테이블 삭제 전: {before_remove} / 삭제 후: {after_remove} 개의 행으로 감소하였습니다.")

    print(f"전체 행 {before_total} 중에서 {before_total - after_taotal} 개의 행이 삭제되었습니다.\n현재 {after_taotal} 개의 행이 존재합니다.")
    conn.commit()
    conn.close()

def remove_keywords(new_db_path) :
    # keywords.json 로드
    # 테이블명, 컬럼, 키워드 정보가 저장되어 있음
    removes_json_path = os.path.join(os.getcwd(), "apps", "case", "STD_Exclude", "keywords.json")

    with open(removes_json_path, "r", encoding='utf8') as f:
        f = f.read()
        json_data = json.loads(f)

    # removal_target 딕셔너리 선언
    removal_target = json_data['removal_target']

    # 첫 번째 딕셔너리: 'table'이 key, 'column'이 value
    table_column_dict = {item['table']: item['column'] for item in removal_target}
    # 두 번째 딕셔너리: 'table'이 key, 'values'가 value
    table_values_dict = {item['table']: item['values'] for item in removal_target}

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
        
        # 지워야 할 키워드 리스트 removes에 저장
        removes = table_values_dict[table]
        if len(removes) < 1:
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
        print(f"{table} 테이블 삭제 전: {before_remove} / 삭제 후: {after_remove} 개의 행으로 감소하였습니다.")

    print(f"전체 행 {total} 중에서 {before_total - after_taotal} 개의 행이 삭제되었습니다.\n현재 {total - before_total + after_taotal} 개의 행이 존재합니다.")

