import sqlite3, os, json
import pandas as pd
from flask import request, render_template, session, redirect, url_for, flash, Request, jsonify, render_template_string
from apps.authentication.models import Upload_Case, Normalization, GraphData, PromptQuries, UsbData, FilteringData, GroupParingResults
from apps import db
from apps.case.case_analyze import case_analyze_view
from apps.analyze.analyze_usb import usb_connection
from apps.analyze.analyze_filtering import analyze_case_filtering, analyze_case_filtering_to_minutes
from apps.analyze.analyze_tagging import all_table_parsing, all_tag_process
from apps.analyze.analyze_util import *
from apps.analyze.analyze_tag_group_graph import *
from apps.analyze.analyze_tag_ranking import *
from apps.analyze.USB.case_normalization_time_group import *
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

def redirect_analyze_case_final(data) :
    user = session.get('username')
    case_id = data['case_id']
    case_number = Upload_Case.query.filter_by(id = case_id).first().case_number
    case_folder = os.path.join(os.getcwd(), "uploads", user, case_number)
    db_path = os.path.join(case_folder, "normalization.db")
    time_db_path = os.path.join(case_folder, "time_normalization.db")
    if time_parsing(db_path, time_db_path) :
        print("Success Time Parsing")
    else :
        print("Failed Time Parsing")
    




def redirect_analyze_case_group(data) :
    output_path = all_table_parsing(data)
    with open(output_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    tag_process = all_tag_process(data, json_data, output_path)
    return jsonify({'success': True})

def redirect_case_analyze_group_result(id) :
    group_data = GroupParingResults.query.filter_by(case_id = id).first()
    gmail_subject_to_web_pdf_download = json.loads(group_data.result1)
    gmail_subject_to_google_drive_sharing = json.loads(group_data.result2)
    gmail_subject_to_google_redirection = json.loads(group_data.result3)
    file_web_access_to_pdf_document = json.loads(group_data.result4)
    result_dict = {}
    result_dict['gmail_subject_to_web_pdf_download'] = gmail_subject_to_web_pdf_download
    result_dict['gmail_subject_to_google_drive_sharing'] = gmail_subject_to_google_drive_sharing
    result_dict['gmail_subject_to_google_redirection'] = gmail_subject_to_google_redirection
    result_dict['file_web_access_to_pdf_document'] = file_web_access_to_pdf_document

    html_files = make_analyze_tag_group_graph(result_dict, str(id))
    graph_datas = {"gmail_subject_to_web_pdf_download" : [],
                   "gmail_subject_to_google_drive_sharing" : [],
                   "gmail_subject_to_google_redirection" : [],
                   "file_web_access_to_pdf_document" : []
                    }
    for group_name, code in html_files : 
        with open(code, 'r') as file:
            html_content = file.read()
        soup = BeautifulSoup(html_content, 'html.parser')
        body_content = soup.body
        scripts = soup.find_all('script')
        body_html = str(body_content)
        scripts_html = ''.join([str(script) for script in scripts])
        graph_datas[group_name].append([body_html, scripts_html])

    for i in range(len(result_dict['gmail_subject_to_web_pdf_download'])) :
        result_dict['gmail_subject_to_web_pdf_download'][i]['body'] = graph_datas['gmail_subject_to_web_pdf_download'][i][0]
        result_dict['gmail_subject_to_web_pdf_download'][i]['script'] = graph_datas['gmail_subject_to_web_pdf_download'][i][1]
    

    for i in range(len(result_dict['gmail_subject_to_google_drive_sharing'])) :
        result_dict['gmail_subject_to_google_drive_sharing'][i]['body'] = graph_datas['gmail_subject_to_google_drive_sharing'][i][0]
        result_dict['gmail_subject_to_google_drive_sharing'][i]['script'] = graph_datas['gmail_subject_to_google_drive_sharing'][i][1]
    
    for i in range(len(result_dict['gmail_subject_to_google_redirection'])) :
        result_dict['gmail_subject_to_google_redirection'][i]['body'] = graph_datas['gmail_subject_to_google_redirection'][i][0]
        result_dict['gmail_subject_to_google_redirection'][i]['script'] = graph_datas['gmail_subject_to_google_redirection'][i][1]
    
    for i in range(len(result_dict['file_web_access_to_pdf_document'])) :
        result_dict['file_web_access_to_pdf_document'][i]['body'] = graph_datas['file_web_access_to_pdf_document'][i][0]
        result_dict['file_web_access_to_pdf_document'][i]['script'] = graph_datas['file_web_access_to_pdf_document'][i][1]
    
    ranking_run('파일이 Gmail Drive를 통해 외부로 유출될 가능성이 있습니다.', case_id=id)

    def classify_priority_dynamic(priority, total_priorities):
        # Calculate thresholds for High, Medium, Low groups based on total priorities
        high_threshold = int(total_priorities * 0.33)
        medium_threshold = int(total_priorities * 0.66)
        
        if priority <= high_threshold:
            return 'High'
        elif high_threshold < priority <= medium_threshold:
            return 'Medium'
        else:
            return 'Low'

    user = session.get('username')
    case_number = Upload_Case.query.filter_by(id=id).first().case_number
    priority_data_path = os.path.join(os.getcwd(), "uploads", user, case_number, "tag_priority_data.json")
    with open(priority_data_path, 'r', encoding='utf-8') as file:
        priority_data = json.load(file)
    # Collect all priorities for dynamic classification
    all_priorities = [value['priority'] for value in priority_data.values()]
    total_priorities = len(all_priorities)

    # Transforming the data into a structured format with dynamic classification
    structured_data_dynamic = []
    for key, value in priority_data.items():
        priority = value['priority']
        group = classify_priority_dynamic(priority, total_priorities)
        structured_data_dynamic.append({
            'name': key,
            'priority': priority,
            'group': group,
            'description': value['description']
        })
    sorted_structured_data_dynamic = sorted(structured_data_dynamic, key=lambda x: x['group'])

    group_tag_count_dict = {}

    for category, items in result_dict.items():
        for item in items:
            for key, value in item.items():
                if isinstance(value, dict) and '_Tag_' in value:
                    tag = value['_Tag_']
                    if tag in group_tag_count_dict:
                        group_tag_count_dict[tag] += 1
                    else:
                        group_tag_count_dict[tag] = 1

    all_tag_data_path = os.path.join(os.getcwd(), "uploads", user, case_number, "tagged_data_add_upload.json")
    with open(all_tag_data_path, 'r', encoding='utf-8') as file:
        all_tag_data = json.load(file)
    tagged_items_dict = {}
    
    # 태그별 개수를 저장할 딕셔너리
    all_tag_count = {}

    # 태그가 포함된 아이템을 추출
    for category, items in all_tag_data.items():
        for item in items:
            # 태그가 포함된 아이템만 따로 저장
            for key, value in item.items():
                if isinstance(value, dict) and '_Tag_' in value:
                    tag = value['_Tag_']
                    # 태그가 있는 아이템을 따로 저장
                    if tag not in tagged_items_dict:
                        tagged_items_dict[tag] = []
                    tagged_items_dict[tag].append({key: value})

                    # 태그 개수 카운팅
                    if tag in all_tag_count:
                        all_tag_count[tag] += 1
                    else:
                        all_tag_count[tag] = 1

                # '_Tag_'가 최상위에 있을 경우 처리
                elif key == '_Tag_':
                    tag = value
                    # 태그가 있는 최상위 아이템을 따로 저장
                    if tag not in tagged_items_dict:
                        tagged_items_dict[tag] = []
                    tagged_items_dict[tag].append(item)

                    # 태그 개수 카운팅
                    if tag in all_tag_count:
                        all_tag_count[tag] += 1
                    else:
                        all_tag_count[tag] = 1
    print(tagged_items_dict)
    return render_template('analyze/group_result.html', 
                           result_dict = result_dict,
                           sorted_structured_data_dynamic = sorted_structured_data_dynamic,
                           group_tag_count_dict = group_tag_count_dict,
                           all_tag_count = all_tag_count,
                           all_tag_data = tagged_items_dict)
