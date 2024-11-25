import argparse
import sys
import os
import pandas as pd
from data_loader import get_excel_sheets

import networkx as nx
import csv
import time
import psutil
from typing import Dict, Tuple

from biclique_analysis import (
    process_bicliques,
    process_enhancer_info,
    create_node_metadata,
    process_components,
    reporting,
)
from biclique_analysis.reader import read_bicliques_file
from biclique_analysis.reporting import print_bicliques_summary, print_bicliques_detail
from visualization import calculate_node_positions  # Import from package root
from visualization.core import create_biclique_visualization
from visualization import create_node_biclique_map
from data_loader import validate_bipartite_graph
from data_loader import create_bipartite_graph
from data_loader import read_excel_file
from rb_domination import (
    greedy_rb_domination,
    calculate_dominating_sets,  # Changed name
    print_domination_statistics,
    copy_dominating_set,  # Add new function
)

# Add version constant at top of file
__version__ = "0.0.3-alpha"


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Process DMR data and generate biclique analysis",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "--input", default="./data/DSS1.xlsx", help="Path to input Excel file"
    )
    parser.add_argument(
        "--output",
        default="bipartite_graph_output.txt",
        help="Path to output graph file",
    )
    parser.add_argument(
        "--format",
        choices=["gene-name", "number"],
        default="gene-name",
        help="Format for biclique file parsing (gene-name or number)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    return parser.parse_args()


def write_bipartite_graph(
    graph: nx.Graph, output_file: str, df: pd.DataFrame, gene_id_mapping: Dict[str, int]
):
    """Write bipartite graph to file using consistent gene IDs."""
    try:
        # Get unique edges (DMR first, gene second)
        unique_edges = set()
        for edge in graph.edges():
            dmr_node = edge[0] if graph.nodes[edge[0]]["bipartite"] == 0 else edge[1]
            gene_node = edge[1] if graph.nodes[edge[0]]["bipartite"] == 0 else edge[0]
            unique_edges.add((dmr_node, gene_node))

        # Sort edges for deterministic output
        sorted_edges = sorted(unique_edges)

        with open(output_file, "w") as file:
            # Write header
            n_dmrs = len(df["DMR_No."].unique())
            n_genes = len(gene_id_mapping)
            file.write(f"{n_dmrs} {n_genes}\n")

            # Write edges
            for dmr_id, gene_id in sorted_edges:
                file.write(f"{dmr_id} {gene_id}\n")

        # Validation output
        print(f"\nWrote graph to {output_file}:")
        print(f"DMRs: {n_dmrs}")
        print(f"Genes: {n_genes}")
        print(f"Edges: {len(sorted_edges)}")

        # Debug first few edges
        print("\nFirst 5 edges written:")
        for dmr_id, gene_id in sorted_edges[:5]:
            gene_name = [k for k, v in gene_id_mapping.items() if v == gene_id][0]
            print(f"DMR_{dmr_id + 1} -> Gene_{gene_id} ({gene_name})")

    except Exception as e:
        print(f"Error writing {output_file}: {e}")
        raise


def write_gene_mappings(
    gene_id_mapping: Dict[str, int], output_file: str, dataset_name: str
):
    """Write gene ID mappings to CSV file for a specific dataset."""
    try:
        print(f"\nWriting gene mappings for {dataset_name}:")
        print(f"Number of genes to write: {len(gene_id_mapping)}")
        print(
            f"ID range: {min(gene_id_mapping.values())} to {max(gene_id_mapping.values())}"
        )
        print("\nFirst few mappings:")
        for gene, gene_id in sorted(list(gene_id_mapping.items())[:5]):
            print(f"{gene}: {gene_id}")

        with open(output_file, "w", newline="") as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(["Gene", "ID"])
            for gene, gene_id in sorted(gene_id_mapping.items()):
                csvwriter.writerow([gene, gene_id])
        print(f"Wrote {len(gene_id_mapping)} gene mappings to {output_file}")
    except Exception as e:
        print(f"Error writing {output_file}: {e}")
        raise


import json


def process_single_dataset(df, output_file, args, gene_id_mapping=None, max_dmr=None):
    """Process a single dataset and write the bipartite graph to a file."""
    try:
        # Process enhancer info if not already processed
        if "Processed_Enhancer_Info" not in df.columns:
            df["Processed_Enhancer_Info"] = df["ENCODE_Enhancer_Interaction(BingRen_Lab)"].apply(process_enhancer_info)

        # If no master mapping provided, create one
        if gene_id_mapping is None or max_dmr is None:
            all_genes = set()
            gene_col = (
                "Gene_Symbol_Nearby"
                if "Gene_Symbol_Nearby" in df.columns
                else "Gene_Symbol"
            )

            # Add genes from gene column (case-insensitive)
            gene_names = df[gene_col].dropna().str.strip().str.lower()
            all_genes.update(gene_names)

            # Now we can safely process enhancer info
            for genes in df["Processed_Enhancer_Info"]:
                if genes:  # Check if not None/empty
                    all_genes.update(g.strip().lower() for g in genes)

            # Sort genes alphabetically for deterministic assignment
            sorted_genes = sorted(all_genes)

            # Create gene mapping starting after max DMR number
            max_dmr = df["DMR_No."].max()
            gene_id_mapping = {
                gene: idx + max_dmr + 1 for idx, gene in enumerate(sorted_genes)
            }

        # Create bipartite graph using master mapping
        bipartite_graph = create_bipartite_graph(df, gene_id_mapping, max_dmr)

        # Validate graph
        print("\n=== Graph Statistics ===")
        validate_bipartite_graph(bipartite_graph)

        # Write bipartite graph to file
        write_bipartite_graph(bipartite_graph, output_file, df, gene_id_mapping)

    except Exception as e:
        print(f"Error processing dataset: {e}")
        raise


def main():
    args = parse_arguments()

    # First process DSS1 (overall) file to establish master node sets
    print("\nProcessing DSS1 overall file to establish master node sets...")
    df_overall = read_excel_file(args.input)
    
    # Process enhancer info for overall file
    df_overall["Processed_Enhancer_Info"] = df_overall["ENCODE_Enhancer_Interaction(BingRen_Lab)"].apply(process_enhancer_info)
    
    # Create master gene mapping from overall data
    all_genes = set()
    gene_names = df_overall["Gene_Symbol_Nearby"].dropna().str.strip().str.lower()
    all_genes.update(gene_names)
    for genes in df_overall["Processed_Enhancer_Info"]:
        if genes:
            all_genes.update(g.strip().lower() for g in genes)
    
    # Get master DMR count
    max_dmr = df_overall["DMR_No."].max()
    print(f"\nMaster reference contains:")
    print(f"Maximum DMR number: {max_dmr}")
    print(f"Total unique genes: {len(all_genes)}")
    
    # Create master gene ID mapping
    gene_id_mapping = {
        gene: idx + max_dmr + 1 for idx, gene in enumerate(sorted(all_genes))
    }

    # Write the single gene mappings file
    write_gene_mappings(gene_id_mapping, "bipartite_graph_output_gene_ids.csv", "Master")

    # Process overall file with master mapping
    print("\nProcessing DSS1 overall file...")
    process_single_dataset(df_overall, "bipartite_graph_output.txt", args, gene_id_mapping, max_dmr)

    # Process DSS_PAIRWISE file using same mapping and DMR count
    print("\nProcessing DSS_PAIRWISE file...")
    pairwise_sheets = get_excel_sheets("./data/DSS_PAIRWISE.xlsx")
    print(f"Found {len(pairwise_sheets)} pairwise comparison sheets")

    # Validation check for each timepoint
    for sheet in pairwise_sheets:
        print(f"\nProcessing pairwise comparison: {sheet}")
        df_pairwise = read_excel_file("./data/DSS_PAIRWISE.xlsx", sheet_name=sheet)
        
        # Validate DMR numbers
        timepoint_max_dmr = df_pairwise["DMR_No."].max()
        if timepoint_max_dmr > max_dmr:
            print(f"WARNING: Timepoint {sheet} has larger DMR number ({timepoint_max_dmr}) than master set ({max_dmr})")
        
        # Validate gene sets
        timepoint_genes = set()
        tp_gene_names = df_pairwise["Gene_Symbol_Nearby"].dropna().str.strip().str.lower()
        timepoint_genes.update(tp_gene_names)
        
        df_pairwise["Processed_Enhancer_Info"] = df_pairwise["ENCODE_Enhancer_Interaction(BingRen_Lab)"].apply(process_enhancer_info)
        for genes in df_pairwise["Processed_Enhancer_Info"]:
            if genes:
                timepoint_genes.update(g.strip().lower() for g in genes)
        
        # Check for genes not in master set
        new_genes = timepoint_genes - all_genes
        if new_genes:
            print(f"WARNING: Timepoint {sheet} contains {len(new_genes)} genes not in master set")
            print(f"First 5 new genes: {list(new_genes)[:5]}")
        
        output_file = f"bipartite_graph_output_{sheet}.txt"
        process_single_dataset(df_pairwise, output_file, args, gene_id_mapping, max_dmr)


if __name__ == "__main__":
    main()
