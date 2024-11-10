from flask import jsonify, session
from apps.authentication.models import Normalization
from apps.analyze.USB.make_usb_analysis_db import extract_transaction_LogFile_Analysis
import sqlite3
import pandas as pd

def redirect_logfile(data) :
    try :
        case_id = data.get('case_id')
        filename = data.get('filename')
        db_path = Normalization.query.filter_by(normalization_definition=case_id).first().file
        
        db_conn = sqlite3.connect(db_path)
        
        result = extract_transaction_LogFile_Analysis(db_conn, filename)
        for key, value in result.items() :
            tmp = value[['Event_Date/Time_-_UTC_(yyyy-mm-dd)', 'Original_File_Name', 'Current_File_Name', 'File_Operation']]
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
        
        new_df = pd.DataFrame(columns=['timestamp', 'operation', 'filename', 'after_filename', 'mft_num'])
        rows = []
        for time_data in time_data_list :
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
                    'label' : f'Rename\n{row["filename"]} -> {row["after_filename"]}',
                    'shape' : 'ellipse'
                })
            else :
                nodes.append({
                    'id' : idx,
                    'label' : '\n'.join([row['operation'], row['filename']]),
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
    
    