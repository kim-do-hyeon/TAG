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
from apps.analyze.Upload.mail_upload_parser import mail_behavior
import threading

from flask import current_app
from datetime import datetime

def create_dict_from_file_paths(file_path):
    # 파일명 추출
    file_name = os.path.basename(file_path)
    # 확장자를 제외한 파일명
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

    ''' Mail Behavior Process '''
    if TAG_Process:
        mail_results = mail_behavior(db_path)
        
        # Convert all datetime objects to strings recursively
        mail_results = convert_datetime_to_string(mail_results)

        mail_data_db = Mail_final(case_id=case_id, mail_data=mail_results)
        db.session.add(mail_data_db)
        db.session.commit()

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


    analyzed_file_list = []
    ''' USB Filelist process '''
    usb_json = UsbData_final.query.filter(case_id==case_id).first().usb_data
    for group_usb_time in usb_json :
        usb_df = pd.DataFrame(group_usb_time['filtered_df'])
        for filename in group_usb_time['Accessed_File_List'] :
            timelist_df = usb_df[usb_df['main_data'].str.contains(filename)]
            usb_file_row = {
                'type' : 'USB',
                'usb_name' : group_usb_time['Connection'],
                'filename' : filename,
                'data' : timelist_df.to_dict(orient='records')
            }
            analyzed_file_list.append(usb_file_row)
            
    analyzed_file_db = Analyzed_file_list(case_id = case_id, data = analyzed_file_list)
    db.session.add(analyzed_file_db)
    db.session.commit()
    
    # Print Debug
    # for i in printer_results :
        # print(i['Print_Event_Date'], i['Accessed_File_List'], i['df'])

    return jsonify({'success': True})

def redirect_analyze_case_final_result(id):
    usb_results = UsbData_final.query.filter_by(case_id=id).first().usb_data
    printer_results = PrinterData_final.query.filter_by(case_id=id).first().printer_data
    analyzed_file_list = Analyzed_file_list.query.filter_by(case_id=id).first().data
    mail_results = Mail_final.query.filter_by(case_id=id).first().mail_data

    
    timeline_data = []
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
        timeline_data.append(event_data)
        

    return render_template('analyze/final_result.html',
                         usb_results=usb_results,
                         printer_results=printer_results,
                         timeline_data=timeline_data,
                         has_valid_timeline=has_valid_timeline,
                         analyzed_file_list=analyzed_file_list,
                         mail_results=mail_results,
                         case_id = id)
    
def redirect_analyze_case_final_connection_result(id, row_index):
    
    return render_template('analyze/final_connection_result.html')