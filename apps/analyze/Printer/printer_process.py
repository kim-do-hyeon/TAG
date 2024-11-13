import sqlite3
import pandas as pd

def printer_behavior(db_path) :
    print(db_path)
    # 데이터베이스 파일 연결
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(LogFile_Analysis)")
    columns = [column[1] for column in cursor.fetchall()]

    ORIGINAL_FILE_NAME = (columns.index("Original_File_Name"))
    FILE_OPERATION = (columns.index("File_Operation"))
    MFT_RECORD_NUMBER = (columns.index("MFT_Record_Number"))

    # LogFile_Analysis 테이블의 모든 데이터를 가져옴
    cursor.execute("SELECT * FROM LogFile_Analysis")
    all_data = cursor.fetchall()

    # "SPL"로 시작하거나 ".tmp"로 끝나는 데이터를 포함한 행의 인덱스를 모두 찾기
    spl_shd_indices = [i for i, row in enumerate(all_data) if any((str(cell).startswith("SPL") and str(cell).endswith(".tmp")) for cell in row if cell is not None)]

    spl_fixed_date = []
    for i in spl_shd_indices :
        if (all_data[i][FILE_OPERATION]) == "Delete" or (all_data[i][FILE_OPERATION]) == "Create" :
            spl_fixed_date.append(i)


    # 중복 제거를 위한 set 생성


    file_name_datas = []

    for index in spl_fixed_date:
        start_index = max(0, index - 1000)
        result_data = all_data[start_index:index] 
        unique_results = []
        for row in result_data:
            # 마지막 값이 지정된 확장자로 끝나는지 확인
            if row[-1] and any(str(row[-1]).endswith(ext) for ext in ('pptx', 'xlsx', 'docx', 'hwp', 'pdf', 'jpg', 'lnk')):
                unique_results.append(row[ORIGINAL_FILE_NAME])
        unique_results = list(set(unique_results))
        file_name_datas.append(unique_results)
    results = []
    for index, value in enumerate(file_name_datas) :
        data = {}
        # print(f"Print Event Date : {all_data[spl_fixed_date[index]][17]}")
        # print(f"Accessed File List : {value}")
        df_datas = []
        min_timestamp = None
        max_timestamp = None  # Initialize timestamps
        if value != [] :
            renamed_value = []
            for i in value :
                if "~$" in i :
                    renamed_value.append(i.replace("~$", ""))
            
            for i in renamed_value :
                final_data = []
                print(f"File {i} Behavior")
                cursor.execute(f"SELECT * FROM LogFile_Analysis WHERE Original_File_Name LIKE '%{i}%'")
                all_datas = cursor.fetchall()
                mft_record_number = list(set(j[MFT_RECORD_NUMBER ] for j in all_datas))

                for record_number in mft_record_number:
                    cursor.execute(f"SELECT `Event_Date/Time_-_UTC_(yyyy-mm-dd)` AS Event_Date, File_Operation, Original_File_Name FROM LogFile_Analysis WHERE MFT_Record_Number = '{record_number}' ORDER BY Event_Date ASC")
                    mft_data = cursor.fetchall()

                    for row in mft_data:
                        final_data.append((row[0], row[1], row[2]))


                df = pd.DataFrame(final_data, columns=["timestamp", "type", "main_data"])
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                current_min = df["timestamp"].min()
                current_max = df["timestamp"].max()
                
                # Update min_timestamp and max_timestamp
                if min_timestamp is None or current_min < min_timestamp:
                    min_timestamp = current_min
                if max_timestamp is None or current_max > max_timestamp:
                    max_timestamp = current_max
                
                # timestamp 열을 문자열로 변환
                df["timestamp"] = df["timestamp"].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S.%f'))
                
                # DataFrame을 dictionary로 변환
                df_dict = {
                    'data': df.to_dict('records'),
                    'min_timestamp': min_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f'),
                    'max_timestamp': max_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')
                }
                df_datas.append(df_dict)
                
        data['Print_Event_Date'] = all_data[spl_fixed_date[index]][17]
        # Add checks before using timestamps
        if min_timestamp and max_timestamp:
            data['Start'] = min_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')
            data['End'] = max_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')
        else:
            data['Start'] = None
            data['End'] = None
        data['Accessed_File_List'] = value
        data['df'] = df_datas
        results.append(data)

    # 데이터베이스 연결 닫기
    conn.close()
    return results