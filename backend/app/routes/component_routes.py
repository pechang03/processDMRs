import json
from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from ..schemas import (
    ComponentSummarySchema,
    ComponentDetailsSchema,
    GeneTimepointAnnotationSchema,
    DmrTimepointAnnotationSchema,
    NodeSymbolRequest,
    NodeStatusRequest
)
from flask_cors import CORS
from ..utils.extensions import app
from ..database import get_db_engine, get_db_session
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from ..database.models import Timepoint
from ..schemas import (
    ComponentSummarySchema,
    ComponentDetailsSchema,
    GeneTimepointAnnotationSchema,
    DmrTimepointAnnotationSchema,
)
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


@component_bp.route(
    "/api/components/<int:timepoint_id>/<int:component_id>/details", methods=["GET"]
)
def get_component_details(timepoint_id, component_id):
    app.logger.info(
        f"Getting details for timepoint {timepoint_id}, component {component_id}"
    )
    try:
        engine = get_db_engine()
        with Session(engine) as session:
            # Get the component details including bicliques
            query = text("""
                WITH component_info AS (
                    SELECT 
                        cd.timepoint_id,
                        cd.timepoint,
                        cd.component_id,
                        cd.graph_type,
                        cd.categories,
                        cd.total_dmr_count,
                        cd.total_gene_count,
                        cd.all_dmr_ids,
                        cd.all_gene_ids
                    FROM component_details_view cd
                    WHERE cd.timepoint_id = :timepoint_id 
                    AND cd.component_id = :component_id
                    AND LOWER(cd.graph_type) = 'split'
                ),
                biclique_info AS (
                    SELECT 
                        b.id as biclique_id,
                        b.dmr_ids,
                        b.gene_ids,
                        b.category
                    FROM bicliques b
                    JOIN component_bicliques cb ON b.id = cb.biclique_id
                    WHERE cb.component_id = :component_id
                    AND cb.timepoint_id = :timepoint_id
                )
                SELECT 
                    ci.*,
                    json_group_array(
                        json_object(
                            'biclique_id', bi.biclique_id,
                            'category', bi.category,
                            'dmr_ids', bi.dmr_ids,
                            'gene_ids', bi.gene_ids
                        )
                    ) as bicliques
                FROM component_info ci
                LEFT JOIN biclique_info bi ON 1=1
                GROUP BY ci.component_id
            """)

            result = session.execute(
                query, {"timepoint_id": timepoint_id, "component_id": component_id}
            ).first()

            if not result:
                app.logger.error("Query returned no results")
                return jsonify(
                    {
                        "status": "error",
                        "message": "Failed to retrieve component details",
                    }
                ), 500

            # Parse arrays
            def parse_array_string(arr_str):
                if not arr_str:
                    return []
                cleaned = arr_str.replace("[", "").replace("]", "").strip()
                return [int(x.strip()) for x in cleaned.split(",") if x.strip()]

            all_dmr_ids = parse_array_string(result.all_dmr_ids)
            all_gene_ids = parse_array_string(result.all_gene_ids)

            # Parse the bicliques JSON array
            bicliques = json.loads(result.bicliques) if result.bicliques else []

            component_data = {
                "timepoint_id": result.timepoint_id,
                "timepoint": result.timepoint,
                "component_id": result.component_id,
                "graph_type": result.graph_type,
                "categories": result.categories,
                "total_dmr_count": result.total_dmr_count,
                "total_gene_count": result.total_gene_count,
                "biclique_count": len(bicliques),
                "all_dmr_ids": all_dmr_ids,
                "all_gene_ids": all_gene_ids,
                "bicliques": bicliques,
            }

            app.logger.info(f"Returning details for component {component_id}")
            app.logger.debug(f"Component data: {component_data}")

            return jsonify({"status": "success", "data": component_data})

    except Exception as e:
        app.logger.error(f"Error getting component details: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@component_bp.route("/api/genes/symbols", methods=["POST"])
def get_gene_symbols():
    try:
        data = request.get_json()
        timepoint_id = data.get('timepoint_id')
        component_id = data.get('component_id')

        if not all([timepoint_id, component_id]):
            return jsonify({
                "status": "error",
                "message": "Missing required parameters"
            }), 400

        engine = get_db_engine()
        with Session(engine) as session:
            # Simplified query to only get gene IDs and symbols
            query = text("""
                SELECT DISTINCT g.id as gene_id, g.symbol
                FROM genes g
                JOIN bicliques b ON instr(b.gene_ids, g.id) > 0
                JOIN component_bicliques cb ON b.id = cb.biclique_id
                WHERE cb.component_id = :component_id
                AND cb.timepoint_id = :timepoint_id
            """)

            results = session.execute(query, {
                "timepoint_id": timepoint_id,
                "component_id": component_id
            }).fetchall()

            gene_info = {
                str(row.gene_id): {
                    "symbol": row.symbol or f"Gene_{row.gene_id}"
                }
                for row in results
            }

            return jsonify({"status": "success", "gene_info": gene_info})

    except Exception as e:
        app.logger.error(f"Error getting gene symbols: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@component_bp.route("/api/genes/annotations", methods=["POST"])
def get_gene_annotations():
    try:
        data = request.get_json()
        # gene_ids = data.get('gene_ids', [])
        timepoint_id = data.get("timepoint_id")
        component_id = data.get("component_id")

        if not timepoint_id:
            return jsonify(
                {"status": "error", "message": "timepoint_id is required"}
            ), 400

        if not component_id:
            return jsonify(
                {"status": "error", "message": "component_id is required"}
            ), 400

        engine = get_db_engine()
        with Session(engine) as session:
            query = text("""
                SELECT 
                    g.id as gene_id,
                    g.symbol,
                    gta.node_type,
                    gta.gene_type,
                    gta.degree,
                    gta.is_isolate,
                    gta.biclique_ids
                FROM genes g
                JOIN gene_timepoint_annotations gta ON g.id = gta.gene_id
                JOIN component_details_view cdv ON cdv.timepoint_id = gta.timepoint_id
                WHERE gta.timepoint_id = :timepoint_id
                AND cdv.component_id = :component_id
                AND g.id = ANY(string_to_array(cdv.all_gene_ids, ',')::integer[])
            """)

            results = session.execute(
                query, {"timepoint_id": timepoint_id, "component_id": component_id}
            ).fetchall()

            # Convert results to dictionary using schema
            gene_info = {}
            for row in results:
                try:
                    annotation = GeneTimepointAnnotationSchema(
                        timepoint_id=timepoint_id,
                        gene_id=row.gene_id,
                        node_type=row.node_type,
                        gene_type=row.gene_type,
                        degree=row.degree,
                        is_isolate=row.is_isolate,
                        biclique_ids=row.biclique_ids,
                    )

                    gene_info[str(row.gene_id)] = {
                        "symbol": row.symbol,
                        "is_split": annotation.gene_type == "split"
                        if annotation.gene_type
                        else False,
                        "is_hub": annotation.node_type == "hub"
                        if annotation.node_type
                        else False,
                        "degree": annotation.degree,
                        "biclique_count": len(annotation.biclique_ids.split(","))
                        if annotation.biclique_ids
                        else 0,
                    }
                except Exception as e:
                    app.logger.error(f"Error processing gene {row.gene_id}: {str(e)}")
                    continue

            return jsonify({"status": "success", "gene_info": gene_info})

    except Exception as e:
        app.logger.error(f"Error getting gene annotations: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@component_bp.route("/api/dmrs/status", methods=["POST"])
def get_dmr_status():
    try:
        # Validate request data
        try:
            request_data = NodeStatusRequest(**request.get_json())
        except ValidationError as e:
            return jsonify({
                "status": "error",
                "message": "Invalid request data",
                "details": e.errors()
            }), 400

        # Use validated data
        dmr_ids = request_data.dmr_ids
        timepoint_id = request_data.timepoint_id

        engine = get_db_engine()
        with Session(engine) as session:
            query = text("""
                SELECT 
                    d.id as dmr_id,
                    dta.node_type,
                    dta.degree,
                    dta.is_isolate,
                    dta.biclique_ids
                FROM dmrs d
                JOIN dmr_timepoint_annotations dta ON d.id = dta.dmr_id
                WHERE dta.timepoint_id = :timepoint_id
            """)

            results = session.execute(query, {"timepoint_id": timepoint_id}).fetchall()

            # Convert results to dictionary using schema
            dmr_info = {}
            for row in results:
                try:
                    annotation = DmrTimepointAnnotationSchema(
                        timepoint_id=timepoint_id,
                        dmr_id=row.dmr_id,
                        node_type=row.node_type,
                        degree=row.degree,
                        is_isolate=row.is_isolate,
                        biclique_ids=row.biclique_ids,
                    )

                    dmr_info[str(row.dmr_id)] = {
                        "is_hub": annotation.node_type == "hub"
                        if annotation.node_type
                        else False,
                        "degree": annotation.degree,
                        "biclique_count": len(annotation.biclique_ids.split(","))
                        if annotation.biclique_ids
                        else 0,
                    }
                except Exception as e:
                    app.logger.error(f"Error processing DMR {row.dmr_id}: {str(e)}")
                    continue

            return jsonify({"status": "success", "dmr_status": dmr_info})

    except Exception as e:
        app.logger.error(f"Error getting DMR status: {str(e)}")
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
