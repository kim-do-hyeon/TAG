import sqlite3
import pandas as pd

def printer_behavior(db_path) :
    print(db_path)
    # 데이터베이스 파일 연결
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # LogFile_Analysis 테이블의 모든 데이터를 가져옴
    cursor.execute("SELECT * FROM LogFile_Analysis")
    all_data = cursor.fetchall()

    # "SPL"로 시작하거나 ".tmp"로 끝나는 데이터를 포함한 행의 인덱스를 모두 찾기
    spl_shd_indices = [i for i, row in enumerate(all_data) if any((str(cell).startswith("SPL") and str(cell).endswith(".tmp")) for cell in row if cell is not None)]

    spl_fixed_date = []
    for i in spl_shd_indices :
        if (all_data[i][18]) == "Create" :
            spl_fixed_date.append(i)
    print(spl_fixed_date)


    # 중복 제거를 위한 set 생성


    file_name_datas = []

    for index in spl_fixed_date:
        start_index = max(0, index - 1000)
        result_data = all_data[start_index:index]
        unique_results = []
        for row in result_data:
            # 마지막 값이 지정된 확장자로 끝나는지 확인
            if row[-1] and any(str(row[-1]).endswith(ext) for ext in ('pptx', 'xlsx', 'docx', 'hwp', 'pdf', 'jpg')):
                unique_results.append(row[21])
        unique_results = list(set(unique_results))
        file_name_datas.append(unique_results)

    results = []
    for index, value in enumerate(file_name_datas) :
        data = {}
        # print(f"Print Event Date : {all_data[spl_fixed_date[index]][17]}")
        # print(f"Accessed File List : {value}")
        data['Print_Event_Date'] = all_data[spl_fixed_date[index]][17]
        data['Accessed_File_List'] = value
        if value != [] :
            renamed_value = []
            for i in value :
                if "~$" in i :
                    renamed_value.append(i.replace("~$", ""))
            # print("=" * 50)
            for i in renamed_value :
                final_data = []
                print(f"File {i} Behavior")
                cursor.execute(f"SELECT * FROM LogFile_Analysis WHERE Original_File_Name LIKE '%{i}%'")
                all_datas = cursor.fetchall()
                mft_record_number = list(set(j[3] for j in all_datas))

                for record_number in mft_record_number:
                    cursor.execute(f"SELECT `Event_Date/Time_-_UTC_(yyyy-mm-dd)` AS Event_Date, File_Operation, Original_File_Name FROM LogFile_Analysis WHERE MFT_Record_Number = '{record_number}' ORDER BY Event_Date ASC")
                    mft_data = cursor.fetchall()

                    # 결과를 final_data 리스트에 추가
                    for row in mft_data:
                        final_data.append((row[0], row[1], row[2]))


                df = pd.DataFrame(final_data, columns=["timestamp", "type", "main_data"])
                df["timestamp"] = pd.to_datetime(df["timestamp"])  # Convert to datetime format
                min_timestamp = df["timestamp"].min()
                max_timestamp = df["timestamp"].max()
                print(f"Print Event : {min_timestamp} ~ {max_timestamp}")
                df = df.sort_values(by="timestamp", ascending=True)
                # with pd.option_context('display.colheader_justify', 'center'):
                #     print(df.to_string(index=False, justify="center"))
                # print("=" * 50)
                # print()
        results.append(data)

    # 데이터베이스 연결 닫기
    conn.close()
    return results