import json
from flask import Blueprint, jsonify, request, current_app
from ..biclique_analysis.edge_classification import classify_edges
from pydantic import ValidationError
from ..utils.id_mapping import reverse_create_dmr_id
from ..schemas import (
    ComponentSummarySchema,
    ComponentDetailsSchema,
    GeneTimepointAnnotationSchema,
    DmrTimepointAnnotationSchema,
    NodeSymbolRequest,
    NodeStatusRequest,
    BicliqueMemberSchema,
    DominatingSetSchema,
    EdgeStatsSchema,
)
from ..utils.id_mapping import create_dmr_id
from flask_cors import CORS
from ..utils.extensions import app
from ..database import get_db_engine, get_db_session
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from ..database.models import Timepoint
from typing import List, Dict, Any

component_bp = Blueprint("component_routes", __name__, url_prefix="/api/component")


# Parse arrays and JSON first
def parse_array_string(arr_str):
    if not arr_str:
        return []
    cleaned = arr_str.replace("[", "").replace("]", "").strip()
    return [int(x.strip()) for x in cleaned.split(",") if x.strip()]


@component_bp.route("/components/<int:timepoint_id>/summary", methods=["GET"])
def get_component_summary_by_timepoint(timepoint_id):
    app.logger.info(f"Processing summary request for timepoint_id={timepoint_id}")
    try:
        # Get graph manager and initialize mapping
        graph_manager = current_app.graph_manager

        # Load and validate graphs first
        original_graph = graph_manager.get_original_graph(timepoint_id)
        split_graph = graph_manager.get_split_graph(timepoint_id)

        if not original_graph or not split_graph:
            app.logger.error(f"Failed to load graphs for timepoint {timepoint_id}")
            return jsonify(
                {"status": "error", "message": "Failed to load required graphs"}
            ), 500

        # Log graph sizes for debugging
        app.logger.info(
            f"Original graph: {len(original_graph.nodes())} nodes, {len(original_graph.edges())} edges"
        )
        app.logger.info(
            f"Split graph: {len(split_graph.nodes())} nodes, {len(split_graph.edges())} edges"
        )

        # Initialize component mapping
        try:
            component_mapping = graph_manager.initialize_timepoint_mapping(timepoint_id)
            app.logger.info(
                f"Successfully initialized component mapping for timepoint {timepoint_id}"
            )
            app.logger.info(
                f"Found {len(component_mapping.original_components)} original components"
            )
            app.logger.info(
                f"Found {len(component_mapping.split_components)} split components"
            )
        except Exception as e:
            app.logger.error(f"Error initializing component mapping: {str(e)}")
            return jsonify(
                {
                    "status": "error",
                    "message": f"Failed to initialize component mapping: {str(e)}",
                }
            ), 500

        engine = get_db_engine()
        with Session(engine) as session:
            # First verify timepoint exists
            timepoint = session.query(Timepoint).filter_by(id=timepoint_id).first()
            if not timepoint:
                app.logger.error(f"Timepoint {timepoint_id} not found")
                return jsonify(
                    {
                        "status": "error",
                        "message": f"Timepoint {timepoint_id} not found",
                        "code": "TIMEPOINT_NOT_FOUND",
                    }
                ), 404

            # Modified query to ensure all fields match the Pydantic model
            query = text("""
                SELECT 
                    c.id as component_id,
                    c.timepoint_id,
                    t.name as timepoint,
                    COALESCE(c.graph_type, 'split') as graph_type,
                    COALESCE(c.category, '') as category,
                    COALESCE(c.size, 0) as size,
                    COALESCE(c.dmr_count, 0) as dmr_count,
                    COALESCE(c.gene_count, 0) as gene_count,
                    COALESCE(c.edge_count, 0) as edge_count,
                    COALESCE(c.density, 0.0) as density,
                    COALESCE(COUNT(DISTINCT cb.biclique_id), 0) as biclique_count,
                    COALESCE(group_concat(DISTINCT b.category), '') as biclique_categories
                FROM components c
                JOIN timepoints t ON c.timepoint_id = t.id
                LEFT JOIN component_bicliques cb ON c.id = cb.component_id 
                    AND c.timepoint_id = cb.timepoint_id
                LEFT JOIN bicliques b ON cb.biclique_id = b.id
                WHERE c.timepoint_id = :timepoint_id 
                GROUP BY 
                    c.id,
                    c.timepoint_id,
                    t.name,
                    c.graph_type,
                    c.category,
                    c.size,
                    c.dmr_count,
                    c.gene_count,
                    c.edge_count,
                    c.density
            """)

            # Add debug logging for raw query results
            app.logger.info("Executing component summary query...")
            results = session.execute(query, {"timepoint_id": timepoint_id}).fetchall()
            app.logger.info(f"Query returned {len(results)} rows")

            components = []
            for idx, row in enumerate(results):
                try:
                    # Log raw row data
                    # app.logger.debug(f"Processing row {idx}: {row._asdict()}")

                    # Convert SQLAlchemy row to dictionary with explicit type conversion and null checks
                    component_data = {
                        "component_id": int(row.component_id)
                        if row.component_id
                        else 0,
                        "timepoint_id": int(row.timepoint_id)
                        if row.timepoint_id
                        else 0,
                        "timepoint": str(row.timepoint) if row.timepoint else "",
                        "graph_type": str(row.graph_type) if row.graph_type else "",
                        "category": str(row.category) if row.category else "",
                        "size": int(row.size) if row.size else 0,
                        "dmr_count": int(row.dmr_count) if row.dmr_count else 0,
                        "gene_count": int(row.gene_count) if row.gene_count else 0,
                        "edge_count": int(row.edge_count) if row.edge_count else 0,
                        "density": float(row.density) if row.density else 0.0,
                        "biclique_count": int(row.biclique_count)
                        if row.biclique_count
                        else 0,
                        "biclique_categories": str(row.biclique_categories)
                        if row.biclique_categories
                        else "",
                    }

                    # Log converted data
                    # app.logger.debug(f"Converted data for row {idx}: {component_data}")

                    # Validate with Pydantic
                    component = ComponentSummarySchema(**component_data)
                    components.append(component.model_dump())
                    # app.logger.debug(f"Successfully processed component {component_data['component_id']}")
                except ValidationError as e:
                    app.logger.error(f"Validation error for row {idx}: {str(e)}")
                    app.logger.error(f"Problematic data: {component_data}")
                    continue
                except Exception as e:
                    app.logger.error(f"Unexpected error processing row {idx}: {str(e)}")
                    app.logger.error(f"Raw row data: {row}")
                    continue

            # Add component mapping info to response
            response_data = {
                "status": "success",
                "timepoint": timepoint.name,
                "data": components,
                "mapping_info": {
                    "original_components": len(component_mapping.original_components),
                    "split_components": len(component_mapping.split_components),
                    "mapped_components": len(component_mapping.split_to_original),
                },
            }

            app.logger.info(
                f"Successfully processed {len(components)} components with mapping"
            )
            return jsonify(response_data)

    except Exception as e:
        app.logger.error(f"Error processing component summary request: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@component_bp.route("/<int:timepoint_id>/<int:component_id>/details", methods=["GET"])
def get_component_details(timepoint_id, component_id):
    app.logger.info(
        f"Getting details for timepoint {timepoint_id}, component {component_id}"
    )
    try:
        # Get graph manager for later use
        graph_manager = current_app.graph_manager

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
                    SELECT DISTINCT
                        b.id as biclique_id,
                        b.dmr_ids,
                        b.gene_ids,
                        b.category,
                        cb.component_id
                    FROM bicliques b
                    JOIN component_bicliques cb ON b.id = cb.biclique_id
                    WHERE cb.component_id = :component_id
                    AND cb.timepoint_id = :timepoint_id
                ),
                dominating_info AS (
                    SELECT 
                        ds.dmr_id,
                        ds.dominated_gene_count,
                        ds.utility_score
                    FROM dominating_sets ds
                    WHERE ds.timepoint_id = :timepoint_id
                    AND ds.dmr_id IN (
                        SELECT CAST(trim(value) AS INTEGER)
                        FROM json_each(
                            CASE 
                                WHEN json_valid((SELECT all_dmr_ids FROM component_info))
                                THEN (SELECT all_dmr_ids FROM component_info)
                                ELSE json_array((SELECT all_dmr_ids FROM component_info))
                            END
                        )
                    )
                )
                SELECT 
                    ci.*,
                    CASE 
                        WHEN bi.biclique_id IS NULL THEN '[]'
                        ELSE json_group_array(
                            json_object(
                                'biclique_id', bi.biclique_id,
                                'category', bi.category,
                                'dmr_ids', bi.dmr_ids,
                                'gene_ids', bi.gene_ids
                            )
                        ) 
                    END as bicliques,
                    (
                        SELECT json_group_array(
                            json_object(
                                'dmr_id', dmr_id,
                                'dominated_gene_count', dominated_gene_count,
                                'utility_score', utility_score
                            )
                        )
                        FROM dominating_info
                    ) as dominating_sets
                FROM component_info ci
                LEFT JOIN biclique_info bi ON ci.component_id = bi.component_id
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

            # Convert DMR IDs to raw graph IDs immediately when parsing
            raw_dmr_ids = {
                reverse_create_dmr_id(dmr_id, timepoint_id, is_original=True)
                for dmr_id in parse_array_string(result.all_dmr_ids)
            }
            all_dmr_ids = set(parse_array_string(result.all_dmr_ids))
            app.logger.info(f"all_dmr_ids{all_dmr_ids}")
            gene_ids = set(parse_array_string(result.all_gene_ids))
            # Use raw_dmr_ids directly for component_nodes

            component_nodes = raw_dmr_ids | gene_ids  ## THIS IS right
            # component_nodes = parse_array_string(   ## THIS IS WRONG because get_original_graph_componetns expects 0 indexed ids
            #    result.all_dmr_ids
            # ) + parse_array_string(result.all_gene_ids)
            # component_nodes = all_dmr_ids | gene_ids  ## THIS IS wrong
            # Get the component subgraphs using raw node IDs
            original_component = graph_manager.get_original_graph_component(
                timepoint_id, component_nodes
            )
            split_component = graph_manager.get_split_graph_component(
                timepoint_id, component_nodes
            )

            if not original_component or not split_component:
                app.logger.error(
                    f"Failed to load component graphs for timepoint {timepoint_id}, component {component_id}"
                )
                return jsonify(
                    {
                        "status": "error",
                        "message": "Failed to load required component graphs",
                    }
                ), 500

            # Store the split_component for reuse
            app.logger.info(
                # f"Split graph component has {len(split_component.nodes())} nodes and {len(split_component.edges())} edges"
                f"Split graph component (CR) has {split_component.nodes()} nodes and {len(split_component.edges())} edges"
            )

            # Calculate edge statistics for this specific component
            edge_sources = {}  # Initialize empty edge sources dictionary

            # Parse bicliques JSON string to get table format
            bicliques_data = json.loads(result.bicliques) if result.bicliques else []
            table_bicliques = [BicliqueMemberSchema(**b) for b in bicliques_data]

            # Convert table bicliques to raw networkx format
            raw_bicliques = []
            edge_sources = {}
            for b in table_bicliques:
                # Convert DMR IDs from table format to raw networkx IDs
                table_dmr_ids = set(int(x) for x in parse_array_string(b.dmr_ids))
                bicliques_raw_dmr_ids = {
                    reverse_create_dmr_id(cid, timepoint_id, is_original=True)
                    for cid in table_dmr_ids
                }
                biclique_gene_ids = set(int(x) for x in parse_array_string(b.gene_ids))

                # Add to raw bicliques list
                # Build edge sources mapping and track biclique participation
                biclique_idx = len(raw_bicliques)-1
                current_dmrs = {reverse_create_dmr_id(int(did), timepoint_id, True) for did in parse_array_string(b.dmr_ids)}
                current_genes = set(parse_array_string(b.gene_ids))
                
                for dmr in current_dmrs:
                    for gene in current_genes:
                        edge = (min(dmr, gene), max(dmr, gene))
            # Convert DMR IDs to raw networkx format for component data
            # raw_dmr_ids = {
            # reverse_create_dmr_id(int(dmr_id), timepoint_id, is_original=True)
            # for dmr_id in parse_array_string(result.all_dmr_ids)
            # }
            # gene_ids = set(int(x) for x in parse_array_string(result.all_gene_ids))

            # DMR IDs are already in raw format from earlier conversion
            # Just create the component data structure
            component_data = {
                "component": raw_dmr_ids | gene_ids,  # Use raw DMR IDs for component
                "dmrs": raw_dmr_ids,
                "genes": gene_ids,
            }

            # Call classify_edges with raw networkx IDs
            component_union = set(component_data["dmrs"]) | set(component_data["genes"])
            classification_result = classify_edges(
                original_component,
                split_component,
                edge_sources,
                bicliques=raw_bicliques,
                component={
                    "component": component_union,
                    "dmrs": set(component_data["dmrs"]),
                    "genes": set(component_data["genes"]),
                },
            )

            def convert_edge_list(edge_list, timepoint_id):
                return [(create_dmr_id(e.edge[0], timepoint_id), e.edge[1]) for e in edge_list]

            classification_result["classifications"]["permanent"] = convert_edge_list(
                classification_result["classifications"]["permanent"], timepoint_id
            )
            classification_result["classifications"]["false_positive"] = convert_edge_list(
                classification_result["classifications"]["false_positive"], timepoint_id
            )
            classification_result["classifications"]["false_negative"] = convert_edge_list(
                classification_result["classifications"]["false_negative"], timepoint_id
            )

            # Create edge stats using the Pydantic model
            # Extract reliability metrics from the stats
            reliability_stats = classification_result["stats"]["component"]
            # Create edge stats matching frontend expectations
            edge_stats = {
                "permanent_edges": len(
                    classification_result["classifications"]["permanent"]
                ),
                "false_positives": len(
                    classification_result["classifications"]["false_positive"]
                ),
                "false_negatives": len(
                    classification_result["classifications"]["false_negative"]
                ),
                # Include reliability metrics at top level
                "accuracy": reliability_stats.get("accuracy", 0.0),
                "noise_percentage": reliability_stats.get("noise_percentage", 0.0),
                "false_positive_rate": reliability_stats.get(
                    "false_positive_rate", 0.0
                ),
                "false_negative_rate": reliability_stats.get(
                    "false_negative_rate", 0.0
                ),
            }

            app.logger.info(
                f"Edge statistics for component {component_id}: {edge_stats}"
            )

            # Get DMR metadata from graph manager
            dmr_metadata = graph_manager.get_dmr_metadata(timepoint_id)

            # Calculate edge statistics for this specific component
            edge_sources = {}  # Initialize empty edge sources dictionary
            
            # Parse bicliques JSON string to get table format
            bicliques_data = json.loads(result.bicliques) if result.bicliques else []
            table_bicliques = [BicliqueMemberSchema(**b) for b in bicliques_data]
            
            # Convert table bicliques to raw networkx format and track biclique IDs
            raw_bicliques = []
            biclique_edge_stats = []
                        # Update dmr_metadata edge_type based on classifications
            updates = []
            for cls_type in ["permanent", "false_positive", "false_negative"]:
                for edge_tuple in classification_result["classifications"].get(cls_type, []):
                    dmr_id, gene_id = edge_tuple
                    updates.append((dmr_id, gene_id, cls_type))
                    if dmr_id in dmr_metadata:
                        for rec in dmr_metadata[dmr_id]["edge_details"]:
                            if rec.get("gene_id") == gene_id:
                                rec["edge_type"] = cls_type

            # Update edge details in database
            from backend.app.database.operations import update_edge_details

            update_edge_details(timepoint_id, updates)

            try:
                # Parse bicliques
                bicliques_data = (
                    json.loads(result.bicliques) if result.bicliques else []
                )
                bicliques = [BicliqueMemberSchema(**b) for b in bicliques_data]

                # Parse dominating sets
                dominating_sets_data = (
                    json.loads(result.dominating_sets) if result.dominating_sets else []
                )
                dominating_sets = {
                    str(ds["dmr_id"]): DominatingSetSchema(**ds)
                    for ds in dominating_sets_data
                    if ds and "dmr_id" in ds
                }

                # Create component details with Pydantic model
                component_details = ComponentDetailsSchema(
                    timepoint_id=result.timepoint_id,
                    timepoint=result.timepoint,
                    component_id=result.component_id,
                    graph_type=result.graph_type,
                    categories=result.categories,
                    total_dmr_count=result.total_dmr_count,
                    total_gene_count=result.total_gene_count,
                    biclique_count=len(bicliques),
                    all_dmr_ids=parse_array_string(result.all_dmr_ids),
                    all_gene_ids=parse_array_string(result.all_gene_ids),
                    bicliques=bicliques,
                    dominating_sets=dominating_sets,
                    edge_stats=edge_stats,
                )

                app.logger.info(
                    f"Successfully processed component {component_id} details"
                )

                # Add DMR details summary
                graph_manager = current_app.graph_manager
                dmr_metadata = graph_manager.get_dmr_metadata(timepoint_id)
                summary_lines = []
                for dmr_id, meta in dmr_metadata.items():
                    count = len(meta.get("edge_details", []))
                    summary_lines.append(
                        f"DMR_{dmr_id}: {count} edge{'s' if count != 1 else ''}"
                    )
                summary_string = "; ".join(summary_lines)

                # Convert the Pydantic model to a dict and add the summary field
                component_dict = component_details.model_dump()
                component_dict["dmr_details_summary"] = summary_string
                return jsonify({"status": "success", "data": component_dict})

            except ValidationError as e:
                app.logger.error(f"Validation error: {str(e)}")
                return jsonify(
                    {
                        "status": "error",
                        "message": "Invalid component data",
                        "details": e.errors(),
                    }
                ), 400

    except Exception as e:
        app.logger.error(f"Error getting component details: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@component_bp.route(
    "/<int:timepoint_id>/<int:component_id>/edge_stats", methods=["GET"]
)
def get_component_edge_stats(timepoint_id, component_id):
    app.logger.info(
        f"Getting edge statistics for timepoint {timepoint_id}, component {component_id}"
    )
    try:
        # Get graph manager for later use
        graph_manager = current_app.graph_manager

        # Get the component nodes
        engine = get_db_engine()
        with Session(engine) as session:
            query = text("""
                SELECT 
                    cd.all_dmr_ids,
                    cd.all_gene_ids
                FROM component_details_view cd
                WHERE cd.timepoint_id = :timepoint_id 
                AND cd.component_id = :component_id
                AND LOWER(cd.graph_type) = 'split'
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

            # Create component nodes set from query results
            raw_dmr_ids = {
                reverse_create_dmr_id(int(dmr_id), timepoint_id, is_original=True)
                for dmr_id in parse_array_string(result.all_dmr_ids)
            }
            component_nodes = raw_dmr_ids | set(parse_array_string(result.all_gene_ids))

            # Get the component subgraphs using the node set
            original_component = graph_manager.get_original_graph_component(
                timepoint_id, component_nodes
            )
            split_component = graph_manager.get_split_graph_component(
                timepoint_id, component_nodes
            )

            if not original_component or not split_component:
                app.logger.error(
                    f"Failed to load component graphs for timepoint {timepoint_id}, component {component_id}"
                )
                return jsonify(
                    {
                        "status": "error",
                        "message": "Failed to load required component graphs",
                    }
                ), 500

            # Query bicliques for this component
            query = text("""
                SELECT DISTINCT
                    b.id as biclique_id,
                    b.dmr_ids,
                    b.gene_ids
                FROM bicliques b
                JOIN component_bicliques cb ON b.id = cb.biclique_id
                WHERE cb.component_id = :component_id
                AND cb.timepoint_id = :timepoint_id
            """)

            bicliques_results = session.execute(
                query, {"timepoint_id": timepoint_id, "component_id": component_id}
            ).fetchall()

            # Convert bicliques to the format needed for classify_edges
            bicliques = [
                (
                    set(parse_array_string(b.dmr_ids)),
                    set(parse_array_string(b.gene_ids)),
                )
                for b in bicliques_results
            ]

            # Create component data using the already created component_nodes set
            component_data = {
                "component": component_nodes,
                "dmrs": {
                    reverse_create_dmr_id(int(did), timepoint_id, is_original=True)
                    for did in parse_array_string(result.all_dmr_ids)
                },
                "genes": set(parse_array_string(result.all_gene_ids)),
            }

            edge_sources = {}  # Initialize empty edge sources dictionary
            # Call classify_edges with all required parameters
            classification_result = classify_edges(
                original_component,
                split_component,
                edge_sources,
                bicliques=bicliques,
                component=component_data,
            )

            def convert_edge_list(edge_list, timepoint_id):
                return [(create_dmr_id(e.edge[0], timepoint_id), e.edge[1]) for e in edge_list]

            classification_result["classifications"]["permanent"] = convert_edge_list(
                classification_result["classifications"]["permanent"], timepoint_id
            )
            classification_result["classifications"]["false_positive"] = convert_edge_list(
                classification_result["classifications"]["false_positive"], timepoint_id
            )
            classification_result["classifications"]["false_negative"] = convert_edge_list(
                classification_result["classifications"]["false_negative"], timepoint_id
            )

            # Create edge stats using the Pydantic model
            reliability_stats = classification_result["stats"]["component"]
            edge_stats = {
                "permanent_edges": len(
                    classification_result["classifications"]["permanent"]
                ),
                "false_positives": len(
                    classification_result["classifications"]["false_positive"]
                ),
                "false_negatives": len(
                    classification_result["classifications"]["false_negative"]
                ),
                "accuracy": reliability_stats.get("accuracy", 0.0),
                "noise_percentage": reliability_stats.get("noise_percentage", 0.0),
                "false_positive_rate": reliability_stats.get(
                    "false_positive_rate", 0.0
                ),
                "false_negative_rate": reliability_stats.get(
                    "false_negative_rate", 0.0
                ),
            }

            app.logger.info(
                f"Edge statistics 2 for component {component_id}: {edge_stats}"
            )
            return jsonify({"status": "success", "data": edge_stats})

    except Exception as e:
        app.logger.error(f"Error getting edge statistics: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@component_bp.route("/genes/symbols", methods=["POST"])
def get_gene_symbols():
    if request.method == "OPTIONS":
        return jsonify({"status": "success"}), 200

    try:
        data = request.get_json()
        timepoint_id = data.get("timepoint_id")
        component_id = data.get("component_id")

        app.logger.info(
            f"Fetching gene symbols for timepoint={timepoint_id}, component={component_id}"
        )

        if not all([timepoint_id, component_id]):
            return jsonify(
                {"status": "error", "message": "Missing required parameters"}
            ), 400

        engine = get_db_engine()
        with Session(engine) as session:
            # Modified query to get genes through component_bicliques
            query = text("""
                WITH component_genes AS (
                    SELECT DISTINCT
                        g.id as gene_id,
                        COUNT(DISTINCT cb.biclique_id) as biclique_count
                    FROM genes g
                    JOIN bicliques b ON instr(b.gene_ids, g.id) > 0
                    JOIN component_bicliques cb ON b.id = cb.biclique_id
                    WHERE cb.component_id = :component_id
                    AND cb.timepoint_id = :timepoint_id
                    GROUP BY g.id
                )
                SELECT 
                    g.id as gene_id,
                    g.symbol,
                    gta.node_type,
                    gta.gene_type,
                    gta.degree,
                    gta.is_isolate,
                    gta.biclique_ids,
                    cg.biclique_count,
                    CASE WHEN cg.biclique_count > 1 THEN 1 ELSE 0 END as is_split
                FROM component_genes cg
                JOIN genes g ON g.id = cg.gene_id
                JOIN gene_timepoint_annotations gta ON g.id = gta.gene_id
                WHERE gta.timepoint_id = :timepoint_id
            """)

            results = session.execute(
                query, {"timepoint_id": timepoint_id, "component_id": component_id}
            ).fetchall()

            app.logger.info(f"Found {len(results)} genes")

            # Convert results to dictionary with string keys
            gene_info = {}
            for row in results:
                # app.logger.debug(f"Processing gene {row.gene_id}: node_type={row.node_type}, gene_type={row.gene_type}, biclique_count={row.biclique_count}")
                gene_info[str(row.gene_id)] = {
                    "gene_id": row.gene_id,
                    "symbol": row.symbol or f"Gene_{row.gene_id}",
                    "node_type": row.node_type,  # Include raw node_type
                    "gene_type": row.gene_type,  # Include raw gene_type
                    "is_split": row.node_type == "SPLIT_GENE" or row.biclique_count > 1,
                    "is_hub": row.node_type == "HUB",
                    "degree": row.degree or 0,
                    "biclique_count": row.biclique_count or 0,
                    "biclique_ids": row.biclique_ids.split(",")
                    if row.biclique_ids
                    else [],
                }

            #app.logger.info(f"Processed gene info: {gene_info}")
            return jsonify(
                {
                    "status": "success",
                    "data": gene_info,
                }
            )
    except Exception as e:
        app.logger.error(f"Error getting gene symbols: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@component_bp.route("/genes/annotations", methods=["POST"])
def get_gene_annotations():
    if request.method == "OPTIONS":
        return jsonify({"status": "success"}), 200
    try:
        data = request.get_json()
        timepoint_id = data.get("timepoint_id")
        component_id = data.get("component_id")

        if not all([timepoint_id, component_id]):
            return jsonify(
                {"status": "error", "message": "Missing required parameters"}
            ), 400

        engine = get_db_engine()
        with Session(engine) as session:
            # Modified query for SQLite using json_each to split the array
            query = text("""
                WITH RECURSIVE split(gene_id, rest) AS (
                    SELECT '', all_gene_ids || ',' FROM component_details_view 
                    WHERE timepoint_id = :timepoint_id AND component_id = :component_id
                    UNION ALL
                    SELECT substr(rest, 0, instr(rest, ',')),
                           substr(rest, instr(rest, ',') + 1)
                    FROM split WHERE rest <> ''
                ),
                component_genes AS (
                    SELECT CAST(gene_id AS INTEGER) as gene_id 
                    FROM split 
                    WHERE gene_id <> ''
                )
                SELECT 
                    g.id as gene_id,
                    g.symbol,
                    gta.node_type,
                    gta.gene_type,
                    gta.degree,
                    gta.is_isolate,
                    gta.biclique_ids,
                    COUNT(DISTINCT cb.biclique_id) as biclique_count
                FROM component_genes cg
                JOIN genes g ON g.id = cg.gene_id
                JOIN gene_timepoint_annotations gta ON g.id = gta.gene_id
                LEFT JOIN component_bicliques cb ON cb.component_id = :component_id
                WHERE gta.timepoint_id = :timepoint_id
                GROUP BY 
                    g.id, g.symbol, gta.node_type, gta.gene_type, 
                    gta.degree, gta.is_isolate, gta.biclique_ids
            """)

            results = session.execute(
                query, {"timepoint_id": timepoint_id, "component_id": component_id}
            ).fetchall()

            gene_info = {}
            for row in results:
                gene_info[str(row.gene_id)] = {
                    "symbol": row.symbol or f"Gene_{row.gene_id}",
                    "is_split": row.gene_type == "split" or row.biclique_count > 1,
                    "is_hub": row.node_type == "hub",
                    "degree": row.degree or 0,
                    "biclique_count": row.biclique_count or 0,
                    "biclique_ids": row.biclique_ids,
                }

            return jsonify({"status": "success", "gene_info": gene_info})

    except Exception as e:
        app.logger.error(f"Error getting gene annotations: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@component_bp.route("/dmrs/status", methods=["POST"])
def get_dmr_status():
    try:
        # Validate request data
        try:
            request_data = NodeStatusRequest(**request.get_json())
        except ValidationError as e:
            return jsonify(
                {
                    "status": "error",
                    "message": "Invalid request data",
                    "details": e.errors(),
                }
            ), 400

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


@component_bp.route(
    "/<int:timepoint_id>/<int:component_id>/dmr_details", methods=["GET"]
)
def get_component_dmr_details(timepoint_id, component_id):
    """Get detailed DMR information for a specific component."""
    try:
        engine = get_db_engine()
        with Session(engine) as session:
            query = text("""
                SELECT 
                    dav.dmr_id,
                    dav.chromosome,
                    dav.start_position,
                    dav.end_position,
                    dav.methylation_difference AS methylation_diff,  -- Keep alias for response
                    dav.p_value,
                    dav.q_value,
                    dav.node_type,
                    dav.degree,
                    dav.is_isolate,
                    dav.biclique_ids,
                    t.name AS timepoint
                FROM dmr_annotations_view dav
                JOIN timepoints t ON dav.timepoint_id = t.id
                WHERE dav.timepoint_id = :timepoint_id
                AND dav.component_id = :component_id
                ORDER BY dav.chromosome, dav.start_position
            """)

            results = session.execute(
                query, {"timepoint_id": timepoint_id, "component_id": component_id}
            ).fetchall()

            dmrs = []
            for row in results:
                dmrs.append(
                    {
                        "dmr_id": row.dmr_id,
                        "chromosome": row.chromosome,
                        "start": row.start_position,
                        "end": row.end_position,
                        "methylation_diff": row.methylation_diff,  # Changed from methylation_difference
                        "p_value": row.p_value,
                        "q_value": row.q_value,
                        "node_type": row.node_type,
                        "degree": row.degree,
                        "is_isolate": row.is_isolate,
                        "biclique_count": len(row.biclique_ids.split(","))
                        if row.biclique_ids
                        else 0,
                        "timepoint": row.timepoint,
                    }
                )

            return jsonify({"status": "success", "data": dmrs})

    except Exception as e:
        current_app.logger.error(f"Error getting DMR details: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@component_bp.route("/<int:timepoint_id>/details", methods=["GET"])
def get_component_details_by_timepoint(timepoint_id):
    try:
        engine = get_db_engine()

        with Session(engine) as session:
            query = text("""
                SELECT 
                    cd.timepoint_id,
                    cd.timepoint,
                    cd.component_id,
                    cd.graph_type,
                    cd.categories,
                    cd.total_dmr_count,
                    cd.total_gene_count,
                    (SELECT json_group_array(DISTINCT value) 
                     FROM json_each(cd.all_dmr_ids)) AS all_dmr_ids,
                    (SELECT json_group_array(DISTINCT value) 
                     FROM json_each(cd.all_gene_ids)) AS all_gene_ids
                FROM component_details_view cd
                WHERE cd.timepoint_id = :timepoint_id 
                AND LOWER(cd.graph_type) = 'split'
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
