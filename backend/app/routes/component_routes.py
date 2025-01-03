from flask import Blueprint, jsonify, request
from flask_cors import CORS
from ..utils.extensions import app
from ..database import get_db_engine, get_db_session
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from ..database.models import Timepoint
from ..schemas import ComponentSummarySchema, ComponentDetailsSchema
from typing import List, Dict, Any

component_bp = Blueprint("components", __name__)
CORS(component_bp)  # Enable CORS for all routes in this blueprint


@component_bp.route("/api/components/<int:timepoint_id>/summary", methods=["GET"])
def get_component_summary_by_timepoint(timepoint_id):
    app.logger.info(f"Processing summary request for timepoint_id={timepoint_id}")
    app.logger.debug(f"Request headers: {request.headers}")
    try:
        engine = get_db_engine()
        app.logger.info("Database engine created successfully")

        # First verify timepoint exists
        with Session(engine) as session:
            timepoint = session.query(Timepoint).filter_by(id=timepoint_id).first()

            if not timepoint:
                app.logger.error(f"Timepoint {timepoint_id} not found")
                return jsonify(
                    {
                        "status": "error",
                        "message": f"Timepoint {timepoint_id} not found",
                    }
                ), 404

            app.logger.info(f"Found timepoint: {timepoint.name}")

            # Execute component summary query in same session
            query = text("""
                SELECT 
                    component_id,
                    timepoint_id,
                    timepoint,
                    graph_type,
                    category,
                    size,
                    dmr_count,
                    gene_count,
                    edge_count,
                    density,
                    biclique_count,
                    biclique_categories
                FROM component_summary_view
                WHERE timepoint_id = :timepoint_id AND LOWER(graph_type) = 'split'
            """)

            app.logger.info("Executing component summary query")
            results = session.execute(query, {"timepoint_id": timepoint_id}).fetchall()
            app.logger.info(f"Query returned {len(results)} rows")

            components = []
            for row in results:
                component_data = {
                    "component_id": row.component_id,
                    "timepoint_id": row.timepoint_id,
                    "timepoint": row.timepoint,
                    "graph_type": row.graph_type,
                    "category": row.category,
                    "size": row.size,
                    "dmr_count": row.dmr_count,
                    "gene_count": row.gene_count,
                    "edge_count": row.edge_count,
                    "density": row.density,
                    "biclique_count": row.biclique_count,
                    "biclique_categories": row.biclique_categories,
                }
                try:
                    component = ComponentSummarySchema(**component_data)
                    components.append(component.dict())
                    # app.logger.debug(f"Processed component summary: {component.dict()}")
                except Exception as e:
                    app.logger.error(f"Error validating component summary: {e}")
                    continue

            app.logger.info(f"Returning {len(components)} component summaries")
            response = jsonify(
                {"status": "success", "timepoint": timepoint.name, "data": components}
            )
            response.headers.add("Access-Control-Allow-Origin", "*")
            return response

    except Exception as e:
        app.logger.error(f"Error processing component summary request: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@component_bp.route("/api/components/<int:timepoint_id>/<int:component_id>/details", methods=["GET"])
def get_component_details(timepoint_id, component_id):
    app.logger.info(f"Getting details for timepoint {timepoint_id}, component {component_id}")
    try:
        engine = get_db_engine()
        with Session(engine) as session:
            # First verify the component exists
            verify_query = text("""
                SELECT COUNT(*) 
                FROM component_details_view
                WHERE timepoint_id = :timepoint_id 
                AND component_id = :component_id
                AND LOWER(graph_type) = 'split'
            """)
            
            count = session.execute(
                verify_query, 
                {"timepoint_id": timepoint_id, "component_id": component_id}
            ).scalar()
            
            app.logger.info(f"Found {count} matching components")
            
            if count == 0:
                app.logger.error(f"No component found with ID {component_id} for timepoint {timepoint_id}")
                return jsonify({
                    "status": "error",
                    "message": f"Component {component_id} not found for timepoint {timepoint_id}"
                }), 404

            # If component exists, get the details
            query = text("""
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
                WHERE timepoint_id = :timepoint_id 
                AND component_id = :component_id
                AND LOWER(graph_type) = 'split'
            """)
            
            result = session.execute(query, {
                "timepoint_id": timepoint_id,
                "component_id": component_id
            }).first()
            
            if not result:
                app.logger.error("Query returned no results after verifying existence")
                return jsonify({
                    "status": "error",
                    "message": "Failed to retrieve component details"
                }), 500
                
            # Log the actual data being returned
            component_data = {
                "timepoint_id": result.timepoint_id,
                "timepoint": result.timepoint,
                "component_id": result.component_id,
                "graph_type": result.graph_type,
                "categories": result.categories,
                "total_dmr_count": result.total_dmr_count,
                "total_gene_count": result.total_gene_count,
                "all_dmr_ids": result.all_dmr_ids.split(",") if result.all_dmr_ids else [],
                "all_gene_ids": result.all_gene_ids.split(",") if result.all_gene_ids else []
            }
            
            app.logger.info(f"Returning details for component {component_id}")
            app.logger.debug(f"Component data: {component_data}")
            
            return jsonify({
                "status": "success",
                "data": component_data
            })
            
    except Exception as e:
        app.logger.error(f"Error getting component details: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@component_bp.route("/api/genes/symbols", methods=["POST"])
def get_gene_symbols():
    try:
        data = request.get_json()
        gene_ids = data.get('gene_ids', [])
        
        if not gene_ids:
            return jsonify({"status": "error", "message": "No gene IDs provided"}), 400
            
        engine = get_db_engine()
        with Session(engine) as session:
            query = text("""
                SELECT id, symbol 
                FROM genes 
                WHERE id = ANY(:gene_ids)
            """)
            
            results = session.execute(query, {"gene_ids": gene_ids}).fetchall()
            symbols = {str(row.id): row.symbol for row in results}
            
            return jsonify({
                "status": "success",
                "symbols": symbols
            })
            
    except Exception as e:
        app.logger.error(f"Error getting gene symbols: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@component_bp.route("/api/dmrs/names", methods=["POST"])
def get_dmr_names():
    try:
        data = request.get_json()
        dmr_ids = data.get('dmr_ids', [])
        
        if not dmr_ids:
            return jsonify({"status": "error", "message": "No DMR IDs provided"}), 400
            
        engine = get_db_engine()
        with Session(engine) as session:
            query = text("""
                SELECT id, name 
                FROM dmrs 
                WHERE id = ANY(:dmr_ids)
            """)
            
            results = session.execute(query, {"dmr_ids": dmr_ids}).fetchall()
            names = {str(row.id): row.name for row in results}
            
            return jsonify({
                "status": "success",
                "names": names
            })
            
    except Exception as e:
        app.logger.error(f"Error getting DMR names: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@component_bp.route("/api/components/<int:timepoint_id>/details", methods=["GET"])
def get_component_details_by_timepoint(timepoint_id):
    try:
        engine = get_db_engine()

        with Session(engine) as session:
            query = text("""
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
                WHERE timepoint_id = :timepoint_id AND LOWER(graph_type) = 'split'
            """)

            app.logger.info("Executing component details query")
            results = session.execute(query, {"timepoint_id": timepoint_id}).fetchall()
            app.logger.info(f"Query returned {len(results)} rows")

            components = []
            for row in results:
                app.logger.debug(f"Processing row: {row}")
                # Convert row tuple to dict matching Pydantic model
                component_data = {
                    "timepoint_id": row.timepoint_id,
                    "timepoint": row.timepoint,
                    "component_id": row.component_id,
                    "graph_type": row.graph_type,
                    "categories": row.categories,
                    "total_dmr_count": row.total_dmr_count,
                    "total_gene_count": row.total_gene_count,
                    "all_dmr_ids": row.all_dmr_ids.split(",")
                    if row.all_dmr_ids
                    else [],
                    "all_gene_ids": row.all_gene_ids.split(",")
                    if row.all_gene_ids
                    else [],
                }
                try:
                    # Validate with Pydantic
                    component = ComponentDetailsSchema(**component_data)
                    components.append(component.dict())
                    app.logger.debug(f"Processed component details: {component.dict()}")
                except Exception as e:
                    app.logger.error(f"Error validating component details: {e}")
                    continue

            app.logger.info(f"Returning {len(components)} component details")
            return jsonify({"status": "success", "data": components})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
