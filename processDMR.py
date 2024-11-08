import pandas as pd
import networkx as nx
import csv
import time
import psutil

from graph_layout import calculate_node_positions
from graph_utils import (
    process_enhancer_info,
    validate_bipartite_graph,  # Add this line
)
from rb_domination import (
    greedy_rb_domination,
    process_components,
    print_domination_statistics,
)
from process_bicliques import (
    read_bicliques_file,
    print_bicliques_summary,
    print_bicliques_detail,
)
from graph_visualize import create_biclique_visualization, create_node_biclique_map
from typing import Dict


def read_excel_file(filepath):
    """Read and validate an Excel file."""
    try:
        df = pd.read_excel(filepath, header=0)
        print(f"Column names: {df.columns.tolist()}")
        print("\nSample of input data:")
        # Determine which columns to display based on what's available
        if "Gene_Symbol_Nearby" in df.columns:
            gene_col = "Gene_Symbol_Nearby"
        elif "Gene_Symbol" in df.columns:
            gene_col = "Gene_Symbol"
        else:
            raise KeyError("No gene symbol column found in the file")

        print(
            df[
                [
                    "DMR_No.",
                    gene_col,
                    "ENCODE_Enhancer_Interaction(BingRen_Lab)",
                    "Gene_Description",
                ]
            ].head(10)
        )
        return df
    except FileNotFoundError:
        error_msg = f"Error: The file {filepath} was not found."
        print(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        raise


def create_bipartite_graph(df: pd.DataFrame, gene_id_mapping: Dict[str, int], closest_gene_col: str = "Gene_Symbol_Nearby") -> nx.Graph:
    """Create a bipartite graph from DataFrame."""
    B = nx.Graph()  # Note: nx.Graph() already prevents multi-edges
    dmr_nodes = df["DMR_No."].values  # Ensure this is zero-based

    # Add DMR nodes with explicit bipartite attribute (0-based indexing)
    for dmr in dmr_nodes:
        B.add_node(dmr - 1, bipartite=0)

    print(f"\nDebugging create_bipartite_graph:")
    print(f"Number of DMR nodes added: {len(dmr_nodes)}")

    # Track edges we've already added
    edges_seen = set()
    duplicate_edges = []
    edges_added = 0

    for _, row in df.iterrows():
        dmr_id = row["DMR_No."] - 1  # Zero-based indexing
        associated_genes = set()  # Initialize a set to collect unique genes

        # Add closest gene if it exists
        gene_col = closest_gene_col
        if pd.notna(row[gene_col]) and row[gene_col]:
            gene_name = str(row[gene_col]).strip().lower()  # Standardize to lowercase
            associated_genes.add(gene_name)

        # Add enhancer genes if they exist
        if isinstance(row["Processed_Enhancer_Info"], (set, list)):
            enhancer_genes = {g.lower() for g in row["Processed_Enhancer_Info"] if g}  # Standardize to lowercase
            associated_genes.update(enhancer_genes)

        # Debugging output for associated genes
        # print(f"DMR {dmr}: Associated genes: {associated_genes}")

        # Add edges and gene nodes
        for gene in associated_genes:
            if gene in gene_id_mapping:
                gene_id = gene_id_mapping[gene]

                # Add gene node if it doesn't exist
                if not B.has_node(gene_id):  # Add gene node if it doesn't exist
                    B.add_node(gene_id, bipartite=1)  # Mark as gene node
                    # print(f"Added gene node: {gene_id} for gene: {gene}")

                # Ensure all associated genes are processed
                # print(f"Processing gene: {gene} with ID: {gene_id}")

                # Check if we've seen this edge before
                edge = tuple(sorted([dmr_id, gene_id]))  # Normalize edge representation
                if edge not in edges_seen:
                    B.add_edge(dmr_id, gene_id)
                    edges_seen.add(edge)
                    edges_added += 1
                else:
                    duplicate_edges.append((dmr_id, gene_id, gene))

    # Report duplicate edges
    if duplicate_edges:
        print("\nFound duplicate edges that were skipped:")
        for dmr, gene_id, gene_name in duplicate_edges[:5]:  # Show first 5 duplicates
            print(f"DMR {dmr} -> Gene {gene_id} [{gene_name}]")

    print(f"Total edges added: {edges_added}")  # Log total edges added
    print(f"Total duplicate edges skipped: {len(duplicate_edges)}")
    print(f"Final graph: {len(B.nodes())} nodes, {len(B.edges())} edges")  # Log final graph size

    return B


def write_bipartite_graph(graph, output_file, df, gene_id_mapping):
    """Write bipartite graph to file."""

    def validate_edge(dmr, gene_id):
        return graph.has_edge(dmr, gene_id)

    try:
        with open(output_file, "w") as file:
            unique_dmrs = df["DMR_No."].nunique()
            all_genes = set()

            # Add genes from enhancer info
            enhancer_genes = df["Processed_Enhancer_Info"].explode().dropna().unique()
            all_genes.update(enhancer_genes)

            # Add genes from gene symbol column (using the correct column name)
            gene_col = (
                "Gene_Symbol_Nearby"
                if "Gene_Symbol_Nearby" in df.columns
                else "Gene_Symbol"
            )
            symbol_genes = df[gene_col].dropna().unique()
            all_genes.update(symbol_genes)

            unique_genes = len(all_genes)

            file.write(f"{unique_dmrs} {unique_genes}\n")

            edges = []
            for dmr, gene in graph.edges():
                if isinstance(gene, str):
                    gene_id = gene_id_mapping[gene]
                    edges.append((dmr, gene_id))
                else:
                    edges.append((dmr, gene))

            sorted_edges = sorted(
                [
                    (dmr, gene)
                    for dmr, gene in graph.edges()
                    if validate_edge(dmr, gene)
                ],
                key=lambda x: (x[0], x[1]),
            )
            for dmr, gene_id in sorted_edges:
                file.write(f"{dmr} {gene_id}\n")
    except Exception as e:
        print(f"Error writing {output_file}: {e}")
        raise


def write_gene_mappings(gene_id_mapping, output_file):
    """Write gene ID mappings to CSV file."""
    try:
        with open(output_file, "w", newline="") as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(["Gene", "ID"])
            for gene, gene_id in gene_id_mapping.items():
                csvwriter.writerow([gene, gene_id])
    except Exception as e:
        print(f"Error writing {output_file}: {e}")
        raise


def main():
    try:
        # Add logging
        import logging

        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )

        # Read DSS1 data
        df = read_excel_file("./data/DSS1.xlsx")
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

        # Add genes from HOME1
        home1_gene_col = (
            "Gene_Symbol_Nearby"
            if "Gene_Symbol_Nearby" in df_home1.columns
            else "Gene_Symbol"
        )
        all_genes.update(df_home1["Processed_Enhancer_Info"].explode().dropna())
        all_genes.update(df_home1[home1_gene_col].dropna())

        def create_gene_id_mapping(df: pd.DataFrame, dmr_max: int) -> Dict[str, int]:
            """Create gene ID mapping using dataset's own max DMR number"""
            all_genes = set()
            gene_col = (
                "Gene_Symbol_Nearby"
                if "Gene_Symbol_Nearby" in df.columns
                else "Gene_Symbol"
            )

            # Add genes from gene column
            gene_symbols = df[gene_col].dropna().str.strip().str.lower()
            all_genes.update(gene_symbols)

            # Add genes from enhancer info
            enhancer_genes = {
                gene
                for genes in df["Processed_Enhancer_Info"]
                for gene in genes
                if gene
            }
            all_genes.update(enhancer_genes)

            # Create mapping starting after this dataset's max DMR
            sorted_genes = sorted(all_genes)
            return {gene: idx + dmr_max for idx, gene in enumerate(sorted_genes)}

        # Create separate mappings for each dataset
        dss1_max_dmr = max(df["DMR_No."])
        home1_max_dmr = max(df_home1["DMR_No."])

        dss1_gene_mapping = create_gene_id_mapping(df, dss1_max_dmr)
        home1_gene_mapping = create_gene_id_mapping(df_home1, home1_max_dmr)

        # Create bipgraphs with their respective mappings and column names
        bipartite_graph = create_bipartite_graph(
            df, dss1_gene_mapping, closest_gene_col="Gene_Symbol_Nearby"
        )
        bipartite_graph_home1 = create_bipartite_graph(
            df_home1, home1_gene_mapping, closest_gene_col="Gene_Symbol"
        )
    except Exception as e:
        print(f"Error in initialization: {e}")
        raise

    # Validate graphs
    print("\n=== DSS1 Graph Statistics ===")
    validate_bipartite_graph(bipartite_graph)

    print("\n=== HOME1 Graph Statistics ===")
    validate_bipartite_graph(bipartite_graph_home1)

    # Write output files
    write_bipartite_graph(
        bipartite_graph, "bipartite_graph_output.txt", df, dss1_gene_mapping
    )
    write_bipartite_graph(
        bipartite_graph_home1,
        "bipartite_graph_home1_output.txt",
        df_home1,
        home1_gene_mapping,
    )
    write_gene_mappings(dss1_gene_mapping, "dss1_gene_ids.csv")
    write_gene_mappings(home1_gene_mapping, "home1_gene_ids.csv")

    # Process bicliques after they've been generated by external tool

    def process_bicliques(graph, filename, max_dmr_id, dataset_name):
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
                original_graph=graph,  # Remove validate_fn parameter
            )
            if bicliques_result:
                print_bicliques_summary(bicliques_result, graph)
            return bicliques_result
        except Exception as e:
            print(f"\nError processing bicliques for {dataset_name}: {str(e)}")
            return None

    # Process DSS1 bicliques
    bicliques_result = process_bicliques(
        bipartite_graph,
        "./data/bipartite_graph_output.txt.biclusters",
        max(df["DMR_No."]),
        "DSS1",
    )

    # Only then create visualization if we have bicliques results
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
            node_id = dmr_id
            node_labels[node_id] = f"DMR_{dmr_id+1}"

        for gene, gene_id in dss1_gene_mapping.items():
            node_labels[gene_id] = gene

        dmr_nodes_set = {
            node
            for node, data in bipartite_graph.nodes(data=True)
            if data["bipartite"] == 0
        }
        dmr_metadata = {}
        for dmr_id in range(len(df)):
            area_stat = (
                df.iloc[dmr_id]["Area_Stat"] if "Area_Stat" in df.columns else "N/A"
            )
            dmr_metadata[f"DMR_{dmr_id+1}"] = {
                "area": area_stat,
                "bicliques": node_biclique_map.get(dmr_id, []),
            }

        gene_metadata = {}
        for gene, gene_id in dss1_gene_mapping.items():
            gene_matches = df[df["Gene_Symbol_Nearby"] == gene]
            desc = (
                gene_matches.iloc[0]["Gene_Description"]
                if len(gene_matches) > 0
                else "N/A"
            )
            gene_metadata[gene] = {
                "description": desc,
                "bicliques": node_biclique_map.get(gene_id, []),
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
            dominating_set=dominating_set,  # Now dominating_set is defined
            dmr_metadata=dmr_metadata,
            gene_metadata=gene_metadata,
        )

        # Save visualization
    with open("biclique_visualization.json", "w") as f:
        f.write(viz_json)


if __name__ == "__main__":
    main()
# Remove duplicate import statement
