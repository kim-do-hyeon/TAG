import pandas as pd
import sqlite3
import json, os
from apps import db
from flask import session
from apps.authentication.models import Upload_Case, GroupParsingProcess, GroupParingResults
from apps.analyze.analyze_tag_class import LogTagger, LogTagger_1, LogTagger_1_1, LogTagger_1_2, LogTagger_1_3, LogTagger_2
from apps.manager.progress_bar import ProgressBar

def all_table_parsing(data) :
    ProgressBar.get_instance().start_progress(0)
    user = session.get('username')
    case_id = data['case_id']
    isExist = GroupParsingProcess.query.filter_by(case_id = case_id).first()
    if isExist :
        return isExist.output_path
    case_number = Upload_Case.query.filter_by(id=case_id).first().case_number
    case_folder = os.path.join(os.getcwd(), "uploads", user, case_number)
    db_path = os.path.join(case_folder, "normalization.db")
    conn = sqlite3.connect(db_path)
    # 테이블 목록 가져오기
    ProgressBar.get_instance().set_now_log('SELECT name FROM sqlite_master WHERE type="table";')
    tables_query = 'SELECT name FROM sqlite_master WHERE type="table";'
    tables = pd.read_sql_query(tables_query, conn)
    # 모든 테이블 데이터를 저장할 사전
    all_data = {}
    # 특정 테이블에 대해 작업
    ProgressBar.get_instance().start_progress(len(tables['name']) + 1)
    for table_name in tables['name']:
        ProgressBar.get_instance().done_1_task()
        try:
            query = f'SELECT * FROM "{table_name}"'
            ProgressBar.get_instance().set_now_log(query)
            df = pd.read_sql_query(query, conn)
            # 사전에 테이블 데이터 추가
            all_data[table_name] = df.to_dict('records')
        except Exception as e:
            print(f"테이블 '{table_name}' 처리 중 오류 발생: {e}")
    # 모든 테이블 데이터를 하나의 JSON 파일로 저장
    output_path = os.path.join(case_folder, 'all_tables_data_email_phishing.json')
    ProgressBar.get_instance().set_now_log('save to ' + output_path + '...')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=4)
    ProgressBar.get_instance().done_1_task()
    print("모든 테이블 데이터가 'all_tables_data_email_phishing.json' 파일에 저장되었습니다.")
    ProgressBar.get_instance().set_now_log("모든 테이블 데이터가 'all_tables_data_email_phishing.json' 파일에 저장되었습니다.")
    conn.close()
    result_data = GroupParsingProcess(case_id = case_id, result = 1, output_path = output_path)
    db.session.add(result_data)
    db.session.commit()
    ProgressBar.get_instance().progress_end()
    return output_path

def all_tag_process(data, json_data, output_path) :
    user = session.get('username')
    case_id = data['case_id']
    isExist = GroupParingResults.query.filter_by(case_id = case_id).first()
    if isExist :
        return "Exist"
    ProgressBar.get_instance().start_progress(6)
    case_number = Upload_Case.query.filter_by(id=case_id).first().case_number
    case_folder = os.path.join(os.getcwd(), "uploads", user, case_number)
    output_path = os.path.join(case_folder, 'tagged_data_add_upload.json')
    LogTagger_output_path = ""
    LogTagger_results = []
    for i in [LogTagger(json_data), LogTagger_1(json_data), LogTagger_1_1(json_data), LogTagger_1_2(json_data), LogTagger_1_3(json_data)] :
        tagger = i
        if tagger :
            if isinstance(tagger, LogTagger):
                tagger.apply_tags()
                LogTagger_output_path = tagger.save_data(output_path)
            elif isinstance(tagger, (LogTagger_1, LogTagger_1_1, LogTagger_1_2, LogTagger_1_3)):
                tagged_data = None
                with open(output_path, 'r', encoding='utf-8') as f:
                    tagged_data = json.load(f)
                
                tagger.data = tagged_data  # 태그된 데이터를 다시 로드
                LogTagger_results.append(tagger.apply_tags())
        ProgressBar.get_instance().done_1_task()
    group_parsing_resulsts = GroupParingResults(case_id = case_id,
                                                logTagger_output_path = LogTagger_output_path,
                                                result1 = LogTagger_results[0],
                                                result2 = LogTagger_results[1],
                                                result3 = LogTagger_results[2],
                                                result4 = LogTagger_results[3])
    ProgressBar.get_instance().done_1_task()
    db.session.add(group_parsing_resulsts)
    db.session.commit()
    return True