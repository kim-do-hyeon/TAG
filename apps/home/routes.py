# -*- encoding: utf-8 -*-

from apps.home import blueprint
from flask import request, render_template, session, redirect, url_for, flash, Request
import os
from werkzeug.utils import secure_filename
from flask_login import login_required
from jinja2 import TemplateNotFound
from apps.case.upload import case_upload
from apps.case.delete import case_delete

from apps.authentication.models import Upload_Case

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
    session['username'] = "test"
    if subpath == "upload" :
        if request.method == "GET" :
            return render_template('case/upload.html')
        elif request.method == "POST" :
            return case_upload()
    elif subpath == "list" :
        user = session.get('username')
        if not user:
            flash('사용자 정보를 찾을 수 없습니다. 다시 로그인 해주세요.', 'danger')
            return redirect('/login')
        user_cases = Upload_Case.query.filter_by(user=user).all()
        return render_template('case/list.html', cases=user_cases)
    elif subpath == "delete" :
        return case_delete()


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
