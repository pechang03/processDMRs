from flask import jsonify, abort
from app.utils.extensions import app
from app.database.connection import get_db_engine
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.database.models import Timepoint, Biclique



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
            bicliques_query = text("""
                SELECT 
                    biclique_id,
                    category,
                    component_id,
                    graph_type,
                    dmr_count,
                    gene_count,
                    timepoint,
                    timepoint_id
                FROM biclique_details_view 
                WHERE timepoint_id = :timepoint_id
            """)

            app.logger.info(f"Executing bicliques query for timepoint: {timepoint.name}")
            biclique_results = session.execute(
                bicliques_query, {"timepoint_id": timepoint_id}
            ).fetchall()

            if not biclique_results:
                app.logger.info(f"No biclique data found for {timepoint.name}")
                return jsonify({
                    "status": "error", 
                    "code": 404,
                    "message": f"No biclique data found for timepoint {timepoint.name}",
                    "details": "The timepoint exists but has no associated biclique data"
                }), 404

            app.logger.info(f"Retrieved {len(biclique_results)} bicliques")

            # Convert the results to a list of dictionaries
            bicliques = [{
                "biclique_id": row.biclique_id,
                "category": row.category, 
                "component_id": row.component_id,
                "graph_type": row.graph_type,
                "dmr_count": row.dmr_count,
                "gene_count": row.gene_count,
                "timepoint": row.timepoint,
                "timepoint_id": row.timepoint_id
            } for row in biclique_results]

            return jsonify({
                "id": timepoint.id,
                "name": timepoint.name,
                "description": timepoint.description,
                "sheet_name": timepoint.sheet_name,
                "bicliques": bicliques
            })

    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")
        return jsonify({
            "status": "error",
            "code": 500,
            "message": "Internal server error while fetching timepoint details",
            "details": str(e) if app.debug else "Please contact the administrator"
        }), 500
