import pandas as pd
import networkx as nx


def process_enhancer_info(enhancer_str):
    """
    Process the enhancer information from the ENCODE data.

    Parameters:
    enhancer_str (str): A string containing enhancer information, separated by ';'.

    Returns:
    list: A list of processed gene names, with any suffixes removed.
    """
    if pd.isna(enhancer_str) or enhancer_str == ".":
        return []
    genes = enhancer_str.split(";")
    processed_genes = [gene.split("/")[0] for gene in genes]
    return processed_genes


def create_bipartite_graph(df):
    """
    Create a bipartite graph connecting DMRs to their associated genes.

    Parameters:
    df (DataFrame): A Pandas DataFrame containing DMR and gene information.

    Returns:
    Graph: A NetworkX bipartite graph with DMRs and genes as nodes.
    """
    B = nx.Graph()
    # Add nodes with the node attribute "bipartite"
    B.add_nodes_from(df["DMR_No."].apply(lambda x: x - 1), bipartite=0)
    for index, row in df.iterrows():
        associated_genes = set()

        # Add closest gene if it's not None
        if row["Gene_Symbol_Nearby"] is not None:
            associated_genes.add(row["Gene_Symbol_Nearby"])

        # Add additional genes from Processed_Enhancer_Info
        for gene in row["Processed_Enhancer_Info"]:
            if gene:  # Check if gene is not empty
                associated_genes.add(gene)

        # Add gene nodes with the 'bipartite' attribute set to 1
        for gene in associated_genes:
            if not B.has_node(gene):
                B.add_node(gene, bipartite=1)
            B.add_edge(row["DMR_No."] - 1, gene)

        # Check if enhancer information is missing
        if (
            pd.isna(row["ENCODE_Enhancer_Interaction(BingRen_Lab)"])
            or row["ENCODE_Enhancer_Interaction(BingRen_Lab)"] == "."
        ):
            if row["Gene_Symbol_Nearby"] is not None:
                B.add_edge(row["DMR_No."] - 1, row["Gene_Symbol_Nearby"])

    return B


def validate_bipartite_graph(B):
    """Validate the bipartite graph properties and print detailed statistics"""
    print("\nGraph Statistics:")
    print("-----------------")
    
    # Check for isolated nodes (degree 0)
    isolated = list(nx.isolates(B))
    if isolated:
        print(f"WARNING: Found {len(isolated)} isolated nodes: {isolated[:5]}")
    else:
        print("✓ No isolated nodes found")

    # Degree statistics
    degrees = dict(B.degree())
    min_degree = min(degrees.values())
    max_degree = max(degrees.values())
    print(f"Degree statistics:")
    print(f"  - Minimum degree: {min_degree}")
    print(f"  - Maximum degree: {max_degree}")
    
    if min_degree == 0:
        zero_degree_nodes = [n for n, d in degrees.items() if d == 0]
        print(f"WARNING: Graph contains {len(zero_degree_nodes)} nodes with degree 0")
        print(f"First 5 zero-degree nodes: {zero_degree_nodes[:5]}")

    # Connected components analysis
    components = list(nx.connected_components(B))
    print(f"Connected components:")
    print(f"  - Number of components: {len(components)}")
    print(f"  - Largest component size: {len(max(components, key=len))}")
    print(f"  - Smallest component size: {len(min(components, key=len))}")

    # Verify bipartite property
    if not nx.is_bipartite(B):
        print("WARNING: Graph is not bipartite")
    else:
        print("✓ Graph is bipartite")

    # Print overall graph size
    print(f"\nTotal graph size:")
    print(f"  - Nodes: {B.number_of_nodes()}")
    print(f"  - Edges: {B.number_of_edges()}")
