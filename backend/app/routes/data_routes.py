from flask import jsonify, abort
from ..utils.extensions import app
from ..database.connection import get_db_engine
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from ..database.models import Timepoint, Biclique



@app.route("/api/timepoint-stats/<int:timepoint_id>", methods=["GET"])
def get_timepoint_stats(timepoint_id):
    """Get detailed information for a specific timepoint."""
    app.logger.info(f"Processing request for timepoint_id={timepoint_id}")

    try:
        engine = get_db_engine()
        app.logger.info("Database engine created successfully")

        with Session(engine) as session:
            # Query timepoint
            timepoint = session.query(Timepoint).filter(Timepoint.id == timepoint_id).first()
            
            if not timepoint:
                app.logger.info(f"No timepoint found with ID {timepoint_id}")
                return jsonify({
                    "status": "error",
                    "code": 404,
                    "message": f"Timepoint with id {timepoint_id} not found",
                    "details": "The requested timepoint does not exist in the database"
                }), 404

            app.logger.info(f"Found timepoint: {timepoint.name} (ID: {timepoint.id})")

            # Get biclique details
            # First get the bicliques data
            # Get the component details
            query = text("""
                WITH gene_symbols AS (
                    SELECT DISTINCT
                        g.component_id,
                        GROUP_CONCAT(DISTINCT g.symbol) as symbols
                    FROM gene_annotations_view g
                    WHERE g.timepoint_id = :timepoint_id
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
                WHERE c.timepoint_id = :timepoint_id
                ORDER BY c.component_id
            """)
            
            results = session.execute(
                query, {"timepoint_id": timepoint_id}
            ).fetchall()

            app.logger.debug(f"Raw query results: {results}")

            if not results:
                return jsonify({
                    "id": timepoint.id,
                    "name": timepoint.name,
                    "description": timepoint.description,
                    "sheet_name": timepoint.sheet_name,
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

            timepoint = session.query(Timepoint).filter(Timepoint.id == timepoint_id).first()

            response_data = {
                "id": timepoint.id,
                "name": timepoint.name, 
                "description": timepoint.description,
                "sheet_name": timepoint.sheet_name,
                "components": components
            }
            
            app.logger.debug(f"Sending response: {response_data}")
            return jsonify(response_data)

    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")
        return jsonify({
            "status": "error",
            "code": 500,
            "message": "Internal server error while fetching timepoint details",
            "details": str(e) if app.debug else "Please contact the administrator"
        }), 500
