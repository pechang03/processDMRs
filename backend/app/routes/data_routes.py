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

            # Convert the results to a list of dictionaries
            components = []
            for row in results:
                # Parse the DMR IDs with error handling
                dmr_ids = []
                if row.all_dmr_ids:
                    dmr_lists = row.all_dmr_ids.replace('[', '').replace(']', '').split('],[')
                    for dmr_list in dmr_lists:
                        for dmr_id in dmr_list.split(','):
                            try:
                                clean_id = dmr_id.strip('[]').strip()
                                if clean_id:
                                    dmr_ids.append(int(clean_id))
                            except ValueError:
                                app.logger.warning(f"Could not parse DMR ID: {dmr_id}")
                                continue
                
                # Parse the gene IDs with error handling
                gene_ids = []
                if row.all_gene_ids:
                    gene_lists = row.all_gene_ids.replace('[', '').replace(']', '').split('],[')
                    for gene_list in gene_lists:
                        for gene_id in gene_list.split(','):
                            try:
                                clean_id = gene_id.strip('[]').strip()
                                if clean_id:
                                    gene_ids.append(int(clean_id))
                            except ValueError:
                                app.logger.warning(f"Could not parse gene ID: {gene_id}")
                                continue
                
                # Look up symbols for each gene ID using the mapping
                # Convert gene IDs to their symbols
                # Get gene symbols for this component and timepoint
                gene_symbols_query = text("""
                    SELECT DISTINCT g.gene_id, g.symbol 
                    FROM gene_annotations_view g
                    WHERE g.timepoint_id = :timepoint_id 
                    AND g.component_id = :component_id
                    AND g.symbol IS NOT NULL
                    ORDER BY g.symbol
                """)

                try:
                    gene_symbols_results = session.execute(
                        gene_symbols_query,
                        {"timepoint_id": timepoint_id, "component_id": row.component_id}
                    ).fetchall()

                    app.logger.debug(f"Gene symbols query results for component {row.component_id}: {gene_symbols_results}")
                    
                    # Create gene ID to symbol mapping
                    gene_id_to_symbol = {str(row.gene_id): str(row.symbol).strip() for row in gene_symbols_results}
                except Exception as e:
                    app.logger.error(f"Error fetching gene symbols for component {row.component_id}: {str(e)}")
                    gene_id_to_symbol = {}

                gene_symbols = []
                for gene_id in gene_ids:
                    gene_id_str = str(gene_id)
                    try:
                        symbol = gene_id_to_symbol.get(gene_id_str)
                        if symbol and symbol.strip():
                            gene_symbols.append(symbol.strip())
                        else:
                            app.logger.warning(f"No symbol found for gene_id {gene_id} in component {row.component_id}")
                            gene_symbols.append(f"Gene_{gene_id}")
                    except Exception as e:
                        app.logger.error(f"Error processing gene symbol for gene_id {gene_id}: {str(e)}")
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
