import pprint
from flask import jsonify, session, url_for
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
    
    def cmp_file_loose_ext(filename1, filename2):
        if filename1 is None or filename2 is None:
            return False
        
        
        try:
            # 파일명에서 확장자 분리 시도
            try:
                name1, ext1 = os.path.basename(str(filename1)).rsplit('.', 1)
            except ValueError:
                # 확장자가 없는 경우
                name1, ext1 = str(filename1), ''
            
            try:
                name2, ext2 = os.path.basename(str(filename2)).rsplit('.', 1)
            except ValueError:
                # 확장자가 없는 경우
                name2, ext2 = str(filename2), ''
            
            print(f'Compare with : {name1}.{ext1}({ext1.lower()}), {name2}.{ext2}({ext2.lower()}) : {str(name1==name2 and ext1.lower() == ext2.lower())}')
            return name1==name2 and ext1.lower() == ext2.lower()
        
        except Exception as e:
            print(f'Error in comparison: {str(e)}')
            return False
    
    def shorten_string(s) :
        if len(s) > 40 :
            return s[0:35] + '...'
        else :
            return s
    
    try :
        all_data = dict(data.get('time_data'))
        time_data_list = list(all_data['data'])
        logfile_data_list = dict(data.get('logfile_data'))
        
        ##pprint.pprint(time_data_list)
        
        # 새로운 리스트를 만들어서 통합된 데이터를 저장
        consolidated_time_data_list = []
        i = 0
        while i < len(time_data_list):
            current = time_data_list[i]
            current_timestamp = pd.to_datetime(current['timestamp'])
            
            # 연속된 행을 확인할 수 있는지 체크
            j = i
            while (j < len(time_data_list) and
                   pd.to_datetime(time_data_list[j]['timestamp']) - current_timestamp <= pd.Timedelta(seconds=2) and
                   cmp_file_loose_ext(current['main_data'], time_data_list[j]['main_data'])):
                j += 1
            
            # 'modify', 'access', 'create'가 모두 포함되어 있는지 확인
            types = {time_data_list[k]['type'] for k in range(i, j)}
            if 'modify' in types and 'access' in types and 'create' in types:
                # 'create'가 포함된 행으로 통합
                consolidated_time_data_list.append({
                    'timestamp': current['timestamp'],
                    'type': 'create',
                    'main_data': current['main_data']
                })
            else:
                consolidated_time_data_list.extend(time_data_list[i:j])
            
            i = j  # 다음 그룹으로 이동
        
        new_df = pd.DataFrame(columns=['timestamp', 'operation', 'filename', 'after_filename', 'mft_num'])
        rows = []
        if all_data['type'] == 'USB' :
            rows.append({
                'timestamp' : pd.to_datetime(all_data['time_start']),
                'operation' : 'USB_Connected',
                'filename' : all_data['usb_name'],
                'after_filename' : None,
                'mft_num' : None
            })
            rows.append({
                'timestamp' : pd.to_datetime(all_data['time_end']),
                'operation' : 'USB_Disconnected',
                'filename' : all_data['usb_name'],
                'after_filename' : None,
                'mft_num' : None
            })
        
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
                # if (logfile_data['File_Operation'] == 'Move') :
                #     continue
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
        new_df = new_df.sort_values(by='timestamp').reset_index(drop=True)
        new_dict = new_df.to_dict(orient='records')
        #new_df['timestamp'] = new_df['timestamp'].astype(str)
        
        # Consolidate entries
        consolidated_dict = []
        i = 0
        while i < len(new_dict):
            current = new_dict[i]
            current_timestamp = current['timestamp']
            
            j = i + 1
            while j < len(new_dict):
                next_item = new_dict[j]
                next_timestamp = next_item['timestamp']
                
                if (next_timestamp - current_timestamp <= pd.Timedelta(seconds=1) and
                    current['operation'] == next_item['operation'] and
                    cmp_file_loose_ext(current['filename'], next_item['filename'])):
                    print(current['timestamp'])
                    j += 1
                else:
                    break
            
            consolidated_dict.append(current)  # Use the first item of the group
            i = j
        #pprint.pprint(consolidated_dict)
        
        
        img_dict = {
            'usb' : url_for('static', filename='graph_img/usb.svg', _external=True),
            'printer' : url_for('static', filename='graph_img/printer.svg', _external=True),
            'firefox' : url_for('static', filename='graph_img/firefox_logo.svg', _external=True),
            'chrome' : url_for('static', filename='graph_img/chrome-logo.svg', _external=True),
            'mail' : url_for('static', filename='graph_img/gmail-icon.svg', _external=True),
            'google_drive' : url_for('static', filename='graph_img/google_drive_icon.svg', _external=True),
            '.ppt' : url_for('static', filename='graph_img/powerpoint.svg', _external=True),
            '.hwp' : url_for('static', filename='graph_img/hwp.svg', _external=True),
            '.show' : url_for('static', filename='graph_img/hanshow.svg', _external=True),
            '.docx' : url_for('static', filename='graph_img/docx.svg', _external=True),
            '.pdf' : url_for('static', filename='graph_img/pdf.svg', _external=True),
            'mega_drive' : url_for('static', filename='graph_img/mega_drive.svg', _external=True),
            '.zip' : url_for('static', filename='graph_img/zip.svg', _external=True),
            'dropbox' : url_for('static', filename='graph_img/dropbox_icon.svg', _external=True),
            'one_drive' : url_for('static', filename='graph_img/onedrive.svg', _external=True)
        }
        nodes = []
        edges = []
        node_x = 0
        node_y = 0
        for idx, row in enumerate(consolidated_dict) :
            #row['filename'] = shorten_string(row['filename'])
            node = {}
            if 'USB' in row['operation'] :
                node = {
                    'id' : idx,
                    'label' : f'{row["operation"]}\n{row["filename"]}',
                    'image' : url_for('static', filename='graph_img/usb.svg', _external=True),
                    'shape' : 'image',
                    'size' : 25
                }
            elif row['operation'] == 'Rename' :
                node = {
                    'id' : idx,
                    'label' : f'Rename\n{row["filename"]} -> {row["after_filename"]}'
                    
                }
            elif row['operation'] == 'Move' :
                node = {
                    'id' : idx,
                    'label' : f'Move Detected!',
                }
            else :
                node = {
                    'id' : idx,
                    'label' : '\n'.join([row['operation'], os.path.basename(row['filename'])]),
                }
            
            for keyword, val in img_dict.items() :
                if keyword in row['operation'].lower() :
                    node['image'] = val
                    node['shape'] = 'image'
                    node['size'] = 25
                elif  keyword in row['filename'].lower() :
                    node['image'] = val
                    node['shape'] = 'image'
                    node['size'] = 25
            
            if (idx % 5) != 0 :
                if (idx // 5) % 2 == 0 :
                    node_x += 220
                else :
                    node_x -= 220
            node_y += 150 if idx % 5 == 0 else 0
            node['x'] = node_x
            node['y'] = node_y + 15 if idx % 2 == 0 else node_y - 15
            nodes.append(node)
            if idx != 0 :
                edges.append({'from' : idx-1, 'to' : idx})                
        
        
        result = {
            'data' : new_df.to_dict(orient='records'),
            'nodes' : nodes,
            'edges' : edges,
            'success' : True
        }
        #pprint.pprint(result)
        return jsonify(result)
    except Exception as e :
        return jsonify({'success' : False, 'message' : e})
    
    