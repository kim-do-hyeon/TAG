import os
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from flask import session
from apps import db
from apps.authentication.models import Upload_Case, FilteringData
from pyvis.network import Network
from apps.analyze.analyze_util import shorten_string, insert_char_enter

def analyze_case_filtering(data) :
    user = session.get('username')
    case_id = data['case_id']
    case_number = data['case_number']
    start_date_str = data['startDate']
    end_date_str = data['endDate']
    start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')
    start = pd.to_datetime(start_date) - timedelta(hours=9)
    end = pd.to_datetime(end_date) - timedelta(hours=9)
    case_number = Upload_Case.query.filter_by(id = case_number).first().case_number
    case_folder = os.path.join(os.getcwd(), "uploads", user, case_number)
    db_path = os.path.join(case_folder, "normalization.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    related_data = []

    tables_query = "SELECT name FROM sqlite_master WHERE type='table';"
    tables = pd.read_sql_query(tables_query, conn)['name'].tolist()
    for table in tables:
            if ("Windows" not  in table or "LogFile" not in table) \
                and ("Edge_Chromium_Web" in table \
                    or "Chrome_Web" in table \
                    or "Document" in table \
                    or "Recycle_Bin" in table \
                    or "MRU_Recent_Files_&_Folders" in table):
                
                columns = pd.read_sql_query(f"PRAGMA table_info('{table}');", conn)['name'].tolist()
                date_columns = [col for col in columns if 'Date' in col]
                if date_columns:
                    for date_col in date_columns:
                        query = f"SELECT * FROM '{table}';"
                        result_df = pd.read_sql_query(query, conn)
                        if date_col in result_df.columns:
                            try:
                                result_df[date_col] = pd.to_datetime(result_df[date_col], errors='coerce')
                                filtered_df = result_df[(result_df[date_col] >= pd.to_datetime(start)) & 
                                                        (result_df[date_col] <= pd.to_datetime(end))]
                                # 'artifact_id' 열을 제외한 데이터로 작업
                                if 'artifact_id' in filtered_df.columns:
                                    filtered_df = filtered_df.drop(columns=['artifact_id', 'artifact_version_id', 'artifact_name'])
                                
                                if not filtered_df.empty:
                                    for col in filtered_df.columns:
                                        values = filtered_df[col].dropna().unique()
                                        for value in values:
                                            related_data.append({
                                                'Table': table, 
                                                'Column': col, 
                                                'Value': value, 
                                                'Data': filtered_df.to_dict()  # artifact_id 제외 후 데이터
                                            })
                            except Exception as e:
                                print(f"테이블 '{table}'에서 열 '{col}'로 검색 중 오류 발생: {e}")
    net = Network(height="750px", width="100%", notebook=True)
    net.force_atlas_2based()
    for record in related_data :
        table = record['Table']
        data = record['Data']
        artifacts_dict = {
            "AmCache_File_Entries" : "Name",
            "AutoRun_Items" : "Trigger_Condition",
            "Chrome_Cookies" : "Host",
            "Chrome_Cache_Records" : "URL",
            "Chrome_Web_History" : "URL",
            "Chrome_Web_Visits" : "URL",
            "Edge_Chromium_Web_History" : "URL",
            "Edge_Chromium_Cookies" : "Host",
            "Edge_Chromium_Cache_Records" : "URL",
            "Edge_Chromium_Web_Visits" : "URL",
            "Jump_Lists" : "Data",
            "LNK_Files" : "Linked_Path",
            "PDF_Documents" : "Filename",
            "Recycle_Bin" : "File_Name",
            "MRU_Recent_Files_&_Folders" : "File/Folder_Link",
            "AmCache_Pnp_Devices" : "Inf",
            "Shellbags" : "Path",
            "System_Services" : "Service_Location",
            "USB_Devices" : "Friendly_Name",
            "Text_Documents" : "Filename"
        }

        hit_artfacts = '\n'.join([shorten_string(str(data[artifacts_dict[table]][index])) for index in data[artifacts_dict[table]].keys()])
        # 최상위 부모 노드는 테이블 이름
        root_title = (f"Root Node : {table}\nnumber of Hit artifact : {str(len(data[artifacts_dict[table]]))}\n"+
                    f"\nhit artifact :\n{hit_artfacts}")
        net.add_node(table, label=f"Table: {shorten_string(table)}", title=root_title, color="red", shape="ellipse", size=50)  # 테이블 이름을 최상위 부모로 설정
        
        # Data의 각 인덱스(예: 322)를 중간 부모 노드로 설정
        for index in data[artifacts_dict[table]].keys():
            index_node = f"{table}_index_{index}"
            index_node_title = (insert_char_enter(str(data[artifacts_dict[table]][index])+'\n\n') +
                                insert_char_enter(f"table : {table}\n") +
                                "columns : \n" + '\n'.join([col for col in data.keys()]))
            net.add_node(index_node, label=f"Index: {shorten_string(data[artifacts_dict[table]][index])}", title=index_node_title, color="orange", shape="ellipse", size=40)  # 중간 부모 노드 (각 인덱스)
            net.add_edge(table, index_node)  # 테이블 노드와 인덱스 노드 연결
            
            # 해당 인덱스 아래에 있는 각 열을 중간 부모 노드로 추가
            for col in data.keys():
                column_node = f"{table}_{col}_{index}"
                
                net.add_node(column_node, label=f"{shorten_string(str(data[col][index]))}", title=col+'\n'+insert_char_enter(str(data[col][index])), color="skyblue", shape="box", size=30)  # 중간 부모 노드 (각 컬럼)
                net.add_edge(index_node, column_node)  # 인덱스 노드와 컬럼 노드를 연결
                
                # 각 열의 값을 자식 노드로 추가
                # value = data[col][index]
                # child_node = f"{table}_value_{col}_{index}"
                # net.add_node(child_node, label=f"{shorten_string(str(value))}", color="pink", shape="box", size=50)  # 자식 노드
                # net.add_edge(column_node, child_node)  # 컬럼 노드와 값 노드를 연결
    # 네트워크 그래프를 HTML 파일로 저장
    output_file = os.path.join(case_folder, "Filter_" + str(start).replace(" ", "_").replace(":", "_") + "_to_" + str(end).replace(" ", "_").replace(":", "_") + ".html")

    # Write the HTML file with utf-8 encoding to avoid Unicode issues
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(net.generate_html())  # Generates the HTML and writes it with utf-8 encoding

    data = FilteringData(case_id = case_id,
                         start_time = str(start),
                         end_time = str(end),
                         filtering_data = output_file)
    db.session.add(data)
    db.session.commit()

    return output_file


def analyze_case_filtering_to_minutes(data):
    user = session.get('username')
    case_id = data['case_id']
    case_number = data['case_number']
    start_date_str = data['startDate']
    end_date_str = data['endDate']
    start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')
    start = pd.to_datetime(start_date) - timedelta(hours=9)
    end = pd.to_datetime(end_date) - timedelta(hours=9)
    case_number = Upload_Case.query.filter_by(id=case_number).first().case_number
    case_folder = os.path.join(os.getcwd(), "uploads", user, case_number)
    db_path = os.path.join(case_folder, "normalization.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    related_data = []

    # Calculate time difference and set interval
    time_diff = end - start
    if time_diff <= timedelta(minutes=10):
        interval = timedelta(minutes=1)  # 1분 간격
    elif time_diff <= timedelta(hours=1):
        interval = timedelta(minutes=5)  # 5분 간격
    else:
        interval = timedelta(minutes=10)  # 10분 간격

    # Function to generate time slots
    def generate_time_slots(start, end, interval):
        slots = []
        current_time = start
        while current_time < end:
            next_time = current_time + interval
            if next_time > end:
                next_time = end
            slots.append((current_time, next_time))
            current_time = next_time
        return slots

    time_slots = generate_time_slots(start, end, interval)

    # Query all tables and filter data
    tables_query = "SELECT name FROM sqlite_master WHERE type='table';"
    tables = pd.read_sql_query(tables_query, conn)['name'].tolist()
    for table in tables:
        if ("Windows" not in table or "LogFile" not in table) \
                and ("Edge_Chromium_Web" in table \
                     or "Chrome_Web" in table \
                     or "Document" in table \
                     or "Recycle_Bin" in table \
                     or "MRU_Recent_Files_&_Folders" in table):

            columns = pd.read_sql_query(f"PRAGMA table_info('{table}');", conn)['name'].tolist()
            date_columns = [col for col in columns if 'Date' in col]
            if date_columns:
                for date_col in date_columns:
                    query = f"SELECT * FROM '{table}';"
                    result_df = pd.read_sql_query(query, conn)
                    if date_col in result_df.columns:
                        try:
                            result_df[date_col] = pd.to_datetime(result_df[date_col], errors='coerce')
                            for slot_start, slot_end in time_slots:
                                filtered_df = result_df[(result_df[date_col] >= pd.to_datetime(slot_start)) &
                                                        (result_df[date_col] <= pd.to_datetime(slot_end))]
                                if 'artifact_id' in filtered_df.columns:
                                    filtered_df = filtered_df.drop(columns=['artifact_id', 'artifact_version_id', 'artifact_name'])

                                if not filtered_df.empty:
                                    for col in filtered_df.columns:
                                        values = filtered_df[col].dropna().unique()
                                        for value in values:
                                            related_data.append({
                                                'Table': table,
                                                'Column': col,
                                                'Value': value,
                                                'Data': filtered_df.to_dict(),
                                                'Time Slot': (slot_start, slot_end)  # 추가된 시간 간격
                                            })
                        except Exception as e:
                            print(f"테이블 '{table}'에서 열 '{col}'로 검색 중 오류 발생: {e}")

    # Create network graph
    net = Network(height="750px", width="100%", notebook=True)
    net.force_atlas_2based()

    for record in related_data:
        time_slot = record['Time Slot']
        table = record['Table']
        data = record['Data']
        slot_label = f"{time_slot[0]} - {time_slot[1]}"

        # Check if time slot node exists
        if not any(node['id'] == slot_label for node in net.nodes):
            net.add_node(slot_label, label=f"Time Slot: {shorten_string(slot_label)}", title=slot_label, color="red", shape="ellipse", size=50)

        artifacts_dict = {
            "AmCache_File_Entries": "Name",
            "AutoRun_Items": "Trigger_Condition",
            "Chrome_Cookies": "Host",
            "Chrome_Cache_Records": "URL",
            "Chrome_Web_History": "URL",
            "Chrome_Web_Visits": "URL",
            "Edge_Chromium_Web_History": "URL",
            "Edge_Chromium_Cookies": "Host",
            "Edge_Chromium_Cache_Records": "URL",
            "Edge_Chromium_Web_Visits": "URL",
            "Jump_Lists": "Data",
            "LNK_Files": "Linked_Path",
            "PDF_Documents": "Filename",
            "Recycle_Bin": "File_Name",
            "MRU_Recent_Files_&_Folders": "File/Folder_Link",
            "AmCache_Pnp_Devices": "Inf",
            "Shellbags": "Path",
            "System_Services": "Service_Location",
            "USB_Devices": "Friendly_Name",
            "Text_Documents": "Filename"
        }

        hit_artifacts = '\n'.join([shorten_string(str(data[artifacts_dict[table]][index])) for index in data[artifacts_dict[table]].keys()])
        table_title = (f"Table: {table}\nTime Slot: {slot_label}\nNumber of Hit Artifacts: {len(data[artifacts_dict[table]])}\n" +
                       f"Hit Artifacts:\n{hit_artifacts}")
        net.add_node(f"{table}_{slot_label}", label=f"Table: {shorten_string(table)}", title=table_title, color="orange", shape="ellipse", size=40)
        net.add_edge(slot_label, f"{table}_{slot_label}")  # Connect the time slot node to the table node

        for index in data[artifacts_dict[table]].keys():
            index_node = f"{table}_index_{index}_{slot_label}"
            index_node_title = (insert_char_enter(str(data[artifacts_dict[table]][index]) + '\n\n') +
                                insert_char_enter(f"Table: {table}\n") +
                                "Columns:\n" + '\n'.join([col for col in data.keys()]))
            net.add_node(index_node, label=f"Index: {shorten_string(data[artifacts_dict[table]][index])}", title=index_node_title, color="skyblue", shape="box", size=30)
            net.add_edge(f"{table}_{slot_label}", index_node)  # Connect the table node to the index node

            for col in data.keys():
                column_node = f"{table}_{col}_{index}_{slot_label}"
                net.add_node(column_node, label=f"{shorten_string(str(data[col][index]))}", title=col + '\n' + insert_char_enter(str(data[col][index])), color="lightgreen", shape="box", size=20)
                net.add_edge(index_node, column_node)  # Connect the index node to the column node

    output_file = os.path.join(case_folder, "Filter_" + str(start).replace(" ", "_").replace(":", "_") + "_to_" + str(end).replace(" ", "_").replace(":", "_") + ".html")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(net.generate_html())

    data = FilteringData(case_id=case_id,
                         start_time=str(start),
                         end_time=str(end),
                         filtering_data=output_file)
    db.session.add(data)
    db.session.commit()

    return output_file
