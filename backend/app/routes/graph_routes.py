import json
from flask import jsonify
from pydantic import ValidationError
from ..utils.extensions import app
from ..schemas import (
    GraphComponentSchema, 
    BicliqueMemberSchema, 
    DmrComponentSchema,
    GeneAnnotationViewSchema,
    DmrAnnotationViewSchema
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


@app.route("/api/graph/<int:timepoint_id>/<int:component_id>", methods=["GET"])
def get_component_graph(timepoint_id, component_id):
    """Get graph visualization data for a specific component."""
    app.logger.info(
        f"Fetching graph for timepoint={timepoint_id}, component={component_id}"
    )

    try:
        engine = get_db_engine()
        with Session(engine) as session:
            # First verify component exists
            verify_query = text("""
                SELECT COUNT(*)
                FROM components c
                WHERE c.timepoint_id = :timepoint_id 
                AND c.id = :component_id
            """)

            count = session.execute(
                verify_query,
                {"timepoint_id": timepoint_id, "component_id": component_id},
            ).scalar()

            app.logger.info(f"Found {count} matching components")

            if count == 0:
                app.logger.error(
                    f"Component {component_id} not found for timepoint {timepoint_id}"
                )
                return jsonify({"error": "Component not found", "status": 404}), 404

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
                app.logger.error("Query returned no results after verifying existence")
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
                app.logger.error(f"Validation error: {e}")
                return jsonify(
                    {
                        "error": "Invalid component data",
                        "details": e.errors(),
                        "status": 500,
                    }
                ), 500

            app.logger.debug(f"Validated component data: {component_data}")

            # Get bicliques for this component
            bicliques_query = text("""
                SELECT 
                    b.dmr_ids,
                    b.gene_ids
                FROM bicliques b
                JOIN component_bicliques cb ON b.id = cb.biclique_id
                WHERE cb.component_id = :component_id
            """)

            bicliques_result = session.execute(
                bicliques_query, {"component_id": component_id}
            ).fetchall()

            app.logger.info(f"Found {len(bicliques_result)} bicliques")

            # Parse bicliques data
            bicliques = []
            for b in component_data.bicliques:
                try:
                    app.logger.debug(f"Component {b}")
                    # Parse DMR and gene IDs using the helper function
                    dmr_set = parse_id_string(b.dmr_ids)
                    gene_set = parse_id_string(b.gene_ids)
                    bicliques.append((dmr_set, gene_set))
                except Exception as e:
                    app.logger.error(f"Error parsing biclique data: {str(e)}")
                    app.logger.error(f"DMR IDs: {b.dmr_ids}")
                    app.logger.error(f"Gene IDs: {b.gene_ids}")
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
            gene_metadata = {}

            dmr_results = session.execute(
                dmr_query, {"timepoint_id": timepoint_id, "component_id": component_id}
            ).fetchall()

            gene_results = session.execute(
                gene_query, {"timepoint_id": timepoint_id, "component_id": component_id}
            ).fetchall()
            app.logger.debug("graph_routes point 1")
            # Create metadata dictionaries using Pydantic models
            for dmr in dmr_results:
                try:
                    dmr_data = DmrComponentSchema.model_validate(dmr)
                    dmr_metadata[dmr_data.id] = dmr_data.model_dump()
                except ValidationError as e:
                    app.logger.error(f"Error validating DMR data: {e}")
                    continue

            # Identify split genes from annotations using Pydantic models
            app.logger.debug("graph_routes point 2")
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
                        biclique_ids=row.biclique_ids
                    )
                    
                    gene_metadata = GeneAnnotationViewSchema(**gene_data)
                    gene_id = gene_metadata.gene_id

                    # Check if gene is split based on gene_type or biclique_ids
                    if gene_metadata.gene_type and gene_metadata.gene_type.lower() == "split":
                        split_genes.add(gene_id)
                    elif gene_metadata.biclique_ids:
                        biclique_count = len(
                            [x for x in gene_metadata.biclique_ids.split(",") if x.strip()]
                        )
                        if biclique_count > 1:
                            split_genes.add(gene_id)
                except ValidationError as e:
                    app.logger.error(f"Error validating gene data: {e}")
                    continue

            app.logger.debug(
                f"Found {len(split_genes)} split genes from annotations: {split_genes}"
            )

            # Create node labels
            node_labels = {}
            for dmr_id in all_dmr_ids:
                node_labels[dmr_id] = f"DMR_{dmr_id}"
            for gene_id in all_gene_ids:
                symbol = gene_metadata.get(gene_id, {}).get("symbol")
                node_labels[gene_id] = symbol if symbol else f"Gene_{gene_id}"

            # Create graph and calculate layout
            graph = nx.Graph()
            for dmr_set, gene_set in bicliques:
                for dmr in dmr_set:
                    for gene in gene_set:
                        graph.add_edge(dmr, gene)

            # Add debug logging for node IDs before creating NodeInfo
            app.logger.debug(
                f"all_dmr_ids type: {type(all_dmr_ids)}, content: {all_dmr_ids}"
            )
            app.logger.debug(
                f"all_gene_ids type: {type(all_gene_ids)}, content: {all_gene_ids}"
            )

            # Ensure all IDs are integers
            all_dmr_ids = {int(x) for x in all_dmr_ids}
            all_gene_ids = {int(x) for x in all_gene_ids}

            # Add debug logging for min_gene_id calculation
            min_gene_id = min(all_gene_ids) if all_gene_ids else 0
            app.logger.debug(f"min_gene_id: {min_gene_id}")

            # Create NodeInfo object using annotated split genes
            node_info = NodeInfo(
                all_nodes=all_dmr_ids | all_gene_ids,
                dmr_nodes=all_dmr_ids,
                regular_genes={int(g) for g in all_gene_ids},
                split_genes=split_genes,  # Using split genes from annotations
                node_degrees={int(node): graph.degree(node) for node in graph.nodes()},
                min_gene_id=min_gene_id,
            )

            # Calculate positions using CircularBicliqueLayout
            layout = CircularBicliqueLayout()
            node_positions = layout.calculate_positions(graph, node_info)

            # Create visualization
            visualization_data = create_biclique_visualization(
                bicliques=bicliques,
                node_labels=node_labels,
                node_positions=node_positions,
                node_biclique_map={},  # You might want to calculate this
                edge_classifications={},
                original_graph=graph,
                bipartite_graph=graph,
                dmr_metadata=dmr_metadata,
                gene_metadata=gene_metadata,
            )

            return visualization_data

    except Exception as e:
        app.logger.error(f"Error generating graph visualization: {str(e)}")
        return jsonify(
            {
                "error": "Failed to generate graph visualization",
                "details": str(e) if app.debug else "Internal server error",
                "status": 500,
            }
        ), 500
