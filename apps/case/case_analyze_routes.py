import sqlite3, os
from flask import request, render_template, session, redirect, url_for, flash, Request, jsonify
from apps.authentication.models import Upload_Case, Normalization, GraphData, PromptQuries, UsbData
from apps import db
from apps.case.case_analyze import case_analyze_view
from apps.analyze.analyze_usb import usb_connection
import threading
from flask import current_app

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
    if not user_case:
        return jsonify({'success': False, 'message': 'Case not found'}), 404

    normalization_case = Normalization.query.filter_by(normalization_definition=user_case.id).first()
    if not normalization_case:
        return jsonify({'success': False, 'message': 'Normalization case not found'}), 404

    normalization_db_file = normalization_case.file
    conn = sqlite3.connect(normalization_db_file)
    cursor = conn.cursor()

    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        if not columns:
            return jsonify({'success': False, 'message': 'No columns found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': f"Error fetching columns: {str(e)}"}), 400
    finally:
        cursor.close()
        conn.close()

    return jsonify({'success': True, 'columns': columns})

def redirect_get_selected_columns_data(id, table_name):
    user_case = Upload_Case.query.filter_by(id=id).first()
    if not user_case:
        return jsonify({'success': False, 'message': 'Case not found'}), 404

    normalization_case = Normalization.query.filter_by(normalization_definition=user_case.id).first()
    if not normalization_case:
        return jsonify({'success': False, 'message': 'Normalization case not found'}), 404

    normalization_db_file = normalization_case.file
    selected_columns = request.json.get('columns', [])

    # Check if selected_columns is a valid list and not empty
    if not isinstance(selected_columns, list) or not selected_columns:
        return jsonify({'success': False, 'message': 'Invalid columns format or no columns selected'}), 400

    conn = sqlite3.connect(normalization_db_file)
    cursor = conn.cursor()

    # Fetch all valid column names from the table
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        valid_columns = {col[1] for col in cursor.fetchall()}  # Using a set for faster lookup
    except Exception as e:
        return jsonify({'success': False, 'message': f"Error fetching table info: {str(e)}"}), 400

    # Filter selected_columns to only include valid columns
    selected_columns = [col for col in selected_columns if col in valid_columns]

    if not selected_columns:
        return jsonify({'success': False, 'message': 'None of the selected columns are valid.'}), 400

    try:
        # Safe string join with quotes for SQL execution
        columns_str = ', '.join(f'"{col}"' for col in selected_columns)
        cursor.execute(f"SELECT {columns_str} FROM {table_name}")
        rows = cursor.fetchall()
    except Exception as e:
        return jsonify({'success': False, 'message': f"Error fetching data: {str(e)}"}), 400
    finally:
        cursor.close()
        conn.close()

    table_data = [
        {col: val for col, val in zip(selected_columns, row) if val is not None}
        for row in rows
    ]

    return jsonify({'success': True, 'data': table_data, 'columns': selected_columns})


