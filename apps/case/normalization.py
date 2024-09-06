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

    query_artifact_name = """
        SELECT artifact_name FROM artifact;
    """

    cursor.execute(query_artifact_name)
    artifact_names = [row[0].split(" ")[0] for row in cursor.fetchall()]
    artifact_names = list(set(artifact_names))
    print(artifact_names)

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

                    pivot_df = df.pivot_table(
                        index=['artifact_id', 'artifact_version_id', 'artifact_name', 'hit_id'],
                        columns='name',
                        values='value',
                        aggfunc='first'
                    ).reset_index()

                    pivot_df.columns.name = None
                    pivot_df.columns = [f'"{col.replace(" ", "_")}"' for col in pivot_df.columns]

                    new_conn = sqlite3.connect(new_db_path)
                    new_cursor = new_conn.cursor()

                    # Check existing columns to avoid duplicates
                    create_table_query = f"""
                    CREATE TABLE IF NOT EXISTS {artifact_name_normalization} (
                        {', '.join([f'{col} TEXT' for col in set(pivot_df.columns)])}
                    )
                    """
                    try:
                        new_cursor.execute(create_table_query)
                    except sqlite3.OperationalError as e:
                        print(f"Error creating table {artifact_name_normalization}: {e}")
                        continue  # Skip to the next artifact if table creation fails

                    # Insert data into the correct table
                    insert_query = f"""
                    INSERT INTO {artifact_name_normalization} ({', '.join(pivot_df.columns)})
                    VALUES ({', '.join(['?'] * len(pivot_df.columns))})
                    """

                    new_cursor.executemany(insert_query, pivot_df.values.tolist())

                    new_conn.commit()
                    new_cursor.close()
                    new_conn.close()
                    print(f"Data successfully inserted into {artifact_name_normalization} table.")
                else:
                    print("No fragment_definition_id found in fragment_definition table.")
            else:
                print("No artifact_version_id found in artifact_version table.")
        else:
            print(f"No artifact_id containing '{artifact_name_normalization}' found in artifact table.")

    cursor.close()
    conn.close()

    # Create a new Normalization entry
    new_normalization_data = Normalization(
        normalization_definition=case_id,
        file=new_db_path,
        result="Success",
        artifacts_names = str(artifact_names)
    )
    
    # Use the correct session object to add and commit the new data
    db.session.add(new_normalization_data)
    db.session.commit()

    return new_db_path