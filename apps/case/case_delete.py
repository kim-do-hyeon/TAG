import os
from apps import db
import shutil
from apps.authentication.models import Upload_Case, Analyzed_file_list, Mail_final, Normalization, PrinterData_final, Porn_Data, UsbData, UsbData_final
from flask import request, session, redirect, url_for, flash

def case_delete() :
    case_id = request.form.get('case_id')
    case_to_delete = Upload_Case.query.get(case_id)
    try : db.session.delete(Analyzed_file_list.query.get(case_id))
    except : pass
    try : db.session.delete(Mail_final.query.get(case_id))
    except : pass
    try : db.session.delete(Normalization.query.get(case_id))
    except : pass
    try : db.session.delete(PrinterData_final.query.get(case_id))
    except : pass
    try : db.session.delete(Porn_Data.query.get(case_id))
    except : pass
    try : db.session.delete(UsbData.query.get(case_id))
    except : pass
    try : db.session.delete(UsbData_final.query.get(case_id))
    except : pass

    if case_to_delete:
        case_path = os.path.dirname(os.path.join(os.getcwd(), case_to_delete.file))
        if os.path.exists(case_path):
            shutil.rmtree(case_path)
            db.session.delete(case_to_delete)
            db.session.commit()
            flash('Case file deleted successfully.', 'success')
        else:
            flash('Case file not found.', 'danger')
        
        return redirect('/case/list')