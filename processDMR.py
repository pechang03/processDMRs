import argparse
import sys
import os
import pandas as pd
import networkx as nx
import csv
import time
import psutil
from typing import Dict, Tuple

from biclique_analysis.processor import process_enhancer_info
from biclique_analysis import (
    process_bicliques,
    process_enhancer_info,
    create_node_metadata,
    process_components,  # Add this import
    reporting
)
from biclique_analysis.reader import read_bicliques_file
from biclique_analysis.reporting import print_bicliques_summary, print_bicliques_detail
from visualization import calculate_node_positions  # Import from package root
from visualization.core import create_biclique_visualization
from visualization import create_node_biclique_map
from graph_utils import validate_bipartite_graph
from graph_utils import create_bipartite_graph
from graph_utils import read_excel_file
from rb_domination import (
    greedy_rb_domination,
    calculate_dominating_sets,  # Changed name
    print_domination_statistics,
    copy_dominating_set  # Add new function
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


def main():
    args = parse_arguments()

    # Update main function to use arguments
    try:
        # Add logging
        import logging

        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )

        # Read DSS1 data
        df = read_excel_file(args.input)
        df["Processed_Enhancer_Info"] = df[
            "ENCODE_Enhancer_Interaction(BingRen_Lab)"
        ].apply(process_enhancer_info)

        # Read HOME1 data
        df_home1 = read_excel_file("./data/HOME1.xlsx")
        df_home1["Processed_Enhancer_Info"] = df_home1[
            "ENCODE_Enhancer_Interaction(BingRen_Lab)"
        ].apply(process_enhancer_info)

        # Get all unique genes from both datasets
        all_genes = set()
        dmr_nodes = df["DMR_No."].values

        # Add genes from DSS1
        dss1_gene_col = (
            "Gene_Symbol_Nearby"
            if "Gene_Symbol_Nearby" in df.columns
            else "Gene_Symbol"
        )
        all_genes.update(df["Processed_Enhancer_Info"].explode().dropna())
        all_genes.update(df[dss1_gene_col].dropna())

        """
        # Add genes from HOME1
        home1_gene_col = (
            "Gene_Symbol_Nearby"
            if "Gene_Symbol_Nearby" in df_home1.columns
            else "Gene_Symbol"
        )
        all_genes.update(df_home1["Processed_Enhancer_Info"].explode().dropna())
        all_genes.update(df_home1[home1_gene_col].dropna())
        """

        def create_gene_id_mapping(df: pd.DataFrame, dmr_max: int) -> Dict[str, int]:
            # Create gene ID mapping using dataset's own max DMR number
            all_genes = set()
            gene_col = (
                "Gene_Symbol_Nearby"
                if "Gene_Symbol_Nearby" in df.columns
                else "Gene_Symbol"
            )

            # Add genes from gene column (case-insensitive)
            gene_names = df["Gene_Symbol_Nearby"].dropna().str.strip().str.lower()
            all_genes.update(gene_names)

            # Add genes from enhancer info (case-insensitive)
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

            print("\nGene ID Mapping Statistics:")
            print(f"Total unique genes (case-insensitive): {len(all_genes)}")
            print(f"ID range: {max_dmr + 1} to {max(gene_id_mapping.values())}")
            print("\nFirst 5 gene mappings:")
            for gene in sorted_genes[:5]:
                print(f"{gene}: {gene_id_mapping[gene]}")

            # Create mapping starting after this dataset's max DMR
            sorted_genes = sorted(all_genes)
            return {gene: idx + dmr_max for idx, gene in enumerate(sorted_genes)}

        # Create separate mappings for each dataset
        dss1_max_dmr = max(df["DMR_No."])
        # home1_max_dmr = max(df_home1["DMR_No."])

        dss1_gene_mapping = create_gene_id_mapping(df, dss1_max_dmr)
        # home1_gene_mapping = create_gene_id_mapping(df_home1, home1_max_dmr)

        # Create bipgraphs with their respective mappings and column names
        bipartite_graph = create_bipartite_graph(
            df, dss1_gene_mapping, closest_gene_col="Gene_Symbol_Nearby"
        )
        # bipartite_graph_home1 = create_bipartite_graph(
        #    df_home1, home1_gene_mapping, closest_gene_col="Gene_Symbol"
        # )
    except Exception as e:
        print(f"Error in initialization: {e}")
        raise

    # Validate graphs
    print("\n=== DSS1 Graph Statistics ===")
    validate_bipartite_graph(bipartite_graph)

    # print("\n=== HOME1 Graph Statistics ===")
    # validate_bipartite_graph(bipartite_graph_home1)

    # Write DSS1 outputs
    write_bipartite_graph(bipartite_graph, args.output, df, dss1_gene_mapping)
    write_gene_mappings(dss1_gene_mapping, "dss1_gene_ids.csv", "DSS1")

    # Write HOME1 outputs
    # write_bipartite_graph(bipartite_graph_home1, "bipartite_graph_home1_output.txt", df_home1, home1_gene_mapping)
    # write_gene_mappings(home1_gene_mapping, "home1_gene_ids.csv", "HOME1")

    # Process bicliques after they've been generated by external tool

    def process_bicliques(
        graph, filename, max_dmr_id, dataset_name, gene_id_mapping, file_format
    ):
        """Helper function to process bicliques for a given graph"""

        if not nx.is_bipartite(graph):
            print(
                f"\n{dataset_name} graph is not bipartite, skipping bicliques processing."
            )
            return None

        try:
            bicliques_result = read_bicliques_file(
                filename,
                max_DMR_id=max_dmr_id,
                original_graph=graph,
                gene_id_mapping=gene_id_mapping,
                file_format="gene_name",
            )
            if bicliques_result:
                print_bicliques_summary(bicliques_result, graph)
            return bicliques_result
        except Exception as e:
            print(f"\nError processing bicliques for {dataset_name}: {str(e)}")
            return None

    # Process DSS1 bicliques
    try:
        file_format = "gene_name" if args.format == "gene-name" else "id"
        bicliques_result = process_bicliques(
            bipartite_graph,
            os.path.join("./data", "bipartite_graph_output.txt.biclusters"),
            max(df["DMR_No."]),
            "DSS1",
            gene_id_mapping=dss1_gene_mapping,
            file_format=file_format,
        )

        if bicliques_result:
            print_bicliques_detail(bicliques_result, df, dss1_gene_mapping)

            # Create biclique membership mapping
            node_biclique_map = create_node_biclique_map(bicliques_result["bicliques"])

            # Calculate node positions
            node_positions = calculate_node_positions(
                bicliques_result["bicliques"], node_biclique_map
            )

            # Create node labels
            node_labels = {}
            for dmr_id in range(len(df)):
                node_labels[dmr_id] = f"DMR_{dmr_id+1}"

            # Use actual gene names for gene labels
            for gene_name, gene_id in dss1_gene_mapping.items():
                node_labels[gene_id] = gene_name

            dmr_nodes_set = {
                node
                for node, data in bipartite_graph.nodes(data=True)
                if data["bipartite"] == 0
            }
            dmr_metadata = {}
            for _, row in df.iterrows():
                dmr_id = row["DMR_No."] - 1  # Convert to 0-based index
                dmr_metadata[f"DMR_{dmr_id+1}"] = {
                    "area": str(row["Area_Stat"])
                    if "Area_Stat" in df.columns
                    else "N/A",
                    "description": str(row["Gene_Description"])
                    if "Gene_Description" in df.columns
                    else "N/A",
                    "name": f"DMR_{row['DMR_No.']}",
                    "bicliques": node_biclique_map.get(dmr_id, []),
                }

            gene_metadata = {}
            for gene_name, gene_id in dss1_gene_mapping.items():
                gene_matches = df[
                    df["Gene_Symbol_Nearby"].str.lower() == gene_name.lower()
                ]
                description = "N/A"
                if (
                    not gene_matches.empty
                    and "Gene_Description" in gene_matches.columns
                ):
                    description = str(gene_matches.iloc[0]["Gene_Description"])

                gene_metadata[gene_name] = {
                    "description": description,
                    "id": gene_id,
                    "bicliques": node_biclique_map.get(gene_id, []),
                    "name": gene_name,
                }

            # Calculate dominating set before visualization
            print("\n=== RB-Domination Analysis (DSS1) ===")
            dominating_set = process_components(bipartite_graph, df)
            print_domination_statistics(dominating_set, bipartite_graph, df)

            # Create visualization with dominating set
            viz_json = create_biclique_visualization(
                bicliques_result["bicliques"],
                node_labels,
                node_positions,
                node_biclique_map,
                dominating_set=dominating_set,
                dmr_metadata=dmr_metadata,
                gene_metadata=gene_metadata,
            )

            # Define component_data
            component_data = []  # Assuming this is where component data is stored

            # Instead of saving to file, add the visualization to each component
            for component in component_data:
                if component.get("bicliques"):
                    # Create visualization specific to this component's bicliques
                    component_viz = create_biclique_visualization(
                        component["bicliques"],
                        node_labels,
                        node_positions,
                        node_biclique_map,
                        dominating_set=dominating_set,
                        dmr_metadata=dmr_metadata,
                        gene_metadata=gene_metadata,
                    )
                    component["plotly_graph"] = json.loads(component_viz)

            # You can still save the full visualization if needed
            with open("biclique_visualization.json", "w") as f:
                f.write(viz_json)
            print("\nVisualization saved to biclique_visualization.json")
        else:
            print("\nNo bicliques results to visualize")

    except Exception as e:
        print(f"\nError processing and visualizing bicliques: {str(e)}")


if __name__ == "__main__":
    main()
# Remove duplicate import statement
