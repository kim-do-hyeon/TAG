import os
from apps import db  # Ensure you're importing db correctly from your app
from apps.authentication.models import Upload_Case, Normalization
from apps.case.case_normalization_std import *
import sqlite3
import pandas as pd

def case_normalization(case_id, progress):
    db_instance = Upload_Case.query.filter_by(id=case_id).first()  # Renamed to avoid confusion with db session
    db_path = db_instance.file
    user = db_instance.user
    case_number = db_instance.case_number
    new_db_name = "normalization.db"
    new_db_path = os.path.join(os.getcwd(), "uploads", user, case_number, new_db_name )
    directory = os.path.dirname(new_db_path)
    # 디렉토리가 존재하지 않으면 생성
    if not os.path.exists(directory):
        os.makedirs(directory)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    progress[case_id] = 10
    query_artifact_name = """
        SELECT artifact_name FROM artifact;
    """

    cursor.execute(query_artifact_name)
    artifact_names = [row[0] for row in cursor.fetchall()]

    increment = 80 / len(artifact_names)  # 90 - 10 = 80 for loop increments

    # Iterate over each artifact name to create individual tables
    for artifact_name_normalization in artifact_names:
        query_artifact = """
            SELECT artifact_id
            FROM artifact
            WHERE artifact_name LIKE ?
        """

        cursor.execute(query_artifact, (f'%{artifact_name_normalization}%',))
        artifact_ids = [row[0] for row in cursor.fetchall()]

        if artifact_ids:
            query_version = """
                SELECT artifact_version_id, artifact_name, artifact_id
                FROM artifact_version
                WHERE artifact_id IN ({})
            """.format(','.join(['?'] * len(artifact_ids)))

            cursor.execute(query_version, artifact_ids)
            version_results = cursor.fetchall()

            version_data = [(row[0], row[1], row[2]) for row in version_results]

            if version_data:
                query_fragment = """
                    SELECT fragment_definition_id, name, artifact_version_id
                    FROM fragment_definition
                    WHERE artifact_version_id IN ({})
                """.format(','.join(['?'] * len([row[0] for row in version_data])))

                cursor.execute(query_fragment, [row[0] for row in version_data])
                fragment_results = cursor.fetchall()

                fragment_data = [(row[0], row[1], row[2]) for row in fragment_results]
                if fragment_data:
                    query_hit_fragment = """
                        SELECT hit_id, value, fragment_definition_id
                        FROM hit_fragment
                        WHERE fragment_definition_id IN ({})
                    """.format(','.join(['?'] * len([row[0] for row in fragment_data])))

                    cursor.execute(query_hit_fragment, [row[0] for row in fragment_data])
                    hit_results = cursor.fetchall()

                    hit_data = [
                        (version[2], version[0], version[1], fragment[0], fragment[1], hit[0], hit[1])
                        for version in version_data
                        for fragment in fragment_data
                        if fragment[2] == version[0]
                        for hit in hit_results
                        if hit[2] == fragment[0]
                    ]
                    df = pd.DataFrame(hit_data, columns=[
                        'artifact_id', 'artifact_version_id', 'artifact_name', 
                        'fragment_definition_id', 'name', 'hit_id', 'value'
                    ])

                    # Pivot the DataFrame
                    pivot_df = df.pivot_table(
                        index=['artifact_id', 'artifact_version_id', 'artifact_name', 'hit_id'],
                        columns='name',
                        values='value',
                        aggfunc='first'
                    ).reset_index()

                    pivot_df.columns.name = None
                    pivot_df.columns = [f'"{col.replace(" ", "_")}"' for col in pivot_df.columns]

                    # Connect to the new database
                    new_conn = sqlite3.connect(new_db_path)
                    new_cursor = new_conn.cursor()

                    # Sanitize table name by replacing spaces and special characters
                    safe_table_name = artifact_name_normalization.replace(' ', '_').replace('-', '_').replace('$', '').replace('(', '').replace(')', '')

                    pivot_df = exclude_column(pivot_df, safe_table_name)
                    print(pivot_df.columns)

                    # Create table with sanitized table name
                    create_table_query = f"""
                    CREATE TABLE IF NOT EXISTS "{safe_table_name}" (
                        {', '.join([f'{col} TEXT' for col in set(pivot_df.columns)])}
                    )
                    """
                    try:
                        new_cursor.execute(create_table_query)
                    except sqlite3.OperationalError as e:
                        print(f"Error creating table {safe_table_name}: {e}")
                        continue  # Skip to the next artifact if table creation fails

                    # Insert data into the correct table
                    insert_query = f"""
                    INSERT INTO "{safe_table_name}" ({', '.join(pivot_df.columns)})
                    VALUES ({', '.join(['?'] * len(pivot_df.columns))})
                    """

                    try:
                        new_cursor.executemany(insert_query, pivot_df.values.tolist())
                        new_conn.commit()
                        print(f"Data successfully inserted into {safe_table_name} table.")
                    except sqlite3.OperationalError as e:
                        print(f"Error inserting data into {safe_table_name}: {e}")

                    # Close connection to the new database
                    new_cursor.close()
                    new_conn.close()
                else:
                    print("No fragment_definition_id found in fragment_definition table.")
            else:
                print("No artifact_version_id found in artifact_version table.")
        else:
            print(f"No artifact_id containing '{artifact_name_normalization}' found in artifact table.")
        
        progress[case_id] = min(90, progress[case_id] + increment)

    ''' Remove System Files '''
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
    progress[case_id] = 100

    # Create a new Normalization entry
    new_normalization_data = Normalization(
        normalization_definition=case_id,
        file=new_db_path,
        result="Success",
        artifacts_names = str([name.replace(' ', '_').replace('-', '_').replace('$', '').replace('(', '').replace(')', '') for name in artifact_names])
    )
    
    # Use the correct session object to add and commit the new data
    db.session.add(new_normalization_data)
    db.session.commit()

    return new_db_path


def exclude_column(df, table) :
    exclude_dict = {
        "common" : [
            '"artifact_version_id"',
            '"artifact_id"'
            ],
        "LogFile_Analysis" : [
            '"Current_Short_File_Name"',
            '"Original_Short_File_Name"'
        ]
    }
    # 공통적으로 제외할 열
    columns_to_exclude = exclude_dict.get("common", [])
    
    # 특정 테이블에 대해 추가적으로 제외할 열
    if table in exclude_dict:
        columns_to_exclude.extend(exclude_dict[table])
    
    # DataFrame에서 제외할 열 제거
    df = df.drop(columns=[col for col in columns_to_exclude if col in df.columns], errors='ignore')
    
    return df
