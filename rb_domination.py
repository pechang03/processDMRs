# file rb_domination.py

from networkx import bipartite
import networkx as nx




from heapq import heapify, heappush, heappop

def greedy_rb_domination(graph, df, area_col=None):
    """Calculate a red-blue dominating set using a greedy approach with heap"""
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
            dmr = list(graph.neighbors(gene))[0]
            dominating_set.add(dmr)
            dominated_genes.update(graph.neighbors(dmr))
    
    print(f"After processing degree-1 genes:")
    print(f"Dominating set size: {len(dominating_set)}")
    print(f"Dominated genes: {len(dominated_genes)}")

    # Initialize utility heap
    # Using negative utility for max-heap behavior
    utility_heap = []
    utility_map = {}  # Keep track of current utility for each DMR
    
    # Initialize utilities for remaining DMRs
    for dmr, data in graph.nodes(data=True):
        if data["bipartite"] == 0 and dmr not in dominating_set:
            new_genes = set(graph.neighbors(dmr)) - dominated_genes
            if new_genes:  # Only consider DMRs that would dominate new genes
                area = df.loc[df['DMR_No.'] == dmr + 1, area_col].iloc[0] if area_col else 1.0
                utility = len(new_genes)
                entry = (-utility, -area, dmr)
                utility_map[dmr] = entry
                heappush(utility_heap, entry)
    
    # While there are still undominated genes and DMRs to choose from
    while utility_heap and dominated_genes < gene_nodes:
        # Get DMR with highest utility
        neg_utility, neg_area, best_dmr = heappop(utility_heap)
        
        # Skip if this DMR is no longer in utility_map (already processed)
        if best_dmr not in utility_map:
            continue
            
        # Skip if utility has changed
        current_entry = utility_map[best_dmr]
        if current_entry != (neg_utility, neg_area, best_dmr):
            if current_entry[0] > neg_utility:  # If utility improved, re-add with new value
                heappush(utility_heap, current_entry)
            continue
            
        # Add to dominating set
        dominating_set.add(best_dmr)
        new_dominated = set(graph.neighbors(best_dmr)) - dominated_genes
        dominated_genes.update(new_dominated)
        
        # Remove the used DMR from utility tracking
        del utility_map[best_dmr]
        
        # Update utilities for affected DMRs
        affected_dmrs = set()
        for gene in new_dominated:
            affected_dmrs.update(dmr for dmr in graph.neighbors(gene) 
                               if dmr not in dominating_set and dmr in utility_map)
        
        for dmr in affected_dmrs:
            new_genes = set(graph.neighbors(dmr)) - dominated_genes
            if new_genes:  # Only keep DMRs that would dominate new genes
                area = df.loc[df['DMR_No.'] == dmr + 1, area_col].iloc[0] if area_col else 1.0
                utility = len(new_genes)
                new_entry = (-utility, -area, dmr)
                utility_map[dmr] = new_entry
                heappush(utility_heap, new_entry)
            else:
                del utility_map[dmr]  # Remove DMRs that wouldn't dominate any new genes
    
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
