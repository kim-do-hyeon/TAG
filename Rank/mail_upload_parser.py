import sqlite3
from datetime import datetime, timedelta
import json
import pandas as pd

# Step 1: 점수 기준 파일 로드 (criteria.json)
with open("criteria.json", "r", encoding="utf-8") as f:
    scoring_criteria = json.load(f)
print("점수 기준 파일이 성공적으로 로드되었습니다.")

# Step 2: DB 연결 및 특정 확장자의 파일 이름 중복 제거하여 가져오기
conn = sqlite3.connect(r"C:\Users\addy0\OneDrive\바탕 화면\DB 모음\2024-10-27 - 복사본.db")
cursor = conn.cursor()
query = """
SELECT DISTINCT File_Name
FROM UsnJrnl
WHERE File_Name LIKE '%.pdf'
   OR File_Name LIKE '%.pptx'
   OR File_Name LIKE '%.zip'
   OR File_Name LIKE '%.hwp'
"""
cursor.execute(query)
unique_files = [row[0] for row in cursor.fetchall()]
print(f"중복 제거된 파일 이름 리스트가 성공적으로 가져왔습니다. 파일 개수: {len(unique_files)}")

# Step 3: 테이블에서 데이터 검색 및 그룹화
search_results = {}

tables_to_search = {
    "UsnJrnl": {"search_column": "File_Name"},
    "LNK_Files": {"search_column": "Linked_Path"},
    "Edge/Internet_Explorer_10_11_Main_History": {"search_column": "URL"},
    "MRU_Recent_Files_&_Folders": {"search_column": "File/Folder_Name"},
    "Jump_Lists": {"search_column": "Data"},
    "Locally_Accessed_Files_and_Folders": {"search_column": "Path"}
}

time_columns = {
    "UsnJrnl": ["Timestamp_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "LNK_Files": ["Created_Date/Time_-_UTC_(yyyy-mm-dd)", "Last_Modified_Date/Time_-_UTC_(yyyy-mm-dd)", "Accessed_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "Edge/Internet_Explorer_10_11_Main_History": ["Accessed_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "MRU_Recent_Files_&_Folders": ["Registry_Key_Modified_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "Jump_Lists": ["Target_File_Created_Date/Time_-_UTC_(yyyy-mm-dd)", "Last_Access_Date/Time_-_UTC_(yyyy-mm-dd)", "Target_File_Last_Accessed_Date/Time_-_UTC_(yyyy-mm-dd)", "Target_File_Last_Modified_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "Locally_Accessed_Files_and_Folders": ["Accessed_Date/Time_-_UTC_(yyyy-mm-dd)"]
}

for file_name in unique_files:
    search_results[file_name] = []
    like_pattern = f"%{file_name}%"
    
    for table, columns in tables_to_search.items():
        search_column = columns["search_column"]
        query = f"""
        SELECT *
        FROM "{table}"
        WHERE "{search_column}" LIKE ?
        """
        cursor.execute(query, (like_pattern,))
        column_names = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        for row in rows:
            base_data = {col: val for col, val in zip(column_names, row)}
            for column_name in time_columns.get(table, []):
                if column_name in base_data and base_data[column_name] is not None:
                    try:
                        timestamp = datetime.strptime(base_data[column_name], "%Y-%m-%d %H:%M:%S.%f")
                        entry = {
                            "Table": table,
                            "Timestamp": timestamp,
                            "Data": base_data,
                            "Time_Column": column_name
                        }
                        search_results[file_name].append(entry)
                    except Exception as e:
                        print(f"시간 변환 오류 발생: {e}")

# Step 4: 각 파일의 검색 결과를 시간순으로 정렬 및 그룹화
for file_name, entries in search_results.items():
    sorted_entries = sorted(entries, key=lambda x: x["Timestamp"])
    grouped_entries = []
    group = [sorted_entries[0]] if sorted_entries else []
    
    for i in range(1, len(sorted_entries)):
        current_entry = sorted_entries[i]
        previous_entry = sorted_entries[i - 1]
        if (current_entry["Timestamp"] - previous_entry["Timestamp"]) <= timedelta(seconds=1):
            group.append(current_entry)
        else:
            grouped_entries.append(group)
            group = [current_entry]
    
    if group:
        grouped_entries.append(group)
    search_results[file_name] = grouped_entries
print("데이터 검색 및 그룹화가 완료되었습니다.")


# Step 4: 그룹 점수 추가

for file_name, grouped_entries in search_results.items():
    for group in grouped_entries:
        group_score = 0
        tables_in_group = {entry["Table"] for entry in group}
        for entry in group:
            table = entry["Table"]
            data = entry["Data"]
            
            if table in scoring_criteria:
                if "presence_score" in scoring_criteria[table]:
                    group_score += scoring_criteria[table]["presence_score"]
                
                table_criteria = scoring_criteria[table]
                for key, conditions in table_criteria.items():
                    if isinstance(conditions, list):
                        for condition in conditions:
                            if key in data and "match_value" in condition and data[key] == condition["match_value"]:
                                group_score += condition["score"]
                    elif key in data and "match_value" in table_criteria[key] and data[key] == table_criteria[key]["match_value"]:
                        group_score += table_criteria[key]["score"]

        group.append({"Group_Score": group_score})
print("각 그룹에 점수가 부여되었습니다.")

# Step 5: Group_Score 기준으로 정렬 및 출력
# 모든 그룹을 단일 리스트로 수집 (Group_Score 기준으로 정렬하기 위함)
all_groups = []
for file_name, grouped_entries in search_results.items():
    for group in grouped_entries:
        group_with_score = {
            "File_Name": file_name,
            "Group_Data": group[:-1],
            "Group_Score": group[-1]["Group_Score"],
            "First_Timestamp": group[0]["Timestamp"]
        }
        all_groups.append(group_with_score)

# Group_Score 기준으로 내림차순 정렬
all_groups_sorted = sorted(all_groups, key=lambda x: x["Group_Score"], reverse=True)

# 첫 데이터의 시간값과 파일 이름 출력
# for group in all_groups_sorted:
#     print(f"File Name: {group['File_Name']}, First Timestamp: {group['First_Timestamp']}, Group Score: {group['Group_Score']}")



all_tagged_data = []

tables_with_tags = {
    "Edge_Chromium_Web_Visits": ["Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "Chrome_Web_Visits": ["Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "Firefox_Web_Visits": ["Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "Chrome_Cache_Records": ["First_Visited_Date/Time_-_UTC_(yyyy-mm-dd)", "Last_Synced_Date/Time_-_UTC_(yyyy-mm-dd)", "Last_Visited_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "Edge_Chromium_Cache_Records": ["First_Visited_Date/Time_-_UTC_(yyyy-mm-dd)", "Last_Synced_Date/Time_-_UTC_(yyyy-mm-dd)", "Last_Visited_Date/Time_-_UTC_(yyyy-mm-dd)"],
    "Firefox_Cache_Records": ["Created_Date/Time_-_UTC_(yyyy-mm-dd)"]
}

for table, time_columns in tables_with_tags.items():
    query = f"""
    SELECT *, "_Tag_"
    FROM "{table}"
    WHERE "_Tag_" IS NOT NULL
    """
    cursor.execute(query)
    column_names = [description[0] for description in cursor.description]
    rows = cursor.fetchall()

    for row in rows:
        base_data = {col: val for col, val in zip(column_names, row)}

        for time_column in time_columns:
            if time_column in base_data and base_data[time_column] is not None:
                try:
                    timestamp = datetime.strptime(base_data[time_column], "%Y-%m-%d %H:%M:%S.%f")
                    tagged_entry = {
                        "Table": table,
                        "Timestamp": timestamp,
                        "Data": base_data,
                        "Time_Column": time_column
                    }
                    all_tagged_data.append(tagged_entry)
                except ValueError as e:
                    print(f"시간 변환 오류 발생 (테이블: {table}, 컬럼: {time_column}): {e}")

# 전체 데이터를 시간 순서대로 정렬
all_tagged_data_sorted = sorted(all_tagged_data, key=lambda x: x["Timestamp"])

# 결과 출력
# for entry in all_tagged_data_sorted:
#     print(f"Table: {entry['Table']}, Time Column: {entry['Time_Column']}, Timestamp: {entry['Timestamp']}")
#     print(f"Data: {entry['Data']}\n")


# Step: 각 그룹의 First_Timestamp 기준으로 가장 가까운 이전 태그 데이터 찾기 및 서비스별 관련 데이터 추가
result_with_tag_data = []

for group in all_groups_sorted:
    first_timestamp = group["First_Timestamp"]
    closest_tag_data = None

    # all_tagged_data_sorted를 역순으로 순회하여 가장 가까운 이전 태그 데이터를 찾음
    for tag_data in reversed(all_tagged_data_sorted):
        if tag_data["Timestamp"] < first_timestamp:
            closest_tag_data = tag_data
            break  # 가장 가까운 이전 timestamp를 찾으면 중단

    # closest_tag_data에서 서비스 이름 추출 및 해당 테이블의 데이터만 필터링
    if closest_tag_data:
        tag_value = closest_tag_data["Data"].get("_TAG_", "No _TAG_ found")
        service_name = "_".join(tag_value.split("_")[:2]) if "_" in tag_value else tag_value
        target_table = closest_tag_data["Table"]

        # service_name이 포함되고, Table이 closest_tag_data와 동일한 데이터를 필터링
        related_tagged_data = [
            data for data in all_tagged_data_sorted 
            if service_name in data["Data"].get("_TAG_", "") and data["Table"] == target_table
        ]
        
        # 시간순으로 정렬
        related_tagged_data_sorted = sorted(related_tagged_data, key=lambda x: x["Timestamp"])

        # 최소 및 최대 타임스탬프 계산
        min_timestamp = related_tagged_data_sorted[0]["Timestamp"] if related_tagged_data_sorted else None
        max_timestamp = related_tagged_data_sorted[-1]["Timestamp"] if related_tagged_data_sorted else None

        # DataFrame 생성
        df_data = {
            "timestamp": [entry["Timestamp"] for entry in related_tagged_data_sorted],
            "type": [entry["Data"].get("_TAG_", "") for entry in related_tagged_data_sorted],
            "main_data": [entry["Data"].get("URL", "None") for entry in related_tagged_data_sorted]
        }
        df = pd.DataFrame(df_data)

        # 결과에 그룹 데이터와 가장 가까운 태그 데이터 및 관련된 태그 데이터를 결합
        result_with_tag_data.append({
            "File_Name": group["File_Name"],
            "Group_Score": group["Group_Score"],
            "First_Timestamp": first_timestamp,
            "Group_Data": group["Group_Data"],
            "Closest_Tag_Data": closest_tag_data,
            "Related_Tag_Data": related_tagged_data_sorted 
        })

        # Print Event Summary and DataFrame
        print(f"Event Date : {first_timestamp}")
        print(f"Accessed File : [{group['File_Name']}]")
        print("=" * 50)
        print(f"File {group['File_Name']} Behavior")
        print(f"Event : {min_timestamp} ~ {max_timestamp}")
        print(df.to_string(index=False),"\n")
    else:
        # 태그 데이터가 없는 경우
        result_with_tag_data.append({
            "File_Name": group["File_Name"],
            "Group_Score": group["Group_Score"],
            "First_Timestamp": first_timestamp,
            "Group_Data": group["Group_Data"],
            "Closest_Tag_Data": None,
            "Related_Tag_Data": []  # 관련된 태그 데이터 없음
        })

# 최종 결과를 JSON 파일로 저장
output_file = "grouped_data_with_related_tag_data.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(result_with_tag_data, f, indent=4, ensure_ascii=False, default=str)

print(f"최종 그룹 데이터가 {output_file} 파일에 저장되었습니다.")
