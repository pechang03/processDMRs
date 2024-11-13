import networkx as nx
from typing import List, Dict, Tuple
from .classifier import is_interesting_component
from visualization import (
    create_node_biclique_map,
    create_biclique_visualization,
    calculate_node_positions
)

def process_components(
    bipartite_graph: nx.Graph, 
    bicliques_result: Dict,
    dmr_metadata: Dict[str, Dict] = None,  # Add these parameters
    gene_metadata: Dict[str, Dict] = None,
    gene_id_mapping: Dict[str, int] = None  # Add this parameter
) -> Tuple[List[Dict], List[Dict]]:
    """Process connected components of the graph."""
    print(f"Starting component processing...")  # Debug logging
    components = list(nx.connected_components(bipartite_graph))
    interesting_components = []
    simple_connections = []
    
    # Create reverse mapping for gene IDs
    reverse_gene_mapping = {v: k for k, v in gene_id_mapping.items()} if gene_id_mapping else {}

    print(f"Found {len(components)} components")  # Debug logging
    print(f"Number of bicliques: {len(bicliques_result['bicliques'])}")  # Debug logging

    for idx, component in enumerate(components):
        subgraph = bipartite_graph.subgraph(component)
        component_bicliques = []
        single_connection_genes = []
        
        # Get nodes in this component
        component_nodes = set(component)
        
        # Collect component's bicliques
        component_raw_bicliques = []
        for dmr_nodes, gene_nodes in bicliques_result["bicliques"]:
            biclique_nodes = dmr_nodes | gene_nodes
            if biclique_nodes & component_nodes:
                component_raw_bicliques.append((dmr_nodes, gene_nodes))
        
        # Find split genes in this component
        gene_to_bicliques = {}
        for bidx, (_, gene_nodes) in enumerate(component_raw_bicliques):
            for gene in gene_nodes:
                if gene not in gene_to_bicliques:
                    gene_to_bicliques[gene] = []
                gene_to_bicliques[gene].append(bidx + 1)  # Store 1-based biclique index
        
        split_genes = {
            gene: bicliques 
            for gene, bicliques in gene_to_bicliques.items() 
            if len(bicliques) > 1
        }

        # Skip if component isn't interesting
        if not is_interesting_component(component_raw_bicliques):
            # Process as simple connection
            for node in component_nodes:
                if node in gene_id_mapping.values():  # If it's a gene
                    neighbors = list(bipartite_graph.neighbors(node))
                    for dmr in neighbors:
                        gene_name = reverse_gene_mapping.get(node, f"Gene_{node}")
                        simple_connections.append({
                            "gene": node,
                            "dmr": dmr,
                            "gene_name": gene_name,
                            "dmr_name": f"DMR_{dmr+1}",
                            "gene_description": gene_metadata.get(gene_name, {}).get("description", "N/A"),
                            "dmr_area": dmr_metadata.get(f"DMR_{dmr+1}", {}).get("area", "N/A")
                        })
            continue

        # Process interesting bicliques
        for bidx, (dmr_nodes, gene_nodes) in enumerate(component_raw_bicliques):
            if len(dmr_nodes) >= 3 and len(gene_nodes) >= 3:  # Only include interesting bicliques
                biclique_info = {
                    "dmrs": sorted(list(dmr_nodes)),
                    "genes": sorted(list(gene_nodes)),
                    "size": f"{len(dmr_nodes)}×{len(gene_nodes)}",
                    "details": {
                        "dmrs": [
                            {
                                "id": f"DMR_{dmr+1}",
                                "area": dmr_metadata.get(f"DMR_{dmr+1}", {}).get("area", "N/A"),
                                "description": dmr_metadata.get(f"DMR_{dmr+1}", {}).get("description", "N/A")
                            } 
                            for dmr in dmr_nodes
                        ],
                        "genes": [
                            {
                                "name": reverse_gene_mapping.get(gene, f"Gene_{gene}"),
                                "description": gene_metadata.get(
                                    reverse_gene_mapping.get(gene, f"Gene_{gene}"), 
                                    {}
                                ).get("description", "N/A"),
                                "is_split": gene in split_genes
                            }
                            for gene in gene_nodes
                        ]
                    }
                }
                component_bicliques.append(biclique_info)

        if component_bicliques:  # Only add if there are interesting bicliques
            dmr_count = len([n for n in subgraph.nodes() if bipartite_graph.nodes[n]["bipartite"] == 0])
            gene_count = len([n for n in subgraph.nodes() if bipartite_graph.nodes[n]["bipartite"] == 1])
            
            # Add split genes information
            split_genes_info = [
                {
                    "gene_name": reverse_gene_mapping.get(gene, f"Gene_{gene}"),
                    "description": gene_metadata.get(
                        reverse_gene_mapping.get(gene, f"Gene_{gene}"), 
                        {}
                    ).get("description", "N/A"),
                    "bicliques": bicliques
                }
                for gene, bicliques in split_genes.items()
            ]
            
            component_info = {
                "id": idx + 1,
                "size": len(component),
                "dmrs": dmr_count,
                "genes": gene_count,
                "split_genes": split_genes_info,
                "bicliques": component_bicliques,
                "raw_bicliques": [(set(bic["dmrs"]), set(bic["genes"])) for bic in component_bicliques]
            }
            interesting_components.append(component_info)

    return interesting_components, simple_connections
