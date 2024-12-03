import sqlite3
import pandas as pd
import json

# 데이터베이스 파일 경로 설정
db_file = r"C:\Users\addy0\OneDrive\바탕 화면\DB 모음\2024-10-27.db"
output_file = 'merged_sorted_data.json'  # 저장할 JSON 파일 경로

# 가져올 테이블과 각 테이블의 시간값이 있는 여러 컬럼 설정
selected_tables = {
    "AmCache_File_Entries": ["Key_Last_Updated_Date/Time_-_UTC_(yyyy-mm-dd)"],  # 'table1'의 여러 시간값 컬럼
    "Chrome_Cache_Records": ["Last_Visited_Date/Time_-_UTC_(yyyy-mm-dd)", "Last_Synced_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "Chrome_Last_Tabs": ["Last_Visited_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "Chrome_Web_Visits": ["Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "Edge/Internet_Explorer_10_11_Daily/Weekly_History": ["Accessed_Date/Time_-_Local_Time_(yyyy-mm-dd)"],
    "Edge/Internet_Explorer_10_11_Main_History": ["Accessed_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "Edge_Chromium_Cache_Records": ["Last_Visited_Date/Time_-_UTC_(yyyy-mm-dd)", "Last_Synced_Date/Time_-_UTC_(yyyy-mm-dd)", "First_Visited_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "Edge_Chromium_Web_Visits": ["Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "Files": ["Last_Run_Date/Time_-_UTC_(yyyy-mm-dd)", "Target_File_Created_Date/Time_-_UTC_(yyyy-mm-dd)", "2nd_Last_Run_Date/Time_-_UTC_(yyyy-mm-dd)", "3rd_Last_Run_Date/Time_-_UTC_(yyyy-mm-dd)", "Volume_2_Created_Date/Time_-_UTC_(yyyy-mm-dd)", "5th_Last_Run_Date/Time_-_UTC_(yyyy-mm-dd)", "4th_Last_Run_Date/Time_-_UTC_(yyyy-mm-dd)", "Last_Modified_Date/Time_-_UTC_(yyyy-mm-dd)", "Accessed_Date/Time_-_Local_Time_(yyyy-mm-dd)", "Volume_Created_Date/Time_-_UTC_(yyyy-mm-dd)", "File_Modified_Date/Time_-_UTC_(yyyy-mm-dd)", "Registry_Key_Modified_Date/Time_-_UTC_(yyyy-mm-dd)", "Created_Date/Time_-_UTC_(yyyy-mm-dd)", "File_Accessed_Date/Time_-_UTC_(yyyy-mm-dd)", "Accessed_Date/Time_-_UTC_(yyyy-mm-dd)", "Last_Connected_Date/Time_-_Local_Time_(yyyy-mm-dd)", "8th_Last_Run_Date/Time_-_UTC_(yyyy-mm-dd)", "File_Created_Date/Time_-_UTC_(yyyy-mm-dd)", "Target_File_Last_Accessed_Date/Time_-_UTC_(yyyy-mm-dd)", "Target_File_Last_Modified_Date/Time_-_UTC_(yyyy-mm-dd)", "6th_Last_Run_Date/Time_-_UTC_(yyyy-mm-dd)", "Profile_Created_Date/Time_-_Local_Time_(yyyy-mm-dd)", "7th_Last_Run_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "Firefox_Cache_Records": ["Created_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "Firefox_Web_Visits": ["Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "Jump_Lists": ["Target_File_Created_Date/Time_-_UTC_(yyyy-mm-dd)", "Last_Access_Date/Time_-_UTC_(yyyy-mm-dd)", "Target_File_Last_Accessed_Date/Time_-_UTC_(yyyy-mm-dd)", "Target_File_Last_Modified_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "LNK_Files": ["Target_File_Created_Date/Time_-_UTC_(yyyy-mm-dd)", "Target_File_Last_Accessed_Date/Time_-_UTC_(yyyy-mm-dd)", "Created_Date/Time_-_UTC_(yyyy-mm-dd)", "Target_File_Last_Modified_Date/Time_-_UTC_(yyyy-mm-dd)", "Last_Modified_Date/Time_-_UTC_(yyyy-mm-dd)", "Accessed_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "Locally_Accessed_Files_and_Folders": ["Accessed_Date/Time_-_Local_Time_(yyyy-mm-dd)", "Accessed_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "LogFile_Analysis": ["Original_Accessed_Date/Time_-_UTC_(yyyy-mm-dd)", "Event_Date/Time_-_UTC_(yyyy-mm-dd)", "Current_Accessed_Date/Time_-_UTC_(yyyy-mm-dd)", "Current_MFT_Modified_Date/Time_-_UTC_(yyyy-mm-dd)", "Original_MFT_Modified_Date/Time_-_UTC_(yyyy-mm-dd)", "Current_Created_Date/Time_-_UTC_(yyyy-mm-dd)", "Current_Modified_Date/Time_-_UTC_(yyyy-mm-dd)", "Original_Modified_Date/Time_-_UTC_(yyyy-mm-dd)", "Original_Created_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "MRU_Folder_Access": ["Registry_Key_Modified_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "MRU_Opened/Saved_Files": ["Registry_Key_Modified_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "MRU_Recent_Files_&_Folders": ["Registry_Key_Modified_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "Rebuilt_Webpages": ["Created_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "SRUM_Network_Usage": ["Recorded_Timestamp_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "SRUM_Application_Resource_Usage": ["Recorded_Timestamp_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "System_Services": ["Registry_Key_Modified_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "UsnJrnl": ["Timestamp_Date/Time_-_UTC_(yyyy-mm-dd)"],
    # 추가 테이블과 시간 컬럼 리스트를 여기에 설정
}

# 데이터베이스 연결
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# 모든 테이블 이름 가져오기
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
all_tables = {table[0] for table in cursor.fetchall()}

# 데이터를 병합하여 저장할 리스트 생성
merged_data = []

# 유효한 테이블 이름 확인 및 데이터 가져오기
for table_name, timestamp_columns in selected_tables.items():
    if table_name in all_tables:
        # 테이블 이름을 " "로 묶어 특수 문자 문제 해결
        cursor.execute(f'PRAGMA table_info("{table_name}");')
        columns = {col[1] for col in cursor.fetchall()}
        
        valid_timestamp_columns = [col for col in timestamp_columns if col in columns]
        
        if valid_timestamp_columns:
            query = f'SELECT * FROM "{table_name}"'  # 테이블 이름을 " "로 묶어 쿼리에서 특수 문자 문제 해결
            data = pd.read_sql_query(query, conn)  # pandas 데이터프레임으로 변환
            
            # 각 시간값 컬럼을 변환하여 병합 데이터에 추가
            for col in valid_timestamp_columns:
                temp_df = data.copy()
                # UTC+9 변환
                temp_df['timestamp'] = pd.to_datetime(temp_df[col], errors='coerce').dt.tz_localize('UTC').dt.tz_convert('Asia/Seoul')
                temp_df['source'] = f"{table_name}.{col}"
                
                # timestamp가 null이 아닌 데이터만 추가
                temp_df = temp_df[temp_df['timestamp'].notna()]
                
                # 중복 방지를 위해 선택된 시간 컬럼을 제외하고 추가
                temp_df = temp_df[['timestamp', 'source'] + [c for c in temp_df.columns if c not in valid_timestamp_columns]]
                merged_data.extend(temp_df.to_dict(orient='records'))
        else:
            print(f"No valid timestamp columns in table '{table_name}'.")
    else:
        print(f"Table '{table_name}' does not exist in the database.")

# 연결 종료
conn.close()

# timestamp 컬럼 기준으로 데이터 정렬
merged_data.sort(key=lambda x: x['timestamp'])

# JSON 파일로 저장
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(merged_data, f, ensure_ascii=False, indent=4, default=str)

print(f"Data saved to {output_file}")

# hit_id로 JSON 데이터 찾는 함수
def find_data_by_hit_id(hit_id):
    results = [item for item in merged_data if item.get('hit_id') == hit_id]
    if results:
        print(f"Data for hit_id '{hit_id}':")
        print(json.dumps(results, ensure_ascii=False, indent=4, default=str))
    else:
        print(f"No data found for hit_id '{hit_id}'.")

# 사용자로부터 hit_id를 입력받아 반복적으로 검색
while True:
    user_input = input("Enter hit_id to search (or 'q' to quit): ")
    if user_input.lower() == 'q':
        print("Exiting the program.")
        break
    try:
        hit_id = int(user_input)
        find_data_by_hit_id(hit_id)
    except ValueError:
        print("Invalid input. Please enter a numeric hit_id or 'q' to quit.")