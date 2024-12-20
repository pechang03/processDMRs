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

            app.logger.debug(f"Raw query results: {results}")

            if results is None or len(results) == 0:
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
                    gene_ids_str = row.all_gene_ids.strip('[]')
                    gene_ids = [int(id.strip()) for id in gene_ids_str.split(',') if id.strip()]
                    all_gene_ids.update(gene_ids)

            app.logger.debug(f"Extracted gene IDs: {all_gene_ids}")

            # Get gene symbol mappings for this timepoint
            gene_id_to_symbol = {}
            if all_gene_ids:
                gene_symbols_query = text("""
                    SELECT gene_id, symbol 
                    FROM gene_annotations_view 
                    WHERE gene_id IN ({}) 
                    AND timepoint_id = :timepoint_id
                """.format(','.join(str(id) for id in all_gene_ids)))

                gene_symbols_results = session.execute(
                    gene_symbols_query,
                    {"timepoint_id": timepoint_id}
                ).fetchall()

                app.logger.debug(f"Gene symbols query results: {gene_symbols_results}")
                
                # Create gene ID to symbol mapping
                gene_id_to_symbol = {row.gene_id: row.symbol for row in gene_symbols_results}

            app.logger.debug(f"Gene ID to symbol mapping: {gene_id_to_symbol}")

            # Convert the results to a list of dictionaries
            components = []
            for row in results:
                # Parse the DMR IDs
                dmr_ids_str = row.all_dmr_ids.strip('[]')
                dmr_ids = [int(id.strip()) for id in dmr_ids_str.split(',') if id.strip()]
                
                # Parse the gene IDs
                gene_ids_str = row.all_gene_ids.strip('[]')
                gene_ids = [int(id.strip()) for id in gene_ids_str.split(',') if id.strip()]
                
                # Look up symbols for each gene ID using the mapping
                gene_symbols = []
                for gene_id in gene_ids:
                    symbol = gene_id_to_symbol.get(gene_id)
                    if symbol:
                        gene_symbols.append(symbol)
                    else:
                        # Fallback to ID if no symbol found
                        gene_symbols.append(f"Gene_{gene_id}")

                components.append({
                    "component_id": row.component_id,
                    "timepoint": row.timepoint,
                    "graph_type": row.graph_type,
                    "category": row.category,
                    "dmr_count": row.dmr_count,
                    "gene_count": row.gene_count,
                    "all_dmr_ids": dmr_ids,
                    "all_gene_ids": gene_ids,
                    "gene_symbols": gene_symbols
                })

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
