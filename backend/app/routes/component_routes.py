from flask import Blueprint, jsonify
from ..database import get_db

component_bp = Blueprint('components', __name__)

@component_bp.route('/timepoint/<int:timepoint_id>/components', methods=['GET'])
def get_components_by_timepoint(timepoint_id):
    try:
        db = get_db()
        cursor = db.cursor()
        
        query = """
            SELECT 
                timepoint_id,
                timepoint,
                component_id,
                graph_type,
                categories,
                total_dmr_count,
                total_gene_count,
                all_dmr_ids,
                all_gene_ids
            FROM component_details_view
            WHERE timepoint_id = ?
        """
        
        cursor.execute(query, (timepoint_id,))
        results = cursor.fetchall()
        
        components = []
        for row in results:
            components.append({
                'timepoint_id': row[0],
                'timepoint': row[1],
                'component_id': row[2],
                'graph_type': row[3],
                'categories': row[4],
                'total_dmr_count': row[5],
                'total_gene_count': row[6],
                'all_dmr_ids': row[7].split(',') if row[7] else [],
                'all_gene_ids': row[8].split(',') if row[8] else []
            })
        
        return jsonify({
            'status': 'success',
            'data': components
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

