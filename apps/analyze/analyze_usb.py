import os, sqlite3, re
import numpy as np
import pandas as pd
from apps.authentication.models import Upload_Case
from pyvis.network import Network

def shorten_string(s) :
    if s == None :
        return "0"
    if len(s) > 40 :
        return s[0:35] + '...'
    else :
        return s

def insert_char_enter(string):
    return '\n'.join([string[i:i+60] for i in range(0, len(string), 60)])


def usb_connection(db_path, case_id, username, progress):
    case_number = Upload_Case.query.filter_by(id = case_id).first().case_number
    case_folder = os.path.join(os.getcwd(), "uploads", username, case_number)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    related_data = []
    times = []
    cursor = conn.cursor()
    query = f"SELECT * FROM 'USB_Devices';"
    result_df = pd.read_sql_query(query, conn)
    result_df['Last_Connected_Date/Time_-_UTC_(yyyy-mm-dd)'] = pd.to_datetime(result_df['Last_Connected_Date/Time_-_UTC_(yyyy-mm-dd)'], errors='coerce')
    result_df['Last_Removal_Date/Time_-_UTC_(yyyy-mm-dd)'] = pd.to_datetime(result_df['Last_Removal_Date/Time_-_UTC_(yyyy-mm-dd)'], errors='coerce')
    result = result_df.groupby('Serial_Number').agg({
        'Last_Connected_Date/Time_-_UTC_(yyyy-mm-dd)': 'min',
        'Last_Removal_Date/Time_-_UTC_(yyyy-mm-dd)': 'max',
        'Friendly_Name': 'first'
    }).reset_index()
    filtered_result = result[(result['Last_Connected_Date/Time_-_UTC_(yyyy-mm-dd)'].notna()) & 
                    (result['Last_Removal_Date/Time_-_UTC_(yyyy-mm-dd)'].notna()) & 
                    (result['Friendly_Name'].notna())]

    for index, row in filtered_result.iterrows():
        times.append([str(row['Friendly_Name']), str(row['Last_Connected_Date/Time_-_UTC_(yyyy-mm-dd)']), str(row['Last_Removal_Date/Time_-_UTC_(yyyy-mm-dd)'])])
    times_data = (list(set(tuple(time) for time in times)))
    print(times_data)

    tables_query = "SELECT name FROM sqlite_master WHERE type='table';"
    tables = pd.read_sql_query(tables_query, conn)['name'].tolist()

    for name, start, end in times_data:
        print(name, start, end)
        usb_data = []
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
                                            usb_data.append({
                                                'Table': table, 
                                                'Column': col, 
                                                'Value': value, 
                                                'Data': filtered_df.to_dict()  # artifact_id 제외 후 데이터
                                            })
                            except Exception as e:
                                print(f"테이블 '{table}'에서 열 '{col}'로 검색 중 오류 발생: {e}")
        related_data.append(usb_data)

    print(len(related_data))

    column_value_to_node = {}
    output_files = []
    for usb_index, usb_data in enumerate(related_data) :
        net = Network(height="750px", width="100%", notebook=True)
        net.force_atlas_2based()
        for record in usb_data :
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
                "USB_Devices" : "Friendly_Name"
            }

            hit_artfacts = '\n'.join([shorten_string(str(data[artifacts_dict[table]][index])) for index in data[artifacts_dict[table]].keys()])
            # 최상위 부모 노드는 테이블 이름
            root_title = (f"Root Node : {table}\nnumber of Hit artifact : {str(len(data[artifacts_dict[table]]))}\n"+
                        f"\nhit artifact :\n{hit_artfacts}")
            net.add_node(table, label=f"Table: {shorten_string(table)}", title=root_title, color="red", shape="ellipse", size=50)  # 테이블 이름을 최상위 부모로 설정
            print(table)
            
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
        output_file = os.path.join(case_folder, "USB_" + str(times_data[usb_index][0]) + ".html")

        # Write the HTML file with utf-8 encoding to avoid Unicode issues
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(net.generate_html())  # Generates the HTML and writes it with utf-8 encoding

        print(f"Saved graph to {output_file}")
        output_files.append(output_file)
    

    # 데이터베이스 연결 종료
    conn.close()
    return output_files
