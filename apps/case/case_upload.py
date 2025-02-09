import os
from apps import db
from flask import request, session, redirect, url_for, flash
from werkzeug.utils import secure_filename
from apps.authentication.models import Upload_Case

UPLOAD_FOLDER = 'uploads'  # You can adjust this path as per your project structure
ALLOWED_EXTENSIONS = {'case', 'db', 'mfdb'}  # Define allowed file extensions

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def case_upload() :
    analyst = request.form.get('analyst')
    case_number = request.form.get('caseNumber')
    description = request.form.get('description')
    case_type = request.form.get('caseType')
    file = request.files.get('caseFile')
    if case_type == "음란물" :
        addtitonal_file = request.files.get('caseAttachments')

    # Check if file is present and allowed
    if file and allowed_file(file.filename):
        # Get the current user from the session
        user = session.get('username')  # Assuming 'username' is stored in session
        if not user:
            flash('사용자 정보를 찾을 수 없습니다. 다시 로그인 해주세요.', 'danger')
            return redirect('/case/upload')

        # Create the user-specific folder
        user_folder = os.path.join(UPLOAD_FOLDER, secure_filename(user))
        os.makedirs(user_folder, exist_ok=True)

        # Create the case-specific folder
        case_folder = os.path.join(user_folder, secure_filename(case_number))
        os.makedirs(case_folder, exist_ok=True)

        # Save the uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(case_folder, filename)
        file.save(file_path)
        
        if case_type == "음란물" : 
            addititonal_file_name = secure_filename(addtitonal_file.filename)
            addititonal_file_path = os.path.join(case_folder, addititonal_file_name)
            addtitonal_file.save(addititonal_file_path)

        # Save the upload details to the database
        new_case = Upload_Case(
            user = user,
            analyst=analyst,
            case_number=case_number,
            description=description,
            file=file_path,
            case_type = case_type,
            normalization = None
        )
        db.session.add(new_case)
        db.session.commit()

        flash('정상적으로 업로드 되었습니다!', 'success')
        return redirect('/case/upload')
    else:
        flash('파일 타입이 올바르지 않습니다.', 'danger')
        return redirect('/case/upload')