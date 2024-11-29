import os
import networkx as nx
from typing import Dict
from utils.json_utils import convert_for_json
from utils.constants import BIPARTITE_GRAPH_OVERALL, BIPARTITE_GRAPH_TEMPLATE
from data_loader import create_bipartite_graph
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

def process_timepoint(df, timepoint, gene_id_mapping, layout_options=None):
    """Process a single timepoint with configurable layout options."""
    try:
        # Create original bipartite graph
        print("Creating original bipartite graph...")
        original_graph = create_bipartite_graph(df, gene_id_mapping, timepoint)
        print(f"Original graph created with {original_graph.number_of_nodes()} nodes and {original_graph.number_of_edges()} edges")

        # Create empty biclique graph
        biclique_graph = nx.Graph()
        
        # Create metadata dictionaries
        dmr_metadata = {}
        gene_metadata = {}
        
        # Populate DMR metadata
        for _, row in df.iterrows():
            dmr_id = f"DMR_{row['DMR_No.']}"
            dmr_metadata[dmr_id] = {
                "area": str(row["Area_Stat"]) if "Area_Stat" in df.columns else "N/A",
                "description": str(row["Gene_Description"]) if "Gene_Description" in df.columns else "N/A"
            }
        
        # Populate gene metadata
        for gene_name in gene_id_mapping.keys():
            gene_matches = df[df["Gene_Symbol_Nearby"].str.lower() == gene_name.lower()]
            gene_metadata[gene_name] = {
                "description": str(gene_matches.iloc[0]["Gene_Description"]) if not gene_matches.empty else "N/A"
            }

        # Initialize base result structure
        result = {
            "status": "success",
            "stats": {
                "components": calculate_component_statistics([], original_graph),
                "coverage": {
                    "dmrs": {"covered": 0, "total": 0, "percentage": 0},
                    "genes": {"covered": 0, "total": 0, "percentage": 0},
                    "edges": {
                        "single_coverage": 0,
                        "multiple_coverage": 0,
                        "uncovered": 0,
                        "total": 0,
                        "single_percentage": 0,
                        "multiple_percentage": 0,
                        "uncovered_percentage": 0,
                    },
                },
                "biclique_types": {
                    "empty": 0,
                    "simple": 0,
                    "interesting": 0,
                    "complex": 0,
                },
            },
            "layout_used": layout_options,
            "dmr_metadata": dmr_metadata,
            "gene_metadata": gene_metadata,
            "complex_components": [],
            "interesting_components": [],
            "simple_components": [],
            "non_simple_components": []
        }

        # Process bicliques if file exists
        biclique_file = BIPARTITE_GRAPH_OVERALL if timepoint == "DSStimeseries" else BIPARTITE_GRAPH_TEMPLATE.format(timepoint)
        if os.path.exists(biclique_file):
            print(f"Processing bicliques from {biclique_file}")
            bicliques_result = process_bicliques(original_graph, biclique_file, timepoint, 
                                               gene_id_mapping=gene_id_mapping,
                                               file_format="gene-name")

            if bicliques_result and "bicliques" in bicliques_result:
                # Process components with all required parameters
                (complex_components, interesting_components, 
                 simple_components, non_simple_components,
                 component_stats, statistics) = process_components(
                    bipartite_graph=original_graph,
                    bicliques_result=bicliques_result,
                    biclique_graph=biclique_graph,
                    dmr_metadata=dmr_metadata,
                    gene_metadata=gene_metadata,
                    gene_id_mapping=gene_id_mapping
                )

                # Update result with processed data
                result.update({
                    "complex_components": convert_for_json(complex_components),
                    "interesting_components": convert_for_json(interesting_components),
                    "simple_components": convert_for_json(simple_components),
                    "non_simple_components": convert_for_json(non_simple_components),
                    "stats": convert_for_json({
                        "components": component_stats,
                        "coverage": calculate_coverage_statistics(bicliques_result["bicliques"], original_graph),
                        "edge_coverage": calculate_edge_coverage(bicliques_result["bicliques"], original_graph),
                        "biclique_types": classify_biclique_types(bicliques_result["bicliques"])
                    }),
                    "graphs": {
                        "original": convert_for_json(original_graph),
                        "biclique": convert_for_json(biclique_graph)
                    }
                })

        return result

    except Exception as e:
        print(f"Error processing timepoint {timepoint}: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
