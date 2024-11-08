"""
Script to generate TikZ visualizations of interesting bicliques using tikzplotlib
"""
import matplotlib.pyplot as plt
import tikzplotlib
import networkx as nx
from typing import Dict, List, Set, Tuple
import pandas as pd
import numpy as np  # Add this import for np.linspace

from graph_layout import calculate_node_positions
from process_bicliques import read_bicliques_file, classify_biclique
from processDMR import read_excel_file, create_bipartite_graph
from graph_utils import process_enhancer_info

def create_tikz_visualization(bicliques: List[Tuple[Set[int], Set[int]]], node_positions: Dict[int, Tuple[float, float]], node_labels: Dict[int, str], output_file: str):
    """
    Create a TikZ visualization of the bicliques.

    Args:
        bicliques: List of (dmr_nodes, gene_nodes) tuples
        node_positions: Maps node IDs to (x,y) positions
        node_labels: Maps node IDs to display labels
        output_file: Path to save the TikZ file
    """
    plt.figure(figsize=(10, 10))
    pos = node_positions

    # Draw edges
    for biclique in bicliques:
        dmr_nodes, gene_nodes = biclique
        for dmr in dmr_nodes:
            for gene in gene_nodes:
                plt.plot(
                    [pos[dmr][0], pos[gene][0]],
                    [pos[dmr][1], pos[gene][1]],
                    'k-', alpha=0.5
                )

    # Draw nodes
    dmr_nodes = {n for dmr_nodes, _ in bicliques for n in dmr_nodes}
    gene_nodes = {n for _, gene_nodes in bicliques for n in gene_nodes}

    dmr_pos = {n: pos[n] for n in dmr_nodes}
    gene_pos = {n: pos[n] for n in gene_nodes}

    nx.draw_networkx_nodes(
        nx.Graph(),
        pos=dmr_pos,
        node_color='blue',
        node_size=500,
        alpha=0.8
    )
    nx.draw_networkx_nodes(
        nx.Graph(),
        pos=gene_pos,
        node_color='red',
        node_size=500,
        alpha=0.8
    )

    # Draw labels
    nx.draw_networkx_labels(
        nx.Graph(),
        pos=pos,
        labels=node_labels,
        font_size=12,
        font_color='black'
    )

    # Save TikZ file
    tikzplotlib.save(output_file)
    plt.close()

def main():
    # Read DSS1 data
    df = read_excel_file("./data/DSS1.xlsx")
    df["Processed_Enhancer_Info"] = df["ENCODE_Enhancer_Interaction(BingRen_Lab)"].apply(process_enhancer_info)

    # Create gene_id_mapping
    all_genes = set()
    all_genes.update(df["Gene_Symbol_Nearby"].dropna())
    all_genes.update([g for genes in df["Processed_Enhancer_Info"] for g in genes if g])
    gene_id_mapping = {gene: idx + len(df) for idx, gene in enumerate(sorted(all_genes))}

    # Create bipartite graph
    bipartite_graph = create_bipartite_graph(df, gene_id_mapping)

    # Read bicliques file
    bicliques_result = read_bicliques_file(
        "./data/bipartite_graph_output.txt.biclusters",
        max(df["DMR_No."]),
        bipartite_graph
    )

    # Filter interesting bicliques
    interesting_bicliques = [
        biclique for biclique in bicliques_result['bicliques']
        if classify_biclique(*biclique) == 'interesting'
    ]

    # Calculate node positions
    node_positions = calculate_node_positions(interesting_bicliques, {})

    # Create node labels
    node_labels = {}
    for dmr_id in range(len(df)):
        node_id = dmr_id
        node_labels[node_id] = f"DMR_{dmr_id+1}"

    for gene, gene_id in gene_id_mapping.items():
        node_labels[gene_id] = gene

    # Create TikZ visualization
    create_tikz_visualization(
        interesting_bicliques,
        node_positions,
        node_labels,
        "biclique_visualization.tex"
    )

if __name__ == "__main__":
    main()
