import json
from flask import jsonify, current_app, Blueprint
from pydantic import ValidationError
from ..schemas import (
    GraphComponentSchema,
    BicliqueMemberSchema,
    DmrComponentSchema,
    GeneAnnotationViewSchema,
    DmrAnnotationViewSchema,
)
from ..database.connection import get_db_engine
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..visualization.core import create_biclique_visualization
from ..visualization.graph_layout_biclique import CircularBicliqueLayout
from ..utils.node_info import NodeInfo
import networkx as nx


def parse_id_string(id_str):
    """Helper function to parse string representation of ID arrays"""
    if not id_str:
        return set()
    # Remove brackets and split by comma
    cleaned = id_str.replace("[", "").replace("]", "").strip()
    # Split and convert to integers, filtering out empty strings
    return {int(x.strip()) for x in cleaned.split(",") if x.strip()}


graph_bp = Blueprint("graph_routes", __name__, url_prefix="/api/graph")


@graph_bp.route("/<int:timepoint_id>/<int:component_id>", methods=["GET"])
def get_component_graph(timepoint_id, component_id):
    """Get graph visualization data for a specific component."""
    current_app.logger.info(
        f"Fetching graph for timepoint={timepoint_id}, component={component_id}"
    )

    try:
        # Get timepoint name from database
        engine = get_db_engine()
        with Session(engine) as session:
            # First verify component exists and get timepoint name
            verify_query = text("""
                SELECT t.name as timepoint_name
                FROM components c
                JOIN timepoints t ON c.timepoint_id = t.id
                WHERE c.timepoint_id = :timepoint_id 
                AND c.id = :component_id
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

            timepoint_name = result.timepoint_name
            current_app.logger.info(f"Found timepoint name: {timepoint_name}")

            # Get the split graph from GraphManager
            graph_manager = current_app.graph_manager
            split_graph = graph_manager.get_split_graph(timepoint_name)

            if not split_graph:
                current_app.logger.error(f"No split graph found for timepoint {timepoint_name}")
                return jsonify({"error": "Split graph not found", "status": 404}), 404

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
                        JOIN component_bicliques cb ON b.id = cb.biclique_id
                        WHERE cb.component_id = c.component_id
                        AND cb.timepoint_id = c.timepoint_id
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
            for b in component_data.bicliques:
                try:
                    current_app.logger.debug(f"Component {b}")
                    # Parse DMR and gene IDs using the helper function
                    dmr_set = parse_id_string(b.dmr_ids)
                    gene_set = parse_id_string(b.gene_ids)
                    bicliques.append((dmr_set, gene_set))
                except Exception as e:
                    current_app.logger.error(f"Error parsing biclique data: {str(e)}")
                    current_app.logger.error(f"DMR IDs: {b.dmr_ids}")
                    current_app.logger.error(f"Gene IDs: {b.gene_ids}")
                    continue

            # Extract all DMR and gene IDs from the component data
            all_dmr_ids = parse_id_string(component_data.dmr_ids)
            all_gene_ids = parse_id_string(component_data.gene_ids)

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

            # Use the split graph from GraphManager
            graph = split_graph

            # Add debug logging for node IDs before creating NodeInfo
            current_app.logger.debug(
                f"all_dmr_ids type: {type(all_dmr_ids)}, content: {all_dmr_ids}"
            )
            current_app.logger.debug(
                f"all_gene_ids type: {type(all_gene_ids)}, content: {all_gene_ids}"
            )

            # Ensure all IDs are integers
            all_dmr_ids = {int(x) for x in all_dmr_ids}
            all_gene_ids = {int(x) for x in all_gene_ids}

            # Add debug logging for min_gene_id calculation
            min_gene_id = min(all_gene_ids) if all_gene_ids else 0
            current_app.logger.debug(f"min_gene_id: {min_gene_id}")

            # Create NodeInfo object using annotated split genes
            node_info = NodeInfo(
                all_nodes=all_dmr_ids | all_gene_ids,
                dmr_nodes=all_dmr_ids,
                regular_genes={int(g) for g in all_gene_ids},
                split_genes=split_genes,  # Using split genes from annotations
                node_degrees={int(node): graph.degree(node) for node in graph.nodes()},
                min_gene_id=min_gene_id,
            )

            from ..visualization.graph_layout_biclique import CircularBicliqueLayout
            
            # Initialize the circular layout
            layout = CircularBicliqueLayout()

            # Debug logging
            current_app.logger.debug(f"Using CircularBicliqueLayout for graph visualization")
            current_app.logger.debug(f"Number of nodes to position: {len(all_dmr_ids | all_gene_ids)}")
            current_app.logger.debug(f"DMR nodes: {len(all_dmr_ids)}")
            current_app.logger.debug(f"Regular genes: {len(all_gene_ids - split_genes)}")
            current_app.logger.debug(f"Split genes: {len(split_genes)}")

            # Calculate positions using the layout
            node_positions = layout.calculate_positions(
                graph=split_graph,
                node_info=NodeInfo(
                    all_nodes=all_dmr_ids | all_gene_ids,
                    dmr_nodes=all_dmr_ids,
                    regular_genes=all_gene_ids - split_genes,
                    split_genes=split_genes,
                    node_degrees={int(node): split_graph.degree(node) for node in split_graph.nodes()},
                    min_gene_id=min(all_gene_ids) if all_gene_ids else 0
                )
            )

            # Debug the positions
            current_app.logger.debug(f"Generated positions for {len(node_positions)} nodes")
            current_app.logger.debug(f"Sample positions: {list(node_positions.items())[:5]}")

            # Get dominating set from component details
            try:
                component_details_response = session.execute(
                    text("""
                        SELECT dominating_sets
                        FROM component_details_view
                        WHERE timepoint_id = :timepoint_id 
                        AND component_id = :component_id
                    """),
                    {"timepoint_id": timepoint_id, "component_id": component_id}
                ).first()
                
                if component_details_response and component_details_response.dominating_sets:
                    dominating_sets = json.loads(component_details_response.dominating_sets)
                    dominating_set = {int(ds["dmr_id"]) for ds in dominating_sets if "dmr_id" in ds}
                else:
                    dominating_set = set()
                    
                current_app.logger.debug(f"Found dominating set: {dominating_set}")
            except Exception as e:
                current_app.logger.error(f"Error getting dominating set: {e}")
                dominating_set = set()

            # Create visualization with the new layout
            visualization_data = create_biclique_visualization(
                bicliques=bicliques,
                node_labels=node_labels,
                node_positions=node_positions,
                node_biclique_map={},
                edge_classifications={},
                original_graph=split_graph,
                bipartite_graph=split_graph,
                dmr_metadata=dmr_metadata,
                gene_metadata=gene_metadata,
                dominating_set=dominating_set  # Add this parameter
            )

            return visualization_data

    except Exception as e:
        current_app.logger.error(f"Error generating graph visualization: {str(e)}")
        return jsonify(
            {
                "error": "Failed to generate graph visualization",
                "details": str(e) if current_app.debug else "Internal server error",
                "status": 500,
            },
            500,
        )
