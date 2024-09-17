from flask import request, render_template, session, redirect, url_for, flash, Request, jsonify
from apps.case.case_upload import case_upload
from apps.case.case_delete import case_delete
from apps.authentication.models import Upload_Case

def redirect_case(subpath) :
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