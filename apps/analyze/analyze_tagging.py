import pandas as pd
import sqlite3
import json, os
from apps import db
from flask import session
from apps.authentication.models import Upload_Case, GroupParingResults
from apps.analyze.analyze_tag_class import LogTaggerManager
from apps.manager.progress_bar import *

def all_tag_process(data) :
    progressBar = ProgressBar.get_instance()
    progressBar.append_log("Tagging Process")
    print("Tagging Process")
    user = session.get('username')
    case_id = data['case_id']
    # isExist = GroupParingResults.query.filter_by(case_id = case_id).first()
    # if isExist :
    #     return "Exist"
    case_number = Upload_Case.query.filter_by(id=case_id).first().case_number
    case_folder = os.path.join(os.getcwd(), "uploads", user, case_number)
    db_path = os.path.join(case_folder, "normalization.db")
    db_path = db_path.replace('\\', '/')
    db_url = f"sqlite:///{db_path}"
    manager = LogTaggerManager(db_url)
    manager.run_tagger()

    return True