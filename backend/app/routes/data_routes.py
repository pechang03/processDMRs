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
                    b.all_gene_ids
                FROM biclique_details_view b
                WHERE b.timepoint_id = :timepoint_id
            """)

            biclique_results = session.execute(
                bicliques_query, {"timepoint_id": timepoint_id}
            ).fetchall()

            if not biclique_results:
                return jsonify({
                    "status": "error", 
                    "code": 404,
                    "message": f"No biclique data found for timepoint {timepoint_id}",
                    "details": "The timepoint exists but has no associated biclique data"
                }), 404

            # Get all unique gene IDs from all bicliques
            all_gene_ids = set()
            for row in biclique_results:
                if row.all_gene_ids:  # Check if not None
                    all_gene_ids.update(row.all_gene_ids)

            # Query gene symbols for all gene IDs
            gene_symbols_query = text("""
                SELECT gene_id, symbol 
                FROM gene_annotations_view 
                WHERE gene_id IN :gene_ids 
                AND timepoint = :timepoint
            """)

            gene_symbols_results = session.execute(
                gene_symbols_query, 
                {
                    "gene_ids": tuple(all_gene_ids),
                    "timepoint": biclique_results[0].timepoint
                }
            ).fetchall()

            # Create gene ID to symbol mapping
            gene_id_to_symbol = {str(row.gene_id): row.symbol for row in gene_symbols_results}

            # Convert the results to a list of dictionaries
            bicliques = []
            for row in biclique_results:
                # Get symbols for this biclique's genes
                gene_symbols = []
                if row.all_gene_ids:
                    gene_symbols = [
                        gene_id_to_symbol.get(str(gene_id), str(gene_id))
                        for gene_id in row.all_gene_ids
                    ]

                bicliques.append({
                    "biclique_id": row.biclique_id,
                    "category": row.category, 
                    "component_id": row.component_id,
                    "graph_type": row.graph_type,
                    "dmr_count": row.dmr_count,
                    "gene_count": row.gene_count,
                    "timepoint": row.timepoint,
                    "timepoint_id": row.timepoint_id,
                    "all_dmr_ids": row.all_dmr_ids,
                    "all_gene_ids": row.all_gene_ids,
                    "gene_symbols": gene_symbols
                })

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
