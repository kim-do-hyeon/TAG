from flask import jsonify, session
from apps.authentication.models import Normalization
from apps.analyze.USB.make_usb_analysis_db import extract_transaction_LogFile_Analysis
import sqlite3
import pandas as pd

def redirect_logfile(data) :
    try :
        case_id = data.get('case_id')
        filename = data.get('filename')
        db_path = Normalization.query.filter_by(normalization_definition=case_id).first().file
        
        db_conn = sqlite3.connect(db_path)
        
        result = extract_transaction_LogFile_Analysis(db_conn, filename)
        for key, value in result.items() :
            tmp = value[['Event_Date/Time_-_UTC_(yyyy-mm-dd)', 'Original_File_Name', 'Current_File_Name', 'File_Operation']]
            tmp['Event_Date/Time_-_UTC_(yyyy-mm-dd)'] = tmp['Event_Date/Time_-_UTC_(yyyy-mm-dd)'].astype(str)
            result[key] = tmp.to_dict(orient='records')
        result['success'] = True     
        
        return jsonify(result)
    except Exception as e :
        return jsonify({'success' : False, 'message' : e})
    
    
    