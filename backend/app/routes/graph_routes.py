from flask import jsonify
from ..utils.extensions import app
from ..database.connection import get_db_engine
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..visualization.core import create_biclique_visualization
from ..visualization.graph_layout_biclique import CircularBicliqueLayout
from ..utils.node_info import NodeInfo
import networkx as nx

@app.route("/api/graph/<int:timepoint_id>/<int:component_id>", methods=["GET"])
def get_component_graph(timepoint_id, component_id):
    """Get graph visualization data for a specific component."""
    app.logger.info(f"Fetching graph for timepoint={timepoint_id}, component={component_id}")
    
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
                {"timepoint_id": timepoint_id, "component_id": component_id}
            ).scalar()
            
            app.logger.info(f"Found {count} matching components")
            
            if count == 0:
                app.logger.error(f"Component {component_id} not found for timepoint {timepoint_id}")
                return jsonify({
                    "error": "Component not found",
                    "status": 404
                }), 404

            # Get component data
            query = text("""
                SELECT 
                    c.component_id,
                    c.timepoint_id,
                    c.all_dmr_ids as dmr_ids,
                    c.all_gene_ids as gene_ids,
                    c.graph_type,
                    c.categories as category
                FROM component_details_view c
                WHERE c.timepoint_id = :timepoint_id 
                AND c.component_id = :component_id
            """)
            
            result = session.execute(
                query, 
                {"timepoint_id": timepoint_id, "component_id": component_id}
            ).first()
            
            if not result:
                app.logger.error("Query returned no results after verifying existence")
                return jsonify({
                    "error": "Failed to retrieve component data",
                    "status": 500
                }), 500

            app.logger.debug(f"Component data found: {result}")

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
                bicliques_query, 
                {"component_id": component_id}
            ).fetchall()

            app.logger.info(f"Found {len(bicliques_result)} bicliques")

            # Parse bicliques data
            bicliques = []
            for b in bicliques_result:
                try:
                    dmr_ids = [int(x) for x in b.dmr_ids.strip('{}').split(',') if x]
                    gene_ids = [int(x) for x in b.gene_ids.strip('{}').split(',') if x]
                    bicliques.append((set(dmr_ids), set(gene_ids)))
                except Exception as e:
                    app.logger.error(f"Error parsing biclique data: {str(e)}")
                    continue

            # Get node metadata
            dmr_query = text("""
                SELECT 
                    d.id,
                    d.area,
                    d.description
                FROM dmr_timepoint_annotation d
                WHERE d.timepoint_id = :timepoint_id
                AND d.id = ANY(:dmr_ids)
            """)

            gene_query = text("""
                SELECT 
                    g.gene_id,
                    g.symbol,
                    g.description
                FROM gene_timepoint_annotation g
                WHERE g.timepoint_id = :timepoint_id
                AND g.gene_id = ANY(:gene_ids)
            """)

            # Extract all DMR and gene IDs
            all_dmr_ids = set()
            all_gene_ids = set()
            for dmr_set, gene_set in bicliques:
                all_dmr_ids.update(dmr_set)
                all_gene_ids.update(gene_set)

            # Get metadata
            dmr_metadata = {}
            gene_metadata = {}
            
            dmr_results = session.execute(
                dmr_query, 
                {
                    "timepoint_id": timepoint_id,
                    "dmr_ids": list(all_dmr_ids)
                }
            ).fetchall()
            
            gene_results = session.execute(
                gene_query,
                {
                    "timepoint_id": timepoint_id,
                    "gene_ids": list(all_gene_ids)
                }
            ).fetchall()

            # Create metadata dictionaries
            for dmr in dmr_results:
                dmr_metadata[dmr.id] = {
                    "area": dmr.area,
                    "description": dmr.description
                }

            for gene in gene_results:
                gene_metadata[gene.gene_id] = {
                    "symbol": gene.symbol,
                    "description": gene.description
                }

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

            # Create NodeInfo object
            node_info = NodeInfo(
                all_nodes=all_dmr_ids | all_gene_ids,
                dmr_nodes=all_dmr_ids,
                regular_genes={g for g in all_gene_ids},
                split_genes=set(),  # You might want to calculate this
                node_degrees={node: graph.degree(node) for node in graph.nodes()},
                min_gene_id=min(all_gene_ids) if all_gene_ids else 0
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
                gene_metadata=gene_metadata
            )

            return visualization_data

    except Exception as e:
        app.logger.error(f"Error generating graph visualization: {str(e)}")
        return jsonify({
            "error": "Failed to generate graph visualization",
            "details": str(e) if app.debug else "Internal server error",
            "status": 500
        }), 500
