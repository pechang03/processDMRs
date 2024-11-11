import networkx as nx
from typing import List, Dict

def process_components(bipartite_graph: nx.Graph, bicliques_result: Dict) -> List[Dict]:
    """Process connected components of the graph."""
    components = list(nx.connected_components(bipartite_graph))
    component_data = []

    for idx, component in enumerate(components):
        subgraph = bipartite_graph.subgraph(component)
        component_bicliques = []

        for bidx, (dmr_nodes, gene_nodes) in enumerate(bicliques_result["bicliques"]):
            if any(node in component for node in dmr_nodes):
                biclique_info = {
                    "dmrs": sorted(list(dmr_nodes)),
                    "genes": sorted(list(gene_nodes)),
                    "size": f"{len(dmr_nodes)}×{len(gene_nodes)}",
                    "details": bicliques_result.get(f"biclique_{bidx+1}_details", {}),
                }
                if len(dmr_nodes) > 1 or len(gene_nodes) > 1:
                    component_bicliques.append(biclique_info)

        if component_bicliques:
            component_data.append(
                {
                    "id": idx + 1,
                    "size": len(component),
                    "dmrs": len(
                        [
                            n
                            for n in subgraph.nodes()
                            if bipartite_graph.nodes[n]["bipartite"] == 0
                        ]
                    ),
                    "genes": len(
                        [
                            n
                            for n in subgraph.nodes()
                            if bipartite_graph.nodes[n]["bipartite"] == 1
                        ]
                    ),
                    "bicliques": component_bicliques,
                }
            )

    return component_data
