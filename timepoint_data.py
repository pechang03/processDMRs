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

        # Initialize base result with original graph data
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
            "complex_components": [],
            "interesting_components": [],
            "non_simple_components": [],
            "layout_used": layout_options,
            "graphs": {
                "original": convert_for_json(original_graph),
                "biclique": None  # Will be populated if bicliques exist
            }
        }

        # Process bicliques if file exists
        biclique_file = BIPARTITE_GRAPH_OVERALL if timepoint == "DSStimeseries" else BIPARTITE_GRAPH_TEMPLATE.format(timepoint)
        if os.path.exists(biclique_file):
            print(f"Processing bicliques from {biclique_file}")
            bicliques_result = process_bicliques(original_graph, biclique_file, timepoint, 
                                               gene_id_mapping=gene_id_mapping,
                                               file_format="gene-name")

            if bicliques_result and "bicliques" in bicliques_result:
                # Create biclique graph
                biclique_graph = nx.Graph()
                for dmr_nodes, gene_nodes in bicliques_result["bicliques"]:
                    biclique_graph.add_nodes_from(dmr_nodes, bipartite=0)
                    biclique_graph.add_nodes_from(gene_nodes, bipartite=1)
                    biclique_graph.add_edges_from((d, g) for d in dmr_nodes for g in gene_nodes)

                # Add biclique graph to result
                result["graphs"]["biclique"] = convert_for_json(biclique_graph)

                # Process components using both graphs
                (complex_components, interesting_components, 
                 simple_components, non_simple_components,
                 component_stats, statistics) = process_components(
                    original_graph=original_graph,
                    biclique_graph=biclique_graph,
                    bicliques_result=bicliques_result
                )

                # Calculate additional statistics
                coverage_stats = calculate_coverage_statistics(bicliques_result["bicliques"], original_graph)
                edge_coverage = calculate_edge_coverage(bicliques_result["bicliques"], original_graph)
                bicliques_summary = get_bicliques_summary(bicliques_result, original_graph)

                # Update result with biclique-specific data
                result["stats"].update({
                    "components": convert_for_json(component_stats),
                    "coverage": convert_for_json(coverage_stats),
                    "edge_coverage": convert_for_json(edge_coverage),
                    "biclique_types": convert_for_json(
                        classify_biclique_types(bicliques_result["bicliques"])
                    ),
                    "bicliques_summary": convert_for_json(bicliques_summary)
                })
                result["complex_components"] = convert_for_json(complex_components)
                result["interesting_components"] = convert_for_json(interesting_components)
                result["non_simple_components"] = convert_for_json(non_simple_components)

        return result

    except Exception as e:
        print(f"Error processing timepoint {timepoint}: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
