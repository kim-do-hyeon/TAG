# -*- encoding: utf-8 -*-

from apps.home import blueprint
from flask import request, render_template, session, redirect, url_for, flash, Request
import os
from werkzeug.utils import secure_filename
from flask_login import login_required
from jinja2 import TemplateNotFound
from apps.case.upload import case_upload

UPLOAD_FOLDER = 'uploads'  # You can adjust this path as per your project structure
ALLOWED_EXTENSIONS = {'case', 'db', 'mfdb'}  # Define allowed file extensions
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@blueprint.route('/index')
@login_required
def index():
    return render_template('home/index.html', segment='index')

@blueprint.route("/case")
def case_redirect() :
    return redirect("/case/upload")

@blueprint.route('/case/<path:subpath>', methods = ["GET", "POST"])
def case(subpath) :
    session['username'] = "test"
    if subpath == "upload" :
        if request.method == "GET" :
            return render_template('case/upload.html')
        elif request.method == "POST" :
            return case_upload()

    return subpath



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
