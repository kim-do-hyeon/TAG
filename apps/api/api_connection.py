import pprint
import traceback
from flask import jsonify, session, url_for
from apps.authentication.models import Normalization, Upload_Case
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
        
        print(db_path)
        
        db_conn = sqlite3.connect(db_path)
        
        result = extract_transaction_LogFile_Analysis(db_conn, filename)
        for key, value in result.items() :
            tmp = value[['Event_Date/Time_-_UTC_(yyyy-mm-dd)', 'Original_File_Name', 'Current_File_Name', 'File_Operation', 'hit_id']]
            tmp.loc[:,'File_Operation'] = tmp['File_Operation'].replace('Create', 'file_create')
            tmp.loc[:,'Event_Date/Time_-_UTC_(yyyy-mm-dd)'] = tmp['Event_Date/Time_-_UTC_(yyyy-mm-dd)'].astype(str)
            result[key] = tmp.to_dict(orient='records')
        result['success'] = True
        
        return jsonify(result)
    except Exception as e :
        return jsonify({'success' : False, 'message' : '[*] LogFile table error : '+str(e)+'\n' + traceback.format_exc()})


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
                    'main_data': current['main_data'],
                    'hit_id' : current['hit_id']
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
                'mft_num' : None,
                'hit_id' : -1
            })
            rows.append({
                'timestamp' : pd.to_datetime(all_data['time_end']),
                'operation' : 'USB_Disconnected',
                'filename' : all_data['usb_name'],
                'after_filename' : None,
                'mft_num' : None,
                'hit_id' : -1
            })
        
        for time_data in consolidated_time_data_list :
            row = {
                'timestamp' : pd.to_datetime(time_data['timestamp']),
                'operation' : time_data['type'],
                'filename' : time_data['main_data'],
                'after_filename' : None,
                'mft_num' : None
            }
            try : 
                row['hit_id'] = time_data['hit_id']
            except Exception as e:
                row['hit_id'] = -1
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
                    'mft_num' : key,
                    'hit_id' : logfile_data['hit_id']
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
                        row['after_filename'] = None 
                    else : 
                        row['filename'] = logfile_data['Original_File_Name']
                        row['after_filename'] = logfile_data['Current_File_Name']
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
        consolidated_df = pd.DataFrame(consolidated_dict)
        #consolidated_df['timestamp'] = pd.to_datetime(consolidated_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        consolidated_df['timestamp'] = pd.to_datetime(consolidated_df['timestamp'])
        consolidated_df = consolidated_df.sort_values(by=['timestamp', 'operation']).reset_index(drop=True)
        new_consolidated_df = pd.DataFrame(columns=consolidated_df.columns.to_list())
        print('------------------------------')
        for idx, row in consolidated_df.iterrows() :
            if idx != 0 :
                if (row['timestamp'] - consolidated_df.iloc[idx-1]['timestamp'] <= pd.Timedelta(seconds=2) and
                    row['filename'].lower() == consolidated_df.iloc[idx-1]['filename'].lower() and
                    row['operation'].lower() == consolidated_df.iloc[idx-1]['operation'].lower()) :
                    print(f'timestamp\t\tfilename\t\t\toperation')
                    print(f"{consolidated_df.iloc[idx-1]['timestamp']}\t{consolidated_df.iloc[idx-1]['filename']}\t{consolidated_df.iloc[idx-1]['operation']}")
                    print(f"{row['timestamp']}\t{row['filename']}\t{row['operation']}")
                    continue
            new_consolidated_df = pd.concat([new_consolidated_df, pd.DataFrame([row])], ignore_index=True)
        consolidated_dict = new_consolidated_df.to_dict(orient='records')
        #pprint.pprint(consolidated_dict)
        print('------------------------------')
        
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
            'one_drive' : url_for('static', filename='graph_img/onedrive.svg', _external=True),
            'shellbag' : url_for('static', filename='graph_img/folder.svg', _external=True),
            'delete' : url_for('static', filename='graph_img/recycle_bin.svg', _external=True)
        }
        nodes = []
        edges = []
        nodes_data = []
        timestamps = []
        node_x = 0
        node_y = 0
        for idx, row in enumerate(consolidated_dict) :
            #row['filename'] = shorten_string(row['filename'])
            node = {}
            nodes_data.append({
                'id' : idx,
                'hit_id' : row['hit_id'] if isinstance(row['hit_id'], list) else [row['hit_id']],
                'timestamp' : str(row['timestamp']),
                'main_data' : row['filename'],
                'type' : row['operation']
                })
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
                if 'shellbag' in row['operation'] or 'http' in row['filename'] :
                    label = row['filename']
                else :
                    label = os.path.basename(row['filename'])
                node = {
                    'id' : idx,
                    'label' : '\n'.join([row['operation'],shorten_string(label)]),
                }
            
            for keyword, val in img_dict.items() :
                if keyword in row['filename'].lower() :
                    node['image'] = val
                    node['shape'] = 'image'
                    node['size'] = 25
                    break
                if 'after_filename' in row and row['after_filename'] != None :
                    if keyword in row['after_filename'].lower() :
                        node['image'] = val
                        node['shape'] = 'image'
                        node['size'] = 25
                        break
            for keyword, val in img_dict.items() :
                if keyword in row['operation'].lower() :
                    node['image'] = val
                    node['shape'] = 'image'
                    node['size'] = 25
                    break
            
            if (idx % 5) != 0 :
                if (idx // 5) % 2 == 0 :
                    node_x += 240
                else :
                    node_x -= 240
            node_y += 170 if idx % 5 == 0 else 0
            node['x'] = node_x
            node['y'] = node_y + 15 if idx % 2 == 0 else node_y - 15
            nodes.append(node)
            if idx != 0 :
                #edges.append({'from' : idx-1, 'to' : idx, 'label' : calculate_time_difference(nodes_data[idx-1]['timestamp'], nodes_data[idx]['timestamp'])})
                edges.append({'from' : idx-1, 'to' : idx})
        
        #print(nodes_data)
        result = {
            'data' : new_df.to_dict(orient='records'),
            'nodes' : nodes,
            'edges' : edges,
            'nodes_data' : nodes_data,
            'success' : True
        }
        #pprint.pprint(result)
        return jsonify(result)
    except Exception as e :
        error_message = traceback.format_exc()
        return jsonify({'success' : False, 'message' : '[*] connection error : ' + str(e) +'\n' + str(error_message)})
    
def find_data_by_hit_id(data) :
    
    case_id = data.get('case_id')
    hit_ids = data.get('hit_id')
    
    if (hit_ids == -1 or ',' in hit_ids) :
        return jsonify({'success' : False, 'message' : '[*] It doesn\'t have hit_id'})
    if isinstance(hit_ids, int) :
        hit_ids = [hit_ids]
    if isinstance(hit_ids, str) :
        hit_ids = [hit_ids]
    
    db_instance = Upload_Case.query.filter_by(id=case_id).first()  # Renamed to avoid confusion with db session
    db_path = db_instance.file
    source_conn = sqlite3.connect(db_path)
    
    # 데이터베이스의 모든 테이블 이름 가져오기
    query = "SELECT name FROM sqlite_master WHERE type='table';"
    tables = pd.read_sql_query(query, source_conn)
    
    if 'hit_fragment' in tables :
        return jsonify({'success' : False, 'message' : 'It does not exist "hit_fragment" table'})
    
    try :

        # 특정 컬럼을 찾고자 하는 컬럼 이름
        target_column = 'hit_id'
        fragment_column = 'fragment_definition_id'

        # fragment_definition 테이블에서 id와 name 매핑 가져오기
        fragment_query = "SELECT fragment_definition_id, name FROM fragment_definition;"
        fragment_df = pd.read_sql_query(fragment_query, source_conn)
        id_to_name = dict(zip(fragment_df['fragment_definition_id'], fragment_df['name']))

        return_dicts = []
        table_names = []
        print('hit_ids', hit_ids)
        for hit_id in hit_ids :
            query = f"SELECT hit_id, value, fragment_definition_id FROM hit_fragment WHERE hit_id={hit_id}"
            data_by_hit_id_df = pd.read_sql_query(query, source_conn)
            fragment_definition_id = data_by_hit_id_df['fragment_definition_id'].to_list()[0]
            artifact_version_id = pd.read_sql_query(f'SELECT artifact_version_id FROM fragment_definition WHERE fragment_definition_id="{fragment_definition_id}"', source_conn)['artifact_version_id'].to_list()[0]
            table_name = pd.read_sql_query(f'SELECT artifact_name FROM artifact_version WHERE artifact_version_id="{artifact_version_id}"', source_conn)['artifact_name'].to_list()[0]
            
            
            exclude_keyword_list = [
                'Parent MFT',
                'LSN',
                'MFT Record',
                'Sequence',
                'App ID',
                'Jump List Type',
                'Pin Status',
                'NetBIOS',
                'Entry ID',
                'Show Command',
                'Short File Name'
            ]
            return_dict = {}
            for index, row in data_by_hit_id_df.iterrows() :
                column = remove_substrings(id_to_name[row['fragment_definition_id']])
                is_continue = False
                for exclude_keyword in exclude_keyword_list :
                    if exclude_keyword.lower() in column.lower() :
                        is_continue = True
                        break
                if is_continue :
                    continue
                if column == 'Drive Type' :
                    if 'FIXED' in row['value'] :
                        return_dict[column] = '고정 저장장치'
                    elif 'REMOVABLE' in row['value'] :
                        return_dict[column] = '이동식 저장장치'
                    else :
                        return_dict[column] = row['value']
                else :
                    return_dict[column] = row['value']
            return_dicts.append(return_dict)
            table_names.append(table_name)
            #print(return_dict)
        return jsonify({ 'success' : True, 'data' : return_dicts, 'table' : table_names})
    except Exception as e :
        print(e)
        return jsonify({'success' : False, 'message' : str(e)})
    
    
def calculate_time_difference(start_timestamp, end_timestamp):
    # 타임스탬프를 pandas datetime으로 변환
    start_time = pd.to_datetime(start_timestamp)
    end_time = pd.to_datetime(end_timestamp)
    
    # 시간 차이 계산
    time_difference = end_time - start_time
    total_seconds = time_difference.total_seconds()
    
    # 24시간 초과 여부 확인
    if total_seconds > 86400:  # 24시간 = 86400초
        return ''
    
    # 시, 분, 초로 변환
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    
    # 문자열로 반환
    return_str = ''
    if hours != 0 :
        return_str += f'{hours}시간 '
    if minutes != 0 or hours != 0 :
        return_str += f'{minutes}분 '
    return_str += f'{seconds} 초'
    return return_str

def shorten_string(s):
    if len(s) > 30:
        return s[:27] + '...'
    return s

def remove_substrings(original_string):
    substrings_to_remove = [' - UTC (yyyy-mm-dd)']
    for substring in substrings_to_remove:
        original_string = original_string.replace(substring, "")
    return original_string