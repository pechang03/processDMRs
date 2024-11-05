import pandas as pd
import networkx as nx
import csv
from graph_utils import process_enhancer_info

def greedy_rb_domination(graph, df, area_col=None):
    # Initialize the dominating set
    dominating_set = set()
    
    # Get all gene nodes (bipartite=1)
    gene_nodes = set(node for node, data in graph.nodes(data=True) if data['bipartite'] == 1)
    
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
        if not any(remaining_graph.nodes[n]['bipartite'] == 1 for n in component):
            continue
            
        # Get DMR nodes in this component
        dmr_nodes = [node for node in component 
                    if remaining_graph.nodes[node]['bipartite'] == 0]
        
        if dmr_nodes:  # If there are DMR nodes in this component
            # Add weight-based selection
            def get_node_weight(node):
                degree = len(set(graph.neighbors(node)))
                area = df.loc[node, area_col] if area_col else 1.0
                return degree * area

            # Modify selection strategy
            best_dmr = max(dmr_nodes, 
                           key=lambda x: (len(set(remaining_graph.neighbors(x))), 
                                        get_node_weight(x)))
            dominating_set.add(best_dmr)

    return dominating_set

# Read the Excel file into a Pandas DataFrame
try:
    df = pd.read_excel("./data/DSS1.xlsx", header=0)  # Adjust this based on your inspection
    print("Column names:", df.columns.tolist())  # Print the column names for verification
    print("\nSample of input data:")
    print(df[['DMR_No.', 'Gene_Symbol_Nearby', 'ENCODE_Enhancer_Interaction(BingRen_Lab)']].head(10))
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
    dmr_nodes = df["DMR_No."].values
    
    # Add DMR nodes with explicit bipartite attribute
    for dmr in dmr_nodes:
        B.add_node(dmr - 1, bipartite=0)  # Subtract 1 to convert to 0-based indexing
    
    # Add debugging
    print(f"\nDebugging create_bipartite_graph:")
    print(f"Number of DMR nodes added: {len(dmr_nodes)}")
    
    batch_size = 1000
    total_edges = 0
    dmrs_without_edges = set(dmr - 1 for dmr in dmr_nodes)  # Track DMRs that haven't received any edges
    
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        for _, row in batch.iterrows():
            dmr = row["DMR_No."] - 1  # Convert to 0-based indexing
            associated_genes = set()
            
            # Debug closest gene handling
            if pd.notna(row[closest_gene_col]) and row[closest_gene_col]:
                associated_genes.add(row[closest_gene_col])
                print(f"DMR {dmr} has closest gene: {row[closest_gene_col]}")
            else:
                print(f"Warning: DMR {dmr} has no closest gene")
            
            # Debug enhancer genes handling
            if isinstance(row["Processed_Enhancer_Info"], (list, set)):
                enhancer_genes = set(
                    gene for gene in row["Processed_Enhancer_Info"] 
                    if pd.notna(gene) and gene
                )
                if enhancer_genes:
                    associated_genes.update(enhancer_genes)
                    print(f"DMR {dmr} has enhancer genes: {enhancer_genes}")
            
            # Add edges and track them
            if associated_genes:
                for gene in associated_genes:
                    if not B.has_node(gene):
                        B.add_node(gene, bipartite=1)
                    B.add_edge(dmr, gene)
                    total_edges += 1
                dmrs_without_edges.discard(dmr)  # Remove DMR from tracking set
            else:
                print(f"Warning: DMR {dmr} has no associated genes")
    
    print(f"Total edges added: {total_edges}")
    print(f"Final graph: {len(B.nodes())} nodes, {len(B.edges())} edges")
    
    # Check for nodes with degree 0
    zero_degree_nodes = [node for node in B.nodes() if B.degree(node) == 0]
    if zero_degree_nodes:
        print(f"Found {len(zero_degree_nodes)} nodes with degree 0:")
        print(f"First 5 zero-degree nodes: {zero_degree_nodes[:5]}")
        print(f"Node types of zero-degree nodes: {[B.nodes[node].get('bipartite') for node in zero_degree_nodes[:5]]}")
    
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
        if graph.nodes[node]['bipartite'] == 0:  # DMR nodes
            neighbors = set(graph.neighbors(node))
            for other in graph.nodes():
                if (other != node and 
                    graph.nodes[other]['bipartite'] == 0 and
                    set(graph.neighbors(other)).issubset(neighbors)):
                    redundant.append(other)
    graph.remove_nodes_from(redundant)
    return graph

# Preprocess the bipartite graph for DSS1
bipartite_graph = preprocess_graph(create_bipartite_graph(df))

# Calculate min and max degrees for DSS1
degrees = dict(bipartite_graph.degree())
min_degree = min(degrees.values())
max_degree = max(degrees.values())

# Calculate the number of connected components for DSS1
num_connected_components = nx.number_connected_components(bipartite_graph)

import time
import psutil

def process_components(graph):
    # Process larger components first
    components = sorted(nx.connected_components(graph), 
                      key=len, reverse=True)
    dominating_sets = []
    
    for component in components:
        if len(component) > 1:  # Skip isolated nodes
            subgraph = graph.subgraph(component)
            dom_set = greedy_rb_domination(subgraph, df)
            dominating_sets.extend(dom_set)
            
    return dominating_sets

# Calculate a greedy R-B dominating set for DSS1
start_time = time.time()
dominating_set = process_components(bipartite_graph)
end_time = time.time()

# Print the calculated features for DSS1
print(f"Min Degree: {min_degree}")
print(f"Max Degree: {max_degree}")
print(f"Average Degree: {sum(degrees.values()) / len(degrees)}")
print(f"Number of Connected Components: {num_connected_components}")
print(f"Size of Greedy R-B Dominating Set: {len(dominating_set)}")
process = psutil.Process()
memory_info = process.memory_info()
print(f"Execution Time for DSS1: {end_time - start_time} seconds")
print(f"Memory Usage for DSS1: {memory_info.rss} bytes")
print(f"Memory Usage per Node: {memory_info.rss / len(bipartite_graph.nodes())} bytes")
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

        # Sort edges by DMR index first, then by gene ID
        sorted_edges = sorted(bipartite_graph.edges(), 
                            key=lambda x: (x[0] if isinstance(x[0], int) else float('inf'), 
                                         gene_id_mapping[x[1]] if isinstance(x[1], str) else x[1]))
        
        # Write the edges of the bipartite graph with gene IDs for DSS1
        for dmr, gene in sorted_edges:
            if isinstance(gene, str):  # If gene is a string (gene name)
                gene_id = gene_id_mapping[gene]
                file.write(f"{dmr} {gene_id}\n")
            else:  # If gene is already an ID
                file.write(f"{dmr} {gene}\n")
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
        sorted_edges_home1 = sorted(bipartite_graph_home1.edges(), 
                                   key=lambda x: (x[0] if isinstance(x[0], int) else float('inf'), 
                                                gene_id_mapping[x[1]] if isinstance(x[1], str) else x[1]))
        
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

# Preprocess the bipartite graph for HOME1
bipartite_graph_home1 = preprocess_graph(create_bipartite_graph(df_home1, closest_gene_col="Gene_Symbol"))

# Calculate min and max degrees for HOME1
degrees_home1 = dict(bipartite_graph_home1.degree())
min_degree_home1 = min(degrees_home1.values())
max_degree_home1 = max(degrees_home1.values())

# Calculate the number of connected components for HOME1
num_connected_components_home1 = nx.number_connected_components(bipartite_graph_home1)

# Calculate a greedy R-B dominating set for HOME1
start_time = time.time()
dominating_set_home1 = process_components(bipartite_graph_home1)
end_time = time.time()

# Print the calculated features for HOME1
print(f"Min Degree (HOME1): {min_degree_home1}")
print(f"Max Degree (HOME1): {max_degree_home1}")
print(f"Average Degree (HOME1): {sum(degrees_home1.values()) / len(degrees_home1)}")
print(f"Number of Connected Components (HOME1): {num_connected_components_home1}")
print(f"Size of Greedy R-B Dominating Set (HOME1): {len(dominating_set_home1)}")
process = psutil.Process()
memory_info = process.memory_info()
print(f"Execution Time for HOME1: {end_time - start_time} seconds")
print(f"Memory Usage for HOME1: {memory_info.rss} bytes")
print(f"Memory Usage per Node (HOME1): {memory_info.rss / len(bipartite_graph_home1.nodes())} bytes")
def preprocess_graph(graph):
    # Remove redundant edges
    redundant = []
    for node in graph.nodes():
        if graph.nodes[node]['bipartite'] == 0:  # DMR nodes
            neighbors = set(graph.neighbors(node))
            for other in graph.nodes():
                if (other != node and 
                    graph.nodes[other]['bipartite'] == 0 and
                    set(graph.neighbors(other)).issubset(neighbors)):
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
