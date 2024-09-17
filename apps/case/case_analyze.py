from apps.authentication.models import Normalization
import sqlite3

def get_table_names(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return tables

def fetch_all_records(db_path, table_names):
    record_counts = []
    for i in table_names :
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            query = f"SELECT * FROM {i};"
            cursor.execute(query)
            records = cursor.fetchall()
            cursor.close()
            conn.close()
            record_counts.append(len(records))
        except sqlite3.Error as e:
            print(f"Error fetching records: {e}")
    return record_counts

def case_analyze_view(user_case) :
    user_case_original_number = user_case.id
    normalization_case = Normalization.query.filter_by(normalization_definition = user_case_original_number).first()
    normalization_db_file = normalization_case.file

    table_names = (get_table_names(normalization_db_file))
    # record_counts = fetch_all_records(normalization_db_file, table_names)
    return table_names