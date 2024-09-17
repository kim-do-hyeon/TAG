from flask import jsonify
from apps.authentication.models import GraphData

def redirect_get_graph_data(id) :
    graph_data_id = id
    if not graph_data_id:
        return jsonify({'success': False, 'message': 'No data found.'}), 404
    graph_record = GraphData.query.filter_by(case_id = id).all()[-1]
    if not graph_record:
        return jsonify({'success': False, 'message': 'Graph data not found.'}), 404
    return jsonify({
        'graphs': graph_record.graph_data,
        'queries': graph_record.query_data
    })

def redirect_get_graph_data_history(id) :
    graph_data_id = id
    if not graph_data_id:
        return jsonify({'success': False, 'message': 'No data found.'}), 404
    graph_record = GraphData.query.filter_by(id = id).first()
    if not graph_record:
        return jsonify({'success': False, 'message': 'Graph data not found.'}), 404
    return jsonify({
        'graphs': graph_record.graph_data,
        'queries': graph_record.query_data
    })