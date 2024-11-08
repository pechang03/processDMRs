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
from graph_visualize import create_node_biclique_map

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
                if dmr in pos and gene in pos:  # Only draw if both nodes have positions
                    plt.plot(
                        [pos[dmr][0], pos[gene][0]],
                        [pos[dmr][1], pos[gene][1]],
                        'k-', alpha=0.5
                    )

    # Draw nodes
    dmr_nodes = {n for dmr_nodes, _ in bicliques for n in dmr_nodes if n in pos}  # Only include nodes with positions
    gene_nodes = {n for _, gene_nodes in bicliques for n in gene_nodes if n in pos}  # Only include nodes with positions

    dmr_pos = {n: pos[n] for n in dmr_nodes}
    gene_pos = {n: pos[n] for n in gene_nodes}

    nx.draw_networkx_nodes(
        nx.Graph(),
        pos=dmr_pos,
        node_color='blue',
        node_size=500,
        alpha=0.8,
        nodelist=list(dmr_pos.keys())  # Explicitly specify nodes to draw
    )
    nx.draw_networkx_nodes(
        nx.Graph(),
        pos=gene_pos,
        node_color='red',
        node_size=500,
        alpha=0.8,
        nodelist=list(gene_pos.keys())  # Explicitly specify nodes to draw
    )

    # Draw labels only for nodes that have positions
    labels_to_draw = {n: label for n, label in node_labels.items() if n in pos}
    nx.draw_networkx_labels(
        nx.Graph(),
        pos=pos,
        labels=labels_to_draw,
        font_size=12,
        font_color='black'
    )

    # Save TikZ file
    tikzplotlib.save(output_file)
    plt.close()

def main():
    # Read and prepare data using processDMR functions
    df = read_excel_file("./data/DSS1.xlsx")
    df["Processed_Enhancer_Info"] = df["ENCODE_Enhancer_Interaction(BingRen_Lab)"].apply(process_enhancer_info)
    
    # Create gene_id_mapping
    all_genes = set()
    all_genes.update(df["Gene_Symbol_Nearby"].dropna())
    all_genes.update([g for genes in df["Processed_Enhancer_Info"] for g in genes])
    gene_id_mapping = {gene: idx + len(df) for idx, gene in enumerate(sorted(all_genes))}
    
    # Create bipartite graph
    bipartite_graph = create_bipartite_graph(df, gene_id_mapping)

    # Rest of the function remains the same...
    bicliques_result = read_bicliques_file(
        "./data/bipartite_graph_output.txt.biclusters",
        max(df["DMR_No."]),
        bipartite_graph
    )

    interesting_bicliques = [
        biclique for biclique in bicliques_result['bicliques']
        if classify_biclique(*biclique) == 'interesting'
    ]

    node_biclique_map = create_node_biclique_map(interesting_bicliques)
    node_positions = calculate_node_positions(interesting_bicliques, node_biclique_map)

    # Create node labels
    node_labels = {}
    for dmr_id in range(len(df)):
        if dmr_id in node_positions:
            node_labels[dmr_id] = f"DMR_{dmr_id+1}"

    reverse_gene_mapping = {v: k for k, v in gene_id_mapping.items()}
    for gene_id in node_positions:
        if gene_id >= len(df):  # Gene nodes
            gene_name = reverse_gene_mapping.get(gene_id, f"Gene_{gene_id}")
            node_labels[gene_id] = gene_name

    # Create metadata for node labels
    for dmr_id in range(len(df)):
        if dmr_id in node_positions:
            row = df[df['DMR_No.'] == dmr_id + 1].iloc[0]
            gene_desc = row['Gene_Description'] if 'Gene_Description' in df.columns else 'N/A'
            if pd.notna(gene_desc) and gene_desc != "N/A":
                node_labels[dmr_id] = f"{node_labels[dmr_id]}\n{gene_desc}"

    # Create TikZ visualization
    create_tikz_visualization(
        interesting_bicliques,
        node_positions,
        node_labels,
        "biclique_visualization.tex"
    )

if __name__ == "__main__":
    main()
