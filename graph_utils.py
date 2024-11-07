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


def create_bipartite_graph(df, gene_id_mapping):
    """
    Create a bipartite graph connecting DMRs to their associated genes.

    Parameters:
    df (DataFrame): A Pandas DataFrame containing DMR and gene information.

    Returns:
    Graph: A NetworkX bipartite graph with DMRs and genes as nodes.
    """
    B = nx.Graph()

    # Add DMR nodes first with explicit bipartite=0
    dmr_nodes = set(df["DMR_No."].apply(lambda x: x - 1))
    B.add_nodes_from(dmr_nodes, bipartite=0)

    # Track gene nodes to ensure proper bipartite assignment
    gene_nodes = set()

    for index, row in df.iterrows():
        dmr = row["DMR_No."] - 1
        associated_genes = set()

        # Add closest gene if it exists
        gene_col = (
            "Gene_Symbol_Nearby"
            if "Gene_Symbol_Nearby" in df.columns
            else "Gene_Symbol"
        )
        if pd.notna(row[gene_col]) and row[gene_col]:
            associated_genes.add(str(row[gene_col]))

        # Add enhancer genes
        if isinstance(row["Processed_Enhancer_Info"], (list, set)):
            enhancer_genes = {
                str(g) for g in row["Processed_Enhancer_Info"] if pd.notna(g) and g
            }
            associated_genes.update(enhancer_genes)

        # Add edges and gene nodes with proper bipartite value
        for gene in associated_genes:
            if gene in gene_id_mapping:
                gene_id = gene_id_mapping[gene]
                if gene_id not in gene_nodes:
                    B.add_node(gene_id, bipartite=1)
                    gene_nodes.add(gene_id)
                B.add_edge(dmr, gene_id)

    return B


def validate_bipartite_graph(B):
    """Validate the bipartite graph properties and print detailed statistics"""
    # Check for nodes with degree 0
    zero_degree_nodes = [n for n, d in B.degree() if d == 0]
    if zero_degree_nodes:
        print(f"\nERROR: Found {len(zero_degree_nodes)} nodes with degree 0:")
        print(f"First 5 zero-degree nodes: {zero_degree_nodes[:5]}")
        raise ValueError("Graph contains nodes with degree 0")
    else:
        print("✓ All nodes have degree > 0")

    # Get node sets by bipartite attribute
    top_nodes = {n for n, d in B.nodes(data=True) if d.get("bipartite") == 0}  # DMRs
    bottom_nodes = {
        n for n, d in B.nodes(data=True) if d.get("bipartite") == 1
    }  # Genes

    print(f"\nNode distribution:")
    print(f"  - DMR nodes (bipartite=0): {len(top_nodes)}")
    print(f"  - Gene nodes (bipartite=1): {len(bottom_nodes)}")

    # Degree statistics
    degrees = dict(B.degree())
    min_degree = min(degrees.values())
    max_degree = max(degrees.values())
    avg_degree = sum(degrees.values()) / len(degrees)

    print(f"\nDegree statistics:")
    print(f"  - Minimum degree: {min_degree}")
    print(f"  - Maximum degree: {max_degree}")
    print(f"  - Average degree: {avg_degree:.2f}")


    # Connected components analysis
    components = list(nx.connected_components(B))
    print(f"\nConnected components:")
    print(f"  - Number of components: {len(components)}")
    print(f"  - Largest component size: {len(max(components, key=len))}")
    print(f"  - Smallest component size: {len(min(components, key=len))}")

    # Verify bipartite property
    if not nx.is_bipartite(B):
        print("\nERROR: Graph is not bipartite")
        raise ValueError("Graph is not bipartite")
    else:
        print("\n✓ Graph is bipartite")

    # Print overall graph size
    print(f"\nTotal graph size:")
    print(f"  - Nodes: {B.number_of_nodes()}")
    print(f"  - Edges: {B.number_of_edges()}")


def validate_node_ids(dmr, gene_id, max_dmr_id, gene_id_mapping):
    """Validate node IDs are properly assigned"""
    if dmr >= max_dmr_id:
        print(f"Warning: Invalid DMR ID {dmr}")
        return False
    if gene_id not in set(gene_id_mapping.values()):
        print(f"Warning: Invalid gene ID {gene_id}")
        return False
    return True
