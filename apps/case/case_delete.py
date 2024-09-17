import os
from apps import db
from apps.authentication.models import Upload_Case
from flask import request, session, redirect, url_for, flash

def case_delete() :
    case_id = request.form.get('case_id')
    case_to_delete = Upload_Case.query.get(case_id)

    if case_to_delete:
        # Optionally, remove the file from the filesystem if needed
        if os.path.exists(case_to_delete.file):
            os.remove(case_to_delete.file)

        # Delete the case record from the database
            db.session.delete(case_to_delete)
            db.session.commit()
            flash('Case file deleted successfully.', 'success')
        else:
            flash('Case file not found.', 'danger')
        
        return redirect('/case/list')