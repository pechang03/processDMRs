import networkx as nx
from pathlib import Path
from typing import Dict, Optional
from flask import current_app

class GraphManager:
    def __init__(self):
        self.original_graphs: Dict[str, nx.Graph] = {}
        self.split_graphs: Dict[str, nx.Graph] = {}
        
    def load_graphs(self, timepoint: str) -> None:
        """Load graphs for a specific timepoint"""
        graph_dir = Path(current_app.config['GRAPH_DATA_DIR'])
        
        # Load original graph
        original_path = graph_dir / f"original_graph_{timepoint}.graphml"
        if original_path.exists():
            self.original_graphs[timepoint] = nx.read_graphml(original_path)
            
        # Load split graph
        split_path = graph_dir / f"split_graph_{timepoint}.graphml"
        if split_path.exists():
            self.split_graphs[timepoint] = nx.read_graphml(split_path)
    
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
