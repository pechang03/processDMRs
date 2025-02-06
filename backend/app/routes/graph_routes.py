import json
import time
import json
from flask import jsonify, current_app, Blueprint
from backend.app.database.models import EdgeDetails, Gene
from typing import Dict
from plotly.utils import PlotlyJSONEncoder

from sqlalchemy.orm import Session
from sqlalchemy import text
import networkx as nx

from pydantic import ValidationError
from ..schemas import (
    GraphComponentSchema,
    BicliqueMemberSchema,
    DmrComponentSchema,
    GeneAnnotationViewSchema,
    DmrAnnotationViewSchema,
)
from ..database.connection import get_db_engine
from ..visualization.vis_components import create_component_visualization
from ..biclique_analysis.edge_classification import classify_edges
from ..visualization.graph_layout_biclique import CircularBicliqueLayout
from ..utils.node_info import NodeInfo
from ..utils.json_utils import convert_plotly_object

graph_bp = Blueprint("graph_routes", __name__, url_prefix="/api/graph")


@graph_bp.route("/<int:timepoint_id>/<int:component_id>", methods=["GET"])
def get_component_graph(timepoint_id, component_id):
    """
    Rewritten route to generate component graph visualization.
    The order of execution is as follows:
      1. Retrieve component details and verify existence.
      2. Collect component node IDs (DMRs and Genes).
      3. Retrieve the original and split graphs from the graph manager.
      4. Validate the bipartite structure.
      5. Query additional component details and build a Pydantic model.
      6. Calculate the node biclique map, metadata, and node labels.
      7. Calculate node positions using a layout (e.g., CircularBicliqueLayout).
      8. Obtain edge classifications (and stats) from the graph manager.
      9. Call create_component_visualization with the complete inputs.
      10. Convert the Plotly figure to a plain dict and add extra stats.
      11. Return the final JSON.
    """
    current_app.logger.info(
        f"Fetching graph for timepoint={timepoint_id}, component={component_id}"
    )
    try:
        engine = get_db_engine()
        with Session(engine) as session:
            # (1) Retrieve component basic info from a view.
            comp_query = text("""
                SELECT 
                    component_id,
                    timepoint_id,
                    all_dmr_ids as dmr_ids,
                    all_gene_ids as gene_ids,
                    categories,
                    graph_type,
                    dominating_sets,
                    bicliques
                FROM component_details_view
                WHERE timepoint_id = :timepoint_id 
                AND component_id = :component_id
            """)

            result = session.execute(
                verify_query,
                {"timepoint_id": timepoint_id, "component_id": component_id},
            ).first()

            if not result:
                current_app.logger.error(
                    f"Component {component_id} not found for timepoint {timepoint_id}"
                )
                return jsonify({"error": "Component not found", "status": 404}), 404

            # Get component nodes
            all_dmr_ids = {int(x) for x in parse_id_string(result.dmr_ids)}
            all_gene_ids = {int(x) for x in parse_id_string(result.gene_ids)}
            all_component_nodes = set(all_dmr_ids).union(set(all_gene_ids))

            # Get component subgraphs directly from graph manager
            graph_manager = current_app.graph_manager
            original_graph_component = graph_manager.get_original_graph_component(
                timepoint_id, all_component_nodes
            )
            split_graph_component = graph_manager.get_split_graph_component(
                timepoint_id, all_component_nodes
            )

            # Add validation and debugging
            if not original_graph_component or not split_graph_component:
                current_app.logger.error(
                    f"Failed to load graphs for component {component_id}"
                )
                return jsonify(
                    {"error": "Failed to load component graphs", "status": 404}
                ), 404

            # Add debug logging for graph properties
            current_app.logger.info(
                f"Original graph component: {len(original_graph_component.nodes())} nodes, {len(original_graph_component.edges())} edges"
            )
            current_app.logger.info(
                f"Split graph component: {len(split_graph_component.nodes())} nodes, {len(split_graph_component.edges())} edges"
            )

            # Validate that both graphs have edges
            if len(original_graph_component.edges()) == 0:
                current_app.logger.error("Original graph component has no edges!")
                return jsonify(
                    {"error": "Invalid original graph component", "status": 400}
                ), 400

            if len(split_graph_component.edges()) == 0:
                current_app.logger.error("Split graph component has no edges!")
                return jsonify(
                    {"error": "Invalid split graph component", "status": 400}
                ), 400

            # Validate bipartite graph structure
            def validate_bipartite_graphs(
                original_graph: nx.Graph, split_graph: nx.Graph
            ) -> bool:
                """Validate that both graphs have same nodes and maintain bipartite structure"""
                # Check node sets are identical
                if set(original_graph.nodes()) != set(split_graph.nodes()):
                    current_app.logger.error(
                        "Node sets differ between original and split graphs"
                    )
                    current_app.logger.debug(
                        f"Original only: {set(original_graph.nodes()) - set(split_graph.nodes())}"
                    )
                    current_app.logger.debug(
                        f"Split only: {set(split_graph.nodes()) - set(original_graph.nodes())}"
                    )
                    return False

                # Get DMR nodes (nodes with ID < min_gene_id)
                min_gene_id = min(all_gene_ids) if all_gene_ids else 0
                dmr_nodes = {n for n in original_graph.nodes() if n < min_gene_id}
                gene_nodes = {n for n in original_graph.nodes() if n >= min_gene_id}

                # Verify DMR nodes are consistent
                if any(n >= min_gene_id for n in dmr_nodes):
                    current_app.logger.error("Found gene IDs in DMR node set")
                    return False

                if any(n < min_gene_id for n in gene_nodes):
                    current_app.logger.error("Found DMR IDs in gene node set")
                    return False

                # Verify bipartite structure - DMRs should only connect to genes
                for graph in [original_graph, split_graph]:
                    for dmr in dmr_nodes:
                        if any(
                            neighbor < min_gene_id for neighbor in graph.neighbors(dmr)
                        ):
                            current_app.logger.error(
                                f"Found DMR-DMR connection in {'original' if graph == original_graph else 'split'} graph"
                            )
                            return False

                    for gene in gene_nodes:
                        if any(
                            neighbor >= min_gene_id
                            for neighbor in graph.neighbors(gene)
                        ):
                            current_app.logger.error(
                                f"Found gene-gene connection in {'original' if graph == original_graph else 'split'} graph"
                            )
                            return False

                return True

            # Use the validation
            if not validate_bipartite_graphs(
                original_graph_component, split_graph_component
            ):
                return jsonify(
                    {
                        "error": "Invalid graph structure - bipartite property violation",
                        "status": 400,
                    }
                ), 400

            current_app.logger.info(
                "Graph validation passed - bipartite structure maintained"
            )

            # Get component data
            query = text("""
                SELECT 
                    c.component_id,
                    c.timepoint_id,
                    c.all_dmr_ids as dmr_ids,
                    c.all_gene_ids as gene_ids,
                    c.graph_type,
                    c.categories, 
                    (
                        SELECT json_group_array(
                            json_object(
                                'biclique_id', b.id,
                                'category', b.category,
                                'dmr_ids', b.dmr_ids,
                                'gene_ids', b.gene_ids
                            )
                        )
                        FROM bicliques b
                        WHERE b.component_id = c.component_id
                        AND b.timepoint_id = c.timepoint_id
                    ) as bicliques
                FROM component_details_view c
                WHERE c.timepoint_id = :timepoint_id 
                AND c.component_id = :component_id
            """)

            result = session.execute(
                query, {"timepoint_id": timepoint_id, "component_id": component_id}
            ).first()
            if not result:
                current_app.logger.error(
                    "Query returned no results after verifying existence"
                )
                return jsonify(
                    {"error": "Failed to retrieve component data", "status": 500}
                ), 500

            # Validate with Pydantic
            try:
                component_data = GraphComponentSchema(
                    component_id=result.component_id,
                    timepoint_id=result.timepoint_id,
                    dmr_ids=result.dmr_ids,
                    gene_ids=result.gene_ids,
                    graph_type=result.graph_type,
                    categories=result.categories,  # Keep as categories to match the view
                    bicliques=[
                        BicliqueMemberSchema(**b) for b in json.loads(result.bicliques)
                    ],
                )
            except ValidationError as e:
                current_app.logger.error(f"Validation error: {e}")
                return jsonify(
                    {
                        "error": "Invalid component data",
                        "details": e.errors(),
                        "status": 500,
                    }
                ), 500

            current_app.logger.debug(f"Validated component data: {component_data}")

            # Get bicliques for this component

            # Parse bicliques data
            bicliques = []
            biclique_id_map = {}  # Map database IDs to sequential numbers
            node_biclique_map = {}  # Initialize node-to-biclique mapping

            # First, create the mapping of database IDs to sequential numbers
            for idx, b in enumerate(component_data.bicliques):
                biclique_id = b.biclique_id
                biclique_id_map[biclique_id] = (
                    idx + 1
                )  # Use 1-based indexing to match overview

            # Then process all bicliques, including simple ones
            for b in component_data.bicliques:
                try:
                    current_app.logger.debug(f"Processing biclique {b}")
                    # Parse DMR and gene IDs using the helper function
                    dmr_set = parse_id_string(b.dmr_ids) if b.dmr_ids else set()
                    gene_set = parse_id_string(b.gene_ids) if b.gene_ids else set()

                    # Ensure we have valid sets
                    if not isinstance(dmr_set, set):
                        dmr_set = set(dmr_set) if dmr_set else set()
                    if not isinstance(gene_set, set):
                        gene_set = set(gene_set) if gene_set else set()

                    if dmr_set and gene_set:
                        bicliques.append((dmr_set, gene_set))
                    else:
                        current_app.logger.warning(
                            f"Skipping biclique with empty sets: DMRs={dmr_set}, Genes={gene_set}"
                        )

                    # Update node_biclique_map with the correct sequential IDs
                    for dmr_id in dmr_set:
                        if dmr_id not in node_biclique_map:
                            node_biclique_map[dmr_id] = []
                        node_biclique_map[dmr_id].append(
                            biclique_id_map[b.biclique_id] - 1
                        )

                    for gene_id in gene_set:
                        if gene_id not in node_biclique_map:
                            node_biclique_map[gene_id] = []
                        node_biclique_map[gene_id].append(
                            biclique_id_map[b.biclique_id] - 1
                        )

                except Exception as e:
                    current_app.logger.error(f"Error parsing biclique data: {str(e)}")
                    current_app.logger.error(f"DMR IDs: {b.dmr_ids}")
                    current_app.logger.error(f"Gene IDs: {b.gene_ids}")
                    continue

            # Collect all DMR and gene IDs from all bicliques
            all_dmr_ids = set()
            all_gene_ids = set()
            for b in component_data.bicliques:
                dmr_set = parse_id_string(b.dmr_ids)
                gene_set = parse_id_string(b.gene_ids)
                all_dmr_ids.update(dmr_set)
                all_gene_ids.update(gene_set)

            current_app.logger.debug(
                f"Collected DMR IDs from all bicliques: {all_dmr_ids}"
            )
            current_app.logger.debug(
                f"Collected gene IDs from all bicliques: {all_gene_ids}"
            )

            # Update component_data with the complete sets
            component_data.dmr_ids = list(all_dmr_ids)
            component_data.gene_ids = list(all_gene_ids)

            # Get node metadata
            dmr_query = text("""
                SELECT 
                    dmr_id as id,
                    area_stat as area,
                    description,
                    node_type,
                    degree,
                    is_isolate,
                    biclique_ids
                FROM dmr_annotations_view
                WHERE timepoint_id = :timepoint_id
                AND component_id = :component_id
            """)

            # Get gene annotations including split gene information
            gene_query = text("""
                SELECT 
                    gene_id,
                    symbol,
                    node_type,
                    gene_type,
                    degree,
                    is_isolate,
                    biclique_ids
                FROM gene_annotations_view
                WHERE timepoint_id = :timepoint_id
                AND component_id = :component_id
            """)

            # Get metadata
            dmr_metadata = {}
            gene_metadata = {}  # Dictionary to store all gene information

            dmr_results = session.execute(
                dmr_query, {"timepoint_id": timepoint_id, "component_id": component_id}
            ).fetchall()

            gene_results = session.execute(
                gene_query, {"timepoint_id": timepoint_id, "component_id": component_id}
            ).fetchall()
            current_app.logger.debug("graph_routes point 1")

            # Create metadata dictionaries using Pydantic models
            for dmr in dmr_results:
                try:
                    dmr_data = DmrComponentSchema.model_validate(dmr)
                    dmr_metadata[dmr_data.id] = dmr_data.model_dump()
                except ValidationError as e:
                    current_app.logger.error(f"Error validating DMR data: {e}")
                    continue

            # Identify split genes from annotations using Pydantic models
            current_app.logger.debug("graph_routes point 2")
            split_genes = set()
            for row in gene_results:
                try:
                    gene_data = GeneAnnotationViewSchema(
                        gene_id=row.gene_id,
                        symbol=row.symbol,
                        description=None,
                        master_gene_id=None,
                        interaction_source=None,
                        promoter_info=None,
                        timepoint=None,
                        timepoint_id=timepoint_id,
                        component_id=component_id,
                        degree=row.degree,
                        node_type=row.node_type,
                        gene_type=row.gene_type,
                        is_isolate=row.is_isolate,
                        biclique_ids=row.biclique_ids,
                    )

                    # Convert to dictionary and add derived fields
                    gene_dict = gene_data.model_dump()
                    gene_dict.update(
                        {
                            "is_split": gene_data.gene_type == "split"
                            if gene_data.gene_type
                            else False,
                            "is_hub": gene_data.node_type == "hub"
                            if gene_data.node_type
                            else False,
                            "biclique_count": len(gene_data.biclique_ids.split(","))
                            if gene_data.biclique_ids
                            else 0,
                        }
                    )

                    # Store the enhanced gene metadata
                    gene_metadata[gene_data.gene_id] = gene_dict

                    # Check if gene is split based on gene_type or biclique_ids
                    if gene_dict["is_split"] or gene_dict["biclique_count"] > 1:
                        split_genes.add(gene_data.gene_id)

                except ValidationError as e:
                    current_app.logger.error(f"Error validating gene data: {e}")
                    continue

            current_app.logger.debug(
                f"Found {len(split_genes)} split genes from annotations: {split_genes}"
            )

            # Create node labels
            node_labels = {}
            for dmr_id in all_dmr_ids:
                node_labels[dmr_id] = f"DMR_{dmr_id}"
            for gene_id in all_gene_ids:
                symbol = gene_metadata.get(gene_id, {}).get("symbol")
                node_labels[gene_id] = symbol if symbol else f"Gene_{gene_id}"

            # Get node degrees from split graph component
            node_degrees = {
                int(node): split_graph_component.degree(node)
                for node in split_graph_component.nodes()
            }

            # Add debug logging for min_gene_id calculation
            min_gene_id = min(all_gene_ids) if all_gene_ids else 0
            current_app.logger.debug(f"min_gene_id: {min_gene_id}")

            # Add size validation before processing
            if len(original_graph_component) == 0 or len(split_graph_component) == 0:
                current_app.logger.error("Empty graph components")
                return jsonify({"error": "Empty graph components", "status": 400}), 400

            # Validate bicliques before processing
            if not bicliques:
                current_app.logger.error("No bicliques found for component")
                return jsonify({"error": "No bicliques found", "status": 400}), 400

            # Create NodeInfo object using annotated split genes
            node_info = NodeInfo(
                all_nodes=all_dmr_ids | all_gene_ids,
                dmr_nodes=all_dmr_ids,
                regular_genes=all_gene_ids - split_genes,
                split_genes=split_genes,
                node_degrees={
                    int(node): split_graph_component.degree(node)
                    for node in split_graph_component.nodes()
                },
                min_gene_id=min(all_gene_ids) if all_gene_ids else 0,
            )

            # Initialize the circular layout
            layout = CircularBicliqueLayout()

            # Debug logging
            current_app.logger.debug(
                f"Using CircularBicliqueLayout for graph visualization"
            )
            current_app.logger.debug(
                f"Number of nodes to position: {len(all_dmr_ids | all_gene_ids)}"
            )
            current_app.logger.debug(f"DMR nodes: {len(all_dmr_ids)}")
            current_app.logger.debug(
                f"Regular genes: {len(all_gene_ids - split_genes)}"
            )
            current_app.logger.debug(f"Split genes: {len(split_genes)}")

            # Create node-to-biclique mapping from database annotations
            node_biclique_map = {}

            # Process DMR annotations
            for dmr_id, info in dmr_metadata.items():
                if info.get("biclique_ids"):
                    try:
                        raw_value = info["biclique_ids"]
                        # If it's a string, split by comma and convert each part to int
                        if isinstance(raw_value, str):
                            # Remove any quotes and split
                            cleaned = raw_value.strip("\"'")
                            biclique_ids = [
                                int(bid.strip())
                                for bid in cleaned.split(",")
                                if bid.strip()
                            ]
                        else:
                            # Handle case where it might already be a list
                            biclique_ids = [int(bid) for bid in raw_value]

                        node_biclique_map[int(dmr_id)] = biclique_ids
                    except Exception as e:
                        current_app.logger.error(
                            f"Error processing DMR {dmr_id} biclique IDs: {e}\n"
                            f"Raw value: {info['biclique_ids']}"
                        )

            # Process gene annotations
            for gene_id, info in gene_metadata.items():
                if info.get("biclique_ids"):
                    try:
                        raw_value = info["biclique_ids"]
                        # If it's a string, split by comma and convert each part to int
                        if isinstance(raw_value, str):
                            # Remove any quotes and split
                            cleaned = raw_value.strip("\"'")
                            biclique_ids = [
                                int(bid.strip())
                                for bid in cleaned.split(",")
                                if bid.strip()
                            ]
                        else:
                            # Handle case where it might already be a list
                            biclique_ids = [int(bid) for bid in raw_value]

                        node_biclique_map[int(gene_id)] = biclique_ids
                    except Exception as e:
                        current_app.logger.error(
                            f"Error processing gene {gene_id} biclique IDs: {e}\n"
                            f"Raw value: {info['biclique_ids']}"
                        )

            current_app.logger.debug(
                f"Created node-to-biclique mapping for {len(node_biclique_map)} nodes"
            )
            current_app.logger.debug(
                f"Sample node_biclique_map: {dict(list(node_biclique_map.items())[:5])}"
            )

            # Create NodeInfo object
            node_info = NodeInfo(
                all_nodes=all_dmr_ids | all_gene_ids,
                dmr_nodes=all_dmr_ids,
                regular_genes=all_gene_ids - split_genes,
                split_genes=split_genes,
                node_degrees={
                    int(node): split_graph_component.degree(node)
                    for node in split_graph_component.nodes()
                },
                min_gene_id=min(all_gene_ids) if all_gene_ids else 0,
            )

            # Calculate positions using existing node_info and node_biclique_map
            node_positions = layout.calculate_positions(
                graph=split_graph_component,
                node_info=node_info,
                node_biclique_map=node_biclique_map,
            )

            # Debug the positions
            current_app.logger.debug(
                f"Generated positions for {len(node_positions)} nodes"
            )
            current_app.logger.debug(
                f"Sample positions: {list(node_positions.items())[:5]}"
            )

            # Get dominating set for this timepoint's DMRs
            try:
                dominating_set_query = text("""
                    SELECT ds.dmr_id
                    FROM dominating_sets ds
                    WHERE ds.timepoint_id = :timepoint_id
                    AND ds.dmr_id IN (
                        SELECT CAST(trim(value) AS INTEGER)
                        FROM json_each(
                            CASE 
                                WHEN json_valid(:dmr_ids)
                                THEN :dmr_ids
                                ELSE json_array(:dmr_ids)
                            END
                        )
                    )
                """)

                # Get the DMR IDs as a JSON array string
                dmr_ids_json = json.dumps(list(all_dmr_ids))

                dominating_set_results = session.execute(
                    dominating_set_query,
                    {"timepoint_id": timepoint_id, "dmr_ids": dmr_ids_json},
                ).fetchall()

                dominating_set = {int(row.dmr_id) for row in dominating_set_results}
                current_app.logger.debug(f"Found dominating set DMRs: {dominating_set}")

                # Validate that each biclique has at most one dominating set DMR
                for dmr_nodes, _ in bicliques:
                    dom_dmrs = dmr_nodes & dominating_set
                    if len(dom_dmrs) > 1:
                        current_app.logger.warning(
                            f"Biclique contains multiple dominating set DMRs: {dom_dmrs}"
                        )

            except Exception as e:
                current_app.logger.error(f"Error getting dominating set: {e}")
                dominating_set = set()

            # Get component mapping and classify edges
            component_mapping = graph_manager.load_timepoint_components(timepoint_id)

            try:
                # Call the GraphManager method to get both updates and classifications
                updates, edge_classifications = (
                    graph_manager.update_component_edge_classification(
                        timepoint_id,
                        original_graph_component,
                        split_graph_component,
                        bicliques,
                    )
                )
                # current_app.logger.info("Edge classification updates: " + str(updates))

            except Exception as e:
                current_app.logger.error(
                    "Error during edge classification update: " + str(e)
                )
                return jsonify(
                    {"error": "Edge classification update failed", "status": 500}
                ), 500

            # Add detailed logging for edge classification
            total_edges = len(original_graph_component.edges())
            classifications = edge_classifications[
                "classifications"
            ]  # Get the nested dict
            permanent_edges = len(classifications.get("permanent", []))
            false_positives = len(classifications.get("false_positive", []))
            false_negatives = len(classifications.get("false_negative", []))

            current_app.logger.info(
                f"Edge classification results:\n"
                f"Total edges in original graph: {total_edges}\n"
                f"Permanent edges: {permanent_edges}\n"
                f"False positives: {false_positives}\n"
                f"False negatives: {false_negatives}"
            )

            # Validate edge classification results
            if permanent_edges == 0 and total_edges > 0:
                current_app.logger.error(
                    f"Invalid edge classification: Connected component with {total_edges} edges "
                    f"but no permanent edges detected!"
                )
                return jsonify(
                    {"error": "Invalid edge classification", "status": 400}
                ), 400

            # Add timing for performance monitoring
            start_time = time.time()

            # Create component info dictionary specifically for classify_edges
            component_info = {
                "component": set(all_component_nodes),
                "dmrs": set(all_dmr_ids),
                "genes": set(all_gene_ids),
            }

            # Create full component data structure with additional info
            component_data = {
                "component": all_component_nodes,
                "raw_bicliques": bicliques,
                "dmrs": all_dmr_ids,
                "genes": all_gene_ids,
                "total_edges": len(original_graph_component.edges()),
                "dominating_sets": list(dominating_set),  # Add explicit dominating set
            }

            # current_app.logger.debug(f"Point 1{component_data}")
            current_app.logger.debug("Point 1")
            # Use the complete edge_classifications dictionary
            vis_dict = create_component_visualization(
                component=component_data,
                node_positions=node_positions,
                node_labels=node_labels,
                node_biclique_map=node_biclique_map,
                edge_classifications=edge_classifications,
                dmr_metadata=dmr_metadata,
                gene_metadata=gene_metadata,
            )
            # Force conversion to a plain dict
            vis_dict = json.loads(json.dumps(vis_dict, cls=PlotlyJSONEncoder))
            current_app.logger.debug("Point 2")

            end_time = time.time()
            current_app.logger.info(
                f"Visualization created in {end_time - start_time:.2f} seconds"
            )

            # Add the statistics
            # Guard against missing "stats" in edge_classifications
            # Initialize stats if missing
            if (
                "stats" not in edge_classifications
                or edge_classifications["stats"] is None
            ):
                edge_classifications["stats"] = {
                    "component": {
                        "permanent": len(
                            edge_classifications.get("classifications", {}).get(
                                "permanent", []
                            )
                        ),
                        "false_positive": len(
                            edge_classifications.get("classifications", {}).get(
                                "false_positive", []
                            )
                        ),
                        "false_negative": len(
                            edge_classifications.get("classifications", {}).get(
                                "false_negative", []
                            )
                        ),
                    },
                    "bicliques": {},  # Empty biclique stats for now
                }

            current_app.logger.debug(f'Point 2b{edge_classifications["stats"]}')
            stats = edge_classifications.get("stats") or {
                "component": {},
                "bicliques": {},
            }
            current_app.logger.debug(f"Point 2c")
            # vis_dict["edge_stats"] = stats.get("component", {})
            current_app.logger.debug(f"Point 2d")
            # vis_dict["biclique_stats"] = stats.get("bicliques", {})

            # Return the visualization dictionary directly
            # Convert Plotly objects to dicts

            current_app.logger.debug(f"Point 3{vis_dict}")

            converted = convert_plotly_object(vis_dict)
            if converted is None:
                converted = vis_dict
            return converted

    except Exception as e:
        current_app.logger.error(f"Error generating graph visualization: {str(e)}")
        return {
            "error": "Failed to generate graph visualization",
            "details": str(e) if current_app.debug else "Internal server error",
            "status": 500,
        }
