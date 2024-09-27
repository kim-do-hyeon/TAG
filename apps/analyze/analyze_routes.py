import sqlite3, os
from flask import request, render_template, session, redirect, url_for, flash, Request, jsonify, render_template_string
from apps.authentication.models import Upload_Case, Normalization, GraphData, PromptQuries, UsbData, FilteringData
from apps import db
from apps.case.case_analyze import case_analyze_view
from apps.case.case_analyze_RAG import search_query
from apps.analyze.analyze_usb import usb_connection
from apps.analyze.analyze_filtering import analyze_case_filtering
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
    result = analyze_case_filtering(data)
    return jsonify({'success': True})

def redirect_case_analyze_filtering_result(id) :
    filtering_data = FilteringData.query.filter_by(case_id = id).all()[-1]
    result = filtering_data.filtering_data
    with open(result, 'r') as file:
        html_content = file.read()
    return render_template_string(html_content)
