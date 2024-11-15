import sqlite3, os, json
import pandas as pd
from flask import request, render_template, session, redirect, url_for, flash, Request, jsonify, render_template_string
from apps.authentication.models import Analyzed_file_list, Upload_Case, Normalization, GraphData, PromptQuries, UsbData, FilteringData, GroupParingResults, PrinterData_final, UsbData_final, Mail_final
from apps import db
from apps.case.case_analyze import case_analyze_view
from apps.analyze.analyze_usb import usb_connection
from apps.analyze.analyze_filtering import analyze_case_filtering, analyze_case_filtering_to_minutes
from apps.analyze.analyze_tagging import all_tag_process
from apps.analyze.analyze_util import *
from apps.analyze.USB.case_normalization_time_group import *
from apps.analyze.USB.make_usb_analysis_db import usb_behavior
from apps.analyze.Printer.printer_process import printer_behavior
from apps.analyze.Upload.upload_parser import mail_behavior
import threading

from flask import current_app
from datetime import datetime

def create_dict_from_file_paths(file_path):
    # 파일명 추출
    file_name = os.path.basename(file_path)
    # 확장자를 ��외한 파일명
    file_name_without_ext = os.path.splitext(file_name)[0]
    # 딕셔너리 형태로 반환
    return {file_name_without_ext: file_path}

def redirect_analyze_usb(data, progress):
    case_id = data.get('case_id')
    if UsbData.query.filter_by(case_id = case_id).first() :
        progress[case_id] = 100
        return jsonify({'success': True})
    db_path = Normalization.query.filter_by(normalization_definition=case_id).first().file
    user = session.get('username')  # Assuming 'username' is stored in session
    if not user:
        flash('사용자 정보를 찾을 수 없습니다. 다시 로그인 해주세요.', 'danger')
        return redirect('/case/list')

    # Get the current Flask app
    app = current_app._get_current_object()

    # Create and start a new thread for the search query
    thread = threading.Thread(target=handle_usb_data, args=(app, db_path, case_id, user, progress))
    thread.start()
    return jsonify({'success': True})

def handle_usb_data(app, db_path, case_id, user, progress):
    global usb_path
    with app.app_context():
        progress[case_id] = 0
        result = usb_connection(db_path, case_id, user, progress)
        if result :
            progress[case_id] = 100
        else :
            progress[case_id] = 100
            progress['result'] = False


def redirect_analyze_usb_result(id, user) :
    case_number = Upload_Case.query.filter_by(id = id).first().case_number
    files_lists = (os.listdir(os.path.join(os.getcwd(), "uploads", user, case_number)))
    try :
        usb_list = UsbData.query.filter_by(case_id = id).first().usb_data
    except :
        flash("USB 장치 삽입 / 해제 시간이 존재하지 않습니다.")
        return redirect('/case/analyze/' + str(id))
    usb_dict_list = [create_dict_from_file_paths(path) for path in usb_list]
    return render_template("analyze/usb_results.html",
                        case_number = case_number,
                            usb_lists = usb_dict_list)

def redirect_analze_usb_graph(user,case_number, usb_data) :
    html_result = os.path.join(os.getcwd(), "uploads", user, case_number, usb_data + ".html")
    with open(html_result, 'r') as file:
        html_content = file.read()  # HTML 파일 내용을 읽어옴
    return render_template_string(html_content)  # HTML 내용을 렌더링


def redirect_analyze_case_filtering(data) :
    if data['filtering_type'] == "time" :
        result = analyze_case_filtering_to_minutes(data)
    elif data['filtering_type'] == "table" :
        result = analyze_case_filtering(data)
    return jsonify({'success': True})

def redirect_case_analyze_filtering_result(id) :
    filtering_data = FilteringData.query.filter_by(case_id = id).all()[-1]
    body_html, scripts_html, tables = extract_body_and_scripts(filtering_data)
    return render_template('analyze/filtering.html', body_html=body_html, scripts_html=scripts_html,  tables=tables)


def redirect_case_analyze_filtering_history(id) :
    filtering_data = FilteringData.query.filter_by(case_id = id).all()
    for index, item in enumerate(filtering_data) :
        filtering_data[index].start_time = change_local_time(filtering_data[index].start_time)
        filtering_data[index].end_time = change_local_time(filtering_data[index].end_time)
    return render_template('analyze/filtering_results.html',
                           filtering_data = filtering_data)

def redirect_case_analyze_filtering_history_view(id) :
    filtering_data = FilteringData.query.filter_by(id=id).first()
    body_html, scripts_html, tables = extract_body_and_scripts(filtering_data)
    return render_template('analyze/filtering.html', body_html=body_html, scripts_html=scripts_html,  tables=tables)

def convert_datetime_to_string(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: convert_datetime_to_string(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime_to_string(item) for item in obj]
    return obj

def redirect_analyze_case_final(data) :
    user = session.get('username')
    case_id = data['case_id']
    case_number = Upload_Case.query.filter_by(id = case_id).first().case_number
    case_folder = os.path.join(os.getcwd(), "uploads", user, case_number)
    db_path = os.path.join(case_folder, "normalization.db")

    ''' Tagging Process '''
    TAG_Process = all_tag_process(data)

    ''' Upload Behavior Process '''
    if TAG_Process:
        Upload_results = mail_behavior(db_path)

    ''' USB Behavior Process'''
    time_db_path = os.path.join(case_folder, "time_normalization.db")
    if os.path.isfile(time_db_path) == False :
        if time_parsing(db_path, time_db_path) :
            print("Success Time Parsing")

    usb_results = usb_behavior(db_path, time_db_path)
    for result in usb_results:
        if 'df' in result:
            result['filtered_df'] = result['filtered_df'].to_dict('records')  # Convert DataFrame to list of dictionaries
            
    usb_data_db = UsbData_final(case_id = case_id, usb_data = usb_results)
    db.session.add(usb_data_db)
    db.session.commit()
    # USB Debug
    # for i in usb_results :
    #     print(i['Connection'], i['Start'], i['End'], i['Accessed_File_List'])


    ''' Printer Behavior Process'''
    printer_results = printer_behavior(db_path)
    # Convert any DataFrame objects to dictionaries/lists before storing
    for result in printer_results:
        if 'df' in result and hasattr(result['df'], 'to_dict'):  # Check if df is a DataFrame
            result['df'] = result['df'].to_dict('records')  # Convert DataFrame to list of dictionaries
            
    printer_data_db = PrinterData_final(case_id = case_id, printer_data = printer_results)
    db.session.add(printer_data_db)
    db.session.commit()


    ''' USB Filelist process '''
    analyzed_file_list = []
    usb_json = UsbData_final.query.filter_by(case_id = str(case_id)).first().usb_data
    for group_usb_time in usb_json :
        usb_df = pd.DataFrame(group_usb_time['filtered_df'])
        for filename in group_usb_time['Accessed_File_List'] :
            timelist_df = usb_df[usb_df['main_data'].str.contains(filename)]
            usb_file_row = {
                'type' : 'USB',
                'time_start' : group_usb_time['Start'],
                'time_end' : group_usb_time['End'],
                'usb_name' : group_usb_time['Connection'],
                'filename' : filename,
                'data' : timelist_df.to_dict(orient='records')
            }
            analyzed_file_list.append(usb_file_row)

    printer_json = PrinterData_final.query.filter_by(case_id=str(case_id)).first().printer_data
    for printer_time in printer_json:
        if printer_time['df'] and isinstance(printer_time['df'], list):
            # 모든 df 데이터를 하나의 DataFrame으로 통합
            all_data = []
            for df_item in printer_time['df']:
                if 'data' in df_item:
                    all_data.extend(df_item['data'])
            
            if all_data:  # 데이터가 있는 경우에만 처리
                printer_df = pd.DataFrame(all_data)
                
                for filename in printer_time['Accessed_File_List']:
                    if filename:  # filename이 None이 아닌 경우에만 처리
                        # na=False로 NaN 값 처리, 문자열이 아닌 경우 처리
                        mask = printer_df['main_data'].astype(str).str.contains(filename, na=False)
                        timelist_df = printer_df[mask]
                        
                        printer_file_row = {
                            'type': 'Printer',
                            'time_start': printer_time.get('Start'),  # 시작 시간 추가
                            'time_end': printer_time.get('End'),      # 종료 시간 추가
                            'filename': filename,
                            'data': timelist_df.to_dict(orient='records')
                        }
                        analyzed_file_list.append(printer_file_row)

    ''' Upload Behavior Process Complete '''
    case_number = Upload_Case.query.filter_by(id = case_id).first().case_number
    mail_output = (os.path.join(os.getcwd(), "uploads", session['username'], case_number, "output_mail.json"))
    with open(mail_output, 'r', encoding='utf-8') as file:
        mail_results = json.load(file)
    
    # Mail 데이터 처리
    for mail_event in mail_results:
        mail_file_row = {
            'type': 'Mail',
            'time_start': mail_event['timerange'].split(' ~ ')[0],  # timerange에서 시작 시간 추출
            'time_end': mail_event['timerange'].split(' ~ ')[1],    # timerange에서 종료 시간 추출
            'filename': mail_event['filename'],
            'browser': mail_event['browser'],
            'priority': mail_event['priority'],  # 메일의 경우 priority 정보도 포함
            'data': mail_event['connection']     # connection 데이터를 그대로 사용
        }
        analyzed_file_list.append(mail_file_row)


    drive_output = (os.path.join(os.getcwd(), "uploads", session['username'], case_number, "output_drive.json"))
    with open(drive_output, 'r', encoding='utf-8') as file:
        drive_results = json.load(file)

    # Drive 데이터 처리
    for drive_event in drive_results:
        drive_file_row = {
            'type': 'Drive',
            'time_start': drive_event['timerange'].split(' ~ ')[0],  # timerange에서 시작 시간 추출
            'time_end': drive_event['timerange'].split(' ~ ')[1],    # timerange에서 종료 시간 추출
            'filename': drive_event['filename'],
            'browser': drive_event['browser'],
            'data': drive_event['connection']  # connection 데이터를 그대로 사용
        }
        analyzed_file_list.append(drive_file_row)

    blog_output = (os.path.join(os.getcwd(), "uploads", session['username'], case_number, "output_blog.json"))
    with open(blog_output, 'r', encoding='utf-8') as file:
        blog_results = json.load(file)

    # Blog 데이터 처리
    for blog_event in blog_results:
        blog_file_row = {
            'type': 'Blog',
            'time_start': blog_event['timerange'].split(' ~ ')[0],  # timerange에서 시작 시간 추출
            'time_end': blog_event['timerange'].split(' ~ ')[1],    # timerange에서 종료 시간 추출
            'filename': blog_event['filename'],
            'browser': blog_event['browser'],
            'data': blog_event['connection']  # connection 데이터를 그대로 사용
        }
        analyzed_file_list.append(blog_file_row)

    

    analyzed_file_db = Analyzed_file_list(case_id=case_id, data=analyzed_file_list)
    db.session.add(analyzed_file_db)
    db.session.commit()
    
    # Print Debug
    for i in printer_results :
        print(i['Print_Event_Date'], i['Accessed_File_List'], i['df'])

    return jsonify({'success': True})

def redirect_analyze_case_final_result(id):
    usb_results = UsbData_final.query.filter_by(case_id=id).first().usb_data
    printer_results = PrinterData_final.query.filter_by(case_id=id).first().printer_data
    analyzed_file_list = Analyzed_file_list.query.filter_by(case_id=id).first().data
    case_number = Upload_Case.query.filter_by(id = id).first().case_number
    mail_output = (os.path.join(os.getcwd(), "uploads", session['username'], case_number, "output_mail.json"))
    
    with open(mail_output, 'r', encoding='utf-8') as file:
        mail_results = json.load(file)
    
    drive_output = (os.path.join(os.getcwd(), "uploads", session['username'], case_number, "output_drive.json"))
    with open(drive_output, 'r', encoding='utf-8') as file:
        drive_results = json.load(file)

    blog_output = (os.path.join(os.getcwd(), "uploads", session['username'], case_number, "output_blog.json"))
    with open(blog_output, 'r', encoding='utf-8') as file:
        blog_results = json.load(file)
        
    ''' 임시 제거 함수 '''
    def exclude_prioriry_0(results) :
        tmp = []
        for result in results :
            if (result['priority'] != 0) :
                tmp.append(result)
        return tmp
    mail_results = exclude_prioriry_0(mail_results)
    drive_results = exclude_prioriry_0(drive_results)
    blog_results = exclude_prioriry_0(blog_results)
    ''' 없애도 됨 '''
    
    printer_timeline_data = []
    has_valid_timeline = False
    
    for result in printer_results:
        event_data = []
        # Check if there are actual printed files
        # if result['Accessed_File_List']:
        has_valid_timeline = True
        event_data.append({
            'datetime': result['Print_Event_Date'],
            'name': 'Print Event',
            'type': 'Print',
            'Content': f"Printed files: {', '.join(result['Accessed_File_List'])}",
        })
        
        # Add file activities from df
        if 'df' in result and result['df'] and len(result['df']) > 0:
            for activity in result['df'][0]['data']:
                event_data.append({
                    'datetime': activity['timestamp'],
                    'name': f"File {activity['type']}",
                    'type': activity['type'],
                    'Content': activity['main_data'] if activity['main_data'] else 'No additional data'
                })
            
        # Sort activities by datetime
        event_data.sort(key=lambda x: x['datetime'])
        printer_timeline_data.append(event_data)

    # USB 타임라인 데이터 처리 추가
    usb_timeline_data = []
    has_usb_timeline = False
    
    for connection in usb_results:
        has_usb_timeline = True
        event_data = []
        
        # USB 연결/해제 이벤트 추가
        event_data.append({
            'datetime': connection['Start'],
            'name': f"USB Connected - {connection['Connection']}",
            'type': 'usb_connect',
            'Content': f"USB device connected: {connection['Connection']}"
        })
        
        event_data.append({
            'datetime': connection['End'],
            'name': f"USB Disconnected - {connection['Connection']}",
            'type': 'usb_disconnect',
            'Content': f"USB device disconnected: {connection['Connection']}"
        })
        
        # 파일 접근 이벤트 추가
        for activity in connection['filtered_df']:
            event_data.append({
                'datetime': activity['timestamp'],
                'name': f"File {activity['type']}",
                'type': activity['type'],
                'Content': activity['main_data']
            })
        
        # 시간순 정렬
        event_data.sort(key=lambda x: x['datetime'])
        usb_timeline_data.append(event_data)

    # 메일 타임라인 데이터 처리 추가
    mail_timeline_data = []
    has_mail_timeline = False
    
    for mail_event in mail_results:
        has_mail_timeline = True
        event_data = []
        
        # 각 메일 이벤트의 connection 데이터를 타임라인에 추가
        for activity in mail_event['connection']:
            event_data.append({
                'datetime': activity['timestamp'],
                'name': f"Mail Activity - {activity['type']}",
                'type': 'mail',
                'Content': f"File: {mail_event['filename']}, Action: {activity['type']}, URL: {activity['main_data']}"
            })
        
        # 시간순 정렬
        event_data.sort(key=lambda x: x['datetime'])
        mail_timeline_data.append(event_data)

    # 드라이브 타임라인 데이터 처리 추가
    drive_timeline_data = []
    has_drive_timeline = False
    
    for drive_event in drive_results:
        has_drive_timeline = True
        event_data = []
        
        # 각 드라이브 이벤트의 connection 데이터를 타임라인에 추가
        for activity in drive_event['connection']:
            event_data.append({
                'datetime': activity['timestamp'],
                'name': f"Drive Activity - {activity['type']}",
                'type': 'drive',
                'Content': f"File: {drive_event['filename']}, Action: {activity['type']}, URL: {activity['main_data']}"
            })
        
        # 시간순 정렬
        event_data.sort(key=lambda x: x['datetime'])
        drive_timeline_data.append(event_data)

    # 블로그 타임라인 데이터 처리 추가
    blog_timeline_data = []
    has_blog_timeline = False
    
    for blog_event in blog_results:
        has_blog_timeline = True
        event_data = []
        
        # 각 블로그 이벤트의 connection 데이터를 타임라인에 추가
        for activity in blog_event['connection']:
            event_data.append({
                'datetime': activity['timestamp'],
                'name': f"Blog Activity - {activity['type']}",
                'type': 'blog',
                'Content': f"File: {blog_event['filename']}, Action: {activity['type']}, URL: {activity['main_data']}"
            })
        
        # 시간순 정렬
        event_data.sort(key=lambda x: x['datetime'])
        blog_timeline_data.append(event_data)

    return render_template('analyze/final_result.html',
                         usb_results=usb_results,
                         printer_results=printer_results,
                         printer_timeline_data=printer_timeline_data,
                         has_valid_timeline=has_valid_timeline,
                         analyzed_file_list=analyzed_file_list,
                         mail_results=mail_results,
                         mail_timeline_data=mail_timeline_data,
                         has_mail_timeline=has_mail_timeline,
                         drive_timeline_data=drive_timeline_data,
                         has_drive_timeline=has_drive_timeline,
                         blog_timeline_data=blog_timeline_data,
                         has_blog_timeline=has_blog_timeline,
                         usb_timeline_data=usb_timeline_data,
                         has_usb_timeline=has_usb_timeline,
                         case_id=id,
                         drive_results=drive_results,
                         blog_results=blog_results)
    
def redirect_analyze_case_final_connection_result(id, row_index):
    
    return render_template('analyze/final_connection_result.html')