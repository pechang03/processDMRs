import networkx as nx
from typing import List, Set, Dict, Tuple
import re

def read_bicliques_file(filename: str, max_DMR_id: int, original_graph: nx.Graph) -> Dict:
    """
    Read and process bicliques from the .biclusters file.
    
    Parameters:
    -----------
    filename : str
        Path to the .biclusters file
    max_DMR_id : int
        Maximum DMR ID (used to separate DMR nodes from gene nodes)
    original_graph : nx.Graph
        Original bipartite graph to verify edges
        
    Returns:
    --------
    Dict containing:
        'bicliques': List[Tuple[Set[int], Set[int]]] - list of (dmr_nodes, gene_nodes) pairs
        'statistics': Dict - header statistics
        'split_genes': Set[int] - genes that appear in multiple bicliques
        'false_positives': Set[Tuple[int, int]] - edges in bicliques but not in original graph
        'false_negatives': Set[Tuple[int, int]] - edges in original graph but not in any biclique
    """
    
    statistics = {}
    bicliques = []
    all_edges_in_bicliques = set()
    genes_seen = {}  # gene_id -> count of appearances
    header_done = False
    
    with open(filename, 'r') as f:
        # Process header until we find a line that's just numbers
        while not header_done:
            line = next(f).strip()
            
            # Skip blank lines and comment lines
            if not line or line.startswith('#'):
                continue
                
            # Check if this line is the start of bicliques data
            if line and line[0].isdigit():
                # Process first biclique line
                nodes = [int(x) for x in line.split()]
                dmr_nodes = {n for n in nodes if n < max_DMR_id}
                gene_nodes = {n for n in nodes if n >= max_DMR_id}
                bicliques.append((dmr_nodes, gene_nodes))
                header_done = True
                continue
                
            # Process header statistic line
            if line.startswith('- '):
                line = line[2:]  # Remove the "- " prefix
                if ':' in line:
                    key, value = line.split(':', 1)
                    statistics[key.strip()] = value.strip()
        
        # Process remaining bicliques
        for line in f:
            line = line.strip()
            if not line:  # Skip any blank lines
                continue
            nodes = [int(x) for x in line.split()]
            dmr_nodes = {n for n in nodes if n < max_DMR_id}
            gene_nodes = {n for n in nodes if n >= max_DMR_id}
            
            # Track gene appearances
            for gene in gene_nodes:
                genes_seen[gene] = genes_seen.get(gene, 0) + 1
                
            # Track edges in bicliques
            for dmr in dmr_nodes:
                for gene in gene_nodes:
                    all_edges_in_bicliques.add((dmr, gene))
                    
            bicliques.append((dmr_nodes, gene_nodes))
    
    # Find split genes (appearing in multiple bicliques)
    split_genes = {gene for gene, count in genes_seen.items() if count > 1}
    
    # Find false positives (edges in bicliques but not in original graph)
    false_positives = {edge for edge in all_edges_in_bicliques 
                      if not original_graph.has_edge(*edge)}
    
    # Find false negatives (edges in original graph but not in any biclique)
    original_edges = set(original_graph.edges())
    false_negatives = {edge for edge in original_edges 
                      if edge not in all_edges_in_bicliques}
    
    # Enhanced validation section
    false_positives = {edge for edge in all_edges_in_bicliques 
                      if not original_graph.has_edge(*edge)}
    false_negatives = {edge for edge in original_graph.edges() 
                      if edge not in all_edges_in_bicliques}
    
    # Add debug information to return dict
    result = {
        'bicliques': bicliques,
        'statistics': statistics,
        'split_genes': split_genes,
        'false_positives': false_positives,
        'false_negatives': false_negatives,
        'total_bicliques': len(bicliques),
        'total_split_genes': len(split_genes),
        'total_false_positives': len(false_positives),
        'total_false_negatives': len(false_negatives),
        'debug': {
            'edge_tracking': edge_tracking,
            'biclique_edge_density': len(all_edges_in_bicliques) / (len(original_graph.nodes()) * (len(original_graph.nodes()) - 1) / 2),
            'original_edge_density': len(original_graph.edges()) / (len(original_graph.nodes()) * (len(original_graph.nodes()) - 1) / 2)
        }
    }
    
    return result

def print_bicliques_summary(bicliques_result: Dict, original_graph: nx.Graph) -> None:
    """
    Print a detailed summary of the bicliques analysis results.
    
    Parameters:
    -----------
    bicliques_result : Dict
        Dictionary containing bicliques analysis results
    original_graph : nx.Graph
        The original bipartite graph for comparison
    """
    print("\n=== Bicliques Analysis ===")
    print(f"Total bicliques found: {bicliques_result['total_bicliques']}")
    print(f"Split genes: {bicliques_result['total_split_genes']}")
    
    # Calculate and print edge statistics
    total_edges = len(original_graph.edges())
    fp_percentage = (bicliques_result['total_false_positives'] / total_edges) * 100
    fn_percentage = (bicliques_result['total_false_negatives'] / total_edges) * 100
    
    # Add debug information section
    print("\nDebug Information:")
    debug = bicliques_result['debug']
    print(f"Edge counts:")
    print(f"  Original graph: {debug['edge_tracking']['edge_counts']['original']}")
    print(f"  Biclique edges: {debug['edge_tracking']['edge_counts']['bicliques']}")
    print(f"  Unique biclique edges: {len(debug['edge_tracking']['biclique_edges'])}")
    print(f"\nEdge density:")
    print(f"  Original graph: {debug['original_edge_density']:.6f}")
    print(f"  Bicliques: {debug['biclique_edge_density']:.6f}")
    
    # Sample of false positives/negatives
    if bicliques_result['false_positives']:
        print("\nSample false positives (first 5):")
        for edge in list(bicliques_result['false_positives'])[:5]:
            print(f"  {edge}")
    
    if bicliques_result['false_negatives']:
        print("\nSample false negatives (first 5):")
        for edge in list(bicliques_result['false_negatives'])[:5]:
            print(f"  {edge}")
    
    # Print and validate statistics from header
    if 'statistics' in bicliques_result:
        print("\nKey Statistics from Bicliques:")
        for key, value in bicliques_result['statistics'].items():
            print(f"  {key}: {value}")
            
        # Validate number of bicliques
        if 'Number of biclusters' in bicliques_result['statistics']:
            reported_count = int(bicliques_result['statistics']['Number of biclusters'])
            actual_count = bicliques_result['total_bicliques']
            if reported_count != actual_count:
                print(f"\nWARNING: Mismatch in bicluster counts!")
                print(f"  Header reports: {reported_count}")
                print(f"  Actually found: {actual_count}")
            else:
                print(f"\n✓ Verified: Bicluster count matches header ({actual_count})")

        # Validate edge count
        if 'Number of edges' in bicliques_result['statistics']:
            reported_edges = int(bicliques_result['statistics']['Number of edges'])
            actual_edges = len(original_graph.edges())
            if reported_edges != actual_edges:
                print(f"\nWARNING: Mismatch in edge counts!")
                print(f"  Header reports: {reported_edges}")
                print(f"  Original graph has: {actual_edges}")
            else:
                print(f"✓ Verified: Edge count matches header ({actual_edges})")
