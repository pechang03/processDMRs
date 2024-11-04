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
    B.add_nodes_from(df["DMR_No."].apply(lambda x: x - 1), bipartite=0)  # Adjust DMR IDs if needed
    for index, row in df.iterrows():
        associated_genes = set()

        # Add closest gene if it's not None
        if row["Gene_Symbol_Nearby"] is not None:
            associated_genes.add(row["Gene_Symbol_Nearby"])

        # Add additional genes from Processed_Enhancer_Info
        for gene in row["Processed_Enhancer_Info"]:
            if gene:  # Check if gene is not empty
                associated_genes.add(gene)

        # Add edges between the DMR and all associated genes
        for gene in associated_genes:
            if not B.has_node(gene):
                B.add_node(gene, bipartite=1)  # Add gene nodes with the 'bipartite' attribute set to 1
            B.add_edge(row["DMR_No."] - 1, gene)

        # Check if enhancer information is missing
        if pd.isna(row["ENCODE_Enhancer_Interaction(BingRen_Lab)"]) or row["ENCODE_Enhancer_Interaction(BingRen_Lab)"] == ".":
            if row["Gene_Symbol_Nearby"] is not None:
                B.add_edge(row["DMR_No."] - 1, row["Gene_Symbol_Nearby"])
    
    return B
