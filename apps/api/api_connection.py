from flask import jsonify, session
from apps.authentication.models import Normalization
from apps.analyze.USB.make_usb_analysis_db import extract_transaction_LogFile_Analysis
import sqlite3
import pandas as pd
import os

def redirect_logfile(data) :
    
    def replace_multiple(text, replacements):
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text
    
    try :
        case_id = data.get('case_id')
        filename = data.get('filename')
        db_path = Normalization.query.filter_by(normalization_definition=case_id).first().file
        
        db_conn = sqlite3.connect(db_path)
        
        result = extract_transaction_LogFile_Analysis(db_conn, filename)
        for key, value in result.items() :
            tmp = value[['Event_Date/Time_-_UTC_(yyyy-mm-dd)', 'Original_File_Name', 'Current_File_Name', 'File_Operation']]
            tmp['File_Operation'] = tmp['File_Operation'].replace('Create', 'file_create')
            tmp.loc[:,'Event_Date/Time_-_UTC_(yyyy-mm-dd)'] = tmp['Event_Date/Time_-_UTC_(yyyy-mm-dd)'].astype(str)
            result[key] = tmp.to_dict(orient='records')
        result['success'] = True     
        
        return jsonify(result)
    except Exception as e :
        return jsonify({'success' : False, 'message' : e})


def file_connect_node(data) :
    try :
        time_data_list = list(data.get('time_data'))
        logfile_data_list = dict(data.get('logfile_data'))
        
        
        # 새로운 리스트를 만들어서 통합된 데이터를 저장
        consolidated_time_data_list = []
        i = 0
        while i < len(time_data_list):
            current = time_data_list[i]
            current_timestamp = pd.to_datetime(current['timestamp'])
            
            # 연속된 행을 확인할 수 있는지 체크
            j = i
            while (j < len(time_data_list) and
                   pd.to_datetime(time_data_list[j]['timestamp']) - current_timestamp <= pd.Timedelta(seconds=1) and
                   current['main_data'] == time_data_list[j]['main_data']):
                j += 1
            
            # j는 현재 그룹의 끝 다음 인덱스를 가리킴
            types = {time_data_list[k]['type'] for k in range(i, j)}
            
            # 'modify', 'access', 'create'가 모두 포함되어 있는지 확인
            if 'modify' in types and 'access' in types and 'create' in types:
                # 'create'가 포함된 행으로 통합
                consolidated_time_data_list.append({
                    'timestamp': current['timestamp'],
                    'type': 'create',
                    'main_data': current['main_data']
                })
            else:
                # 동일한 'type'이 있는 경우 하나로 통합
                for t in types:
                    # 같은 타입의 데이터가 1초 이내에 발생한 경우 통합
                    same_type_data = [time_data_list[k] for k in range(i, j) if time_data_list[k]['type'] == t]
                    if same_type_data:
                        consolidated_time_data_list.append({
                            'timestamp': same_type_data[0]['timestamp'],
                            'type': t,
                            'main_data': same_type_data[0]['main_data']
                        })
            
            i = j  # 다음 그룹으로 이동
        
        
        new_df = pd.DataFrame(columns=['timestamp', 'operation', 'filename', 'after_filename', 'mft_num'])
        rows = []
        for time_data in consolidated_time_data_list :
            row = {
                'timestamp' : pd.to_datetime(time_data['timestamp']),
                'operation' : time_data['type'],
                'filename' : time_data['main_data'],
                'after_filename' : None,
                'mft_num' : None
            }
            rows.append(row)
        for key, value in logfile_data_list.items() :
            if isinstance(value, bool) :
                continue
            for logfile_data in value :
                row = {
                    'timestamp' : pd.to_datetime(logfile_data['Event_Date/Time_-_UTC_(yyyy-mm-dd)']),
                    'operation' : logfile_data['File_Operation'],
                    'mft_num' : key
                }
                if (row['operation'] == 'Rename') :
                    row['filename'] = logfile_data['Original_File_Name']
                    row['after_filename'] = logfile_data['Current_File_Name']
                elif (logfile_data['Original_File_Name'] == logfile_data['Current_File_Name']) :
                    row['filename'] = logfile_data['Original_File_Name']
                    row['after_filename'] = None
                else :
                    if (logfile_data['Original_File_Name'] is None) :
                        row['filename'] = logfile_data['Current_File_Name']
                    else : 
                        row['filename'] = logfile_data['Original_File_Name']
                    row['after_filename'] = None 
                rows.append(row)
        new_df = pd.concat([new_df, pd.DataFrame(rows)], ignore_index=True)
        new_df = new_df.sort_values(by='timestamp')
        new_dict = new_df.to_dict(orient='records')
        #new_df['timestamp'] = new_df['timestamp'].astype(str)
        
        nodes = []
        edges = []
        for idx, row in enumerate(new_dict) :
            if row['operation'] == 'Rename' :
                nodes.append({
                    'id' : idx,
                    'label' : f'Rename\n{row["filename"]} -> {row["after_filename"]}\n{row["timestamp"].strftime("%Y-%m-%d %H:%M:%S")}',
                    'shape' : 'ellipse'
                })
            elif row['operation'] == 'Move' :
                nodes.append({
                    'id' : idx,
                    'label' : f'Move Detected!\n{row["timestamp"].strftime("%Y-%m-%d %H:%M:%S")}',
                    'shape' : 'ellipse'
                })
            else :
                nodes.append({
                    'id' : idx,
                    'label' : '\n'.join([row['operation'], os.path.basename(row['filename']), row["timestamp"].strftime("%Y-%m-%d %H:%M:%S")]),
                    'shape' : 'ellipse'
                })
            if idx != 0 :
                edges.append({'from' : idx-1, 'to' : idx})                
        
        
        result = {
            'data' : new_df.to_dict(orient='records'),
            'nodes' : nodes,
            'edges' : edges,
            'success' : True
        }
        print(jsonify(result))
        return jsonify(result)
    except Exception as e :
        return jsonify({'success' : False, 'message' : e})
    
    