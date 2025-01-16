# File graph_manager.py
# Author: Peter Shaw
# Started 8 Jan 2025
#

import os
import networkx as nx
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from sqlalchemy.orm import Session
from flask import current_app
from dataclasses import dataclass
from typing import Dict, Set, Tuple
import networkx as nx

class ComponentMapping:
    """Maps components between original and split graphs"""
    def __init__(self, original_graph: nx.Graph, split_graph: nx.Graph):
        self.original_components: Dict[int, Set[int]] = {}  # component_id -> node_ids
        self.split_components: Dict[int, Set[int]] = {}     # component_id -> node_ids
        self.split_to_original: Dict[int, int] = {}         # split_component_id -> original_component_id
        
        # Remove isolated nodes from both graphs
        self.original_graph = original_graph.subgraph([n for n, d in original_graph.degree() if d > 0])
        self.split_graph = split_graph.subgraph([n for n, d in split_graph.degree() if d > 0])
        
        # Get components
        self._compute_components()
        
    def _compute_components(self):
        """Compute components and establish mapping between them"""
        # Get connected components
        orig_components = list(nx.connected_components(self.original_graph))
        split_components = list(nx.connected_components(self.split_graph))
        
        # Store components with IDs
        for i, comp in enumerate(orig_components):
            self.original_components[i] = comp
            
        for i, comp in enumerate(split_components):
            self.split_components[i] = comp
            
        # Map split components to original components
        for split_id, split_nodes in self.split_components.items():
            # Find which original component contains these nodes
            for orig_id, orig_nodes in self.original_components.items():
                if split_nodes.issubset(orig_nodes):
                    self.split_to_original[split_id] = orig_id
                    break
                    
    def get_original_component(self, split_component_id: int) -> Set[int]:
        """Get the original component containing a split component"""
        orig_id = self.split_to_original.get(split_component_id)
        return self.original_components.get(orig_id, set())
        
    def categorize_edges(self, split_component_id: int) -> Dict[str, Set[Tuple[int, int]]]:
        """Categorize edges for a split component"""
        split_nodes = self.split_components[split_component_id]
        orig_nodes = self.get_original_component(split_component_id)
        
        # Get subgraphs for the components
        split_subgraph = self.split_graph.subgraph(split_nodes)
        orig_subgraph = self.original_graph.subgraph(orig_nodes)
        
        # Categorize edges
        permanent = set()
        false_positive = set()
        false_negative = set()
        
        # Check edges in original graph
        for u, v in orig_subgraph.edges():
            edge = (min(u,v), max(u,v))
            if split_subgraph.has_edge(u, v):
                permanent.add(edge)
            else:
                false_positive.add(edge)
                
        # Check edges in split graph
        for u, v in split_subgraph.edges():
            edge = (min(u,v), max(u,v))
            if not orig_subgraph.has_edge(u, v):
                false_negative.add(edge)
                
        return {
            "permanent": permanent,
            "false_positive": false_positive,
            "false_negative": false_negative
        }

@dataclass
class TimepointInfo:
    id: int
    name: str
    dmr_id_offset: int
    sheet_name: Optional[str] = None
    description: Optional[str] = None

    def get_graph_name(self) -> str:
        """Get the name to use for graph files"""
        if self.sheet_name:
            return self.sheet_name
        return f"{self.name}_TSS"

from backend.app.utils.graph_io import read_bipartite_graph
from backend.app.core.data_loader import create_bipartite_graph
from backend.app.database.connection import get_db_engine
from backend.app.database.models import Timepoint
from backend.app.schemas import TimePointSchema
from backend.app.core.data_loader import read_gene_mapping


import logging

logger = logging.getLogger(__name__)


class GraphManager:
    original_graphs: Dict[int, nx.Graph]
    split_graphs: Dict[int, nx.Graph] 
    timepoints: Dict[int, TimepointInfo]  # Change type annotation
    data_dir: str

    def __init__(self, config=None):
        logger.info("Initializing GraphManager")
        self.original_graphs = {}
        self.split_graphs = {}
        self.timepoints = {}  # Add timepoint mapping cache
        self.data_dir = config.get("DATA_DIR", "./data") if config else "./data"
        logger.info(f"Using data directory: {self.data_dir}")
        self.load_all_timepoints()

    @classmethod
    def get_instance(cls):
        """Get or create GraphManager instance"""
        if not hasattr(current_app, "graph_manager"):
            current_app.graph_manager = cls()
        return current_app.graph_manager

    def is_initialized(self):
        """Check if GraphManager is properly initialized"""
        return bool(self.data_dir and hasattr(self, "original_graphs"))

    def get_graph_paths(self, timepoint_info: TimepointInfo) -> Tuple[str, str]:
        """Get paths for original and split graph files"""
        graph_name = timepoint_info.get_graph_name()
        
        if timepoint_info.name.lower() in ["dsstimeseries", "dss_time_series"]:
            original_graph_file = os.path.join(
                self.data_dir, "bipartite_graph_output_DSS_overall.txt"
            )
            split_graph_file = os.path.join(
                self.data_dir, "bipartite_graph_output_DSS1.txt.bicluster"
            )
        else:
            original_graph_file = os.path.join(
                self.data_dir, f"bipartite_graph_output_{graph_name}.txt"
            )
            split_graph_file = os.path.join(
                self.data_dir, f"bipartite_graph_output_{timepoint_info.name}.txt.bicluster"
            )

        logger.info(f"Looking for graphs at:\nOriginal: {original_graph_file}\nSplit: {split_graph_file}")
        return original_graph_file, split_graph_file

    def load_all_timepoints(self):
        """Load graphs for all timepoints from the database"""
        try:
            engine = get_db_engine()
            with Session(engine) as session:
                # Get all timepoints with complete information
                timepoints = session.query(Timepoint).all()
                print(f"\nLoading graphs for {len(timepoints)} timepoints...")

                # Debug logging
                logger.info(f"Found timepoints: {[(tp.id, tp.name) for tp in timepoints]}")

                # Cache timepoint data first
                for timepoint in timepoints:
                    timepoint_info = TimepointInfo(
                        id=int(timepoint.id),
                        name=timepoint.name,
                        dmr_id_offset=timepoint.dmr_id_offset or 0,
                        description=timepoint.description,
                        sheet_name=timepoint.sheet_name if hasattr(timepoint, 'sheet_name') else None
                    )
                    self.timepoints[int(timepoint.id)] = timepoint_info
                    logger.info(f"Cached timepoint {timepoint.id}: {timepoint.name}")

                    try:
                        self.load_graphs(int(timepoint.id))
                    except Exception as e:
                        logger.error(f"Error loading graphs for timepoint {timepoint.name} (ID: {timepoint.id}): {str(e)}")
                        continue

                logger.info(f"Cached {len(self.timepoints)} timepoint records")
                logger.info(f"Available timepoint IDs: {list(self.timepoints.keys())}")

        except Exception as e:
            logger.error(f"Error loading timepoints: {str(e)}")
            raise

    def load_graphs(self, timepoint_id: int) -> None:
        """Load graphs for a specific timepoint"""
        try:
            timepoint_info = self.timepoints.get(timepoint_id)
            if not timepoint_info:
                raise ValueError(f"Timepoint {timepoint_id} not found")

            original_graph_file, split_graph_file = self.get_graph_paths(timepoint_info)

            # Load original graph
            if os.path.exists(original_graph_file):
                try:
                    self.original_graphs[timepoint_id] = read_bipartite_graph(  # Use timepoint_id as key
                        original_graph_file, 
                        timepoint_info.name,
                        dmr_id_offset=timepoint_info.dmr_id_offset or 0
                    )
                    logger.info(f"Loaded original graph for timepoint_id={timepoint_id}")
                except Exception as e:
                    logger.error(f"Error loading original graph for timepoint_id={timepoint_id}: {str(e)}")
                    return

            # Handle split graph
            if os.path.exists(split_graph_file):
                try:
                    self.split_graphs[timepoint_id] = read_bipartite_graph(  # Use timepoint_id as key
                        split_graph_file, 
                        timepoint_info.name,
                        dmr_id_offset=timepoint_info.dmr_id_offset or 0
                    )
                    logger.info(f"Loaded split graph for timepoint_id={timepoint_id}")
                except Exception as e:
                    logger.warning(f"Error loading split graph for timepoint_id={timepoint_id}: {str(e)}")
                    if timepoint_id in self.original_graphs:
                        logger.info(f"Creating empty split graph for timepoint_id={timepoint_id}")
                        self.split_graphs[timepoint_id] = nx.Graph()
                        self.split_graphs[timepoint_id].add_nodes_from(
                            self.original_graphs[timepoint_id].nodes()
                        )
            else:
                logger.warning(f"Split graph file not found: {split_graph_file}")
                if timepoint_id in self.original_graphs:
                    logger.info(f"Creating empty split graph for timepoint_id={timepoint_id}")
                    self.split_graphs[timepoint_id] = nx.Graph()
                    self.split_graphs[timepoint_id].add_nodes_from(
                        self.original_graphs[timepoint_id].nodes()
                    )

        except Exception as e:
            logger.error(f"Error in load_graphs for timepoint {timepoint_id}: {str(e)}")
            raise

    def get_original_graph(self, timepoint_id: int) -> Optional[nx.Graph]:
        """Get the original graph for a timepoint"""
        if timepoint_id not in self.original_graphs:
            try:
                self.load_graphs(timepoint_id)
            except Exception as e:
                logger.error(f"Error loading graphs for timepoint_id={timepoint_id}: {str(e)}")
                return None
        return self.original_graphs.get(timepoint_id)

    def get_split_graph(self, timepoint_id: int) -> Optional[nx.Graph]:
        """Get the split graph for a timepoint"""
        if timepoint_id not in self.split_graphs:
            try:
                self.load_graphs(timepoint_id)
            except Exception as e:
                logger.error(f"Error loading graphs for timepoint_id={timepoint_id}: {str(e)}")
                return None
        return self.split_graphs.get(timepoint_id)

    def clear_graphs(self):
        """Clear all loaded graphs"""
        self.original_graphs.clear()
        self.split_graphs.clear()
        
    def load_timepoint_components(self, timepoint_id: int) -> ComponentMapping:
        """Load and map components for a timepoint"""
        original_graph = self.get_original_graph(timepoint_id)
        split_graph = self.get_split_graph(timepoint_id)
        
        if not original_graph or not split_graph:
            raise ValueError(f"Graphs not found for timepoint {timepoint_id}")
            
        return ComponentMapping(original_graph, split_graph)

    def get_timepoint_name(self, timepoint_id: int) -> str:
        """Get timepoint name from cached mapping."""
        timepoint_id = int(timepoint_id)  # Ensure integer type
        logger.debug(f"Getting name for timepoint_id {timepoint_id}")
        logger.debug(f"Available timepoints: {list(self.timepoints.keys())}")
        
        if timepoint_id not in self.timepoints:
            available_ids = list(self.timepoints.keys())
            raise ValueError(f"Timepoint {timepoint_id} not found in cache. Available IDs: {available_ids}")
        
        return self.timepoints[timepoint_id].name

    def get_original_graph_component(self, timepoint_id: int, component_nodes: set) -> nx.Graph:
        """Get component subgraph from original graph."""
        try:
            original_graph = self.get_original_graph(timepoint_id)  # Use timepoint_id directly
            if not original_graph:
                logger.error(f"No original graph found for timepoint_id={timepoint_id}")
                return None
            return original_graph.subgraph(component_nodes).copy()
        except Exception as e:
            logger.error(f"Error getting original graph component: {str(e)}")
            return None

    def get_split_graph_component(self, timepoint_id: int, component_nodes: set) -> nx.Graph:
        """Get component subgraph from split graph."""
        try:
            split_graph = self.get_split_graph(timepoint_id)  # Use timepoint_id directly
            if not split_graph:
                logger.error(f"No split graph found for timepoint_id={timepoint_id}")
                return None
            return split_graph.subgraph(component_nodes).copy()
        except Exception as e:
            logger.error(f"Error getting split graph component: {str(e)}")
            return None

    def validate_component_graphs(self, original_nodes: set, split_nodes: set) -> bool:
        """Validate that component nodes match between graphs."""
        if not original_nodes or not split_nodes:
            return False
        
        if original_nodes != split_nodes:
            logger.warning(
                f"Node mismatch in component: "
                f"Original has {len(original_nodes)} nodes, "
                f"Split has {len(split_nodes)} nodes. "
                f"Difference: {original_nodes.symmetric_difference(split_nodes)}"
            )
            return False
        return True
