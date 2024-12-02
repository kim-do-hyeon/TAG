import sqlite3, os, json
import pandas as pd
from flask import request, render_template, session, redirect, url_for, flash, Request, jsonify, render_template_string
from apps.authentication.models import Analyzed_file_list, Upload_Case, Normalization, GraphData, PromptQuries, UsbData, FilteringData, GroupParingResults, PrinterData_final, UsbData_final, Mail_final, Porn_Data
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
from apps.analyze.Porn.porn_process import porn_behavior
import threading
import base64
from flask import current_app
from datetime import datetime

def create_dict_from_file_paths(file_path):
    # 파일명 추출
    file_name = os.path.basename(file_path)
    # 확장자를 외한 파일명
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
    case_type = Upload_Case.query.filter_by(id = case_id).first().case_type    
    if Analyzed_file_list.query.filter_by(case_id=case_id).first() :
        return jsonify({'success': True})
    if case_type != "음란물" :
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

        if not UsbData_final.query.filter_by(case_id=case_id).first() :
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
        if not PrinterData_final.query.filter_by(case_id=case_id).first() :
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
                timelist_df = usb_df[usb_df['main_data'].str.contains(filename) | usb_df['type'].str.contains('shellbag')]
                for index, row in timelist_df.iterrows() :
                    if (', ' in row['hit_id']) :
                        timelist_df.loc[index, 'hit_id'] = row['hit_id'].split(', ')
                usb_file_row = {
                    'type' : 'USB',
                    'time_start' : group_usb_time['Start'],
                    'time_end' : group_usb_time['End'],
                    'usb_name' : group_usb_time['Connection'],
                    'filename' : filename,
                    'priority' : 0,
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
                                'priority' : 0,
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
            if mail_event['priority'] != 0 :
                mail_file_row = {
                    'type': 'Mail',
                    'time_start': mail_event['timerange'].split(' ~ ')[0],  # timerange에서 시작 시간 추출
                    'time_end': mail_event['timerange'].split(' ~ ')[1],    # timerange에서 종료 시간 추출
                    'filename': mail_event['filename'],
                    'browser': mail_event['browser'],
                    'priority': round((mail_event['priority']/14)*100, 2), # 메일의 경우 priority 정보도 포함
                    'data': mail_event['connection']     # connection 데이터를 그대로 사용
                }
                try :
                    mail_file_row['service'] = mail_event['description'][0].split('_')[0]
                except Exception as e :
                    print(e)
                    mail_file_row['service'] = ''
                analyzed_file_list.append(mail_file_row)


        drive_output = (os.path.join(os.getcwd(), "uploads", session['username'], case_number, "output_drive.json"))
        with open(drive_output, 'r', encoding='utf-8') as file:
            drive_results = json.load(file)

        # Drive 데이터 처리
        for drive_event in drive_results:
            if drive_event['priority'] != 0 :
                drive_file_row = {
                    'type': 'Drive',
                    'time_start': drive_event['timerange'].split(' ~ ')[0],  # timerange에서 시작 시간 추출
                    'time_end': drive_event['timerange'].split(' ~ ')[1],    # timerange에서 종료 시간 추출
                    'filename': drive_event['filename'],
                    'browser': drive_event['browser'],
                    'priority' : round((drive_event['priority'] / 14)*100, 2),
                    'data': drive_event['connection']  # connection 데이터를 그대로 사용
                }
                try :
                    drive_file_row['service'] = drive_event['description'][0].split('_')[0]
                except Exception as e :
                    print(e)
                    drive_file_row['service'] = ''
                analyzed_file_list.append(drive_file_row)

        blog_output = (os.path.join(os.getcwd(), "uploads", session['username'], case_number, "output_blog.json"))
        with open(blog_output, 'r', encoding='utf-8') as file:
            blog_results = json.load(file)

        # Blog 데이터 처리
        for blog_event in blog_results:
            if drive_event['priority'] != 0 :
                blog_file_row = {
                    'type': 'Blog',
                    'time_start': blog_event['timerange'].split(' ~ ')[0],  # timerange에서 시작 시간 추출
                    'time_end': blog_event['timerange'].split(' ~ ')[1],    # timerange에서 종료 시간 추출
                    'filename': blog_event['filename'],
                    'browser': blog_event['browser'], 
                    'priority': round((blog_event['priority']/14)*100, 2),
                    'data': blog_event['connection']  # connection 데이터를 그대로 사용
                }
                try :
                    blog_file_row['service'] = blog_event['description'][0].split('_')[0]
                except Exception as e :
                    print(e)
                    blog_file_row['service'] = ''
                analyzed_file_list.append(blog_file_row)


        analyzed_file_list = sorted(analyzed_file_list, key=lambda x: x['priority'], reverse=True)
        analyzed_file_db = Analyzed_file_list(case_id=case_id, data=analyzed_file_list)
        db.session.add(analyzed_file_db)
        db.session.commit()
        return jsonify({'success': True})

    elif case_type == "음란물" :
        porn_behavior(case_id, db_path)
        return jsonify({'success' : True})

def redirect_analyze_case_final_result(id):
    analyzed_file_list = Analyzed_file_list.query.filter_by(case_id=id).first().data
    case_number = Upload_Case.query.filter_by(id = id).first().case_number

        
    ''' 임시 제거 함수 '''
    def exclude_prioriry_0(results) :
        tmp = []
        for result in results :
            if (result['priority'] != 0) :
                tmp.append(result)
        return tmp
    ''' 없애도 됨 '''
        
    return render_template('analyze/final_result.html',
                         analyzed_file_list=analyzed_file_list,
                         case_id=id)
    
def redirect_analyze_case_final_connection_result(id, row_index):
    
    return render_template('analyze/final_connection_result.html')

def redirect_analyze_case_porn_result(id) :
    case_number = Upload_Case.query.filter_by(id = id).first().case_number
    porn_folder = (os.path.join(os.getcwd(), "uploads", session['username'], case_number, "Porn"))
    porn_result_folder = (os.path.join(os.getcwd(), "uploads", session['username'], case_number, "Results"))
    porn_datas = Porn_Data.query.filter_by(case_id = id).all()
    # 한국어 설명 추가
    class_descriptions = {
        "FEMALE_GENITALIA_COVERED": (0.9, "여성 생식기 가려짐"),
        "FACE_FEMALE": (0.2, "여성 얼굴"),
        "BUTTOCKS_EXPOSED": (0.9, "노출된 엉덩이"),
        "FEMALE_BREAST_EXPOSED": (0.6, "노출된 여성 가슴"),
        "FEMALE_GENITALIA_EXPOSED": (0.9, "노출된 여성 생식기"),
        "MALE_BREAST_EXPOSED": (0.6, "노출된 남성 가슴"),
        "ANUS_EXPOSED": (0.9, "노출된 항문"),
        "FEET_EXPOSED": (0.2, "노출된 발"),
        "BELLY_COVERED": (0.2, "가려진 배"),
        "FEET_COVERED": (0.2, "가려진 발"),
        "ARMPITS_COVERED": (0.2, "가려진 겨드랑이"),
        "ARMPITS_EXPOSED": (0.2, "노출된 겨드랑이"),
        "FACE_MALE": (0.2, "남성 얼굴"),
        "BELLY_EXPOSED": (0.2, "노출된 배"),
        "MALE_GENITALIA_EXPOSED": (0.9, "노출된 남성 생식기"),
        "ANUS_COVERED": (0.9, "가려진 항문"),
        "FEMALE_BREAST_COVERED": (0.6, "가려진 여성 가슴"),
        "BUTTOCKS_COVERED": (0.9, "가려진 엉덩이"),
    }
    results = []
    total_risk_score = 0
    count = 0
    for i in porn_datas :
        data = {}
        md5 = (i.file_original_name_md5)
        data['file_original_name'] = (i.file_original_name)
        porn_image = os.path.join(porn_folder, str(md5) + ".jpg")
        with open(porn_image, 'rb') as f:
            image_data = f.read()
        encoded_porn_image = base64.b64encode(image_data).decode('utf-8')

        porn_result_image = os.path.join(porn_result_folder, str(md5) + "_detect_result.jpg")
        with open(porn_result_image, 'rb') as f:
            image_data = f.read()
        encoded_porn_result_image = base64.b64encode(image_data).decode('utf-8')
        data['porn_image'] = encoded_porn_image
        data['porn_detect_image'] = encoded_porn_result_image
        data['results'] = json.dumps(i.results)
        
        # 우선순위 평가 및 리스크 점수 계산
        priority_results = evaluate_priority(i.results)
        data['priority'] = priority_results  # 우선순위 저장
        risk_score = calculate_risk_score(priority_results)  # 리스크 점수 계산
        
        data['risk_score'] = risk_score  # 리스크 점수 저장
        results.append(data)
        
        total_risk_score += risk_score
        count += 1
    
    # 전체 리스크 점수의 평균 계산
    average_risk_score = total_risk_score / count if count > 0 else 0
    
    # 평균 리스크 점수를 기준으로 각 데이터 항목의 우선순위 설정
    for result in results:
        if result['risk_score'] >= average_risk_score + 1:  # 평균보다 1 이상
            result['priority'] = '높음'
        elif result['risk_score'] >= average_risk_score:  # 평균과 같거나
            result['priority'] = '중간'
        else:  # 평균보다 낮음
            result['priority'] = '낮음'
    return render_template("analyze/porn_result.html", datas = results, class_descriptions = class_descriptions)

def evaluate_priority(detections):
    # 결과를 저장할 리스트
    prioritized_results = []
    class_descriptions = {
        "FEMALE_GENITALIA_COVERED": (0.9, "여성 생식기 가려짐"),
        "FACE_FEMALE": (0.2, "여성 얼굴"),
        "BUTTOCKS_EXPOSED": (0.9, "노출된 엉덩이"),
        "FEMALE_BREAST_EXPOSED": (0.6, "노출된 여성 가슴"),
        "FEMALE_GENITALIA_EXPOSED": (0.9, "노출된 여성 생식기"),
        "MALE_BREAST_EXPOSED": (0.6, "노출된 남성 가슴"),
        "ANUS_EXPOSED": (0.9, "노출된 항문"),
        "FEET_EXPOSED": (0.2, "노출된 발"),
        "BELLY_COVERED": (0.2, "가려진 배"),
        "FEET_COVERED": (0.2, "가려진 발"),
        "ARMPITS_COVERED": (0.2, "가려진 겨드랑이"),
        "ARMPITS_EXPOSED": (0.2, "노출된 겨드랑이"),
        "FACE_MALE": (0.2, "남성 얼굴"),
        "BELLY_EXPOSED": (0.2, "노출된 배"),
        "MALE_GENITALIA_EXPOSED": (0.9, "노출된 남성 생식기"),
        "ANUS_COVERED": (0.9, "가려진 항문"),
        "FEMALE_BREAST_COVERED": (0.6, "가려진 여성 가슴"),
        "BUTTOCKS_COVERED": (0.9, "가려진 ���덩이"),
    }
    for detection_group in detections:
        group_results = []
        for detection in detection_group:
            class_name = detection['class']
            # 가중치 가져오기
            weight = class_descriptions.get(class_name, (1, "기타"))[0]  # 기본값은 1
            detection['weight'] = weight  # 가중치 추가
            group_results.append(detection)
        prioritized_results.append(group_results)

    return prioritized_results
def calculate_risk_score(detections):
    total_risk_score = 0
    class_descriptions = {
        "FEMALE_GENITALIA_COVERED": (0.9, "여성 생식기 가려짐"),
        "FACE_FEMALE": (0.2, "여성 얼굴"),
        "BUTTOCKS_EXPOSED": (0.9, "노출된 엉덩이"),
        "FEMALE_BREAST_EXPOSED": (0.6, "노출된 여성 가슴"),
        "FEMALE_GENITALIA_EXPOSED": (0.9, "노출된 여성 생식기"),
        "MALE_BREAST_EXPOSED": (0.6, "노출된 남성 가슴"),
        "ANUS_EXPOSED": (0.9, "노출된 항문"),
        "FEET_EXPOSED": (0.2, "노출된 발"),
        "BELLY_COVERED": (0.2, "가려진 배"),
        "FEET_COVERED": (0.2, "가려진 발"),
        "ARMPITS_COVERED": (0.2, "가려진 겨드랑이"),
        "ARMPITS_EXPOSED": (0.2, "노출된 겨드랑이"),
        "FACE_MALE": (0.2, "남성 얼굴"),
        "BELLY_EXPOSED": (0.2, "노출된 배"),
        "MALE_GENITALIA_EXPOSED": (0.9, "노출된 남성 생식기"),
        "ANUS_COVERED": (0.9, "가려진 항문"),
        "FEMALE_BREAST_COVERED": (0.6, "가려진 여성 가슴"),
        "BUTTOCKS_COVERED": (0.9, "가려진 엉덩이"),
    }
    # Define sensitive areas
    sensitive_areas = {
        "FEMALE_GENITALIA_COVERED",
        "FEMALE_GENITALIA_EXPOSED",
        "MALE_GENITALIA_EXPOSED",
        "ANUS_EXPOSED",
        "FEMALE_BREAST_EXPOSED",
        "MALE_BREAST_EXPOSED",
    }
    for detection_group in detections:
        for detection in detection_group:
            score = detection['score']
            class_name = detection['class']
            # 가중치 가져오기
            weight = class_descriptions.get(class_name, (1, "기타"))[0]  # 기본값은 1
            
            # Check if the class is a sensitive area
            if class_name in sensitive_areas:
                risk_score = score * 5  # Assign a high score for sensitive areas
            else:
                risk_score = score * weight
            
            total_risk_score += risk_score

    return total_risk_score