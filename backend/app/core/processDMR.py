import argparse

# import sys
# mport os
# mport pandas as pd
# mport networkx as nx
from backend.app.utils.graph_io import write_gene_mappings

# mport time
# mport psutil
from typing import Dict, Tuple, Set
import json

from backend.app.core.data_loader import (
    get_excel_sheets,
    #   DSS1_FILE,
    #   DSS_PAIRWISE_FILE,
    #   BIPARTITE_GRAPH_TEMPLATE,
    #   BIPARTITE_GRAPH_OVERALL,
    read_excel_file,
    create_bipartite_graph,
    validate_bipartite_graph,
    read_gene_mapping
)
import pandas as pd
from backend.app.utils.data_processing import process_enhancer_info
from backend.app.utils.id_mapping import create_dmr_id
from backend.app.utils.constants import START_GENE_ID
from backend.app.utils.graph_io import write_bipartite_graph, write_gene_mappings
from backend.app.utils.id_mapping import create_gene_mapping
from backend.app.core.rb_domination import (
    greedy_rb_domination,
    calculate_dominating_set,  # Changed name
    print_domination_statistics,
    copy_dominating_set,
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
# These functions are now imported from backend.app.core.data_loader


def process_single_dataset(df, output_file, args, gene_id_mapping=None, timepoint=None):
    """Process a single dataset and write the bipartite graph to a file."""
    try:
        # Use START_GENE_ID for gene mapping
        max_dmr_id = None

        # Use the correct column name based on timepoint
        if timepoint == "DSStimeseries":
            interaction_col = "ENCODE_Promoter_Interaction(BingRen_Lab)"
        else:
            interaction_col = "ENCODE_Enhancer_Interaction(BingRen_Lab)"

        if interaction_col not in df.columns:
            raise ValueError(
                f"Interaction column '{interaction_col}' not found in dataset"
            )

        # Process enhancer info if not already processed
        if "Processed_Enhancer_Info" not in df.columns:
            df["Processed_Enhancer_Info"] = df[interaction_col].apply(
                process_enhancer_info
            )

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

            # Create gene mapping starting after max DMR ID
            gene_id_mapping = create_gene_mapping(all_genes)

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
    """Main entry point for processing DMR data."""
    args = parse_arguments()

    print("\nCollecting all unique genes across timepoints...")

    # Read sheets from pairwise file
    pairwise_sheets = get_excel_sheets("./data/DSS_PAIRWISE.xlsx")
    pairwise_dfs = {}
    all_genes = set()
    max_dmr_id = None  # Will be set based on number of rows

    # Process pairwise sheets
    for sheet in pairwise_sheets:
        print(f"\nProcessing sheet: {sheet}")
        df = read_excel_file("./data/DSS_PAIRWISE.xlsx", sheet_name=sheet)
        if df is None:
            continue
        pairwise_dfs[sheet] = df

        # Update all_genes set from this sheet
        all_genes.update(get_genes_from_df(df))

    # Process overall DSS1 file
    print("\nProcessing DSS1 file...")
    df_DSStimeseries = read_excel_file(args.input)
    if df_DSStimeseries is not None:
        all_genes.update(get_genes_from_df(df_DSStimeseries))
        max_dmr_id = len(df_DSStimeseries) - 1  # Set max_dmr_id based on number of rows

    # Create and write gene mapping
    gene_id_mapping = create_gene_mapping(all_genes)
    write_gene_mappings(gene_id_mapping, "master_gene_ids.csv", "All_Timepoints")

    # Process each timepoint
    for sheet, df in pairwise_dfs.items():
        print(f"\nProcessing timepoint: {sheet}")
        output_file = f"bipartite_graph_output_{sheet}.txt"
        process_single_dataset(df, output_file, args, gene_id_mapping, sheet)

    # Process overall DSS1 file
    print("\nProcessing DSS1 DSStimeseries file...")
    process_single_dataset(
        df_DSStimeseries, "bipartite_graph_output.txt", args, gene_id_mapping, "DSS1"
    )


def get_genes_from_df(df: pd.DataFrame) -> Set[str]:
    """Extract all genes from a dataframe."""
    genes = set()

    # Get gene column
    gene_column = next(
        (
            col
            for col in ["Gene_Symbol_Nearby", "Gene_Symbol", "Gene"]
            if col in df.columns
        ),
        None,
    )
    if gene_column:
        genes.update(df[gene_column].dropna().str.strip().str.lower())

    # Get genes from enhancer/promoter info
    if "Processed_Enhancer_Info" not in df.columns:
        interaction_col = next(
            (
                col
                for col in [
                    "ENCODE_Enhancer_Interaction(BingRen_Lab)",
                    "ENCODE_Promoter_Interaction(BingRen_Lab)",
                ]
                if col in df.columns
            ),
            None,
        )

        if interaction_col:
            df["Processed_Enhancer_Info"] = df[interaction_col].apply(
                process_enhancer_info
            )

    if "Processed_Enhancer_Info" in df.columns:
        for gene_list in df["Processed_Enhancer_Info"]:
            if gene_list:
                genes.update(g.strip().lower() for g in gene_list)

    return genes


if __name__ == "__main__":
    main()
