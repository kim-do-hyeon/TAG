import sqlite3, os
from flask import request, render_template, session, redirect, url_for, flash, Request, jsonify, render_template_string
from apps.authentication.models import Upload_Case, Normalization, GraphData, PromptQuries
from apps import db
from apps.case.case_analyze import case_analyze_view
from apps.case.case_analyze_RAG import search_query
from apps.analyze.analyze_usb import usb_connection
import threading
from flask import current_app

def redirect_analyze_usb_result(id, user) :
    case_number = Upload_Case.query.filter_by(id = id).first().case_number
    files_lists = (os.listdir(os.path.join(os.getcwd(), "uploads", user, case_number)))
    usb_list = []
    for i in files_lists :
        if "USB" in i :
            usb_list.append(i)
    return render_template("analyze/usb_results.html",
                           case_number = case_number,
                            usb_lists = usb_list)

def redirect_analze_usb_graph(user,case_number, usb_data) :
    html_result = os.path.join(os.getcwd(), "uploads", user, case_number, usb_data)
    with open(html_result, 'r') as file:
        html_content = file.read()  # HTML 파일 내용을 읽어옴
    return render_template_string(html_content)  # HTML 내용을 렌더링