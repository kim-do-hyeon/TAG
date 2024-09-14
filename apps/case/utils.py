import os
import json
from flask import current_app

def load_query_data_from_user_folder(username, case_id):
    user_folder = os.path.join(current_app.root_path, 'user_folder', username, str(case_id))
    print('[*] load query from user_folder: ', user_folder)
    if not os.path.exists(user_folder):
        return None, None, None
    query_file = os.path.join(user_folder, 'queries.json')
    if not os.path.exists(query_file):
        return None, None, None
    with open(query_file, 'r', encoding='utf-8') as f:
        query_data = json.load(f)
    return_list = []
    for data in query_data :
        query = data.get('query')
        tables = data.get('tables')
        response = data.get('response')
        return_list.append([query, tables, response])
    return return_list
    