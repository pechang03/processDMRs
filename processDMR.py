import pandas as pd
import networkx as nx

# Read the Excel file into a Pandas DataFrame
# df = pd.read_excel("./data/DSS1.xlsx", header=None)  # Start with no header to inspect the data

# Print the first few rows to understand the structure
# print(df.head(10))

# Based on the output, determine the correct header row and adjust the header parameter
# For example, if the actual headers are in the second row, use header=1
df = pd.read_excel("./data/DSS1.xlsx", header=0)  # Adjust this based on your inspection

# Print the column names to verify they match your expectations
print("Column names:", df.columns)

# Extract specific columns from the DataFrame using the correct column names
dmr_id = df["DMR_No."]  # Column for DMR ID
closest_gene = df["Gene_Symbol_Nearby"]  # Column for the closest gene
area = df["Area_Stat"]  # Column for the area statistic
# additional_genes = df["Additional Genes"]  # Column for additional genes
enhancer_info = df[
    "ENCODE_Enhancer_Interaction(BingRen_Lab)"
]  # Column for enhancer information


# Function to process enhancer information
def process_enhancer_info(enhancer_str):
    if pd.isna(enhancer_str) or enhancer_str == ".":
        return []
    # Split the string by ';' and remove '/e?' from each part
    genes = enhancer_str.split(";")
    processed_genes = [gene.split("/")[0] for gene in genes]
    return processed_genes


# Apply the function to the enhancer_info column
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
print("Additional Genes:")
# print(additional_genes)
print("Processed Enhancer Info:")
print(df["Processed_Enhancer_Info"])


# Function to create a bipartite graph
def create_bipartite_graph(df):
    B = nx.Graph()
    # Add nodes with the node attribute "bipartite"
    B.add_nodes_from(df["DMR_No."], bipartite=0)  # DMRs
    for index, row in df.iterrows():
        # Add closest gene
        B.add_node(row["Gene_Symbol_Nearby"], bipartite=1)
        B.add_edge(row["DMR_No."], row["Gene_Symbol_Nearby"])
        # Add additional genes
        for gene in row["Processed_Enhancer_Info"]:
            B.add_node(gene, bipartite=1)
            B.add_edge(row["DMR_No."], gene)
    return B


# Create the bipartite graph
bipartite_graph = create_bipartite_graph(df)
import csv

# Calculate the number of unique DMRs
unique_dmrs = dmr_id.nunique()

# Calculate the number of unique genes
all_genes = (
    df["Processed_Enhancer_Info"].explode().dropna().unique().tolist()
    + closest_gene.dropna().unique().tolist()
)
unique_genes_list = list(set(all_genes))
unique_genes = len(unique_genes_list)

# Assign unique vertex IDs to each gene starting from 2110
gene_id_start = 2110
gene_id_mapping = {
    gene: idx for idx, gene in enumerate(unique_genes_list, start=gene_id_start)
}

# Create the bipartite graph
bipartite_graph = create_bipartite_graph(df)

# Open an output file to write the bipartite graph
with open("bipartite_graph_output.txt", "w") as file:
    # Write the number of DMRs and genes on the first line
    file.write(f"{unique_dmrs} {unique_genes}\n")

    # Write the edges of the bipartite graph with gene IDs
    for edge in bipartite_graph.edges():
        dmr = edge[0]
        gene = edge[1]
        gene_id = gene_id_mapping[gene]
        file.write(f"{dmr} {gene_id}\n")

print("Bipartite graph written to bipartite_graph_output.txt")

# Write the gene ID mapping to a CSV file
with open("gene_ids.csv", "w", newline="") as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(["Gene", "ID"])
    for gene, gene_id in gene_id_mapping.items():
        csvwriter.writerow([gene, gene_id])

print("Gene IDs written to gene_ids.csv")
