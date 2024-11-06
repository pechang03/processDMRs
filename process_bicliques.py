import networkx as nx
import pandas as pd
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
                    # Only track edges that exist in the original graph
                    if original_graph.has_edge(dmr, gene):
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

def classify_biclique(dmr_nodes: Set, gene_nodes: Set) -> str:
    """
    Classify a biclique based on its size.
    
    Returns:
    --------
    str: 'trivial', 'small', or 'interesting'
    """
    if len(dmr_nodes) == 1 and len(gene_nodes) == 1:
        return 'trivial'
    elif len(dmr_nodes) >= 3 and len(gene_nodes) >= 3:
        return 'interesting'
    else:
        return 'small'

def print_bicliques_detail(bicliques_result: Dict, df: pd.DataFrame, gene_id_mapping: Dict) -> None:
    """
    Print detailed information about each biclique, focusing on interesting ones.
    Trivial bicliques (1 DMR, 1 gene) are ignored.
    """
    reverse_gene_mapping = {v: k for k, v in gene_id_mapping.items()}
    
    # Classify all bicliques and track interesting ones
    biclique_classifications = []
    interesting_bicliques = []
    for i, (dmr_nodes, gene_nodes) in enumerate(bicliques_result['bicliques']):
        classification = classify_biclique(dmr_nodes, gene_nodes)
        biclique_classifications.append(classification)
        if classification == 'interesting':
            interesting_bicliques.append(i)
    
    # Track genes in interesting bicliques only
    gene_to_interesting_bicliques = {}
    for i in interesting_bicliques:
        _, gene_nodes = bicliques_result['bicliques'][i]
        for gene_id in gene_nodes:
            if gene_id not in gene_to_interesting_bicliques:
                gene_to_interesting_bicliques[gene_id] = []
            gene_to_interesting_bicliques[gene_id].append(i)
    
    # Find split genes (only those appearing in multiple interesting bicliques)
    split_genes = {gene_id: biclique_list 
                  for gene_id, biclique_list in gene_to_interesting_bicliques.items() 
                  if len(biclique_list) > 1}
    
    # Print statistics
    total_bicliques = len(bicliques_result['bicliques'])
    trivial_count = biclique_classifications.count('trivial')
    small_count = biclique_classifications.count('small')
    interesting_count = len(interesting_bicliques)
    
    print("\nBiclique Classification Summary:")
    print(f"Total bicliques: {total_bicliques}")
    print(f"Trivial bicliques (1 DMR, 1 gene): {trivial_count}")
    print(f"Small bicliques: {small_count}")
    print(f"Interesting bicliques (≥3 DMRs, ≥3 genes): {interesting_count}")
    
    # Print interesting bicliques
    print("\nInteresting Bicliques:")
    for i in interesting_bicliques[:10]:  # Show first 10 interesting bicliques
        dmr_nodes, gene_nodes = bicliques_result['bicliques'][i]
        print(f"\nBiclique {i+1} ({len(dmr_nodes)} DMRs, {len(gene_nodes)} genes):")
        
        print("  DMRs:")
        for dmr_id in sorted(dmr_nodes):
            print(f"    DMR_{dmr_id + 1}")
        
        print("  Genes:")
        for gene_id in sorted(gene_nodes):
            gene_name = reverse_gene_mapping.get(gene_id, f"Unknown_{gene_id}")
            print(f"    {gene_name}")
            
            # Only show split gene info for interesting bicliques
            if gene_id in split_genes:
                other_bicliques = [b+1 for b in split_genes[gene_id] if b != i]
                if other_bicliques:
                    print(f"      ⚠ Split gene: also appears in interesting bicliques {other_bicliques}")
        
        # Check for false negatives
        for dmr_id in dmr_nodes:
            for gene_id in gene_nodes:
                edge = (dmr_id, gene_id)
                if edge not in bicliques_result['debug']['edge_distribution']:
                    print(f"    ❌ False negative edge: DMR_{dmr_id+1} - {reverse_gene_mapping[gene_id]}")

    # Print summary of split genes in interesting bicliques
    if split_genes:
        print("\nSplit Genes in Interesting Bicliques:")
        for gene_id, biclique_list in split_genes.items():
            gene_name = reverse_gene_mapping[gene_id]
            biclique_nums = [b+1 for b in biclique_list]
            print(f"  {gene_name} appears in interesting bicliques: {biclique_nums}")
