# -*- encoding: utf-8 -*-
from apps.home import blueprint
from flask import request, render_template, session, redirect, url_for, flash, Request, jsonify
import os
from flask_login import login_required
from jinja2 import TemplateNotFound

from apps.case.case_routes import *
from apps.case.case_analyze_routes import *
from apps.case.case_normalization_routes import *
from apps.case.case_graph import *
from apps.dashboard.dashboard_routes import *
from py2neo import Graph


neo4j_url = os.environ.get('neo4j_server')
neo4j_username = os.environ.get('neo4j_id')
neo4j_password = os.environ.get('neo4j_password')
graph = Graph(neo4j_url, auth=(neo4j_username, neo4j_password))




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

@blueprint.route('/case/analyze/view/<int:id>/history', methods = ['GET', 'POST'])
def case_view_history(id) :
    return redirect_case_view_history(id)

@blueprint.route('/case/analyze/view/table/<int:id>/<string:table_name>', methods=['GET'])
def get_table_data(id, table_name):
    return redirect_get_table_data(id, table_name)

@blueprint.route('/case/analyze/view/table/columns/<int:id>/<string:table_name>', methods=['GET'])
def get_table_columns(id, table_name):
    return redirect_get_table_data(id, table_name)

@blueprint.route('/case/analyze/view/table/data/<int:id>/<string:table_name>', methods=['POST'])
def get_selected_columns_data(id, table_name):
    return redirect_get_selected_columns_data(id, table_name)

@blueprint.route('/case/analyze/prompt', methods=['POST'])
def analyze_prompt():
    data = request.get_json()
    return redirect_analyze_prompt(data, progress)

@blueprint.route('/case/analyze/normalization', methods=['POST'])
def analyze_normalization():
    data = request.get_json()
    case_id = data.get('case_id')
    return redirect_analyze_normalization(data, case_id, progress)

@blueprint.route('/case/analyze/normalization/progress/<case_id>', methods=['GET'])
def get_normalization_progress(case_id):
    return redirect_get_normalization_progress(case_id, progress)

@blueprint.route('/case_graph/<int:id>')
def case_graph(id) :
    return render_template("case/connection.html", case_id = id)

@blueprint.route('/case_graph_history/<int:id>')
def case_graph_history(id) :
    return render_template("case/connection_history.html", case_id = id)

@blueprint.route('/case_get_graph_data/<int:id>')
def get_graph_data(id):
    return redirect_get_graph_data(id)

@blueprint.route('/case_get_graph_data_history/<int:id>')
def get_graph_data_history(id):
    return redirect_get_graph_data_history(id)

''' End Case analyze '''

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
