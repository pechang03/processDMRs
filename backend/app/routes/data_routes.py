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
                SELECT 
                    component_id,
                    timepoint,
                    graph_type,
                    categories as category,
                    total_dmr_count as dmr_count,
                    total_gene_count as gene_count,
                    all_dmr_ids,
                    all_gene_ids
                FROM component_details_view
                WHERE timepoint_id = :timepoint_id
            """)
            
            results = session.execute(
                query, {"timepoint_id": timepoint_id}
            ).fetchall()

            if not results:
                return jsonify({
                    "status": "error", 
                    "code": 404,
                    "message": f"No data found for timepoint {timepoint_id}",
                    "details": "The timepoint exists but has no associated data"
                }), 404

            # Get all unique gene IDs from all components
            all_gene_ids = set()
            for row in results:
                if row.all_gene_ids:  # Check if not None
                    # Clean and parse the gene IDs string into integers
                    gene_ids = [int(id.strip()) for id in row.all_gene_ids.strip('[]').split(',') if id.strip().isdigit()]
                    all_gene_ids.update(gene_ids)

            if all_gene_ids:  # Only query if we have gene IDs
                # Query gene symbols for all gene IDs
                # Create the correct number of placeholders for the IN clause
                placeholders = ','.join('?' * len(all_gene_ids))
                gene_symbols_query = text(f"""
                    SELECT gene_id, symbol 
                    FROM gene_annotations_view 
                    WHERE gene_id IN ({placeholders})
                    AND timepoint = ?
                    AND component_id = ?
                """)

                # Convert parameters to a flat list in the correct order
                params = list(all_gene_ids) + [results[0].timepoint, results[0].component_id]

                gene_symbols_results = session.execute(
                    gene_symbols_query, 
                    params
                ).fetchall()

                # Create gene ID to symbol mapping
                gene_id_to_symbol = {str(row.gene_id): row.symbol for row in gene_symbols_results}
            else:
                gene_id_to_symbol = {}

            # Convert the results to a list of dictionaries
            components = []
            for row in results:
                # Get symbols for this component's genes
                gene_symbols = []
                if row.all_gene_ids:
                    gene_symbols = [
                        gene_id_to_symbol.get(str(gene_id), str(gene_id))
                        for gene_id in row.all_gene_ids
                    ]

                components.append({
                    "component_id": row.component_id,
                    "timepoint": row.timepoint,
                    "graph_type": row.graph_type,
                    "category": row.category,
                    "dmr_count": row.dmr_count,
                    "gene_count": row.gene_count,
                    "all_dmr_ids": row.all_dmr_ids,
                    "all_gene_ids": row.all_gene_ids,
                    "gene_symbols": gene_symbols
                })

            timepoint = session.query(Timepoint).filter(Timepoint.id == timepoint_id).first()

            return jsonify({
                "id": timepoint.id,
                "name": timepoint.name,
                "description": timepoint.description,
                "sheet_name": timepoint.sheet_name,
                "components": components  # Changed from bicliques to components
            })

    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")
        return jsonify({
            "status": "error",
            "code": 500,
            "message": "Internal server error while fetching timepoint details",
            "details": str(e) if app.debug else "Please contact the administrator"
        }), 500
