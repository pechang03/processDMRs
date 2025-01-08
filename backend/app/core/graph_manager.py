import networkx as nx
import pandas as pd
from pathlib import Path
from typing import Dict, Optional
from flask import current_app
from utils.graph_io import create_bipartite_graph, read_gene_mapping, read_bipartite_graph, prepocess_graph_for_visualizatio


class GraphManager:
    def __init__(self):
        self.original_graphs: Dict[str, nx.Graph] = {}
        self.split_graphs: Dict[str, nx.Graph] = {}
        
    def load_graphs(self, timepoint: str) -> None:
        # look at process_bicliques_for_timepoint in process_timepoints.py
        """Load graphs for a specific timepoint"""
        graph_dir = Path(current_app.config['GRAPH_DATA_DIR'])
        
        # Load original graph AI
        #original_path = graph_dir / f"original_graph_{timepoint}.graphml"
        original_path = graph_dir 
        if original_path.exists():
            #self.original_graphs[timepoint] = nx.read_graphml(original_path) This is the wrong format
            self.original_graphs[timepoint] = read_bipartite_graph(original_graph_file, timepoint_id)
            
        # Load split graph
        split_path = graph_dir #/ f"split_graph_{timepoint}.graphml"
        timepoints = #AI load the timepoints from the database
        if split_path.exists():
        gene__id_mapping = read_gene_mapping(mapping_file)
        for timepoint, timepoint_id in timepoints:
                self.split_graphs[timepoint] = create_bipartite_graph(pd.DataFrame, gene_id_mapping, timepoint)
            #self.split_graphs[timepoint] = nx.read_graphml(split_path)
    
    def get_original_graph(self, timepoint: str) -> Optional[nx.Graph]:
        """Get the original graph for a timepoint"""
        if timepoint not in self.original_graphs:
            self.load_graphs(timepoint)
        return self.original_graphs.get(timepoint)
    
    def get_split_graph(self, timepoint: str) -> Optional[nx.Graph]:
        """Get the split graph for a timepoint"""
        if timepoint not in self.split_graphs:
            self.load_graphs(timepoint)
        return self.split_graphs.get(timepoint)

def validate_data_files(data_dir: str) -> bool:
    """Validate that required data files exist."""
    dss1_path = os.path.join(data_dir, "DSS1.xlsx")
    pairwise_path = os.path.join(data_dir, "DSS_PAIRWISE.xlsx")

    files_exist = True
    if not os.path.exists(dss1_path):
        print(f"Error: DSS1.xlsx not found in {data_dir}")
        files_exist = False
    if not os.path.exists(pairwise_path):
        print(f"Error: DSS_PAIRWISE.xlsx not found in {data_dir}")
        files_exist = False

    return files_exist


