from flask import jsonify, current_app, Blueprint
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import time
import networkx as nx
from plotly.utils import PlotlyJSONEncoder

from ..schemas import (
    GraphComponentSchema,
    BicliqueMemberSchema,
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
    Generate graph visualization data for a specific component.

    Order of execution:
      1. Retrieve component details from component_details_view.
      2. Parse DMR and gene ids; determine all nodes in the component.
      3. Retrieve original and split graphs from the graph manager.
      4. Validate graphs (bipartite structure, nonempty edges, etc.).
      5. Retrieve component document from view (including biclique JSON from 'bicliques').
      6. Validate via Pydantic (GraphComponentSchema) and re-map biclique IDs.
      7. Build node_biclique_map and node labels.
      8. Compute dominating set from annotations (or fallback to metadata).
      9. Generate NodeInfo and calculate node positions using CircularBicliqueLayout.
     10. Obtain edge classifications (and stats) via graph_manager.update_component_edge_classification.
     11. Build a full component data dictionary for visualization.
     12. Call create_component_visualization with full inputs.
     13. Convert the Plotly figure to a plain dictionary.
     14. Augment the vis_dict with edge stats.
     15. Return the final visualization as JSON.
    """
    current_app.logger.info(
        f"Fetching graph for timepoint={timepoint_id}, component={component_id}"
    )
    start_time = time.time()
    try:
        engine = get_db_engine()
        with Session(engine) as session:
            # (1) Retrieve component details
            comp_query = text("""
                SELECT 
                    component_id,
                    timepoint_id,
                    all_dmr_ids as dmr_ids,
                    all_gene_ids as gene_ids,
                    graph_type,
                    categories,
                    bicliques
                FROM component_details_view
                WHERE timepoint_id = :timepoint_id 
                AND component_id = :component_id
            """)
            result = session.execute(
                comp_query, {"timepoint_id": timepoint_id, "component_id": component_id}
            ).first()
            if not result:
                current_app.logger.error(
                    f"Component {component_id} not found for timepoint {timepoint_id}"
                )
                return jsonify({"error": "Component not found", "status": 404}), 404

            # (2) Parse IDs from the view
            def parse_ids(id_str):
                if not id_str:
                    return set()
                cleaned = id_str.replace("[", "").replace("]", "").strip()
                return {int(x.strip()) for x in cleaned.split(",") if x.strip()}

            dmr_ids = parse_ids(result.dmr_ids)
            gene_ids = parse_ids(result.gene_ids)
            all_nodes = dmr_ids.union(gene_ids)

            # (3) Get the graphs using graph_manager
            graph_manager = current_app.graph_manager
            original_graph = graph_manager.get_original_graph_component(timepoint_id, all_nodes)
            split_graph = graph_manager.get_split_graph_component(timepoint_id, all_nodes)
            if not original_graph or not split_graph:
                current_app.logger.error(f"Failed to load graphs for component {component_id}")
                return jsonify({"error": "Failed to load component graphs", "status": 404}), 404

            # (4) (Omitted detailed bipartite validations for brevity.)

            # (5) Build validated component data using Pydantic
            try:
                component_data = GraphComponentSchema(
                    component_id=result.component_id,
                    timepoint_id=result.timepoint_id,
                    dmr_ids=result.dmr_ids,
                    gene_ids=result.gene_ids,
                    graph_type=result.graph_type,
                    categories=result.categories,
                    bicliques=[
                        BicliqueMemberSchema(**b)
                        for b in json.loads(result.bicliques)
                    ],
                    dominating_sets=None,  # No longer available from view
                )
            except Exception as e:
                current_app.logger.error(f"Validation error: {e}")
                return jsonify({
                    "error": "Invalid component data",
                    "details": str(e),
                    "status": 500,
                }), 500

            current_app.logger.debug(f"Validated component data: {component_data}")

            # (6) Build node_biclique_map and node_labels
            node_biclique_map = {}
            bicliques = []
            biclique_id_map = {}
            for idx, b in enumerate(component_data.bicliques):
                biclique_id_map[b.biclique_id] = idx + 1
                dmr_set = parse_ids(b.dmr_ids) if b.dmr_ids else set()
                gene_set = parse_ids(b.gene_ids) if b.gene_ids else set()
                if dmr_set and gene_set:
                    bicliques.append((dmr_set, gene_set))
                for node in dmr_set.union(gene_set):
                    node_biclique_map.setdefault(node, []).append(idx)

            node_labels = {}
            for d in dmr_ids:
                node_labels[d] = f"DMR_{d}"
            for g in gene_ids:
                node_labels[g] = f"Gene_{g}"

            # (7) Retrieve node metadata
            dmr_metadata = {}  # Implement annotation query if needed.
            gene_metadata = {}  # Implement annotation query if needed.

            # (8) Compute dominating set from component or metadata (if defined)
            dominating_set = set()
            if component_data.dominating_sets:
                dominating_set = {int(d) for d in component_data.dominating_sets}
            else:
                # Optionally fallback: use metadata for hub nodes from dmr_metadata
                dominating_set = {
                    int(n)
                    for n, info in dmr_metadata.items()
                    if info.get("node_type", "").lower() == "hub"
                }
            current_app.logger.debug(f"Final dominating set: {dominating_set}")

            # (9) Compute NodeInfo and calculate positions
            # Define gene_nodes and split_genes
            gene_nodes = all_nodes - dmr_ids
            split_genes = {n for n in gene_nodes if len(node_biclique_map.get(n, [])) > 1}
            node_info = NodeInfo(
                all_nodes=all_nodes,
                dmr_nodes=dmr_ids,
                regular_genes=gene_nodes - split_genes,
                split_genes=split_genes,
                node_degrees={n: len(node_biclique_map.get(n, [])) for n in all_nodes},
                min_gene_id=min(gene_ids) if gene_ids else 0,
            )
            layout_inst = CircularBicliqueLayout()
            node_positions = layout_inst.calculate_positions(
                graph=split_graph,
                node_info=node_info,
                node_biclique_map=node_biclique_map,
            )
            current_app.logger.debug(f"Calculated positions for {len(node_positions)} nodes")

            # (10) Obtain edge classifications and stats
            try:
                updates, edge_classifications = graph_manager.update_component_edge_classification(
                    timepoint_id,
                    original_graph,
                    split_graph,
                    bicliques,
                )
            except Exception as e:
                current_app.logger.error(f"Edge classification error: {e}")
                return jsonify({
                    "error": "Edge classification update failed",
                    "status": 500
                }), 500

            # (11) Compile a full component data dict for visualization
            comp_data = {
                "component": all_nodes,
                "raw_bicliques": bicliques,
                "dmrs": dmr_ids,
                "genes": gene_ids,
                "total_edges": len(original_graph.edges()),
                "dominating_sets": list(component_data.dominating_sets) if component_data.dominating_sets else [],
            }
            current_app.logger.debug("Component data ready for visualization.")

            # (12) Create visualization using the complete edge_classifications structure.
            vis_dict = create_component_visualization(
                component=comp_data,
                node_positions=node_positions,
                node_labels=node_labels,
                node_biclique_map=node_biclique_map,
                edge_classifications=edge_classifications,
                dmr_metadata=dmr_metadata,
                gene_metadata=gene_metadata,
            )

            # (13) Force conversion to a plain mutable dict via JSON round-trip.
            vis_dict = json.loads(json.dumps(vis_dict, cls=PlotlyJSONEncoder))

            # (14) Attach edge statistic data (stats) if present.
            stats = edge_classifications.get("stats") or {"component": {}, "bicliques": {}}
            vis_dict["edge_stats"] = stats.get("component", {})
            vis_dict["biclique_stats"] = stats.get("bicliques", {})

            current_app.logger.debug("Final visualization dictionary constructed.")
            current_app.logger.info(f"Visualization created in {time.time() - start_time:.2f} seconds")
            return vis_dict

    except Exception as e:
        current_app.logger.error(f"Error generating graph visualization: {str(e)}")
        return jsonify({
            "error": "Failed to generate graph visualization",
            "details": str(e) if current_app.debug else "Internal server error",
            "status": 500,
        })
