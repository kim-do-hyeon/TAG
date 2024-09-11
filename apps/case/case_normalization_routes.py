from run import app
import sqlite3, time
from flask import request, render_template, session, redirect, url_for, flash, Request, jsonify
from apps.authentication.models import Upload_Case, Normalization
from apps import db
from apps.case.analyze import case_analyze_view
from apps.case.normalization import case_normalization

def redirect_analyze_normalization(data, case_id) :
    if not case_id:
        return jsonify({'success': False, 'message': 'Invalid input.'}), 400
    progress[case_id] = 0
    def run_normalization(app, case_id):
        global progress
        with app.app_context():
            for i in range(1, 11):
                time.sleep(1)
                progress[case_id] = i * 10
            result = case_normalization(case_id)
            if result:
                Upload_Case.query.filter_by(id=case_id).update(dict(normalization=True))
                db.session.commit()
            progress[case_id] = 100

    from threading import Thread
    thread = Thread(target=run_normalization, args=(app, case_id))
    thread.start()
    return jsonify({'success': True, 'message': "정규화 처리가 시작되었습니다."})

def redirect_get_normalization_progress(case_id) :
    progress_value = progress.get(case_id, 0)
    return jsonify({'progress': progress_value})