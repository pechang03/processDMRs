# Author: Peter Shaw
#
# This file contains core data processing logic to be used by both
# process_data.py and routes/timepoint_data.py, resolving circular imports.

import os
import json
import logging
from typing import Dict, List, Set, Tuple
import networkx as nx
from flask import current_app
from extensions import app
import pandas as pd

from utils.constants import (
    DSS1_FILE,
    DSS_PAIRWISE_FILE,
    BIPARTITE_GRAPH_TEMPLATE,
    BIPARTITE_GRAPH_OVERALL,
    START_GENE_ID,
)
from utils.id_mapping import create_gene_mapping
from utils import process_enhancer_info

from utils.json_utils import (
    convert_dict_keys_to_str,
    convert_for_json,
    convert_sets_to_lists,
)

from biclique_analysis import (
    process_bicliques,
    create_node_metadata,
    process_components,
    reporting,
)
from biclique_analysis.edge_classification import classify_edges
from biclique_analysis.classifier import (
    BicliqueSizeCategory,
    classify_biclique,
    classify_component,
    classify_biclique_types,
)

from biclique_analysis.statistics import (
    analyze_components,
    calculate_edge_coverage,
    calculate_coverage_statistics,
    calculate_component_statistics,
    analyze_biconnected_components,
)

from biclique_analysis.triconnected import analyze_triconnected_components

from data_loader import (
    read_excel_file,
    create_bipartite_graph,
    validate_bipartite_graph,
)

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

def process_timepoint(
    df: pd.DataFrame,
    timepoint: str,
    gene_id_mapping: Dict[str, int],
    layout_options=None,
) -> Dict:
    """
    Process a single timepoint with configurable layout options.

    This is an API boundary function that:
    1. Calls business logic functions that work with native Python types
    2. Converts results to JSON-safe format before returning
    """
    try:
        # Create original bipartite graph
        print("Creating original bipartite graph...")
        original_graph = create_bipartite_graph(df, gene_id_mapping, timepoint)
        print(
            f"Original graph created with {original_graph.number_of_nodes()} nodes and {original_graph.number_of_edges()} edges"
        )

        # Create empty biclique graph
        biclique_graph = nx.Graph()

        # Create metadata dictionaries with native Python types
        dmr_metadata = {}
        gene_metadata = {}

        # Populate DMR metadata
        for _, row in df.iterrows():
            dmr_id = f"DMR_{row['DMR_No.']}"
            dmr_metadata[dmr_id] = {
                "area": str(row["Area_Stat"]) if "Area_Stat" in df.columns else "N/A",
                "description": str(row["Gene_Description"])
                if "Gene_Description" in df.columns
                else "N/A",
            }

        # Populate gene metadata
        for gene_name in gene_id_mapping.keys():
            gene_metadata[gene_name] = {"description": "N/A"}
            if "Gene_Symbol_Nearby" in df.columns:
                gene_matches = df[
                    df["Gene_Symbol_Nearby"].str.lower() == gene_name.lower()
                ]
                if (
                    not gene_matches.empty
                    and "Gene_Description" in gene_matches.columns
                ):
                    gene_metadata[gene_name]["description"] = str(
                        gene_matches.iloc[0]["Gene_Description"]
                    )

        # Initialize result structure with native Python types
        result = {
            "status": "success",
            "stats": {
                "components": {
                    "original": {
                        "connected": {
                            "total": 0,
                            "single_node": 0,
                            "small": 0,
                            "interesting": 0,
                            "complex": 0,
                        },
                        "biconnected": {
                            "total": 0,
                            "single_node": 0,
                            "small": 0,
                            "interesting": 0,
                            "complex": 0,
                        },
                        "triconnected": {
                            "total": 0,
                            "single_node": 0,
                            "small": 0,
                            "interesting": 0,
                            "complex": 0,
                        },
                    },
                    "biclique": {
                        "connected": {
                            "total": 0,
                            "single_node": 0,
                            "small": 0,
                            "interesting": 0,
                            "complex": 0,
                        }
                    },
                },
                "coverage": {
                    "dmrs": {"covered": 0, "total": 0, "percentage": 0},
                    "genes": {"covered": 0, "total": 0, "percentage": 0},
                },
            },
            "dmr_metadata": dmr_metadata,
            "gene_metadata": gene_metadata,
            "bipartite_graph": original_graph,
            "biclique_graph": biclique_graph,
        }

        # Process bicliques if file exists
        biclique_file = (
            BIPARTITE_GRAPH_OVERALL
            if timepoint == "DSStimeseries"
            else BIPARTITE_GRAPH_TEMPLATE.format(timepoint)
        )

        if os.path.exists(biclique_file):
            print(f"\nProcessing bicliques from {biclique_file}")
            bicliques_result = process_bicliques(
                original_graph,
                biclique_file,
                timepoint,
                gene_id_mapping=gene_id_mapping,
                file_format="gene-name",
                biclique_graph=biclique_graph,
            )

            if bicliques_result and "bicliques" in bicliques_result:
                print(f"\nFound {len(bicliques_result['bicliques'])} bicliques")

                # Process components
                (
                    complex_components,
                    interesting_components,
                    simple_components,
                    non_simple_components,
                    component_stats,
                    statistics,
                ) = process_components(
                    bipartite_graph=original_graph,
                    bicliques_result=bicliques_result,
                    biclique_graph=biclique_graph,
                    dmr_metadata=dmr_metadata,
                    gene_metadata=gene_metadata,
                    gene_id_mapping=gene_id_mapping,
                )

                # Update result with processed data (still native Python types)
                result.update(
                    {
                        "complex_components": complex_components,
                        "interesting_components": interesting_components,
                        "simple_components": simple_components,
                        "non_simple_components": non_simple_components,
                        "stats": {
                            "components": component_stats,
                            "coverage": bicliques_result.get("coverage", {}),
                            "edge_coverage": bicliques_result.get("edge_coverage", {}),
                        },
                        "bicliques": bicliques_result.get("bicliques", []),
                    }
                )

        else:
            print(f"\nNo bicliques file found for {timepoint}")
            # For timepoints without bicliques, calculate original graph components only
            connected_comps = list(nx.connected_components(original_graph))
            biconn_comps = list(nx.biconnected_components(original_graph))

            result["stats"]["components"]["original"] = {
                "connected": analyze_components(connected_comps, original_graph),
                "biconnected": analyze_components(biconn_comps, original_graph),
                "triconnected": {
                    "total": 0,
                    "single_node": 0,
                    "small": 0,
                    "interesting": 0,
                    "complex": 0,
                },
            }

        # Convert to JSON-safe format only at the API boundary return
        return convert_for_json(result)

    except Exception as e:
        print(f"Error processing timepoint {timepoint}: {str(e)}", flush=True)
        import traceback

        traceback.print_exc()
        return {"status": "error", "message": str(e)}

def process_data():
    """Process all timepoints including DSStimeseries with configurable layouts"""
    try:
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

        # Process DSStimeseries timepoint first
        print("\nProcessing DSStimeseries timepoint...", flush=True)
        df_DSStimeseries = read_excel_file(app.config["DSS1_FILE"])

        # Create master gene mapping
        gene_id_mapping = create_master_gene_mapping(df_DSStimeseries)

        # Process DSStimeseries timepoint (no longer using "overall")
        timepoint_data["DSStimeseries"] = process_timepoint(
            df_DSStimeseries,
            "DSStimeseries",  # Use consistent timepoint name
            gene_id_mapping,
            layout_options["DSStimeseries"],
        )

        # Process pairwise timepoints
        pairwise_file = app.config["DSS_PAIRWISE_FILE"]
        xl = pd.ExcelFile(pairwise_file)

        for sheet_name in xl.sheet_names:
            print(f"\nProcessing pairwise timepoint: {sheet_name}", flush=True)
            try:
                # Read each sheet directly into a DataFrame
                df = pd.read_excel(pairwise_file, sheet_name=sheet_name)
                if not df.empty:
                    # Process the timepoint with the DataFrame
                    timepoint_data[sheet_name] = process_timepoint(
                        df, sheet_name, gene_id_mapping, layout_options["pairwise"]
                    )
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
