# -*- encoding: utf-8 -*-

from apps.home import blueprint
from flask import request, render_template, session, redirect, url_for, flash, Request, jsonify
import os
from werkzeug.utils import secure_filename
from flask_login import login_required
from jinja2 import TemplateNotFound
from apps import db
from apps.case.upload import case_upload
from apps.case.delete import case_delete
from apps.case.normalization import case_normalization
import time
from run import app
from apps.authentication.models import Upload_Case

progress = {}
UPLOAD_FOLDER = 'uploads'  # You can adjust this path as per your project structure
ALLOWED_EXTENSIONS = {'case', 'db', 'mfdb'}  # Define allowed file extensions
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@blueprint.route('/index')
@login_required
def index():
    return render_template('home/index.html', segment='index')

@blueprint.route("/case")
def case_redirect() :
    return redirect("/case/list")

@blueprint.route('/case/<path:subpath>', methods = ["GET", "POST"])
def case(subpath) :
    subpath = subpath.split("/")
    if subpath[0] == "upload" :
        if request.method == "GET" :
            return render_template('case/upload.html')
        elif request.method == "POST" :
            return case_upload()
    elif subpath[0] == "list" :
        user = session.get('username')
        if not user:
            flash('사용자 정보를 찾을 수 없습니다. 다시 로그인 해주세요.', 'danger')
            return redirect('/login')
        user_cases = Upload_Case.query.filter_by(user=user).all()
        return render_template('case/list.html', cases=user_cases)
    elif subpath[0] == "delete" :
        return case_delete()

@blueprint.route('/case/analyze/<int:id>', methods=['GET', 'POST'])
def case_analyze(id):
    user_case = Upload_Case.query.filter_by(id=id).first()
    if not user_case:
        flash('Case not found', 'danger')
        return redirect('/case/list')
    return render_template('case/analyze.html', case=user_case)

@blueprint.route('/case/analyze/prompt', methods=['POST'])
def analyze_prompt():
    data = request.get_json()
    case_id = data.get('case_id')
    prompt = data.get('prompt')
    if not case_id or not prompt:
        return jsonify({'success': False, 'message': 'Invalid input.'}), 400
    return jsonify({'success': True, 'message': 'Prompt submitted successfully!'})

@blueprint.route('/case/analyze/normalization', methods=['POST'])
def analyze_normalization():
    data = request.get_json()
    case_id = data.get('case_id')
    if not case_id:
        return jsonify({'success': False, 'message': 'Invalid input.'}), 400

    # Initialize progress for this task
    progress[case_id] = 0  # Progress starts at 0%

    # Function to run normalization task with the correct application context
    def run_normalization(app, case_id):
        global progress
        with app.app_context():  # Ensure Flask application context is used
            for i in range(1, 11):
                time.sleep(1)  # Simulate time-consuming task
                progress[case_id] = i * 10  # Update progress (10%, 20%, ..., 100%)
            
            # Call the actual normalization function when task is complete
            result = case_normalization(case_id)
            if result:
                # Update the database within the correct context
                Upload_Case.query.filter_by(id=case_id).update(dict(normalization=True))
                db.session.commit()
            progress[case_id] = 100  # Task complete

    # Run the task in a background thread and pass the app instance
    from threading import Thread
    thread = Thread(target=run_normalization, args=(app, case_id))
    thread.start()

    return jsonify({'success': True, 'message': "정규화 처리가 시작되었습니다."})

@blueprint.route('/case/analyze/normalization/progress/<case_id>', methods=['GET'])
def get_normalization_progress(case_id):
    # Return the progress for the given task ID
    progress_value = progress.get(case_id, 0)
    return jsonify({'progress': progress_value})
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
