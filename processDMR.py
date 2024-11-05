import pandas as pd
import networkx as nx
import csv
import time
import psutil

from graph_utils import process_enhancer_info, validate_bipartite_graph
from rb_domination import greedy_rb_domination, validate_bipartite_graph, process_components


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


def create_bipartite_graph(df, closest_gene_col="Gene_Symbol_Nearby"):
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

            if pd.notna(row[closest_gene_col]) and row[closest_gene_col]:
                associated_genes.add(str(row[closest_gene_col]))

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
                    if not B.has_node(gene):
                        B.add_node(gene, bipartite=1)
                    B.add_edge(dmr, gene)
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
            all_genes = (
                df["Processed_Enhancer_Info"].explode().dropna().unique().tolist()
                + df["Gene_Symbol_Nearby"].dropna().unique().tolist()
            )
            unique_genes = len(set(all_genes))
            
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
    df["Processed_Enhancer_Info"] = df["ENCODE_Enhancer_Interaction(BingRen_Lab)"].apply(
        process_enhancer_info
    )

    # Read HOME1 data
    df_home1 = read_excel_file("./data/HOME1.xlsx")
    df_home1["Processed_Enhancer_Info"] = df_home1["ENCODE_Enhancer_Interaction(BingRen_Lab)"].apply(
        process_enhancer_info
    )

    # Create bipartite graphs
    bipartite_graph = create_bipartite_graph(df)
    bipartite_graph_home1 = create_bipartite_graph(df_home1, closest_gene_col="Gene_Symbol")

    # Validate graphs
    validate_bipartite_graph(bipartite_graph)
    validate_bipartite_graph(bipartite_graph_home1)

    # Create gene ID mapping
    dmr_nodes = df["DMR_No."].values
    all_genes = (
        df["Processed_Enhancer_Info"].explode().dropna().unique().tolist()
        + df["Gene_Symbol_Nearby"].dropna().unique().tolist()
    )
    all_genes_home1 = (
        df_home1["Processed_Enhancer_Info"].explode().dropna().unique().tolist()
        + df_home1["Gene_Symbol"].dropna().unique().tolist()
    )
    
    all_unique_genes = list(set(all_genes + all_genes_home1))
    gene_id_start = len(dmr_nodes)
    gene_id_mapping = {
        gene: idx + gene_id_start for idx, gene in enumerate(all_unique_genes)
    }

    # Write output files
    write_bipartite_graph(bipartite_graph, "bipartite_graph_output.txt", df, gene_id_mapping)
    write_bipartite_graph(bipartite_graph_home1, "bipartite_graph_home1_output.txt", df_home1, gene_id_mapping)
    write_gene_mappings(gene_id_mapping, "gene_ids.csv")


if __name__ == "__main__":
    main()
