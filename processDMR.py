import pandas as pd
import networkx as nx
import csv
import time
import psutil

from graph_utils import process_enhancer_info, validate_bipartite_graph
from rb_domination import greedy_rb_domination, process_components
from process_bicliques import read_bicliques_file, print_bicliques_summary, print_bicliques_detail


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
                    "Gene_Description",  # Add this line
                ]
            ].head(10)
        )
        return df
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        raise


def create_bipartite_graph(df, gene_id_mapping, closest_gene_col="Gene_Symbol_Nearby"):
    """Create a bipartite graph from DataFrame."""
    B = nx.Graph()
    dmr_nodes = df["DMR_No."].values

    # Add DMR nodes with explicit bipartite attribute (0-based indexing)
    for dmr in dmr_nodes:
        B.add_node(dmr - 1, bipartite=0)

    print(f"\nDebugging create_bipartite_graph:")
    print(f"Number of DMR nodes added: {len(dmr_nodes)}")

    batch_size = 1000
    total_edges = 0
    dmrs_without_edges = set(dmr - 1 for dmr in dmr_nodes)

    problematic_edges = []

    for i in range(0, len(df), batch_size):
        batch = df.iloc[i : i + batch_size]
        for _, row in batch.iterrows():
            dmr = row["DMR_No."] - 1
            associated_genes = set()

            gene_col = (
                "Gene_Symbol_Nearby"
                if "Gene_Symbol_Nearby" in df.columns
                else "Gene_Symbol"
            )
            if pd.notna(row[gene_col]) and row[gene_col]:
                associated_genes.add(str(row[gene_col]))

            if isinstance(row["Processed_Enhancer_Info"], (list, set)):
                enhancer_genes = set(
                    str(gene)
                    for gene in row["Processed_Enhancer_Info"]
                    if pd.notna(gene) and gene
                )
                if enhancer_genes:
                    associated_genes.update(enhancer_genes)

            def validate_node_ids(dmr, gene_id):
                if dmr >= max(df["DMR_No."]):
                    print(f"Warning: Invalid DMR ID {dmr}")
                    return False
                if gene_id not in set(gene_id_mapping.values()):
                    print(f"Warning: Invalid gene ID {gene_id}")
                    return False
                return True

            if associated_genes:
                for gene in associated_genes:
                    gene_id = gene_id_mapping[gene]
                    if validate_node_ids(dmr, gene_id):
                        if not B.has_node(gene_id):
                            B.add_node(gene_id, bipartite=1)
                        B.add_edge(dmr, gene_id)
                        total_edges += 1
                        # Check if this creates a non-bipartite edge
                        if B.nodes[dmr]['bipartite'] == B.nodes[gene_id]['bipartite']:
                            problematic_edges.append((dmr, gene_id))
                dmrs_without_edges.discard(dmr)

    if problematic_edges:
        print("\nFound problematic edges in graph:")
        for edge in problematic_edges[:5]:  # Show first 5 problematic edges
            print(f"Edge between nodes with same bipartite value: {edge}")
            dmr_node = edge[0]
            gene_node = edge[1]
            print(f"DMR {dmr_node}: bipartite={B.nodes[dmr_node]['bipartite']}")
            print(f"Gene {gene_node}: bipartite={B.nodes[gene_node]['bipartite']}")
            # Show the actual gene name
            gene_name = [k for k, v in gene_id_mapping.items() if v == gene_node][0]
            print(f"Gene name: {gene_name}")

    print(f"Total edges added: {total_edges}")
    print(f"Final graph: {len(B.nodes())} nodes, {len(B.edges())} edges")
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
                [(dmr, gene) for dmr, gene in graph.edges() 
                 if validate_edge(dmr, gene)],
                key=lambda x: (x[0], x[1])
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
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
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
            "Gene_Symbol_Nearby" if "Gene_Symbol_Nearby" in df.columns else "Gene_Symbol"
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

        # Create gene ID mapping BEFORE creating graphs
        all_genes = set()

        # Add genes from DSS1
        dss1_gene_col = (
            "Gene_Symbol_Nearby" if "Gene_Symbol_Nearby" in df.columns else "Gene_Symbol"
        )
        dss1_genes = set(df[dss1_gene_col].dropna())
        dss1_enhancer_genes = {
            gene for genes in df["Processed_Enhancer_Info"] for gene in genes if gene
        }
        all_genes.update(dss1_genes)
        all_genes.update(dss1_enhancer_genes)

        # Add genes from HOME1
        home1_gene_col = (
            "Gene_Symbol_Nearby"
            if "Gene_Symbol_Nearby" in df_home1.columns
            else "Gene_Symbol"
        )
        home1_genes = set(df_home1[home1_gene_col].dropna())
        home1_enhancer_genes = {
            gene for genes in df_home1["Processed_Enhancer_Info"] for gene in genes if gene
        }
        all_genes.update(home1_genes)
        all_genes.update(home1_enhancer_genes)

        # Create sorted gene list and mapping
        sorted_genes = sorted(all_genes)
        gene_id_mapping = {
            gene: idx + max(df["DMR_No."]) for idx, gene in enumerate(sorted_genes)
        }
    except Exception as e:
        print(f"Error in initialization: {e}")
        raise

    # Create bipartite graphs using the consistent gene_id_mapping
    # TODO what about also passing in ENCODE_Enhancer_Interaction(BingRen_Lab)
    bipartite_graph = create_bipartite_graph(
        df, gene_id_mapping, closest_gene_col="Gene_Symbol_Nearby"
    )
    bipartite_graph_home1 = create_bipartite_graph(
        df_home1, gene_id_mapping, closest_gene_col="Gene_Symbol"
    )

    # Validate graphs
    print("\n=== DSS1 Graph Statistics ===")
    validate_bipartite_graph(bipartite_graph)

    print("\n=== HOME1 Graph Statistics ===")
    validate_bipartite_graph(bipartite_graph_home1)

    # Write output files
    write_bipartite_graph(
        bipartite_graph, "bipartite_graph_output.txt", df, gene_id_mapping
    )
    write_bipartite_graph(
        bipartite_graph_home1,
        "bipartite_graph_home1_output.txt",
        df_home1,
        gene_id_mapping,
    )
    write_gene_mappings(gene_id_mapping, "gene_ids.csv")

     # Process bicliques after they've been generated by external tool

    def process_bicliques(graph, filename, max_dmr_id, dataset_name):
        """Helper function to process bicliques for a given graph"""
        def validate_biclique(dmr_nodes, gene_nodes):
            return all(
                graph.has_edge(dmr, gene)
                for dmr in dmr_nodes
                for gene in gene_nodes
            )

        if not nx.is_bipartite(graph):
            print(f"\n{dataset_name} graph is not bipartite, skipping bicliques processing.")
            return None

        try:
            bicliques_result = read_bicliques_file(
                filename,
                max_DMR_id=max_dmr_id,
                original_graph=graph,
                validate_fn=validate_biclique
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
        "DSS1"
    )

    # Only print details if we have results
    if bicliques_result:
        print_bicliques_detail(bicliques_result, df, gene_id_mapping)

    # Run RB-domination analysis on DSS1 graph
    print("\n=== RB-Domination Analysis (DSS1) ===")

    # Get the dominating set using the area statistic as weight
    dominating_set = process_components(bipartite_graph, df)

    # Calculate coverage statistics
    gene_nodes = {n for n, d in bipartite_graph.nodes(data=True) if d["bipartite"] == 1}
    dmr_nodes = {n for n, d in bipartite_graph.nodes(data=True) if d["bipartite"] == 0}

    # Get dominated genes (neighbors of dominating DMRs)
    dominated_genes = set()
    for dmr in dominating_set:
        dominated_genes.update(bipartite_graph.neighbors(dmr))

    # Calculate statistics
    print(f"\nDominating Set Statistics:")
    print(f"Size of dominating set: {len(dominating_set)} DMRs")
    print(f"Percentage of DMRs in dominating set: {(len(dominating_set)/len(dmr_nodes))*100:.2f}%")
    print(f"Number of genes dominated: {len(dominated_genes)} / {len(gene_nodes)}")
    print(f"Percentage of genes dominated: {(len(dominated_genes)/len(gene_nodes))*100:.2f}%")

    # Optional: Print some example DMRs from the dominating set
    print("\nSample DMRs from dominating set:")
    sample_size = min(5, len(dominating_set))
    for dmr in list(dominating_set)[:sample_size]:
        dmr_row = df[df['DMR_No.'] == dmr + 1].iloc[0]  # +1 because DMR IDs are 1-based in df
        area_stat = dmr_row['Area_Stat'] if 'Area_Stat' in df.columns else 'N/A'
        num_neighbors = len(list(bipartite_graph.neighbors(dmr)))
        print(f"DMR_{dmr + 1}: Area={area_stat}, Dominates {num_neighbors} genes")


if __name__ == "__main__":
    main()
