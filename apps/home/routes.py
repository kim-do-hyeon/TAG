# -*- encoding: utf-8 -*-
from apps.home import blueprint
from flask import request, render_template, session, redirect, url_for, flash, Request, jsonify, render_template_string, send_file
import os
from flask_login import login_required
from jinja2 import TemplateNotFound

from apps.case.case_routes import *
from apps.case.case_analyze_routes import *
from apps.case.case_normalization_routes import *
from apps.analyze.analyze_routes import *
from apps.dashboard.dashboard_routes import *
from apps.analyze.analyze_filtering import *
from apps.api.api_connection import *

progress = {}
UPLOAD_FOLDER = 'uploads'  # You can adjust this path as per your project structure
ALLOWED_EXTENSIONS = {'case', 'db', 'mfdb'}  # Define allowed file extensions
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@blueprint.route('/index')
@login_required
def index():
    return redirect_dashboard()


''' Start Case analyze '''
@blueprint.route("/case")
def case_redirect() :
    return redirect("/case/list")

@blueprint.route('/case/<path:subpath>', methods = ["GET", "POST"])
def case(subpath) :
    return redirect_case(subpath)

@blueprint.route('/case/analyze/<int:id>', methods=['GET', 'POST'])
def case_analyze(id):
    return redirect_case_analyze(id)
    
@blueprint.route('/case/analyze/view/<int:id>', methods = ['GET', 'POST'])
def case_view(id) :
    return redirect_case_view(id)


@blueprint.route('/case/analyze/view/table/<int:id>/<string:table_name>', methods=['GET'])
def get_table_data(id, table_name):
    return redirect_get_table_data(id, table_name)

@blueprint.route('/case/analyze/view/table/columns/<int:id>/<string:table_name>', methods=['GET'])
def get_table_columns(id, table_name):
    return redirect_get_table_data(id, table_name)

@blueprint.route('/case/analyze/view/table/data/<int:id>/<string:table_name>', methods=['POST'])
def get_selected_columns_data(id, table_name):
    return redirect_get_selected_columns_data(id, table_name)


@blueprint.route('/case/analyze/usb', methods=['POST'])
def analyze_usb():
    data = request.get_json()
    return redirect_analyze_usb(data, progress)

@blueprint.route('/case/analyze/usb/<int:id>')
def case_analyze_usb_result(id) :
    user = session.get('username')
    return redirect_analyze_usb_result(id, user)

@blueprint.route('/case/analyze/usb/<string:case_number>/<string:usb_data>')
def case_analyze_usb_graph(case_number, usb_data) :
    user = session.get('username')
    return redirect_analze_usb_graph(user, case_number, usb_data)
    

@blueprint.route('/case/analyze/normalization', methods=['POST'])
def analyze_normalization():
    data = request.get_json()
    case_id = data.get('case_id')
    return redirect_analyze_normalization(data, case_id, progress)

@blueprint.route('/case/analyze/normalization/progress/<case_id>', methods=['GET'])
def get_normalization_progress(case_id):
    return redirect_get_normalization_progress(case_id, progress)

@blueprint.route('/case/analyze/filtering', methods = ['POST'])
def case_analyze_filtering() :
    data = request.get_json()
    return redirect_analyze_case_filtering(data)

@blueprint.route('/case/analyze/filtering/<int:id>')
def case_analyze_filtering_result(id) :
    return redirect_case_analyze_filtering_result(id)

@blueprint.route('/case/analyze/filtering/history/<int:id>', methods = ['GET', 'POST'])
def case_analyze_filtering_history(id) :
    return redirect_case_analyze_filtering_history(id)

@blueprint.route('/case/analyze/filtering/history/view/<int:id>', methods = ['GET', 'POST'])
def case_analyze_filtering_history_view(id) :
    return redirect_case_analyze_filtering_history_view(id, 0)

# Version 1.3 - Analyze Final
@blueprint.route('/case/analyze/final', methods = ['POST'])
def case_analyze_final() :
    data = request.get_json()
    return redirect_analyze_case_final(data)

@blueprint.route('/case/analyze/final/<int:id>')
def case_analyze_final_result(id) :
    return redirect_analyze_case_final_result(id)

@blueprint.route('/case/analyze/final/<int:id>/connection')
def case_analyze_final_connection_result(id) :
    return redirect_analyze_case_final_connection_result(id, 0)

@blueprint.route('/case/analyze/porn/<int:id>')
def case_analyze_porn_result(id) :
    return redirect_analyze_case_porn_result(id)

''' End Case analyze '''

''' URI & API '''
@blueprint.route('/logfile_tracking', methods=['POST'])
def find_from_logfile() :
    data = request.get_json()
    return redirect_logfile(data)

@blueprint.route('/file_connection', methods=['POST'])
def file_connection() :
    data = request.get_json()
    return file_connect_node(data)


@blueprint.route('/<template>')
@login_required
def route_template(template):
    try:
        if not template.endswith('.html'):
            template += '.html'
        # Detect the current page
        segment = get_segment(request)
        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment)
    except TemplateNotFound:
        return render_template('home/page-404.html'), 404
    except:
        return render_template('home/page-500.html'), 500

# Helper - Extract current page name from request
def get_segment(request):
    try:
        segment = request.path.split('/')[-1]
        if segment == '':
            segment = 'index'
        return segment
    except:
        return None
