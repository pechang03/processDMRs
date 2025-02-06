import os

# Gene ID threshold
START_GENE_ID = 100000  # All gene IDs will start from this number

# Directory paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")  # Simplified to just 'data' directory

# File paths
DSS1_FILE = os.path.join(DATA_DIR, "DSS1.xlsx")
DSS_PAIRWISE_FILE = os.path.join(DATA_DIR, "DSS_PAIRWISE.xlsx")

# Biclique file templates
BIPARTITE_GRAPH_TEMPLATE = os.path.join(DATA_DIR, "bipartite_graph_output_{}.txt.biclusters")
BIPARTITE_GRAPH_OVERALL = os.path.join(DATA_DIR, "bipartite_graph_output.txt.biclusters")
