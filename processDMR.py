import pandas as pd
import networkx as nx
import csv
from graph_utils import process_enhancer_info

def greedy_rb_domination(graph, df, area_col="Area_Stat"):
    # Initialize the set of covered genes
    covered_genes = set()
    # Initialize the dominating set
    dominating_set = set()

    # Sort DMRs by degree or area/confidence interval
    dmr_nodes = sorted(
        (node for node, data in graph.nodes(data=True) if data['bipartite'] == 0),
        key=lambda node: (graph.degree(node), df.loc[df["DMR_No."] == node + 1, area_col].values[0]),
        reverse=True
    )

    # Greedily select DMRs until all genes are covered
    for dmr in dmr_nodes:
        if covered_genes >= set(graph.neighbors(dmr)):
            continue
        dominating_set.add(dmr)
        covered_genes.update(graph.neighbors(dmr))

    return dominating_set

# Read the Excel file into a Pandas DataFrame
try:
    df = pd.read_excel("./data/DSS1.xlsx", header=0)  # Adjust this based on your inspection
    print("Column names:", df.columns.tolist())  # Print the column names for verification
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
df["Processed_Enhancer_Info"] = df["ENCODE_Enhancer_Interaction(BingRen_Lab)"].apply(process_enhancer_info)

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
    B.add_nodes_from(df["DMR_No."], bipartite=0)  # Use DMR_No. directly
    for index, row in df.iterrows():
        associated_genes = set()

        # Add closest gene if it's not None
        if row[closest_gene_col] is not None:
            associated_genes.add(row[closest_gene_col])

        # Add additional genes from Processed_Enhancer_Info
        for gene in row["Processed_Enhancer_Info"]:
            if gene:  # Check if gene is not empty
                associated_genes.add(gene)

        # Add edges between the DMR and all associated genes
        for gene in associated_genes:
            B.add_node(gene, bipartite=1)
            B.add_edge(row["DMR_No."] - 1, gene)

        # Check if enhancer information is missing
        if pd.isna(row["ENCODE_Enhancer_Interaction(BingRen_Lab)"]) or row["ENCODE_Enhancer_Interaction(BingRen_Lab)"] == ".":
            if row[closest_gene_col] is not None:
                B.add_edge(row["DMR_No."] - 1, row[closest_gene_col])
    
    return B

# Create the bipartite graph for DSS1
bipartite_graph = create_bipartite_graph(df)

# Calculate min and max degrees for DSS1
degrees = dict(bipartite_graph.degree())
min_degree = min(degrees.values())
max_degree = max(degrees.values())

# Calculate the number of connected components for DSS1
num_connected_components = nx.number_connected_components(bipartite_graph)

# Calculate a greedy R-B dominating set for DSS1
dominating_set = greedy_rb_domination(bipartite_graph, df)

# Print the calculated features for DSS1
print(f"Min Degree: {min_degree}")
print(f"Max Degree: {max_degree}")
print(f"Number of Connected Components: {num_connected_components}")
print(f"Greedy R-B Dominating Set: {dominating_set}")
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
df_home1["Processed_Enhancer_Info"] = df_home1["ENCODE_Enhancer_Interaction(BingRen_Lab)"].apply(process_enhancer_info)

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

# Assign unique vertex IDs to each gene starting from one more than the maximum ID based on unique DMRs
gene_id_start = unique_dmrs + 1
all_unique_genes = list(set(unique_genes_list + unique_genes_home1_list))

# Update gene_id_mapping to include all unique genes
gene_id_mapping = {
    gene: idx for idx, gene in enumerate(all_unique_genes, start=gene_id_start)
}

# Open an output file to write the bipartite graph edges and gene ID mapping for DSS1
try:
    with open("bipartite_graph_output.txt", "w") as file:
        # Write the number of DMRs and genes on the first line
        file.write(f"{unique_dmrs} {unique_genes}\n")

        # Write the edges of the bipartite graph with gene IDs for DSS1
        for edge in bipartite_graph.edges():
            dmr = edge[0] - 1  # Subtract 1 from the DMR number
            gene = edge[1]
            gene_id = gene_id_mapping[gene]
            file.write(f"{dmr} {gene_id}\n")
except Exception as e:
    print(f"Error writing bipartite_graph_output.txt: {e}")
    raise  # Re-raise the exception after logging

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

        # Write the edges of the bipartite graph for HOME1
        for edge in bipartite_graph_home1.edges():
            dmr = edge[0] - 1  # Subtract 1 from the DMR number
            gene = edge[1]
            gene_id = gene_id_mapping[gene]  # Ensure gene_id is always found
            file_home1.write(f"{dmr} {gene_id}\n")
except Exception as e:
    print(f"Error writing bipartite_graph_home1_output.txt: {e}")
    raise  # Re-raise the exception after logging

print("Bipartite graph for HOME1 written to bipartite_graph_home1_output.txt")

# Calculate min and max degrees for HOME1
degrees_home1 = dict(bipartite_graph_home1.degree())
min_degree_home1 = min(degrees_home1.values())
max_degree_home1 = max(degrees_home1.values())

# Calculate the number of connected components for HOME1
num_connected_components_home1 = nx.number_connected_components(bipartite_graph_home1)

# Calculate a greedy R-B dominating set for HOME1
dominating_set_home1 = greedy_rb_domination(bipartite_graph_home1, df_home1, area_col="Confidence_Scores")

# Print the calculated features for HOME1
print(f"Min Degree (HOME1): {min_degree_home1}")
print(f"Max Degree (HOME1): {max_degree_home1}")
print(f"Number of Connected Components (HOME1): {num_connected_components_home1}")
print(f"Greedy R-B Dominating Set (HOME1): {dominating_set_home1}")
