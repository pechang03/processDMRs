from flask import Blueprint, jsonify
from ..database import get_db
from flask import Blueprint, jsonify
from ..database import get_db
from ..database.connection import get_db_engine
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from ..database.models import Timepoint

component_bp = Blueprint('components', __name__)

@component_bp.route('/api/components/<int:timepoint_id>/summary', methods=['GET'])
def get_component_summary_by_timepoint(timepoint_id):
    try:
        db = get_db()
        cursor = db.cursor()
        
        query = """
            SELECT 
                component_id,
                timepoint_id,
                category,
                dmr_count,
                gene_count,
                edge_count,
                biclique_count,
                density
            FROM component_summary_view
            WHERE timepoint_id = ? AND graph_type = 'SPLIT'
            ORDER BY category, component_id
        """
        
        cursor.execute(query, (timepoint_id,))
        results = cursor.fetchall()
        
        components = []
        for row in results:
            components.append({
                'component_id': row[0],
                'timepoint_id': row[1],
                'category': row[2],
                'dmr_count': row[3],
                'gene_count': row[4],
                'edge_count': row[5],
                'biclique_count': row[6],
                'density': row[7]
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

@component_bp.route('/api/components/<int:timepoint_id>/details', methods=['GET'])
def get_component_details_by_timepoint(timepoint_id):
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
            WHERE timepoint_id = ? AND graph_type = 'SPLIT'
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


@component_bp.route("/api/components/<int:component_id>", methods=["GET"])
def get_component_details(component_id):
    """Get detailed information for a specific component."""
    app.logger.info(f"Processing request for component_id={component_id}")

    try:
        engine = get_db_engine()
        app.logger.info("Database engine created successfully")

        with Session(engine) as session:
            # Query component
            component = session.query(Timepoint).filter(Timepoint.id == component_id).first()
            
            if not component:
                app.logger.info(f"No component found with ID {component_id}")
                return jsonify({
                    "status": "error",
                    "code": 404,
                    "message": f"Component with id {component_id} not found",
                    "details": "The requested component does not exist in the database"
                }), 404

            app.logger.info(f"Found component: {component.name} (ID: {component.id})")

            # Get component details
            query = text("""
                WITH gene_symbols AS (
                    SELECT DISTINCT
                        g.component_id,
                        GROUP_CONCAT(DISTINCT g.symbol) as symbols
                    FROM gene_annotations_view g
                    WHERE g.component_id = :component_id
                    GROUP BY g.component_id
                )
                SELECT 
                    c.component_id,
                    c.timepoint,
                    c.graph_type,
                    c.categories as category,
                    c.total_dmr_count as dmr_count,
                    c.total_gene_count as gene_count,
                    c.all_dmr_ids,
                    c.all_gene_ids,
                    gs.symbols as gene_symbols
                FROM component_details_view c
                LEFT JOIN gene_symbols gs ON c.component_id = gs.component_id
                WHERE c.component_id = :component_id
                ORDER BY c.component_id
            """)
            
            results = session.execute(
                query, {"component_id": component_id}
            ).fetchall()

            app.logger.debug(f"Raw query results: {results}")

            if not results:
                return jsonify({
                    "id": component.id,
                    "name": component.name,
                    "description": component.description,
                    "sheet_name": component.sheet_name,
                    "components": []
                })

            # Convert the results to a list of dictionaries
            components = []
            for row in results:
                # Parse DMR IDs
                dmr_ids = []
                if row.all_dmr_ids:
                    try:
                        # Clean the string and split into individual IDs
                        clean_str = row.all_dmr_ids.replace('[', '').replace(']', '')
                        if clean_str:
                            dmr_ids = [int(x.strip()) for x in clean_str.split(',') if x.strip()]
                    except Exception as e:
                        app.logger.warning(f"Error parsing DMR IDs: {e}")

                # Parse gene symbols - ensure it's a list
                gene_symbols = []
                if row.gene_symbols:
                    gene_symbols = [s.strip() for s in row.gene_symbols.split(',') if s.strip()]

                component = {
                    "component_id": row.component_id,
                    "timepoint": row.timepoint,
                    "graph_type": row.graph_type,
                    "category": row.category,
                    "dmr_count": row.dmr_count or 0,
                    "gene_count": row.gene_count or 0,
                    "all_dmr_ids": dmr_ids,
                    "gene_symbols": gene_symbols
                }
                
                app.logger.debug(f"Processed component: {component}")
                components.append(component)

            app.logger.debug(f"Final components data: {components}")

            response_data = {
                "id": component.id,
                "name": component.name, 
                "description": component.description,
                "sheet_name": component.sheet_name,
                "components": components
            }
            
            app.logger.debug(f"Sending response: {response_data}")
            return jsonify(response_data)

    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")
        return jsonify({
            "status": "error",
            "code": 500,
            "message": "Internal server error while fetching component details",
            "details": str(e) if app.debug else "Please contact the administrator"
        }), 500
