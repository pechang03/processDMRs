import pandas as pd
import networkx as nx
import csv
import time
import psutil

from graph_utils import process_enhancer_info, validate_bipartite_graph
from rb_domination import greedy_rb_domination, process_components
from process_bicliques import read_bicliques_file, print_bicliques_summary, print_bicliques_detail
from graph_visualize import create_biclique_visualization, create_node_biclique_map
from graph_layout import calculate_node_positions


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
    B = nx.Graph()  # Note: nx.Graph() already prevents multi-edges
    dmr_nodes = df["DMR_No."].values

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
        dmr = row["DMR_No."] - 1
        associated_genes = set()

        # Add closest gene if it exists
        gene_col = closest_gene_col
        if pd.notna(row[gene_col]) and row[gene_col]:
            associated_genes.add(str(row[gene_col]))

        # Add enhancer genes if they exist
        if isinstance(row["Processed_Enhancer_Info"], (list, set)):
            enhancer_genes = {str(g) for g in row["Processed_Enhancer_Info"] if pd.notna(g) and g}
            associated_genes.update(enhancer_genes)

        # Add edges and gene nodes
        for gene in associated_genes:
            if gene in gene_id_mapping:
                gene_id = gene_id_mapping[gene]
                
                # Add gene node if it doesn't exist
                if not B.has_node(gene_id):
                    B.add_node(gene_id, bipartite=1)
                
                # Check if we've seen this edge before
                edge = tuple(sorted([dmr, gene_id]))  # Normalize edge representation
                if edge not in edges_seen:
                    B.add_edge(dmr, gene_id)
                    edges_seen.add(edge)
                    edges_added += 1
                else:
                    duplicate_edges.append((dmr, gene_id, gene))

    # Report duplicate edges
    if duplicate_edges:
        print("\nFound duplicate edges that were skipped:")
        for dmr, gene_id, gene_name in duplicate_edges[:5]:  # Show first 5 duplicates
            print(f"DMR {dmr} -> Gene {gene_id} [{gene_name}]")

    print(f"Total edges added: {edges_added}")
    print(f"Total duplicate edges skipped: {len(duplicate_edges)}")
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

        def create_gene_id_mapping(df, dmr_max):
            """Create gene ID mapping using dataset's own max DMR number"""
            all_genes = set()
            gene_col = "Gene_Symbol_Nearby" if "Gene_Symbol_Nearby" in df.columns else "Gene_Symbol"
            
            # Add genes from gene column
            all_genes.update(df[gene_col].dropna())
            
            # Add genes from enhancer info
            enhancer_genes = {gene for genes in df["Processed_Enhancer_Info"] for gene in genes if gene}
            all_genes.update(enhancer_genes)
            
            # Create mapping starting after this dataset's max DMR
            sorted_genes = sorted(all_genes)
            return {gene: idx + dmr_max for idx, gene in enumerate(sorted_genes)}

        # Create separate mappings for each dataset
        dss1_max_dmr = max(df["DMR_No."])
        home1_max_dmr = max(df_home1["DMR_No."])

        dss1_gene_mapping = create_gene_id_mapping(df, dss1_max_dmr)
        home1_gene_mapping = create_gene_id_mapping(df_home1, home1_max_dmr)

        # Create graphs with their respective mappings and column names
        bipartite_graph = create_bipartite_graph(df, dss1_gene_mapping, closest_gene_col="Gene_Symbol_Nearby")
        bipartite_graph_home1 = create_bipartite_graph(df_home1, home1_gene_mapping, closest_gene_col="Gene_Symbol")
    except Exception as e:
        print(f"Error in initialization: {e}")
        raise

    # Create bipartite graphs using their respective gene ID mappings
    bipartite_graph = create_bipartite_graph(df, dss1_gene_mapping, closest_gene_col="Gene_Symbol_Nearby")
    bipartite_graph_home1 = create_bipartite_graph(df_home1, home1_gene_mapping, closest_gene_col="Gene_Symbol")

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
            print(f"\n{dataset_name} graph is not bipartite, skipping bicliques processing.")
            return None

        try:
            bicliques_result = read_bicliques_file(
                filename,
                max_DMR_id=max_dmr_id,
                original_graph=graph  # Remove validate_fn parameter
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
        print_bicliques_detail(bicliques_result, df, dss1_gene_mapping)
        
        # Create node labels
        node_labels = {}
        # Add DMR labels (using DMR_Name from df if available)
        for dmr_id in range(len(df)):
            node_id = dmr_id  # Graph uses 0-based indexing
            dmr_name = f"DMR_{dmr_id+1}"  # Display uses 1-based indexing
            if 'DMR_Name' in df.columns:
                dmr_name = df.iloc[dmr_id]['DMR_Name']
            node_labels[node_id] = dmr_name
        # Add gene labels
        for gene, gene_id in dss1_gene_mapping.items():
            node_labels[gene_id] = gene
        
        # Create biclique membership mapping
        node_biclique_map = create_node_biclique_map(bicliques_result['bicliques'])
        
        # Calculate node positions
        node_positions = calculate_node_positions(
            bicliques_result['bicliques'],
            node_biclique_map
        )
        
        # Create visualization
        viz_json = create_biclique_visualization(
            bicliques_result['bicliques'],
            node_labels,
            node_positions,
            node_biclique_map
        )
        
        # Save visualization to file
        with open('biclique_visualization.json', 'w') as f:
            f.write(viz_json)

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
