# File : process_data.py
# Author: Peter Shaw

# Author: Peter Shaw
#
# This file handles all data processing logic separate from web presentation.
# It serves as the main orchestrator for data analysis and visualization preparation.
#
# Responsibilities:
# - Read and process Excel data files
# - Create and analyze bipartite graphs
# - Process bicliques and their components
# - Generate visualization data
# - Create metadata for nodes
# - Calculate statistics
#
# Note: This separation allows the data processing logic to be used independently
# of the web interface, making it more maintainable and testable.

import os
import json

# from extensions import app
import logging
from typing import Dict, List, Set, Tuple
import networkx as nx
from flask import current_app
import pandas as pd

from backend.app.utils.constants import (
    START_GENE_ID,
)
from backend.app.utils.id_mapping import create_gene_mapping
from utils import process_enhancer_info

from backend.app.utils.json_utils import (
    #    convert_dict_keys_to_str,
    convert_for_json,
    # convert_sets_to_lists,
)


# from visualization import create_node_biclique_map, CircularBicliqueLayout

from backend.app.core.data_loader import (
    # get_excel_sheets,
    read_excel_file,
    #    create_bipartite_graph,
    # validate_bipartite_graph,
    read_gene_mapping,
)

from analysis.timepoint_processor import process_timepoint
from backend.app.database.connection import get_db_session
from backend.app.database.operations import insert_metadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# _cached_data = None


def create_master_gene_mapping(df: pd.DataFrame) -> Dict[str, int]:
    """Create a master gene mapping from a DataFrame."""
    all_genes = set()

    # Add genes from gene column (case-insensitive)
    gene_col = next(
        (
            col
            for col in ["Gene_Symbol_Nearby", "Gene_Symbol", "Gene"]
            if col in df.columns
        ),
        None,
    )
    if gene_col:
        # Filter out empty values, ".", "N/A" etc.
        gene_names = df[gene_col].dropna().str.strip().str.lower()
        valid_genes = {g for g in gene_names if g and g != "." and g.lower() != "n/a"}
        all_genes.update(valid_genes)

    # Add genes from enhancer info
    df["Processed_Enhancer_Info"] = df[
        "ENCODE_Enhancer_Interaction(BingRen_Lab)"
    ].apply(process_enhancer_info)

    for genes in df["Processed_Enhancer_Info"]:
        if genes:  # Only process non-empty gene lists
            # Filter out invalid entries
            valid_genes = {
                g.strip().lower()
                for g in genes
                if g.strip() and g.strip() != "." and g.strip().lower() != "n/a"
            }
            all_genes.update(valid_genes)

    # Remove any remaining invalid entries
    all_genes = {g for g in all_genes if g and g != "." and g.lower() != "n/a"}

    # Use utility function to create mapping
    max_dmr_id = df["DMR_No."].max() - 1  # Convert to 0-based index

    print("\nGene mapping creation debug:")
    print(f"Total valid genes found: {len(all_genes)}")
    print("First 5 valid genes:", sorted(list(all_genes))[:5])

    return create_gene_mapping(all_genes, max_dmr_id)


def process_DSStimeseries_timepoint(df: pd.DataFrame) -> Dict:
    """Process the overall DSStimeseries timepoint."""
    gene_id_mapping = create_master_gene_mapping(df)
    return process_timepoint(df, "DSStimeseries", gene_id_mapping)


def update_gene_metadata(
    df: pd.DataFrame, gene_id_mapping: Dict[str, int], timepoint: str = None
) -> None:
    """
    Update gene metadata from DataFrame.

    Args:
        df: DataFrame containing gene metadata
        gene_id_mapping: Mapping of gene symbols to IDs
        timepoint: Optional timepoint name for tracking metadata source
    """

    try:
        # Create a new session
        with get_db_session() as session:
            # Track updates for logging
            updates = 0
            skipped = 0

            # Process each gene in mapping
            for gene_symbol, gene_id in gene_id_mapping.items():
                # Look for gene in DataFrame (case-insensitive)
                gene_rows = df[
                    df["Gene_Symbol_Nearby"].str.lower() == gene_symbol.lower()
                ]

                if not gene_rows.empty:
                    row = gene_rows.iloc[0]

                    # Collect available metadata
                    metadata = {}

                    # Add description if available
                    if "Gene_Description" in row and pd.notna(row["Gene_Description"]):
                        metadata["description"] = str(row["Gene_Description"])

                    # Add other available metadata
                    if "Gene_Type" in row and pd.notna(row["Gene_Type"]):
                        metadata["gene_type"] = str(row["Gene_Type"])
                    if "Chromosome" in row and pd.notna(row["Chromosome"]):
                        metadata["chromosome"] = str(row["Chromosome"])

                    # Add timepoint if provided
                    if timepoint:
                        metadata["timepoint"] = timepoint

                    # Insert each metadata item
                    for key, value in metadata.items():
                        try:
                            insert_metadata(
                                session,
                                entity_type="gene",
                                entity_id=gene_id,
                                key=key,
                                value=value,
                            )
                            updates += 1
                        except Exception as e:
                            print(
                                f"Error updating metadata for gene {gene_symbol}: {str(e)}"
                            )
                            skipped += 1
                else:
                    skipped += 1

            print(f"\nGene metadata update summary:")
            print(f"Updated: {updates} metadata entries")
            print(f"Skipped: {skipped} genes")

    except Exception as e:
        print(f"Error in update_gene_metadata: {str(e)}")
        raise


def process_data(
    gene_mapping_file: str = "./data/master_gene_ids.csv",
    dss1_path: str = "./data/DSS1.xlsx",
    pairwise_path: str = "./data/DSS_PAIRWISE.xlsx",
):
    """Process all timepoints including DSStimeseries with configurable layouts"""
    try:
        # Read existing gene mapping first
        gene_id_mapping = read_gene_mapping()

        # If no existing mapping, create new one
        if not gene_id_mapping:
            print(
                f"Error: No existing gene mapping found, creating new mapping...{gene_mapping_file}"
            )
            return

        # Define layout options for different timepoint types
        layout_options = {
            "DSStimeseries": {
                "triconnected": "spring",
                "bicliques": "circular",
                "default": "original",
            },
            "pairwise": {
                "triconnected": "spring",
                "bicliques": "circular",
                "default": "original",
            },
        }

        # Initialize timepoint data dictionary
        timepoint_data = {}
        if dss1_path is None:
            print(f"Warning: No existing DSS1 file..{dss1_path}")
            exit()

        # Process DSStimeseries timepoint first
        print("\nProcessing DSStimeseries timepoint...", flush=True)
        print(f"Reading spreadsheat {dss1_path}")
        df_DSStimeseries = read_excel_file(dss1_path)

        # Process DSStimeseries timepoint (no longer using "overall")
        timepoint_data["DSStimeseries"] = process_timepoint(
            df_DSStimeseries,
            "DSStimeseries",  # Use consistent timepoint name
            gene_id_mapping,
            layout_options["DSStimeseries"],
        )

        # Process pairwise timepoints
        if pairwise_path is None:
            print("Warning: No existing pairwise file..{pairwise_path}")
            exit()
            # pairwise_path = app.config["PAIRWISE_FILE"]
        xl = pd.ExcelFile(pairwise_path)

        for sheet_name in xl.sheet_names:
            print(f"\nProcessing pairwise timepoint: {sheet_name}", flush=True)
            try:
                # Read each sheet directly into a DataFrame
                df = pd.read_excel(pairwise_path, sheet_name=sheet_name)
                if not df.empty:
                    # Process the timepoint with the DataFrame
                    timepoint_data[sheet_name] = process_timepoint(
                        df, sheet_name, gene_id_mapping, layout_options["pairwise"]
                    )

                    # Update gene metadata
                    update_gene_metadata(df, gene_id_mapping, sheet_name)
                else:
                    print(f"Empty sheet: {sheet_name}", flush=True)
                    timepoint_data[sheet_name] = {
                        "status": "error",
                        "message": "Empty sheet",
                    }
            except Exception as e:
                print(f"Error processing sheet {sheet_name}: {str(e)}", flush=True)
                timepoint_data[sheet_name] = {"status": "error", "message": str(e)}

        # Convert entire timepoint_data to JSON-safe format
        return convert_for_json(timepoint_data)

    except Exception as e:
        print(f"Error in process_data: {str(e)}", flush=True)
        import traceback

        traceback.print_exc()
        return {"error": str(e)}


# Add placeholder functions for missing metadata creation
def create_dmr_metadata(df: pd.DataFrame) -> Dict:
    """Create metadata for DMRs"""
    return {
        str(row["DMR_No."]): {
            "area": row.get("Area_Stat", "N/A"),
            "description": row.get("Gene_Description", "N/A"),
        }
        for _, row in df.iterrows()
    }


def create_gene_metadata(df: pd.DataFrame) -> Dict:
    """Create metadata for genes"""
    gene_metadata = {}

    # Check for gene symbol column
    gene_col = next(
        (col for col in ["Gene_Symbol_Nearby", "Gene_Symbol"] if col in df.columns),
        None,
    )

    if gene_col:
        for _, row in df.iterrows():
            gene_name = row.get(gene_col)
            if gene_name:
                gene_metadata[gene_name] = {
                    "description": row.get("Gene_Description", "N/A")
                }

    return gene_metadata


def create_master_gene_mapping(df: pd.DataFrame) -> Dict[str, int]:
    """Create a master gene mapping from a DataFrame"""
    all_genes = set()

    # Add genes from gene column (case-insensitive)
    gene_names = df["Gene_Symbol_Nearby"].dropna().str.strip().str.lower()
    all_genes.update(gene_names)

    # Add genes from enhancer info (case-insensitive)
    df["Processed_Enhancer_Info"] = df[
        "ENCODE_Enhancer_Interaction(BingRen_Lab)"
    ].apply(process_enhancer_info)

    for genes in df["Processed_Enhancer_Info"]:
        if genes:
            all_genes.update(g.strip().lower() for g in genes)

    # Sort genes alphabetically for deterministic assignment
    sorted_genes = sorted(all_genes)
    max_dmr = df["DMR_No."].max()

    # Create gene mapping starting after max DMR number

    gene_id_mapping = {
        gene: START_GENE_ID + idx for idx, gene in enumerate(sorted_genes)
    }

    return gene_id_mapping


def create_biclique_graph(bicliques: List[Tuple[Set[int], Set[int]]]) -> nx.Graph:
    """Create a biclique graph from bicliques"""
    biclique_graph = nx.Graph()
    for dmr_nodes, gene_nodes in bicliques:
        biclique_graph.add_nodes_from(dmr_nodes, bipartite=0)
        biclique_graph.add_nodes_from(gene_nodes, bipartite=1)
        biclique_graph.add_edges_from(
            (dmr, gene) for dmr in dmr_nodes for gene in gene_nodes
        )
    return biclique_graph


def remove_isolated_genes(graph: nx.Graph) -> nx.Graph:
    """Remove gene nodes with degree 0 from the graph."""
    filtered_graph = graph.copy()

    # Find gene nodes with degree 0
    isolated_genes = [
        node
        for node, degree in filtered_graph.degree()
        if degree == 0 and filtered_graph.nodes[node]["bipartite"] == 1
    ]

    # Remove isolated genes
    filtered_graph.remove_nodes_from(isolated_genes)

    return filtered_graph


def get_isolated_genes(
    graph: nx.Graph, gene_id_mapping: Dict[str, int]
) -> Dict[str, List[str]]:
    """Get information about isolated genes for reporting."""
    reverse_mapping = {v: k for k, v in gene_id_mapping.items()}

    isolated_genes = [
        reverse_mapping[node]
        for node, degree in graph.degree()
        if degree == 0 and graph.nodes[node]["bipartite"] == 1
    ]

    return {"count": len(isolated_genes), "genes": sorted(isolated_genes)}
