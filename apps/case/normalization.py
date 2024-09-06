import re, json
import os
from apps import db  # Ensure you're importing db correctly from your app
from apps.authentication.models import Upload_Case, Normalization
import sqlite3
import pandas as pd

def case_normalization(case_id):
    db_instance = Upload_Case.query.filter_by(id=case_id).first()  # Renamed to avoid confusion with db session
    db_path = db_instance.file
    db_name = db_path.split("/")[-1]
    new_db_name = "normalization_"
    new_db_path = "/".join(db_path.split("/")[:-1]) + "/" + new_db_name + db_name.split(".")[0] + ".db"
    print(new_db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 모든 artifact_name을 가져옴
    query_for_get_artifact = '''
    SELECT artifact_name
    FROM artifact
    '''
    cursor.execute(query_for_get_artifact)
    artifact_names = [row[0] for row in cursor.fetchall()]

    print(artifact_names)

    # 새로운 데이터베이스 연결
    new_conn = sqlite3.connect(new_db_path)
    new_cursor = new_conn.cursor()

    # SQL 테이블 이름으로 사용할 수 있도록 artifact_name을 변환하는 함수
    def sanitize_table_name(name):
        # 모든 비문자(\W)와 숫자로 시작하는 경우(^\d)를 _로 대체하고, 띄어쓰기도 _로 대체
        return re.sub(r'\s+', '_', re.sub(r'\W|^(?=\d)', '_', name)).replace('/', '_')

    # 각 테이블의 컬럼 정보를 저장할 딕셔너리
    table_columns = {}

    # 각 artifact_name에 대해 처리
    for artifact_name in artifact_names:
        query_artifact = """
        SELECT artifact_id
        FROM artifact
        WHERE artifact_name = ?
        """
        cursor.execute(query_artifact, (artifact_name,))
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

                    pivot_df = df.pivot_table(
                        index=['artifact_id', 'artifact_version_id', 'artifact_name', 'hit_id'],
                        columns='name',
                        values='value',
                        aggfunc='first'
                    ).reset_index()

                    pivot_df.columns.name = None

                    # 중복된 열 이름 처리 (대소문자 구분 없이)
                    pivot_df.columns = [f'"{col.replace(" ", "_").replace("/", "_")}"' for col in pivot_df.columns]
                    seen = set()
                    unique_columns = []
                    for col in pivot_df.columns:
                        col_name = col.strip('"').lower()
                        if col_name not in seen:
                            seen.add(col_name)
                            unique_columns.append(col)
                    
                    # 테이블 이름을 artifact_name 기반으로 생성
                    table_name = sanitize_table_name(artifact_name)

                    create_table_query = f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        {', '.join([f'{col} TEXT' for col in unique_columns])}
                    )
                    """
                    new_cursor.execute(create_table_query)

                    insert_query = f"""
                    INSERT INTO {table_name} ({', '.join(unique_columns)})
                    VALUES ({', '.join(['?'] * len(unique_columns))})
                    """

                    new_cursor.executemany(insert_query, pivot_df[unique_columns].values.tolist())
                    new_conn.commit()
                    print(f"Data for artifact '{artifact_name}' successfully inserted into table '{table_name}'.")

                    # 테이블의 컬럼 이름을 리스트로 저장
                    table_columns[table_name] = unique_columns
                else:
                    print(f"No fragment_definition_id found for artifact '{artifact_name}' in fragment_definition table.")
            else:
                print(f"No artifact_version_id found for artifact '{artifact_name}' in artifact_version table.")
        else:
            print(f"No artifact_id found for artifact '{artifact_name}' in artifact table.")

    # 커서와 연결 닫기
    new_cursor.close()
    new_conn.close()
    cursor.close()
    conn.close()

    # 컬럼 정보를 JSON 파일로 저장
    with open('table_columns.json', 'w') as json_file:
        json.dump(table_columns, json_file, indent=4)
    
    

    # Create a new Normalization entry
    new_normalization_data = Normalization(
        normalization_definition=case_id,
        file=new_db_path,
        result="Success"
    )
    
    # Use the correct session object to add and commit the new data
    db.session.add(new_normalization_data)
    db.session.commit()

    return new_db_path