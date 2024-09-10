import sqlite3
from flask import request, render_template, session, redirect, url_for, flash, Request, jsonify
from apps.authentication.models import Upload_Case, Normalization
from apps import db
from apps.case.analyze import case_analyze_view
from apps.case.analyze_RAG import search_query

    
def redirect_case_analyze(id) :
    user_case = Upload_Case.query.filter_by(id=id).first()
    if not user_case:
        flash('Case not found', 'danger')
        return redirect('/case/list')
    return render_template('case/analyze.html', case=user_case)

def redirect_case_view(id) :
    user_case = Upload_Case.query.filter_by(id = id).first()
    if not user_case:
        flash('Case not found', 'danger')
        return redirect('/case/list')
    table_names = case_analyze_view(user_case)
    return render_template('case/view.html',
        case = user_case,
        table_names = table_names,
        # record_counts = sum(record_counts)
        )

def redirect_get_table_data(id, table_name) :
    user_case = Upload_Case.query.filter_by(id=id).first()
    normalization_case = Normalization.query.filter_by(normalization_definition=user_case.id).first()
    normalization_db_file = normalization_case.file
    
    if not user_case:
        return jsonify({'success': False, 'message': 'Case not found'}), 404
    
    # Fetch table data from the database
    conn = sqlite3.connect(normalization_db_file)  # Assuming the file is the database path
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
    except Exception as e:
        return jsonify({'success': False, 'message': f"Error fetching data: {str(e)}"}), 400
    finally:
        cursor.close()
        conn.close()
    
    # Convert rows into a list of dictionaries, excluding NULL values within rows
    table_data = [
        {col: val for col, val in zip(columns, row) if val is not None}  # Include only non-NULL values
        for row in rows
    ]
    
    return jsonify({'success': True, 'data': table_data, 'columns': columns})

def redirect_analyze_prompt(data) :
    case_id = data.get('case_id')
    prompt = data.get('prompt')
    if not case_id or not prompt:
        return jsonify({'success': False, 'message': 'Invalid input.'}), 400
    else :
        db_path = Normalization.query.filter_by(normalization_definition = case_id).first().file
        search_query(prompt, db_path)
    return jsonify({'success': True, 'message': 'Prompt submitted successfully!'})