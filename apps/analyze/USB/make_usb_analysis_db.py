import pandas as pd
import os
import sqlite3
from apps.analyze.USB.ext_info import *
import urllib.parse


def extract_usb_time(usb_df) :
    time_range = []
    start, end = False, False
    for index, row in usb_df.iterrows() :
        this_time = row['Created_Date/Time_-_UTC_(yyyy-mm-dd)']
        if row['Action'] == 'Connected' :
            if not start :
                start = this_time
                model = row['Model']
            else :
                end = (this_time if this_time < start + pd.Timedelta(minutes=10) else start + pd.Timedelta(minutes=10))
                time_range.append((model, start, end))
                end = False
                start = this_time
                model = row['Model']
        elif row['Action'] == 'Disconnected' :
            end = this_time
        
        if start and end :
            time_range.append((model, start, end))
            start, end = False, False
    return time_range

def extract_doc_and_program(LogFile_df, time_df, start_time, end_time) :
    docs_ext = ['hwp', 'hwpx', 'pptx', 'ppt', 'doc', 'docx', 'show', 'xlsx', 'pdf', 'zip', 'jpg', 'lnk']
    filtered_df = time_df[(time_df['timestamp'] >= start_time - pd.Timedelta(minutes=10)) & (time_df['timestamp'] <= end_time)]
    filtered_log_df = LogFile_df[(LogFile_df['Event_Date/Time_-_UTC_(yyyy-mm-dd)'] >= start_time - pd.Timedelta(minutes=10)) & (LogFile_df['Event_Date/Time_-_UTC_(yyyy-mm-dd)'] <= end_time)]
    new_df = pd.DataFrame(columns=filtered_df.columns)
    
    filename_list = set()
    
    for index, row in filtered_df.iterrows() :
        ext = row['main_data'].split('.')[-1]
        type_col = row['type']
        if (ext in docs_ext or 'shellbag' in type_col) :
            new_df = pd.concat([new_df, pd.DataFrame([row])], ignore_index=True)
            if 'shellbag' not in type_col :
                filename = os.path.basename(row['main_data'])
                if '%'in filename :
                    filename = urllib.parse.unquote(filename)
                filename_list.add(filename)
    
    for index, row in filtered_log_df.iterrows() :
        if pd.isna(row['Event_Date/Time_-_UTC_(yyyy-mm-dd)']) :
            continue
        timestamp = pd.to_datetime(row['Event_Date/Time_-_UTC_(yyyy-mm-dd)'])
        original = row.get('Original_File_Name', '') or ''
        current = row.get('Current_File_Name', '') or ''
        operation = row['File_Operation']
        if original.split('.')[-1] in docs_ext or current.split('.')[-1] in docs_ext:
            # append_df를 딕셔너리로 생성
            append_data = {
                'timestamp': timestamp,
                'type': 'Logfile_'+operation,
                'main_data': original if original == current else f'{original} -> {current}'
            }
            # append_df를 데이터프레임으로 변환
            append_df = pd.DataFrame([append_data], columns=new_df.columns)
            # new_df에 추가
            new_df = pd.concat([new_df, append_df], ignore_index=True)        
    
    filename_list = list(filename_list)
    
    new_df = new_df.sort_values(by='timestamp')
    
    return new_df, filename_list

def extract_transaction_LogFile_Analysis(normal_conn, filename) :
        filename = os.path.basename(filename)
        df = pd.read_sql_query(f"SELECT * FROM LogFile_Analysis WHERE Current_File_Name LIKE '%{filename}%' OR Original_File_Name LIKE '%{filename}%'", normal_conn)
        mft_num_list = list(set(df['MFT_Reference_Number'].to_list()))
        return_dict = {}
        for mft_num in mft_num_list :
            if mft_num :
                mft_df = pd.read_sql_query(f"SELECT * FROM LogFile_Analysis WHERE MFT_Reference_Number = {str(mft_num)}", normal_conn)
                mft_df['Event_Date/Time_-_UTC_(yyyy-mm-dd)'] = pd.to_datetime(mft_df['Event_Date/Time_-_UTC_(yyyy-mm-dd)'])
                mft_df = mft_df.sort_values(by='Event_Date/Time_-_UTC_(yyyy-mm-dd)')
                # print(mft_df[['Event_Date/Time_-_UTC_(yyyy-mm-dd)', 'Original_File_Name', 'Current_File_Name', 'File_Operation']])
                return_dict[mft_num] = mft_df
        return return_dict

def printer_behavior(normalization, time_normalization) :
    pd.set_option('display.max_rows', None)  # 모든 행을 출력하도록 설정
    pd.set_option('display.max_columns', None)  # 모든 열을 출력하도록 설정


    normal_conn = sqlite3.connect(normalization)
    time_normal_conn = sqlite3.connect(time_normalization)

    usb_df = pd.read_sql_query("SELECT * FROM Windows_Event_Logs___Storage_Device_Events", normal_conn)
    usb_df['Created_Date/Time_-_UTC_(yyyy-mm-dd)'] = pd.to_datetime(usb_df['Created_Date/Time_-_UTC_(yyyy-mm-dd)'])
    usb_df = usb_df.sort_values(by='Created_Date/Time_-_UTC_(yyyy-mm-dd)')
    LogFile_df = pd.read_sql_query("SELECT * FROM LogFile_Analysis", normal_conn)
    for index, row in LogFile_df.iterrows() :
        if pd.isna(row['Event_Date/Time_-_UTC_(yyyy-mm-dd)']) :
            LogFile_df.loc[index, 'Event_Date/Time_-_UTC_(yyyy-mm-dd)'] = LogFile_df.loc[index-1, 'Event_Date/Time_-_UTC_(yyyy-mm-dd)']
    LogFile_df['Event_Date/Time_-_UTC_(yyyy-mm-dd)'] = pd.to_datetime(LogFile_df['Event_Date/Time_-_UTC_(yyyy-mm-dd)'])
    LogFile_df = LogFile_df.sort_values(by='Event_Date/Time_-_UTC_(yyyy-mm-dd)')
    time_df = pd.read_sql_query("SELECT * FROM data", time_normal_conn)
    for index, row in time_df.iterrows() :
        row['timestamp'] = pd.to_datetime(row['timestamp'])
        if row['main_data'].count('%') > 1 :
            row['main_data'] = urllib.parse.unquote(row['main_data'])
        time_df.loc[index] = row
    time_df.sort_values(by='timestamp')


    time_range = extract_usb_time(usb_df)

    for model, start, end in time_range :
        filetered_df, filename_list = extract_doc_and_program(LogFile_df, time_df, start, end)
        if not filetered_df.empty :
            print(f"Connection with {model} : {start.strftime('%Y-%m-%d %H:%M:%S')} ~ {end.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f'Accessed file list : {filename_list}')
            # 'main_data' 열을 왼쪽 정렬하여 출력
            max_lengths = filetered_df[['timestamp', 'type', 'main_data']].applymap(str).apply(lambda x: x.str.len().max(), axis=0)
            filetered_df['main_data'] = filetered_df['main_data'].apply(lambda x: str(x).ljust(max_lengths['main_data']))
            # print(filetered_df[['timestamp','type', 'main_data']].to_string(index=False, justify='left'))
            # for index, filename in enumerate(filename_list) :
            #     LogFile_dict = extract_transaction_LogFile_Analysis(normal_conn, filename)
            #     print()
            #     print(f'{index}. {filename}')
            #     print(f'  Catched MFT_Reference_Number : {list(LogFile_dict.keys())}')
            #     for key, value in LogFile_dict.items() :
            #         print('  ',key)
            #         print('  ',value[['Event_Date/Time_-_UTC_(yyyy-mm-dd)', 'File_Operation', 'Original_File_Name', 'Current_File_Name']].to_string(index=False, justify='left'))
            # print('\n+-----------------------------------------------------------------------------+\n')