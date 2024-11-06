# file rb_domination.py

from networkx import bipartite
import networkx as nx




def greedy_rb_domination(graph, df, area_col=None):
    """Calculate a red-blue dominating set using a greedy approach"""
    # Initialize the dominating set
    dominating_set = set()

    # Get all gene nodes (bipartite=1)
    gene_nodes = {node for node, data in graph.nodes(data=True) if data["bipartite"] == 1}

    # Keep track of dominated genes
    dominated_genes = set()

    # First, handle degree-1 genes that aren't already dominated
    degree_one_genes = {gene for gene in gene_nodes if graph.degree(gene) == 1}

    print(f"Found {len(degree_one_genes)} genes with degree 1")

    for gene in degree_one_genes:
        if gene not in dominated_genes:
            # Get the single neighbor (DMR) of this gene
            dmr = list(graph.neighbors(gene))[0]
            dominating_set.add(dmr)
            # Update dominated genes with ALL neighbors of this DMR
            dominated_genes.update(graph.neighbors(dmr))

    print(f"After processing degree-1 genes:")
    print(f"Dominating set size: {len(dominating_set)}")
    print(f"Dominated genes: {len(dominated_genes)}")

    # Get remaining undominated subgraph
    remaining_graph = graph.copy()
    remaining_graph.remove_nodes_from(dominating_set)

    # While there are still undominated genes
    while dominated_genes < gene_nodes:
        # Get DMR nodes in remaining graph
        dmr_nodes = [node for node, data in remaining_graph.nodes(data=True) 
                    if data["bipartite"] == 0]
        
        if not dmr_nodes:
            break
            
        # Calculate utility (number of new genes that would be dominated)
        def get_dmr_utility(dmr):
            new_genes = set(remaining_graph.neighbors(dmr)) - dominated_genes
            area = df.loc[df['DMR_No.'] == dmr + 1, area_col].iloc[0] if area_col else 1.0
            return len(new_genes), area
            
        # Choose DMR with highest utility
        best_dmr = max(dmr_nodes, key=lambda x: get_dmr_utility(x))
        
        # Add to dominating set and update dominated genes
        dominating_set.add(best_dmr)
        dominated_genes.update(remaining_graph.neighbors(best_dmr))
        
        # Update remaining graph
        remaining_graph.remove_node(best_dmr)
    
    return dominating_set


def process_components(graph, df):
    # Process larger components first
    components = sorted(nx.connected_components(graph), key=len, reverse=True)
    dominating_sets = []

    for component in components:
        if len(component) > 1:  # Skip isolated nodes
            subgraph = graph.subgraph(component)
            dom_set = greedy_rb_domination(subgraph, df)
            dominating_sets.extend(dom_set)

    return dominating_sets
