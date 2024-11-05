import pandas as pd
import networkx as nx
import csv
from graph_utils import process_enhancer_info


def greedy_rb_domination(graph, df, area_col=None):
    # Initialize the dominating set
    dominating_set = set()

    # Get all gene nodes (bipartite=1)
    gene_nodes = set(
        node for node, data in graph.nodes(data=True) if data["bipartite"] == 1
    )

    # Keep track of dominated genes
    dominated_genes = set()

    # First, handle degree-1 genes that aren't already dominated
    for gene in gene_nodes:
        if graph.degree(gene) == 1 and gene not in dominated_genes:
            # Get the single neighbor (DMR) of this gene
            dmr = list(graph.neighbors(gene))[0]
            dominating_set.add(dmr)
            # Update dominated genes
            dominated_genes.update(graph.neighbors(dmr))

    # Get remaining undominated subgraph
    remaining_graph = graph.copy()
    remaining_graph.remove_nodes_from(dominating_set)
    remaining_graph.remove_nodes_from(dominated_genes)

    # Handle remaining components
    for component in nx.connected_components(remaining_graph):
        # Skip if component has no genes to dominate
        if not any(remaining_graph.nodes[n]["bipartite"] == 1 for n in component):
            continue

        # Get DMR nodes in this component
        dmr_nodes = [
            node for node in component if remaining_graph.nodes[node]["bipartite"] == 0
        ]

        if dmr_nodes:  # If there are DMR nodes in this component
            # Add weight-based selection
            def get_node_weight(node):
                degree = len(set(graph.neighbors(node)))
                area = df.loc[node, area_col] if area_col else 1.0
                return degree * area

            # Modify selection strategy
            best_dmr = max(
                dmr_nodes,
                key=lambda x: (
                    len(set(remaining_graph.neighbors(x))),
                    get_node_weight(x),
                ),
            )
            dominating_set.add(best_dmr)

    return dominating_set


# Read the Excel file into a Pandas DataFrame
try:
    df = pd.read_excel(
        "./data/DSS1.xlsx", header=0
    )  # Adjust this based on your inspection
    print(
        "Column names:", df.columns.tolist()
    )  # Print the column names for verification
    print("\nSample of input data:")
    print(
        df[
            [
                "DMR_No.",
                "Gene_Symbol_Nearby",
                "ENCODE_Enhancer_Interaction(BingRen_Lab)",
            ]
        ].head(10)
    )
except Exception as e:
    print(f"Error reading DSS1.xlsx: {e}")
    raise  # Re-raise the exception after logging

# Print the column names to verify they match your expectations
print("Column names:", df.columns)

# Extract specific columns from the DataFrame
dmr_id = df["DMR_No."]
closest_gene = df["Gene_Symbol_Nearby"]
area = df["Area_Stat"]
enhancer_info = df["ENCODE_Enhancer_Interaction(BingRen_Lab)"]

# Apply the function to the correct column
df["Processed_Enhancer_Info"] = df["ENCODE_Enhancer_Interaction(BingRen_Lab)"].apply(
    process_enhancer_info
)

# Print the extracted data
print("DMR IDs:")
print(dmr_id)
print("Closest Genes:")
print(closest_gene)
print("Area:")
print(area)
print("Processed Enhancer Info:")
print(df["Processed_Enhancer_Info"])


# Function to create a bipartite graph connecting DMRs to their associated genes
def create_bipartite_graph(df, closest_gene_col="Gene_Symbol_Nearby"):
    B = nx.Graph()
    dmr_nodes = df["DMR_No."].values

    # Add DMR nodes with explicit bipartite attribute (0-based indexing)
    for dmr in dmr_nodes:
        B.add_node(dmr - 1, bipartite=0)  # Subtract 1 to convert to 0-based indexing

    print(f"\nDebugging create_bipartite_graph:")
    print(f"Number of DMR nodes added: {len(dmr_nodes)}")

    batch_size = 1000
    total_edges = 0
    dmrs_without_edges = set(dmr - 1 for dmr in dmr_nodes)  # Track DMRs without edges

    for i in range(0, len(df), batch_size):
        batch = df.iloc[i : i + batch_size]
        for _, row in batch.iterrows():
            dmr = row["DMR_No."] - 1  # Convert to 0-based indexing
            associated_genes = set()

            # Add closest gene if it exists
            if pd.notna(row[closest_gene_col]) and row[closest_gene_col]:
                associated_genes.add(
                    str(row[closest_gene_col])
                )  # Ensure gene names are strings
                # print(f"DMR {dmr} has closest gene: {row[closest_gene_col]}")

            # Add enhancer genes if they exist
            if isinstance(row["Processed_Enhancer_Info"], (list, set)):
                enhancer_genes = set(
                    str(gene)
                    for gene in row["Processed_Enhancer_Info"]
                    if pd.notna(gene) and gene
                )
                if enhancer_genes:
                    associated_genes.update(enhancer_genes)
                    # print(f"DMR {dmr} has enhancer genes: {enhancer_genes}")

            # Add edges for all associated genes
            if associated_genes:
                for gene in associated_genes:
                    if not B.has_node(gene):
                        B.add_node(gene, bipartite=1)
                    B.add_edge(dmr, gene)  # Use 0-based DMR index
                    total_edges += 1
                dmrs_without_edges.discard(dmr)

    print(f"Total edges added: {total_edges}")
    print(f"Final graph: {len(B.nodes())} nodes, {len(B.edges())} edges")

    # Debug information about nodes without edges
    zero_degree_nodes = [node for node in B.nodes() if B.degree(node) == 0]
    if zero_degree_nodes:
        print(f"Found {len(zero_degree_nodes)} nodes with degree 0:")
        print(f"First 5 zero-degree nodes: {zero_degree_nodes[:5]}")
        print(
            f"Node types of zero-degree nodes: {[B.nodes[node].get('bipartite') for node in zero_degree_nodes[:5]]}"
        )

    if dmrs_without_edges:
        print(f"Found {len(dmrs_without_edges)} DMRs without any edges:")
        print(f"First 5 DMRs without edges: {list(dmrs_without_edges)[:5]}")

    return B


def preprocess_graph(graph):
    # Add handling for isolated nodes
    isolated_nodes = list(nx.isolates(graph))
    graph.remove_nodes_from(isolated_nodes)

    # Existing redundancy removal code
    redundant = []
    for node in graph.nodes():
        if graph.nodes[node]["bipartite"] == 0:  # DMR nodes
            neighbors = set(graph.neighbors(node))
            for other in graph.nodes():
                if (
                    other != node
                    and graph.nodes[other]["bipartite"] == 0
                    and set(graph.neighbors(other)).issubset(neighbors)
                ):
                    redundant.append(other)
    graph.remove_nodes_from(redundant)
    return graph


# Preprocess the bipartite graph for DSS1
# First create the raw bipartite graph
bipartite_graph = create_bipartite_graph(df)
validate_bipartite_graph(bipartite_graph)

# Write the graph files immediately after creation and validation
try:
    with open("bipartite_graph_output.txt", "w") as file:
        file.write(f"{unique_dmrs} {unique_genes}\n")
        edges = []
        for dmr, gene in bipartite_graph.edges():
            if isinstance(gene, str):
                gene_id = gene_id_mapping[gene]
                edges.append((dmr, gene_id))
            else:
                edges.append((dmr, gene))
        sorted_edges = sorted(edges, key=lambda x: (x[0], x[1]))
        for dmr, gene_id in sorted_edges:
            file.write(f"{dmr} {gene_id}\n")
except Exception as e:
    print(f"Error writing bipartite_graph_output.txt: {e}")
    raise

# Write gene mappings
try:
    with open("gene_ids.csv", "w", newline="") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(["Gene", "ID"])
        for gene, gene_id in gene_id_mapping.items():
            csvwriter.writerow([gene, gene_id])
except Exception as e:
    print(f"Error writing gene_ids.csv: {e}")
    raise

import time
import psutil


def process_components(graph):
    # Process larger components first
    components = sorted(nx.connected_components(graph), key=len, reverse=True)
    dominating_sets = []

    for component in components:
        if len(component) > 1:  # Skip isolated nodes
            subgraph = graph.subgraph(component)
            dom_set = greedy_rb_domination(subgraph, df)
            dominating_sets.extend(dom_set)

    return dominating_sets


try:
    df_home1 = pd.read_excel("./data/HOME1.xlsx", header=0)  # Read HOME1.xlsx
except Exception as e:
    print(f"Error reading HOME1.xlsx: {e}")
    raise  # Re-raise the exception after logging

# Extract specific columns from the HOME1 DataFrame
dmr_id_home1 = df_home1["DMR_No."]
closest_gene_home1 = df_home1["Gene_Symbol"]  # Updated to match HOME1 column name
area_home1 = df_home1["Confidence_Scores"]  # Updated to match HOME1 column name
enhancer_info_home1 = df_home1["ENCODE_Enhancer_Interaction(BingRen_Lab)"]

# Process the enhancer information for HOME1
df_home1["Processed_Enhancer_Info"] = df_home1[
    "ENCODE_Enhancer_Interaction(BingRen_Lab)"
].apply(process_enhancer_info)

# Create the bipartite graph for HOME1
bipartite_graph_home1 = create_bipartite_graph(df_home1, closest_gene_col="Gene_Symbol")

# Calculate the number of unique DMRs for DSS1
unique_dmrs = dmr_id.nunique()

# Calculate the number of unique genes for DSS1
all_genes = (
    df["Processed_Enhancer_Info"].explode().dropna().unique().tolist()
    + closest_gene.dropna().unique().tolist()
)
unique_genes_list = list(set(all_genes))
unique_genes = len(unique_genes_list)

# Calculate the number of unique genes for HOME1
all_genes_home1 = (
    df_home1["Processed_Enhancer_Info"].explode().dropna().unique().tolist()
    + closest_gene_home1.dropna().unique().tolist()
)
unique_genes_home1_list = list(set(all_genes_home1))
unique_genes_home1 = len(unique_genes_home1_list)

# First, create the gene ID mapping starting after the highest DMR number
dmr_nodes = df["DMR_No."].values
all_unique_genes = list(set(unique_genes_list + unique_genes_home1_list))
gene_id_start = len(dmr_nodes)  # This will be the number of DMR vertices
gene_id_mapping = {
    gene: idx + gene_id_start for idx, gene in enumerate(all_unique_genes)
}

# Open an output file to write the bipartite graph edges
try:
    with open("bipartite_graph_output.txt", "w") as file:
        # Write the number of DMRs and genes on the first line
        file.write(f"{unique_dmrs} {unique_genes}\n")

        # Get all edges and convert gene names to IDs
        edges = []
        for dmr, gene in bipartite_graph.edges():
            if isinstance(gene, str):
                gene_id = gene_id_mapping[gene]
                edges.append((dmr, gene_id))
            else:
                edges.append((dmr, gene))

        # Sort edges by DMR index first, then by gene ID
        sorted_edges = sorted(edges, key=lambda x: (x[0], x[1]))

        # Write the edges
        for dmr, gene_id in sorted_edges:
            file.write(f"{dmr} {gene_id}\n")

except Exception as e:
    print(f"Error writing bipartite_graph_output.txt: {e}")
    raise

print("Bipartite graph written to bipartite_graph_output.txt")

# Write the gene ID mapping to a CSV file for DSS1
try:
    with open("gene_ids.csv", "w", newline="") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(["Gene", "ID"])
        for gene, gene_id in gene_id_mapping.items():
            csvwriter.writerow([gene, gene_id])
except Exception as e:
    print(f"Error writing gene_ids.csv: {e}")
    raise  # Re-raise the exception after logging

print("Gene IDs written to gene_ids.csv")

# Calculate the number of unique DMRs for HOME1
unique_dmrs_home1 = dmr_id_home1.nunique()

# Calculate the number of unique genes for HOME1
all_genes_home1 = (
    df_home1["Processed_Enhancer_Info"].explode().dropna().unique().tolist()
    + closest_gene_home1.dropna().unique().tolist()
)
unique_genes_home1_list = list(set(all_genes_home1))
unique_genes_home1 = len(unique_genes_home1_list)

# Open an output file to write the bipartite graph edges for HOME1
try:
    with open("bipartite_graph_home1_output.txt", "w") as file_home1:
        # Write the number of unique DMRs and genes on the first line
        file_home1.write(f"{unique_dmrs_home1} {unique_genes_home1}\n")

        # Sort edges by DMR index first, then by gene ID
        sorted_edges_home1 = sorted(
            bipartite_graph_home1.edges(),
            key=lambda x: (
                x[0] if isinstance(x[0], int) else float("inf"),
                gene_id_mapping[x[1]] if isinstance(x[1], str) else x[1],
            ),
        )

        # Write the edges of the bipartite graph for HOME1
        for dmr, gene in sorted_edges_home1:
            if isinstance(gene, str):  # If gene is a string (gene name)
                gene_id = gene_id_mapping[gene]
                file_home1.write(f"{dmr} {gene_id}\n")
            else:  # If gene is already an ID
                file_home1.write(f"{dmr} {gene}\n")
except Exception as e:
    print(f"Error writing bipartite_graph_home1_output.txt: {e}")
    raise

print("Bipartite graph for HOME1 written to bipartite_graph_home1_output.txt")

# Create and validate HOME1 graph
bipartite_graph_home1 = create_bipartite_graph(df_home1, closest_gene_col="Gene_Symbol")
validate_bipartite_graph(bipartite_graph_home1)

# Write HOME1 graph immediately after creation and validation
try:
    with open("bipartite_graph_home1_output.txt", "w") as file_home1:
        file_home1.write(f"{unique_dmrs_home1} {unique_genes_home1}\n")
        sorted_edges_home1 = sorted(
            bipartite_graph_home1.edges(),
            key=lambda x: (
                x[0] if isinstance(x[0], int) else float("inf"),
                gene_id_mapping[x[1]] if isinstance(x[1], str) else x[1],
            ),
        )
        for dmr, gene in sorted_edges_home1:
            if isinstance(gene, str):
                gene_id = gene_id_mapping[gene]
                file_home1.write(f"{dmr} {gene_id}\n")
            else:
                file_home1.write(f"{dmr} {gene}\n")
except Exception as e:
    print(f"Error writing bipartite_graph_home1_output.txt: {e}")
    raise



def preprocess_graph(graph):
    # Remove redundant edges
    redundant = []
    for node in graph.nodes():
        if graph.nodes[node]["bipartite"] == 0:  # DMR nodes
            neighbors = set(graph.neighbors(node))
            for other in graph.nodes():
                if (
                    other != node
                    and graph.nodes[other]["bipartite"] == 0
                    and set(graph.neighbors(other)).issubset(neighbors)
                ):
                    redundant.append(other)
    graph.remove_nodes_from(redundant)
    return graph


def process_components(graph):
    components = list(nx.connected_components(graph))
    dominating_sets = []
    for component in components:
        subgraph = graph.subgraph(component)
        dom_set = greedy_rb_domination(subgraph, df)
        dominating_sets.extend(dom_set)
    return dominating_sets
def validate_bipartite_graph(B):
    """Validate the bipartite graph properties"""
    # Check for isolated nodes
    isolated = list(nx.isolates(B))
    if isolated:
        print(f"Warning: Found {len(isolated)} isolated nodes: {isolated[:5]}")
        
    # Check node degrees
    degrees = dict(B.degree())
    if min(degrees.values()) == 0:
        zero_degree_nodes = [n for n, d in degrees.items() if d == 0]
        print(f"Warning: Graph contains {len(zero_degree_nodes)} nodes with degree 0")
        print(f"First 5 zero-degree nodes: {zero_degree_nodes[:5]}")

    # Verify bipartite property
    if not nx.is_bipartite(B):
        print("Warning: Graph is not bipartite")
