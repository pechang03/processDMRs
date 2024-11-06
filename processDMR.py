import pandas as pd
import networkx as nx
import csv
import time
import psutil

from graph_utils import process_enhancer_info, validate_bipartite_graph
from rb_domination import greedy_rb_domination, process_components


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

            if associated_genes:
                for gene in associated_genes:
                    gene_id = gene_id_mapping[gene]
                    if not B.has_node(gene_id):
                        B.add_node(gene_id, bipartite=1)
                    B.add_edge(dmr, gene_id)
                    total_edges += 1
                dmrs_without_edges.discard(dmr)

    print(f"Total edges added: {total_edges}")
    print(f"Final graph: {len(B.nodes())} nodes, {len(B.edges())} edges")
    return B


def write_bipartite_graph(graph, output_file, df, gene_id_mapping):
    """Write bipartite graph to file."""
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

            sorted_edges = sorted(edges, key=lambda x: (x[0], x[1]))
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
    from process_bicliques import read_bicliques_file
    
    bicliques_result = read_bicliques_file(
        "./data/bipartite_graph_output.txt.biclusters",
        max_DMR_id=max(df["DMR_No."]),
        original_graph=bipartite_graph
    )
    
    # Print summary and validate bicliques analysis
    print("\n=== Bicliques Analysis ===")
    print(f"Total bicliques found: {bicliques_result['total_bicliques']}")
    print(f"Split genes: {bicliques_result['total_split_genes']}")
    print(f"False positives: {bicliques_result['total_false_positives']}")
    print(f"False negatives: {bicliques_result['total_false_negatives']}")
    
    # Validate header statistics against actual counts
    if 'statistics' in bicliques_result:
        print("\nKey Statistics from Bicliques:")
        for key, value in bicliques_result['statistics'].items():
            print(f"  {key}: {value}")
            
        # Validate number of bicliques
        if 'Number of biclusters' in bicliques_result['statistics']:
            reported_count = int(bicliques_result['statistics']['Number of biclusters'])
            actual_count = bicliques_result['total_bicliques']
            if reported_count != actual_count:
                print(f"\nWARNING: Mismatch in bicluster counts!")
                print(f"  Header reports: {reported_count}")
                print(f"  Actually found: {actual_count}")
            else:
                print(f"\n✓ Verified: Bicluster count matches header ({actual_count})")


if __name__ == "__main__":
    main()
