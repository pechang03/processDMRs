import networkx as nx
from typing import List, Set, Dict, Tuple
import re

def read_bicliques_file(filename: str, max_DMR_id: int, original_graph: nx.Graph) -> Dict:
    """
    Read and process bicliques from a .biclusters file for any bipartite graph.
    
    Parameters:
    -----------
    filename : str
        Path to the .biclusters file
    max_DMR_id : int
        Maximum DMR ID (used to separate DMR nodes from gene nodes)
    original_graph : nx.Graph
        Original bipartite graph to verify edges against
        
    Returns:
    --------
    Dict containing analysis results and debug information
    """
    statistics = {}
    bicliques = []
    dmr_coverage = set()
    gene_coverage = set()
    edge_distribution = {}  # track which bicliques cover each edge
    
    with open(filename, 'r') as f:
        # Process header until we find a line that's just numbers
        while True:
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
                break
                
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
            
            # Track coverage and distribution for any graph
            dmr_coverage.update(dmr_nodes)
            gene_coverage.update(gene_nodes)
            
            # Track which bicliques cover each edge
            for dmr in dmr_nodes:
                for gene in gene_nodes:
                    edge = (dmr, gene)
                    if edge not in edge_distribution:
                        edge_distribution[edge] = []
                    edge_distribution[edge].append(len(bicliques))
            
            bicliques.append((dmr_nodes, gene_nodes))
    
    # Calculate statistics for any graph
    dmr_nodes = {n for n, d in original_graph.nodes(data=True) if d['bipartite'] == 0}
    gene_nodes = {n for n, d in original_graph.nodes(data=True) if d['bipartite'] == 1}
    
    uncovered_edges = set(original_graph.edges()) - set(edge_distribution.keys())
    uncovered_nodes = {node for edge in uncovered_edges for node in edge}
    
    result = {
        'bicliques': bicliques,
        'statistics': statistics,
        'graph_info': {
            'name': filename.split('/')[-1].split('.')[0],  # Extract graph name from filename
            'total_dmrs': len(dmr_nodes),
            'total_genes': len(gene_nodes),
            'total_edges': len(original_graph.edges())
        },
        'coverage': {
            'dmrs': {
                'covered': len(dmr_coverage),
                'total': len(dmr_nodes),
                'percentage': len(dmr_coverage) / len(dmr_nodes)
            },
            'genes': {
                'covered': len(gene_coverage),
                'total': len(gene_nodes),
                'percentage': len(gene_coverage) / len(gene_nodes)
            },
            'edges': {
                'single_coverage': len([e for e, b in edge_distribution.items() if len(b) == 1]),
                'multiple_coverage': len([e for e, b in edge_distribution.items() if len(b) > 1]),
                'uncovered': len(uncovered_edges),
                'total': len(original_graph.edges())
            }
        },
        'debug': {
            'uncovered_edges': list(uncovered_edges)[:5],  # Sample of uncovered edges
            'uncovered_nodes': len(uncovered_nodes),
            'edge_distribution': edge_distribution
        }
    }
    
    return result

def print_bicliques_summary(bicliques_result: Dict, original_graph: nx.Graph) -> None:
    """
    Print detailed summary of bicliques analysis for any bipartite graph.
    
    Parameters:
    -----------
    bicliques_result : Dict
        Results from read_bicliques_file
    original_graph : nx.Graph
        Original bipartite graph used for comparison
    """
    graph_name = bicliques_result['graph_info']['name']
    print(f"\n=== Bicliques Analysis for {graph_name} ===")
    
    # Basic statistics
    print(f"\nGraph Statistics:")
    print(f"DMRs: {bicliques_result['graph_info']['total_dmrs']}")
    print(f"Genes: {bicliques_result['graph_info']['total_genes']}")
    print(f"Total edges: {bicliques_result['graph_info']['total_edges']}")
    print(f"Total bicliques found: {len(bicliques_result['bicliques'])}")
    
    # Coverage statistics
    print(f"\nNode Coverage:")
    dmr_cov = bicliques_result['coverage']['dmrs']
    gene_cov = bicliques_result['coverage']['genes']
    print(f"DMRs: {dmr_cov['covered']}/{dmr_cov['total']} ({dmr_cov['percentage']:.1%})")
    print(f"Genes: {gene_cov['covered']}/{gene_cov['total']} ({gene_cov['percentage']:.1%})")
    
    # Edge coverage
    edge_cov = bicliques_result['coverage']['edges']
    print(f"\nEdge Coverage:")
    print(f"Single coverage: {edge_cov['single_coverage']} edges")
    print(f"Multiple coverage: {edge_cov['multiple_coverage']} edges")
    print(f"Uncovered: {edge_cov['uncovered']} edges ({edge_cov['uncovered']/edge_cov['total']:.1%})")
    
    if edge_cov['uncovered'] > 0:
        print("\nSample of uncovered edges:")
        for edge in bicliques_result['debug']['uncovered_edges']:
            print(f"  {edge}")
        print(f"Total nodes involved in uncovered edges: {bicliques_result['debug']['uncovered_nodes']}")
    
    # Validate statistics from header if present
    if 'statistics' in bicliques_result and bicliques_result['statistics']:
        print("\nValidation of Header Statistics:")
        for key, value in bicliques_result['statistics'].items():
            print(f"  {key}: {value}")
