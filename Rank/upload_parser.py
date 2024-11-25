import sqlite3
from datetime import datetime, timedelta
import json
import pandas as pd
import re, os
from operator import itemgetter
from collections import Counter

# 기준 파일과 출력 파일 이름 설정
criteria_files = {
    "criteria_mail.json": ("mail_grouped_data_with_related_tag_data.json", "output_mail.json"),
    "criteria_drive.json": ("drive_grouped_data_with_related_tag_data.json", "output_drive.json"),
    "criteria_blog.json": ("blog_grouped_data_with_related_tag_data.json", "output_blog.json")
}

learning_output_data = []

fields_by_table = {
    "UsnJrnl": ["File_Name", "Reason", "File_Attributes"],
    "LNK_Files": ["Linked_Path"],
    "Edge/Internet_Explorer_10_11_Main_History": ["Access_Count", "URL"],
    "MRU_Recent_Files_&_Folders": ["File/Folder_Link", "File/Folder_Name"],
    "Jump_Lists": ["Access_Count", "Data", "Linked_Path"],
    "Locally_Accessed_Files_and_Folders": ["Path"]
}

# DB 연결
conn = sqlite3.connect(r"C:\Users\addy0\OneDrive\바탕 화면\DB 모음\file_upload.db")
cursor = conn.cursor()

# 검색할 테이블과 컬럼 설정
tables_to_search = {
    "UsnJrnl": {"search_column": "File_Name"},
    "LNK_Files": {"search_column": "Linked_Path"},
    "Edge/Internet_Explorer_10_11_Main_History": {"search_column": "URL"},
    "MRU_Recent_Files_&_Folders": {"search_column": "File/Folder_Name"},
    "Jump_Lists": {"search_column": "Data"},
    "Locally_Accessed_Files_and_Folders": {"search_column": "Path"}
}

# 특정 확장자를 가진 파일 이름을 가져오는 정규식
file_extensions = (".pdf", ".pptx", ".zip", ".hwp")
file_name_pattern = re.compile(r'[^\\/]+\.(pdf|pptx|zip|hwp)$', re.IGNORECASE)
def generate_numbered_fields(field_name, values, max_length=10):
    """
    Generate a dictionary with numbered field names.
    Example: field_name='usnjrnl_file_names', values=['A', 'B'], max_length=3
    Result: {'usnjrnl_file_names_1': 'A', 'usnjrnl_file_names_2': 'B', 'usnjrnl_file_names_3': None}
    """
    return {
        f"{field_name}_{i+1}": values[i] if i < len(values) else None
        for i in range(max_length)
    }

# 기준 파일별로 전체 코드를 반복 실행
for criteria_file, (output_file, custom_output_file) in criteria_files.items():
    # 기준 파일에서 문자열(예: "mail", "drive", "blog") 추출
    criteria_type = criteria_file.split("_")[1].split(".")[0]    
    # Step 1: 점수 기준 파일 로드
    with open(criteria_file, "r", encoding="utf-8") as f:
        scoring_criteria = json.load(f)
    print(f"{criteria_file} 기준 파일이 성공적으로 로드되었습니다.")

    # 각 기준 파일마다 초기화할 변수들
    unique_files = set()  # 중복 제거를 위해 집합 사용
    unique_file_names = set()
    search_results = {}

    # 각 테이블에서 파일 이름 가져오기
    for table, columns in tables_to_search.items():
        search_column = columns["search_column"]
        
        # 파일 확장자를 기준으로 필터링하는 쿼리 생성
        query = f"""
        SELECT DISTINCT "{search_column}"
        FROM "{table}"
        WHERE { " OR ".join([f'"{search_column}" LIKE "%{ext}"' for ext in file_extensions]) }
        """
        
        try:
            # 쿼리 실행
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # 각 행에서 파일 이름 추출
            for row in rows:
                full_path = row[0]
                # 정규식으로 파일 이름만 추출
                match = file_name_pattern.search(full_path)
                if match:
                    file_name = match.group()
                    unique_files.add(file_name)
                    only_file_name = file_name.rsplit('.', 1)[0]
                    unique_file_names.add(only_file_name)

        except sqlite3.OperationalError as e:
            # 테이블이 없을 때 발생하는 에러를 처리
            if "no such table" in str(e).lower():
                print(f"테이블 '{table}'이(가) 존재하지 않습니다. 다음 테이블로 넘어갑니다.")
                continue
            else:
                # 다른 에러는 다시 발생시킴
                raise
    # 집합을 리스트로 변환하여 정렬
    unique_files = sorted(unique_files)
    unique_file_names = sorted(unique_file_names)

    # 시간 기준 컬럼 설정
    time_columns = {
        "UsnJrnl": ["Timestamp_Date/Time_-_UTC_(yyyy-mm-dd)"],
        "LNK_Files": ["Created_Date/Time_-_UTC_(yyyy-mm-dd)", "Last_Modified_Date/Time_-_UTC_(yyyy-mm-dd)", "Accessed_Date/Time_-_UTC_(yyyy-mm-dd)"],
        "Edge/Internet_Explorer_10_11_Main_History": ["Accessed_Date/Time_-_UTC_(yyyy-mm-dd)"],
        "MRU_Recent_Files_&_Folders": ["Registry_Key_Modified_Date/Time_-_UTC_(yyyy-mm-dd)"],
        "Jump_Lists": ["Target_File_Created_Date/Time_-_UTC_(yyyy-mm-dd)", "Last_Access_Date/Time_-_UTC_(yyyy-mm-dd)", "Target_File_Last_Accessed_Date/Time_-_UTC_(yyyy-mm-dd)", "Target_File_Last_Modified_Date/Time_-_UTC_(yyyy-mm-dd)"],
        "Locally_Accessed_Files_and_Folders": ["Accessed_Date/Time_-_UTC_(yyyy-mm-dd)"]
    }

    # 파일별 데이터 검색 및 정렬, 그룹화
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
            try:
                cursor.execute(query, (like_pattern,))
                column_names = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
            except sqlite3.OperationalError as e:
                # 테이블이 없을 때 발생하는 에러를 처리
                if "no such table" in str(e).lower():
                    print(f"테이블 '{table}'이(가) 존재하지 않습니다. 다음 테이블로 넘어갑니다.")
                    continue
                else:
                    # 다른 에러는 다시 발생시킴
                    raise               
            
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
            for entry in group:
                table = entry["Table"]
                data = entry["Data"]

                # LogFile_Analysis의 동적 Original_File_Name 조건 확인
                if table == "LogFile_Analysis" and "Original_File_Name" in scoring_criteria[table]:
                    for filename in unique_file_names:
                        dynamic_match_value = f"{filename}.lnk"
                        
                        # Original_File_Name 동적 조건이 일치할 경우에만 operation 조건 체크
                        if data.get("Original_File_Name") == dynamic_match_value:
                            for condition in scoring_criteria[table]["operation"]:
                                if data.get("operation") == condition["match_value"]:
                                    group_score += condition["score"]

                            # 동적 조건 일치 시 기본 점수도 추가
                            group_score += scoring_criteria[table]["Original_File_Name"][0]["score"]

                # 기본 presence_score 계산
                if table in scoring_criteria and "presence_score" in scoring_criteria[table]:
                    group_score += scoring_criteria[table]["presence_score"]
                table_criteria = scoring_criteria[table]
                if "conditions" in table_criteria:
                    for condition in table_criteria["conditions"]:
                        all_conditions_met = True
                        for key, match_value in zip(condition["keys"], condition["match_values"]):
                            if key not in data:
                                all_conditions_met = False
                                break
                            # UsnJrnl 테이블에서 File_Name에 ".lnk"가 포함되어 있으면 조건 만족
                            if table == "UsnJrnl" and key == "File_Name" and ".lnk" not in data[key]:
                                all_conditions_met = False
                                break
                            # UsnJrnl 이외의 테이블에서는 기존 조건을 그대로 적용
                            elif key == "File_Name" and table != "UsnJrnl" and data[key] != match_value:
                                all_conditions_met = False
                                break
                            elif key != "File_Name" and data[key] != match_value:
                                all_conditions_met = False
                                break
                        # 모든 조건이 만족된 경우에만 score 추가
                        if all_conditions_met:
                            group_score += condition["score"]                    

                # 기존 조건 처리
                table_criteria = scoring_criteria[table]
                for key, conditions in table_criteria.items():
                    if isinstance(conditions, list) and key not in ["Original_File_Name", "operation"]:  # 중복 방지
                        for condition in conditions:
                            if key in data and "match_value" in condition and data[key] == condition["match_value"]:
                                group_score += condition["score"]

            group.append({"Group_Score": group_score})

    print("각 그룹에 점수가 부여되었습니다.")

    # Step 5: Group_Score 기준으로 정렬 및 출력
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

    all_groups_sorted = sorted(all_groups, key=lambda x: x["Group_Score"], reverse=True)

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
        try:
            cursor.execute(query)
            column_names = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
        except sqlite3.OperationalError as e:
            # 테이블이 없을 때 발생하는 에러를 처리
            if "no such table" in str(e).lower():
                print(f"테이블 '{table}'이(가) 존재하지 않습니다. 다음 테이블로 넘어갑니다.")
                continue
            else:
                # 다른 에러는 다시 발생시킴
                raise

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

    url_cache_data = []
    cache_tables = ["Chrome_Cache_Records", "Edge_Chromium_Cache_Records", "Firefox_Cache_Records"]

    for table in cache_tables:
        query = f"""
        SELECT *, "URL"
        FROM "{table}"
        WHERE "URL" IS NOT NULL
        """
        try:
            cursor.execute(query)
            column_names = [description[0] for description in cursor.description]
            rows = cursor.fetchall()

        except sqlite3.OperationalError as e:
            # 테이블이 없을 때 발생하는 에러를 처리
            if "no such table" in str(e).lower():
                print(f"테이블 '{table}'이(가) 존재하지 않습니다. 다음 테이블로 넘어갑니다.")
                continue
            else:
                # 다른 에러는 다시 발생시킴
                raise

        for row in rows:
            base_data = {col: val for col, val in zip(column_names, row)}
            # "Last_Synced_Date/Time_-_UTC_(yyyy-mm-dd)"를 제외한 나머지 시간값만 처리
            valid_time_columns = [col for col in tables_with_tags[table] if col != "Last_Synced_Date/Time_-_UTC_(yyyy-mm-dd)"]
            
            for time_column in valid_time_columns:
                if time_column in base_data and base_data[time_column] is not None:
                    try:
                        timestamp = datetime.strptime(base_data[time_column], "%Y-%m-%d %H:%M:%S.%f")
                        entry = {
                            "Table": table,
                            "Timestamp": timestamp,
                            "URL": base_data["URL"],
                            "Time_Column": time_column,
                        }
                        url_cache_data.append(entry)
                    except ValueError as e:
                        print(f"시간 변환 오류 발생 (테이블: {table}, 컬럼: {time_column}): {e}")

    # URL 캐시 데이터를 타임스탬프 기준으로 정렬
    url_cache_data_sorted = sorted(url_cache_data, key=lambda x: x["Timestamp"])
    def extract_tag_prefix(tag_value):
        return tag_value.split("_")[0] if "_" in tag_value else tag_value

    all_tagged_data_sorted = sorted(all_tagged_data, key=lambda x: x["Timestamp"])

    # 테이블 이름에서 첫 번째 언더바 이전의 문자열을 추출하는 함수
    def extract_prefix_from_table(table_name):
        return table_name.split("_")[0] if "_" in table_name else table_name

    # Step: 각 그룹의 First_Timestamp 기준으로 가장 가까운 이전 태그 데이터 및 캐시 데이터 찾기 및 관련된 데이터 추가
    result_with_tag_data = []
    custom_output_data = []
    for group in all_groups_sorted:
        first_timestamp = group["First_Timestamp"]
        
        # 1. 가장 가까운 이전의 closest_tag_data 찾기
        closest_tag_data = None
        for tag_data in reversed(all_tagged_data_sorted):
            if tag_data["Timestamp"] <= first_timestamp:
                closest_tag_data = tag_data
                break

        # closest_tag_data의 테이블 이름에서 접두어 추출
        if closest_tag_data:
            tag_table_prefix = extract_prefix_from_table(closest_tag_data["Table"])
            tag_value = closest_tag_data["Data"].get("_TAG_", "").lower()
            if criteria_type not in tag_value:
                group["Group_Score"] = 0            

            # 2. 가장 가까운 이전의 캐시 데이터 찾기 (테이블 접두어가 같은 경우만 선택)
            closest_cache_data = None
            for cache_data in reversed(url_cache_data_sorted):
                cache_table_prefix = extract_prefix_from_table(cache_data["Table"])
                if cache_data["Timestamp"] <= first_timestamp and cache_table_prefix == tag_table_prefix:
                    closest_cache_data = cache_data
                    break

            # 3. 조건 확인 및 Group_Score 설정
            if closest_cache_data:
                # closest_tag_data의 _TAG_에서 서비스 이름 추출
                tag_value = closest_tag_data["Data"].get("_TAG_", "No _TAG_ found")
                tag_prefix = extract_tag_prefix(tag_value)
                tag_prefix_lower = tag_prefix.lower()
                table_name_value = closest_tag_data["Data"].get("artifact_name", "No artifact_name found")          
                
                # closest_cache_data의 URL에서 tag_prefix 포함 여부 확인
                url_check = closest_cache_data.get("URL", "").lower()           
                if tag_prefix_lower in url_check:
                    pass  # 포함되어 있으면 점수를 유지
                elif tag_prefix_lower == "outlook":
                    if "outlook" in url_check:
                        pass
                    elif "owa" in url_check:
                        pass
                    elif "live.com" in url_check:
                        pass
                elif tag_prefix_lower == "onedrive":
                    if "onedrive" in url_check:
                        pass
                    elif "live.com" in url_check:
                        pass
                elif "Firefox" in table_name_value:
                    pass  # Firefox의 경우 예외로 점수를 유지
                else:
                    group["Group_Score"] = 0  # 포함되지 않으면 점수를 0점으로 설정

            service_name = "_".join(tag_value.split("_")[:2]) if "_" in tag_value else tag_value
            target_table = closest_tag_data["Table"]
                      
            related_tagged_data = [
                data for data in all_tagged_data_sorted 
                if service_name in data["Data"].get("_TAG_", "") and data["Table"] == target_table
            ]        
                    
            related_tagged_data_sorted = sorted(related_tagged_data, key=lambda x: x["Timestamp"])
            min_timestamp = related_tagged_data_sorted[0]["Timestamp"] if related_tagged_data_sorted else None
            max_timestamp = related_tagged_data_sorted[-1]["Timestamp"] if related_tagged_data_sorted else None

            df_data = {
                "timestamp": [entry["Timestamp"] for entry in related_tagged_data_sorted],
                "type": [entry["Data"].get("_TAG_", "") for entry in related_tagged_data_sorted],
                "main_data": [entry["Data"].get("URL", "None") for entry in related_tagged_data_sorted]
            }
            df = pd.DataFrame(df_data)        

            # 최종 결과에 저장
            result_with_tag_data.append({
                "File_Name": group["File_Name"],
                "Group_Score": group["Group_Score"],
                "First_Timestamp": first_timestamp,
                "Group_Data": group["Group_Data"],
                "Closest_Tag_Data": closest_tag_data,
                "Closest_Cache_Data": closest_cache_data  # 가장 가까운 캐시 데이터도 결과에 포함
            })

            # 추가 JSON 파일에 포함할 데이터 구성
            custom_output_entry = {
                "timerange": f"{min_timestamp} ~ {max_timestamp}",
                "filename": group["File_Name"],
                "browser": "_".join(closest_tag_data["Table"].split("_")[:1]),
                "description": list(df["type"]),
                "priority": group["Group_Score"],
                "connection": [
                    {
                        "timestamp": timestamp,
                        "type": type_,
                        "main_data": main_data,
                        "hit_id": entry["Data"].get("hit_id")  # Group_Data의 각 entry에서 hit_id 추출
                    }
                    for timestamp, type_, main_data, entry in zip(
                        df["timestamp"],
                        df["type"],
                        df["main_data"],
                        group["Group_Data"]  # Group_Data 리스트에서 각 entry에 접근
                    )
                ],
                "timeline": f"{min_timestamp} ~ {max_timestamp}"
            }

            connection = [
                {
                    "timestamp": timestamp,
                    "type": type_,
                    "main_data": main_data,
                    "hit_id": entry["Data"].get("hit_id")  # Group_Data의 각 entry에서 hit_id 추출
                }
                for timestamp, type_, main_data, entry in zip(
                    df["timestamp"],
                    df["type"],
                    df["main_data"],
                    group["Group_Data"]  # Group_Data 리스트에서 각 entry에 접근
                )
            ]            

            group_data_summary = [
                {
                    "Table": entry.get("Table"),
                    "Timestamp": entry.get("Timestamp"),
                    "Time_Column": entry.get("Time_Column")
                }
                for entry in group["Group_Data"]
            ]

            group_table_data = [
                entry.get("Table")
                for entry in group["Group_Data"]
            ]

            counted_data = Counter(group_table_data)
            json_data_conted = json.dumps(counted_data, indent=2)
            # event_data의 details 구성
            event_data = [
                {
                    "artifact_name": entry["Table"],
                    "time_stamp": entry["Timestamp"],
                    "details": {
                        field: group["Group_Data"][i]["Data"].get(field)
                        for field in fields_by_table.get(entry["Table"], [])  # 테이블별 필드 가져오기
                    }
                }
                for i, entry in enumerate(group_data_summary)
            ]

            learning_output_entry = {
                "incident_type": "웹 파일 업로드",
                "file_name": group["File_Name"],
                "service_type": criteria_type,
                "web_upload_tag": tag_value,
                "web_tag_timestamp": closest_tag_data["Timestamp"],
                "file_system_Timestamp": first_timestamp,
                "usnjrnl_reasons": ", ".join(
                    entry["Data"].get("Reason", "").rstrip(",")
                    for entry in group["Group_Data"] if entry["Table"] == "UsnJrnl"
                ),
                "usnjrnl_attributes_count": sum(1 for entry in group["Group_Data"] if entry["Table"] == "UsnJrnl"),
                "lnk_files_linked_paths_count": sum(1 for entry in group["Group_Data"] if entry["Table"] == "LNK_Files"),
                "edge_internet_explorer_urls_count": sum(1 for entry in group["Group_Data"] if entry["Table"] == "Edge/Internet_Explorer_10_11_Main_History"),
                "mru_recent_files_folder_names_count": sum(1 for entry in group["Group_Data"] if entry["Table"] == "MRU_Recent_Files_&_Folders"),
                "locally_accessed_files_paths_count": sum(1 for entry in group["Group_Data"] if entry["Table"] == "Locally_Accessed_Files_and_Folders"),
                "jumplist_data_entries_count": sum(1 for entry in group["Group_Data"] if entry["Table"] == "Jump_Lists"),
                "jumplist_access_counts": [
                    int(entry["Data"].get("Access_Count", 0))
                    for entry in group["Group_Data"] if entry["Table"] == "Jump_Lists"
                ]
                # "label": 0
            }
                # **generate_numbered_fields(
                #     "usnjrnl_file_names",
                #     [
                #         entry["Data"].get("File_Name", "")
                #         for entry in group["Group_Data"] if entry["Table"] == "UsnJrnl"
                #     ]
                # ),            
                # **generate_numbered_fields(
                #     "lnk_files_linked_paths",
                #     [
                #         entry["Data"].get("Linked_Path", "")
                #         for entry in group["Group_Data"] if entry["Table"] == "LNK_Files"
                #     ]
                # ),
                # **generate_numbered_fields(
                #     "edge_internet_explorer_urls",
                #     [
                #         entry["Data"].get("URL", "")
                #         for entry in group["Group_Data"] if entry["Table"] == "Edge/Internet_Explorer_10_11_Main_History"
                #     ]
                # ),
                # **generate_numbered_fields(
                #     "mru_recent_files_folder_names",
                #     [
                #         entry["Data"].get("File/Folder_Name", "")
                #         for entry in group["Group_Data"] if entry["Table"] == "MRU_Recent_Files_&_Folders"
                #     ]
                # ),
                # **generate_numbered_fields(
                #     "locally_accessed_files_paths",
                #     [
                #         entry["Data"].get("Path", "")
                #         for entry in group["Group_Data"] if entry["Table"] == "Locally_Accessed_Files_and_Folders"
                #     ]
                # ),
                # **generate_numbered_fields(
                #     "jumplist_data_entries",
                #     [
                #         entry["Data"].get("Data", "")
                #         for entry in group["Group_Data"] if entry["Table"] == "Jump_Lists"
                #     ]
                # ),




            # # artifacts 데이터 생성
            # artifacts = []
            # for detail in event_data:
            #     artifact_data = [detail["artifact_name"], detail["time_stamp"]]
            #     artifact_data.extend([f"{key}: {value}" for key, value in detail["details"].items()])
            #     artifacts.append(artifact_data)

            # # artifacts를 learning_output_entry에 추가
            # learning_output_entry["artifacts"] = artifacts

            # learning_output_data에 결과 추가
            learning_output_data.append(learning_output_entry)
            custom_output_data.append(custom_output_entry)

            # print("=" * 80)
            # print(group["File_Name"] + " ---- " + str(group["Group_Score"]) + "\n")
            # print(json_data_conted + "\n")


            # print(f"Accessed File : [{group['File_Name']}]")
            # print("=" * 50)
            # print(f"File {group['File_Name']} Behavior")
            # print(f"Event : {min_timestamp} ~ {max_timestamp}")
            # print(df.to_string(index=False),"\n")        
        else:
            # closest_tag_data가 없는 경우
            result_with_tag_data.append({
                "File_Name": group["File_Name"],
                "Group_Score": group["Group_Score"],
                "First_Timestamp": first_timestamp,
                "Group_Data": group["Group_Data"],
                "Closest_Tag_Data": None,
                "Closest_Cache_Data": None
            })

    # JSON 파일로 결과 저장
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result_with_tag_data, f, indent=4, ensure_ascii=False, default=str)

    output_learning_file = os.path.join(os.getcwd(), r"C:\Users\addy0\OneDrive\바탕 화면\TAG-1\Learning\learning_output_data.json")
    with open(output_learning_file, "w", encoding="utf-8") as f:
        json.dump(learning_output_data, f, indent=4, ensure_ascii=False, default=str)

    # 새로 정의된 조건의 JSON 파일 생성
    with open(custom_output_file, "w", encoding="utf-8") as f:
        json.dump(custom_output_data, f, indent=4, ensure_ascii=False, default=str)

    print(f"최종 그룹 데이터가 {output_file} 파일에 저장되었습니다.")
    print(f"추가 데이터가 {custom_output_file} 파일에 저장되었습니다.")
    print(f"Learning output data가 {output_learning_file} 파일에 저장되었습니다.")


