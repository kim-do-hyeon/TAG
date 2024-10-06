import sqlite3, os
import pandas as pd
from flask import request, render_template, session, redirect, url_for, flash, Request, jsonify, render_template_string
from apps.authentication.models import Upload_Case, Normalization, GraphData, PromptQuries, UsbData, FilteringData
from apps import db
from apps.case.case_analyze import case_analyze_view
from apps.case.case_analyze_RAG import search_query
from apps.analyze.analyze_usb import usb_connection
from apps.analyze.analyze_filtering import analyze_case_filtering, analyze_case_filtering_to_minutes
from apps.analyze.analyze_util import *
import threading

from flask import current_app

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
            progress[case_id] = 0


def redirect_analyze_usb_result(id, user) :
    case_number = Upload_Case.query.filter_by(id = id).first().case_number
    files_lists = (os.listdir(os.path.join(os.getcwd(), "uploads", user, case_number)))
    usb_list = UsbData.query.filter_by(case_id = id).first().usb_data
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
    tables = []
    for i in filtering_data.datas:
        data_frame = pd.DataFrame(i['Data'])  # 'Data'는 판다스 DataFrame
        if not data_frame.empty :
            # 각 셀에 툴팁을 적용할 수 있도록 HTML을 생성
            table_html = data_frame.to_html(classes='table table-striped', index=False, escape=False)
            
            # BeautifulSoup으로 HTML 테이블 파싱하여 각 셀에 툴팁 추가
            soup = BeautifulSoup(table_html, 'html.parser')
            for td in soup.find_all('td'):
                full_text = td.get_text()
                td['title'] = full_text  # 툴팁에 전체 텍스트 추가
                td.string = (full_text[:50] + '...') if len(full_text) > 50 else full_text  # 셀에 50자까지만 표시

            tables.append({
                'title': i['Table'],  # 테이블 제목
                'content': str(soup)  # 툴팁이 적용된 테이블 HTML
            })
    result = filtering_data.filtering_data
    with open(result, 'r') as file:
        html_content = file.read()
    body_html, scripts_html = extract_body_and_scripts(html_content)
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
    
    # 판다스 데이터(DataFrame)를 HTML 테이블로 변환
    tables = []
    for i in filtering_data.datas:
        data_frame = pd.DataFrame(i['Data'])  # 'Data'는 판다스 DataFrame
        if not data_frame.empty :
            # 각 셀에 툴팁을 적용할 수 있도록 HTML을 생성
            table_html = data_frame.to_html(classes='table table-striped', index=False, escape=False)
            
            # BeautifulSoup으로 HTML 테이블 파싱하여 각 셀에 툴팁 추가
            soup = BeautifulSoup(table_html, 'html.parser')
            for td in soup.find_all('td'):
                full_text = td.get_text()
                td['title'] = full_text  # 툴팁에 전체 텍스트 추가
                td.string = (full_text[:50] + '...') if len(full_text) > 50 else full_text  # 셀에 50자까지만 표시

            tables.append({
                'title': i['Table'],  # 테이블 제목
                'content': str(soup)  # 툴팁이 적용된 테이블 HTML
            })
    result = filtering_data.filtering_data
    with open(result, 'r') as file:
        html_content = file.read()
    body_html, scripts_html = extract_body_and_scripts(html_content)
    return render_template('analyze/filtering.html', body_html=body_html, scripts_html=scripts_html,  tables=tables)
