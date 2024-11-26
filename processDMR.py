import argparse

# import sys
# mport os
# mport pandas as pd
# mport networkx as nx
import csv

# mport time
# mport psutil
from typing import Dict, Tuple

from data_loader import (
    get_excel_sheets,
    #   DSS1_FILE,
    #   DSS_PAIRWISE_FILE,
    #   BIPARTITE_GRAPH_TEMPLATE,
    #   BIPARTITE_GRAPH_OVERALL,
    read_excel_file,
    create_bipartite_graph,
    validate_bipartite_graph,
)
from utils import create_dmr_id

from utils import write_bipartite_graph
from biclique_analysis import (
    process_bicliques,
    process_enhancer_info,
    #   create_node_metadata,
    #   process_components,
    #   reporting,
)
from biclique_analysis.reader import read_bicliques_file
from biclique_analysis.reporting import print_bicliques_summary, print_bicliques_detail
from visualization import calculate_node_positions  # Import from package root
from visualization.core import create_biclique_visualization
from visualization import create_node_biclique_map
from rb_domination import (
    greedy_rb_domination,
    calculate_dominating_sets,  # Changed name
    print_domination_statistics,
    copy_dominating_set,  # Add new function
)

# Add version constant at top of file
__version__ = "0.0.4-alpha"


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


# Removed: create_dmr_id() and write_bipartite_graph()
# These functions are now imported from data_loader


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


def process_single_dataset(df, output_file, args, gene_id_mapping=None, timepoint=None):
    """Process a single dataset and write the bipartite graph to a file."""
    try:
        # Process enhancer info if not already processed
        if "Processed_Enhancer_Info" not in df.columns:
            df["Processed_Enhancer_Info"] = df[
                "ENCODE_Enhancer_Interaction(BingRen_Lab)"
            ].apply(process_enhancer_info)

        # If no master mapping provided, create one
        if gene_id_mapping is None:
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

            # Create gene mapping
            gene_id_mapping = {gene: idx + 1 for idx, gene in enumerate(sorted_genes)}

        # Create bipartite graph using master mapping
        bipartite_graph = create_bipartite_graph(
            df, gene_id_mapping, timepoint or "DSS1"
        )

        # Validate graph
        print("\n=== Graph Statistics ===")
        validate_bipartite_graph(bipartite_graph)

        # Write bipartite graph to file
        write_bipartite_graph(
            bipartite_graph, output_file, df, gene_id_mapping, timepoint or "DSS1"
        )

    except Exception as e:
        print(f"Error processing dataset: {e}")
        raise


def main():
    args = parse_arguments()

    # First collect all unique genes across all timepoints
    print("\nCollecting all unique genes across timepoints...")
    all_genes = set()

    # Process DSS_PAIRWISE file first to get complete gene set
    pairwise_sheets = get_excel_sheets("./data/DSS_PAIRWISE.xlsx")
    for sheet in pairwise_sheets:
        print(f"\nProcessing sheet: {sheet}")
        df = read_excel_file("./data/DSS_PAIRWISE.xlsx", sheet_name=sheet)

        # Debug: Print column names
        print(f"Available columns in {sheet}:")
        print(df.columns.tolist())

        # Determine which column contains gene symbols
        gene_column = None
        for possible_name in ["Gene_Symbol_Nearby", "Gene_Symbol", "Gene"]:
            if possible_name in df.columns:
                gene_column = possible_name
                print(f"Using column '{gene_column}' for gene symbols")
                break

        if gene_column is None:
            print(f"WARNING: No gene symbol column found in sheet {sheet}")
            continue

        df["Processed_Enhancer_Info"] = df[
            "ENCODE_Enhancer_Interaction(BingRen_Lab)"
        ].apply(process_enhancer_info)

        # Add genes from gene column
        gene_names = df[gene_column].dropna().str.strip().str.lower()
        all_genes.update(gene_names)

        # Add genes from enhancer info
        for genes in df["Processed_Enhancer_Info"]:
            if genes:
                all_genes.update(g.strip().lower() for g in genes)

    # Also process DSS1 file for genes
    print("\nProcessing DSS1 file...")
    df_overall = read_excel_file(args.input)

    # Debug: Print column names for overall file
    print(f"Available columns in DSS1:")
    print(df_overall.columns.tolist())

    # Determine which column contains gene symbols in overall file
    gene_column = None
    for possible_name in ["Gene_Symbol_Nearby", "Gene_Symbol", "Gene"]:
        if possible_name in df_overall.columns:
            gene_column = possible_name
            print(f"Using column '{gene_column}' for gene symbols in overall file")
            break

    if gene_column is None:
        raise ValueError("No gene symbol column found in overall file")

    df_overall["Processed_Enhancer_Info"] = df_overall[
        "ENCODE_Enhancer_Interaction(BingRen_Lab)"
    ].apply(process_enhancer_info)
    gene_names = df_overall[gene_column].dropna().str.strip().str.lower()
    all_genes.update(gene_names)
    for genes in df_overall["Processed_Enhancer_Info"]:
        if genes:
            all_genes.update(g.strip().lower() for g in genes)

    # Create consistent gene ID mapping
    print(f"\nCreated gene ID mapping for {len(all_genes)} unique genes")
    gene_id_mapping = {gene: idx + 1 for idx, gene in enumerate(sorted(all_genes))}

    # Write the master gene mappings file
    write_gene_mappings(gene_id_mapping, "master_gene_ids.csv", "All_Timepoints")

    # Process each timepoint with its own DMR space
    for sheet in pairwise_sheets:
        print(f"\nProcessing timepoint: {sheet}")
        df = read_excel_file("./data/DSS_PAIRWISE.xlsx", sheet_name=sheet)
        df["Processed_Enhancer_Info"] = df[
            "ENCODE_Enhancer_Interaction(BingRen_Lab)"
        ].apply(process_enhancer_info)

        output_file = f"bipartite_graph_output_{sheet}.txt"
        process_single_dataset(df, output_file, args, gene_id_mapping, sheet)

    # Process overall DSS1 file
    print("\nProcessing DSS1 overall file...")
    process_single_dataset(
        df_overall, "bipartite_graph_output.txt", args, gene_id_mapping, "DSS1"
    )


if __name__ == "__main__":
    main()
