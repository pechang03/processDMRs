import os
import networkx as nx
from typing import Dict
import networkx as nx
import pandas as pd
from biclique_analysis import (
    process_bicliques,
    process_components,
    classify_biclique_types,
)
from biclique_analysis.statistics import (
    calculate_component_statistics,
    calculate_coverage_statistics,
    calculate_edge_coverage,
)
from biclique_analysis.reporting import get_bicliques_summary
from data_loader import create_bipartite_graph
from utils.json_utils import convert_for_json

def process_timepoint(df: pd.DataFrame, timepoint: str, gene_id_mapping: Dict[str, int], layout_options=None) -> Dict:
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
        print(f"Original graph created with {original_graph.number_of_nodes()} nodes and {original_graph.number_of_edges()} edges")

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
                "description": str(row["Gene_Description"]) if "Gene_Description" in df.columns else "N/A",
            }

        # Populate gene metadata
        for gene_name in gene_id_mapping.keys():
            gene_metadata[gene_name] = {"description": "N/A"}
            if "Gene_Symbol_Nearby" in df.columns:
                gene_matches = df[df["Gene_Symbol_Nearby"].str.lower() == gene_name.lower()]
                if not gene_matches.empty and "Gene_Description" in gene_matches.columns:
                    gene_metadata[gene_name]["description"] = str(gene_matches.iloc[0]["Gene_Description"])

        # Initialize result structure with native Python types
        result = {
            "status": "success",
            "stats": {
                "components": {
                    "original": {
                        "connected": {"total": 0, "single_node": 0, "small": 0, "interesting": 0, "complex": 0},
                        "biconnected": {"total": 0, "single_node": 0, "small": 0, "interesting": 0, "complex": 0},
                        "triconnected": {"total": 0, "single_node": 0, "small": 0, "interesting": 0, "complex": 0}
                    },
                    "biclique": {
                        "connected": {"total": 0, "single_node": 0, "small": 0, "interesting": 0, "complex": 0}
                    }
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
        biclique_file = BIPARTITE_GRAPH_OVERALL if timepoint == "DSStimeseries" else BIPARTITE_GRAPH_TEMPLATE.format(timepoint)
        
        if os.path.exists(biclique_file):
            print(f"\nProcessing bicliques from {biclique_file}")
            bicliques_result = process_bicliques(
                original_graph,
                biclique_file,
                timepoint,
                gene_id_mapping=gene_id_mapping,
                file_format="gene-name",
                biclique_graph=biclique_graph
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
                result.update({
                    "complex_components": complex_components,
                    "interesting_components": interesting_components,
                    "simple_components": simple_components,
                    "non_simple_components": non_simple_components,
                    "stats": {
                        "components": component_stats,
                        "coverage": bicliques_result.get("coverage", {}),
                        "edge_coverage": bicliques_result.get("edge_coverage", {}),
                    },
                    "bicliques": bicliques_result.get("bicliques", [])
                })

        else:
            print(f"\nNo bicliques file found for {timepoint}")
            # For timepoints without bicliques, calculate original graph components only
            connected_comps = list(nx.connected_components(original_graph))
            biconn_comps = list(nx.biconnected_components(original_graph))
            
            result["stats"]["components"]["original"] = {
                "connected": analyze_components(connected_comps, original_graph),
                "biconnected": analyze_components(biconn_comps, original_graph),
                "triconnected": {"total": 0, "single_node": 0, "small": 0, "interesting": 0, "complex": 0}
            }

        # Convert to JSON-safe format only at the API boundary return
        return convert_for_json(result)

    except Exception as e:
        print(f"Error processing timepoint {timepoint}: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
