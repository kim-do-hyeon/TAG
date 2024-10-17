import os
from apps import db  # Ensure you're importing db correctly from your app
from apps.authentication.models import Upload_Case, Normalization
from apps.case.case_normalization_std import *
import sqlite3
import pandas as pd

from apps.manager.progress_bar import ProgressBar

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
    progress_bar = ProgressBar.get_instance()
    query_artifact_name = """
        SELECT artifact_name FROM artifact;
    """

    cursor.execute(query_artifact_name)
    artifact_names = [row[0] for row in cursor.fetchall()]

    increment = 60 / len(artifact_names)  # 90 - 10 = 80 for loop increments

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
                    # print(pivot_df.columns)

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
                        # print(f"Data successfully inserted into {safe_table_name} table.")
                        progress['message'] += f"Data successfully inserted into {safe_table_name} table.\n"
                        progress_bar.set_now_log(f"Data successfully inserted into {safe_table_name} table.")
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
        
        progress[case_id] = min(70, progress[case_id] + increment)
        progress_bar.set_progress(min(70, progress[case_id] + increment))

    ''' Remove System Files - Jihye Code '''
    remove_system_files(new_db_path, progress)
    progress[case_id] = 80
    progress_bar.set_progress(80)
    ''' Remove Keywords - Jihye Code '''
    remove_keywords(new_db_path, progress)
    progress[case_id] = 90
    progress_bar.set_progress(90)
    ''' Remove Win 10, 11 Basic Artifacts - Addy Code '''
    remove_win10_11_basic_artifacts(new_db_path, progress) 

    progress[case_id] = 100
    progress_bar.set_progress(100)

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
