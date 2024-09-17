from run import app
import sqlite3, time
from flask import request, render_template, session, redirect, url_for, flash, Request, jsonify
from apps.authentication.models import Upload_Case, Normalization
from apps import db
from apps.case.case_analyze import case_analyze_view
from apps.case.case_normalization import case_normalization

def redirect_analyze_normalization(data, case_id, progress) :
    if not case_id:
        return jsonify({'success': False, 'message': 'Invalid input.'}), 400
    progress[case_id] = 0
    def run_normalization(app, case_id):
        
        with app.app_context():
            result = case_normalization(case_id, progress)
            if result:
                Upload_Case.query.filter_by(id=case_id).update(dict(normalization=True))
                db.session.commit()
            # progress[case_id] = 100

    from threading import Thread
    thread = Thread(target=run_normalization, args=(app, case_id))
    thread.start()
    return jsonify({'success': True, 'message': "정규화 처리가 시작되었습니다."})

def redirect_get_normalization_progress(case_id, progress) :
    progress_value = progress.get(case_id, 0)
    return jsonify({'progress': progress_value})