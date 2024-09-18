import os
from flask import render_template, session
from apps.authentication.models import *
from apps.dashboard.dashboard_utils import *
from apps import db

def redirect_dashboard() :
    user_upload_cases = Upload_Case.query.filter_by(user = session['username']).all()
    user_normalization_cases = Upload_Case.query.filter_by(user = session['username'], normalization = "1").all()
    user_unnormalization_cases = Upload_Case.query.filter_by(user = session['username'], normalization = None).all()
    user_prompt_queries = db.session.query(PromptQuries).filter(PromptQuries.username == session['username']).all()

    folders, total_size = get_total_size(user_upload_cases)
    total_size_gb = get_total_size_gb(total_size)
    
    folder_labels, folder_percentages = get_folder_percentages(folders, total_size)

    return render_template("dashboard/dashboard.html",
                           user_upload_cases = user_upload_cases,
                           user_normalization_cases = user_normalization_cases,
                           user_unnormalization_cases = user_unnormalization_cases,
                           user_prompt_queries = user_prompt_queries,
                           folder_labels = folder_labels,
                           folder_percentages = folder_percentages,
                           total_size_gb = total_size_gb) 