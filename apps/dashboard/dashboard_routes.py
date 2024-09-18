from flask import render_template, session
from apps.authentication.models import *
from apps import db
def redirect_dashboard() :
    user_upload_cases = Upload_Case.query.filter_by(user = session['username']).all()
    user_normalization_cases = Upload_Case.query.filter_by(user = session['username'], normalization = "1").all()
    user_unnormalization_cases = Upload_Case.query.filter_by(user = session['username'], normalization = None).all()
    user_prompt_queries = db.session.query(PromptQuries).filter(PromptQuries.username == session['username']).all()

    return render_template("dashboard/dashboard.html",
                           user_upload_cases = user_upload_cases,
                           user_normalization_cases = user_normalization_cases,
                           user_unnormalization_cases = user_unnormalization_cases,
                           user_prompt_queries = user_prompt_queries) 