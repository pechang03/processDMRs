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
            bicliques_query = text("""
                SELECT 
                    b.biclique_id,
                    b.category,
                    b.component_id,
                    b.graph_type,
                    b.dmr_count,
                    b.gene_count,
                    b.timepoint,
                    b.timepoint_id,
                    b.all_dmr_ids,
                    b.all_gene_ids,
                    array_agg(DISTINCT ga.symbol) as gene_symbols
                FROM biclique_details_view b
                LEFT JOIN unnest(b.all_gene_ids) AS gene_id ON true
                LEFT JOIN gene_annotations_view ga ON ga.gene_id = gene_id 
                    AND ga.timepoint = b.timepoint
                WHERE b.timepoint_id = :timepoint_id
                GROUP BY 
                    b.biclique_id,
                    b.category,
                    b.component_id,
                    b.graph_type,
                    b.dmr_count,
                    b.gene_count,
                    b.timepoint,
                    b.timepoint_id,
                    b.all_dmr_ids,
                    b.all_gene_ids
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
                "timepoint_id": row.timepoint_id,
                "all_dmr_ids": row.all_dmr_ids,
                "gene_symbols": row.gene_symbols
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
