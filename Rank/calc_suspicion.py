import sqlite3
import json
from datetime import datetime

# 데이터베이스 연결
db_path = r""
conn = sqlite3.connect(db_path)
db_cursor = conn.cursor()

# UsnJrnl, Logfile_Analysis, 문서 테이블 에서 문서 파일 추출
# docs_target_table = {
#     "UsnJrnl":["File_Name", "MFT_Record_Number"],
#     "Logfile_Analysis":["Original_File_Name", "Current_File_Name", "MFT_Record_Number"],
#     "PDF_Documents":["Filename"],
#     "Microsoft_Excel_Documents":["Filename"],
#     "Microsoft_PowerPoint_Documents":["Filename"],
#     "Microsoft_Word_Documents":["Filename"],
#     "Hangul_Word_Processor":["File_Name"]
# }

# 수정) UsnJrnl, Logfile_Analysis 에서만 문서 파일 추출
docs_target_table = {
    "UsnJrnl":["File_Name", "MFT_Record_Number"],
    "LogFile_Analysis":["Original_File_Name", "Current_File_Name", "MFT_Record_Number"]
}

# 현재 케이스 파일의 테이블 목록 추출
db_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
res = db_cursor.fetchall()
db_table_list = [row[0] for row in res]
# 필수 테이블이 현재 케이스 파일에 없다면 프로그램 종료
for necessary_table in docs_target_table.keys():
    if necessary_table not in db_table_list:
        print(f"프로그램 실행에 필요한 테이블 {necessary_table} 이 존재하지 않습니다. 프로그램을 종료합니다.")
        exit()

docs_formats = ["hwp", "docx", "pptx", "pdf", "xlsx", "zip"] # 문서 파일 포맷 정의
docs_files_tmp = set([])

# LNK와, Rename 이벤트들을 1초 단위로 그룹화
valid_types = ["LNK_Event_UsnJrnl", "Rename_UsnJrnl", "Rename_Logfile", "LNK_Event_LogFile", "Rename_UsnJrnl", "Rename_Logfile"]

# Function to filter 1-second unique events for valid types
def filter_first_per_second(data):
    for item in data:
        seen_timestamps = {}
        filtered_connections = []
        for conn in item["connection"]:
            # Extract and truncate timestamp to 1-second precision
            ts = datetime.strptime(conn["timestamp"], "%Y-%m-%d %H:%M:%S.%f")
            ts_key = ts.strftime("%Y-%m-%d %H:%M:%S")
            
            # Process valid types with 1-second grouping
            if conn["type"] in valid_types:
                if conn["type"] not in seen_timestamps:
                    seen_timestamps[conn["type"]] = set()
                # Add the first occurrence of the type for each second
                if ts_key not in seen_timestamps[conn["type"]]:
                    seen_timestamps[conn["type"]].add(ts_key)
                    filtered_connections.append(conn)
            else:
                # For invalid types, keep all entries
                filtered_connections.append(conn)
        
        # Replace connection with filtered list
        item["connection"] = filtered_connections
    return data

for table, cols in docs_target_table.items():
    cols_query = '", "'.join(cols)

    like_conditions = ""
    file_cols = []
    for col in cols:
        if "name" in col.lower():
            file_cols.append(col)
    for i in range(len(file_cols)):
        like_conditions = like_conditions + ' OR '.join([f'"{file_cols[i]}" LIKE ?' for _ in docs_formats])
        if len(file_cols) > 1 and i < len(file_cols)-1:
            like_conditions = like_conditions + ' OR'

    if table == "LogFile_Analysis":
        sql_query = f'SELECT "{cols_query}", File_Operation FROM {table} WHERE {like_conditions} AND MFT_Record_Number IS NOT NULL;'
    else:
        sql_query = f'SELECT "{cols_query}" FROM {table} WHERE {like_conditions} AND MFT_Record_Number IS NOT NULL;'
    like_values = [f'%.{value}' for value in docs_formats] * len(file_cols)
    db_cursor.execute(sql_query, like_values)

    for row in db_cursor:
        docs_files_tmp.add(row)

docs_files = set([]) # 최종적으로 문서 이름, MFT_Record_Number 저장하는 set
for doc in docs_files_tmp:
    if len(doc) == 4: # Logfile_Analysis 에서 끌고 온 것이라면
        MFT_Recoed_Num = doc[2]
        if doc[3] == 'Rename':
            # file_name = [doc[0], doc[1]]
            file_name = [doc[1]]
        elif doc[3] == 'Delete':
            file_name = [doc[0]]
        elif doc[3] == 'Create' or doc[3] == 'Move':
            file_name = [doc[1]]
        for item in file_name:
            docs_files.add((item, MFT_Recoed_Num))
    else:
        docs_files.add(doc)

# 1) Rename
#   1. UsnJrnl에서 Rename reason이 있는 경우, Logfile_Analysis에 rename이 있는 경우 가져오기
rename_output_data = []
for doc_file in docs_files:
    doc = doc_file[0] # doc == 파일 이름만 가져옴
    temp = {
        "filename":doc,
        "connection":[]
    }
    # 1. UsnJrnl 에서 해당 파일에 대한 Rename Reason이 있는지 확인
    sql_query = f'SELECT "Timestamp_Date/Time_-_UTC_(yyyy-mm-dd)", Reason, hit_id FROM UsnJrnl WHERE File_Name LIKE "%{doc}" AND MFT_Record_Number = "{doc_file[1]}" AND Reason LIKE "%rename%" ;'
    db_cursor.execute(sql_query)
    for row in db_cursor:
        temp["connection"].append(
            {
                "timestamp":row[0],
                "type":"Rename_UsnJrnl",
                "main_data":row[1],
                "hit_id":row[2],
                "score":3.78
            }
        )

    # 2. Logfile_Analysis 에서 해당파일에 대한 Operation에 Rename이 있는지 확인
    sql_query = f'SELECT "Event_Date/Time_-_UTC_(yyyy-mm-dd)", hit_id FROM LogFile_Analysis WHERE (Original_File_Name LIKE "{doc}" OR Original_File_Name LIKE "{doc}") AND MFT_Record_Number = "{doc_file[1]}" AND File_Operation="Rename";'
    db_cursor.execute(sql_query)
    for row in db_cursor:
        temp["connection"].append(
            {
                "timestamp":row[0],
                "type":"Rename_Logfile",
                "main_data":"Logfile_Analysis File_Operation Rename",
                "hit_id":row[1],
                "score":3.78
            }
        )
    if len(temp["connection"]) > 1: # rename의 흔적이 존재할 때만 저장
        rename_output_data.append(temp)

# 1초 단위로 그룹화하여 저장
rename_output_data_grouped = filter_first_per_second(rename_output_data)
print("Rename scoring 완료")

# rename_output_path = r"./rename_score.json"
# with open(rename_output_path, "w", encoding="utf-8") as f:
#     json.dump(rename_output_data_grouped, f, indent=4, ensure_ascii=False, default=str)
# print("rename_score.json이 저장되었습니다.")


# 2) 과다 열람
#   1. 우선 UsnJrnl에서 문서이름 + .lnk 가 1초 내에 생성된 링크파일이 있는지 확인 후, 존재한다면 그 lnk 파일의 파일명과 모든 timestamp를 저장함.
#   2. 저장된 MFT_Record_Number로 Logfile도 끌고와서 timestamp 저장
#   3. Jump_List, LNK_Files 에서도 파일명+Timestamp를 cross checking 하여 파일에 대한 활동 조사하기
#   4. 최종적으로 1초 단위로 잘려진 원본 문서 파일, 문서 파일의 링크 파일의 UsnJrnl, LogFile_Analysis, LNK_Files, Jump_Lists 등으로 문서에 대한 접근 확인

time_format = '%Y-%m-%d %H:%M:%S.%f'

# UsnJrnl에서 문서 별로 링크 파일 확인
docs_files = [[doc, [mft]] for doc, mft in docs_files]

# 1. 문서 파일의 MFT_Record_Number와 이름 저장
jrnl_original_docs_MFT_name = {} 
jrnl_original_docs_MFT_time = {}

for index, doc_file in enumerate(docs_files):
    doc = doc_file[0] # 문서 파일 이름
    mft_record = doc_file[1][0] # MFT_Record_Number

    # i. 문서 원본 파일에 대한 정보만 조회
    sql_query = f'''
        SELECT "Timestamp_Date/Time_-_UTC_(yyyy-mm-dd)", MFT_Record_Number, File_Name
        FROM UsnJrnl 
        WHERE File_Name LIKE "%{doc}" AND MFT_Record_Number = "{mft_record}";
    '''
    db_cursor.execute(sql_query)
    
    for timestamp, mft, file_name in db_cursor:
        if mft not in jrnl_original_docs_MFT_name:
            jrnl_original_docs_MFT_name[mft] = file_name
            jrnl_original_docs_MFT_time[mft] = set()
        jrnl_original_docs_MFT_time[mft].add(timestamp)

# 2. 링크 파일 조회
for index, doc_file in enumerate(docs_files):
    doc = doc_file[0]  # 문서 파일 이름
    doc_title = doc.split('.')[0]  # "문서이름.lnk" 형태 처리

    # ii. 링크 파일 조회
    sql_query = f'''
    SELECT "Timestamp_Date/Time_-_UTC_(yyyy-mm-dd)", MFT_Record_Number, File_Name
    FROM UsnJrnl
    WHERE File_Name LIKE "%{doc}.lnk" OR File_Name LIKE "%{doc_title}.lnk";
    '''
    db_cursor.execute(sql_query)

    jrnl_lnk_docs = set(row for row in db_cursor)  # 링크 파일 정보 저장

    # iii. 링크 파일 매칭 및 시간 차 계산
    for lnk_timestamp, lnk_mft, lnk_file_name in jrnl_lnk_docs:
        lnk_doc_name = lnk_file_name.split('.lnk')[0]

        # 확장자 포함한 이름 탐색
        possible_original_names = [lnk_doc_name + '.' + ext for ext in docs_formats]
        possible_original_names.append(lnk_doc_name)

        # jrnl_original_docs_MFT_name에서 매칭
        matching_names = [
            key for key, value in jrnl_original_docs_MFT_name.items() 
            if value in possible_original_names
        ]
        
        if matching_names:  # 일치하는 이름이 있다면
            current_mft = matching_names[0]  # 해당 MFT 가져오기

            for original_time in jrnl_original_docs_MFT_time[current_mft]:
                original_doc_time = datetime.strptime(original_time, time_format)
                lnk_time = datetime.strptime(lnk_timestamp, time_format)

                # 시간 차 계산
                time_difference = abs((lnk_time - original_doc_time).total_seconds())
                if time_difference <= 1:  # 1초 이내인 경우
                    # 매칭된 MFT 추가
                    if lnk_mft not in docs_files[index][1]:
                        docs_files[index][0] = [docs_files[index][0], lnk_file_name]
                        docs_files[index][1].append(lnk_mft)
                        

# 3. 문서 링크 파일 별로 모든 UsnJrnl, Logfile 끌고오기
# 3-1. 문서 파일 별로 점프리스트도 끌고오기
excessive_reading_data = []
for doc in docs_files:
    doc_name = doc[0]
    doc_MFT = doc[1]
    temp = {
        "filename":doc_name,
        "connection":[]
    }

    # MFT_Record_Number 조건 생성 - LNK 파일이 있는 경우에만 진행
    if len(doc_MFT) > 1:
        # condition = " OR ".join([f'MFT_Record_Number = "{mft}"' for mft in doc_MFT])
        condition = f'MFT_Record_Number = "{doc_MFT[1]}"'

        # 1. UsnJrnl 에서 해당 링크 파일에 대한 모든 로그 확인
        sql_query = f'''
            SELECT "Timestamp_Date/Time_-_UTC_(yyyy-mm-dd)", Reason, hit_id 
            FROM UsnJrnl 
            WHERE {condition};
        '''
        db_cursor.execute(sql_query)
        for row in db_cursor:
            temp["connection"].append(
                {
                    "timestamp":row[0],
                    "type":"LNK_Event_UsnJrnl",
                    "main_data":row[1],
                    "hit_id":row[2],
                    "score":4.40
                }
            )

        # 2. Logfile_Analysis 에서 해당 링크 파일에 대한 모든 로그 확인
        sql_query = f'''
            SELECT "Event_Date/Time_-_UTC_(yyyy-mm-dd)", File_Operation, hit_id
            FROM LogFile_Analysis 
            WHERE {condition};
            '''
        db_cursor.execute(sql_query)
        for row in db_cursor:
            temp["connection"].append(
                {
                    "timestamp":row[0],
                    "type":"LNK_Event_LogFile",
                    "main_data":row[1],
                    "hit_id":row[2],
                    "score":4.40
                }
            )

    # 3. 점프리스트에서 해당 파일에 대한 Access_Count 가져오기
    sql_query = f'''
        SELECT "Target_File_Created_Date/Time_-_UTC_(yyyy-mm-dd)", "Last_Access_Date/Time_-_UTC_(yyyy-mm-dd)",
                Access_Count, hit_id
        FROM Jump_Lists 
        WHERE Data LIKE "%{doc_name[0]}";
        '''
    db_cursor.execute(sql_query)
    res = db_cursor.fetchall()

    if len(res) > 0: # 결과가 존재할 때만 진행
        for row in res:
            row = res[0]
            target_file_created_time_raw = row[0]
            last_access_time_raw = row[1]
            access_count = int(row[2])
            hit_id = row[3]

            if target_file_created_time_raw is None or last_access_time_raw is None:
                continue

            # access_count / (last_access time - file_created_data) 해서 빈도수 저장
            target_file_created_time = datetime.strptime(target_file_created_time_raw, time_format)
            last_access_time = datetime.strptime(last_access_time_raw, time_format)

            # if access_count > 1:
            #     frequency = access_count / ((last_access_time - target_file_created_time).total_seconds() // 86400) 
            # elif access_count == 1:
            #     frequency = 1
            
            frequency = access_count / ((last_access_time - target_file_created_time).total_seconds())
            score = frequency * 4.40

            temp["connection"].append(
                {
                    "timestamp":last_access_time_raw,
                    "type":"Jump_List_Frequency",
                    "frequency":frequency,
                    "hit_id":hit_id,
                    "score":score
                }
            )

        if len(temp["connection"]) > 1: # 로그가 존재할 때만 저장
            excessive_reading_data.append(temp)

# UsnJrnl, Logfile 데이터 그룹화
excessive_reading_data_grouped = filter_first_per_second(excessive_reading_data)
print("과다 열람 scoring 완료")

# excessive_reading_output_path = r"./excessive_reading_score.json"
# with open(excessive_reading_output_path, "w", encoding="utf-8") as f:
#     json.dump(excessive_reading_data_grouped, f, indent=4, ensure_ascii=False, default=str)
# print("excessive_reading_score.json이 저장되었습니다.")

# rename + 과다 열람 커넥션 하나로 합치는 함수
def final_data_rename_excessive_reading(data, temp):
    for temp_item in temp:
        temp_filename = temp_item["filename"]
        temp_connection = temp_item["connection"]

        # Check if temp filename exists in any data item's filename list
        found = False
        for data_item in data:
            if temp_filename in data_item["filename"]:
                # Append connection if filename exists
                data_item["connection"].extend(temp_connection)
                found = True
                break
        
        # If filename is not found, add a new dictionary to data
        if not found:
            data.append({
                "filename": [temp_filename],
                "connection": temp_connection
            })
    
    return data

# 각 문서 별로 점수 계산, 하위 % 결정하는 함수
def calculate_score_total(data):
    doc_scores = []
    for item in data:
        # Sum the scores from the connection list
        score_total = sum(conn.get("score", 0) for conn in item["connection"])
        # Add the score_total field
        item["score_total"] = score_total
        doc_scores.append(score_total)
    max_score = max(doc_scores)
    percentage = [(score / max_score) * 100 for score in doc_scores]
    for index, item in enumerate(data):
        item["percentage"] = percentage[index]
    return data

concat_data = final_data_rename_excessive_reading(excessive_reading_data_grouped, rename_output_data_grouped)
final_data = calculate_score_total(concat_data)

final_score_output_path = r"./final_score.json"
with open(final_score_output_path, "w", encoding="utf-8") as f:
    json.dump(final_data, f, indent=4, ensure_ascii=False, default=str)
print("final_score.json이 저장되었습니다.")