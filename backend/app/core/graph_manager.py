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

@dataclass
class TimepointInfo:
    id: int
    name: str
    dmr_id_offset: int
    description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

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

    def get_graph_paths(self, timepoint_name: str) -> Tuple[str, str]:
        """Get paths for original and split graph files"""
        # Normalize timepoint name
        if timepoint_name.lower() in ["dsstimeseries", "dss_time_series"]:
            # Special case for time series
            original_graph_file = os.path.join(
                self.data_dir, "bipartite_graph_output_DSS_overall.txt"
            )
            split_graph_file = os.path.join(
                self.data_dir, "bipartite_graph_output_DSS1.txt.bicluster"
            )
        else:
            # Regular timepoint
            original_graph_file = os.path.join(
                self.data_dir, f"bipartite_graph_output_{timepoint_name}_TSS.txt"
            )
            split_graph_file = os.path.join(
                self.data_dir, f"bipartite_graph_output_{timepoint_name}.txt.bicluster"
            )

        logger.info(f"Looking for graphs at:\nOriginal: {original_graph_file}\nSplit: {split_graph_file}")
        return original_graph_file, split_graph_file

    def load_all_timepoints(self):
        """Load graphs for all timepoints from the database"""
        try:
            engine = get_db_engine()
            with Session(engine) as session:
                timepoints = session.query(Timepoint).all()
                print(f"\nLoading graphs for {len(timepoints)} timepoints...")

                # Cache timepoint data and load graphs in a single loop
                for timepoint in timepoints:
                    # Create TimepointInfo object
                    timepoint_info = TimepointInfo(
                        id=int(timepoint.id),
                        name=timepoint.name,
                        dmr_id_offset=timepoint.dmr_id_offset or 0,
                        description=timepoint.description,
                        created_at=timepoint.created_at,
                        updated_at=timepoint.updated_at
                    )
                    self.timepoints[timepoint_info.id] = timepoint_info
                    
                    try:
                        self.load_graphs(timepoint_info.id)
                    except Exception as e:
                        print(f"Error loading graphs for timepoint {timepoint_info.name}: {str(e)}")
                        continue

                logger.info(f"Cached {len(self.timepoints)} timepoint records")
        except Exception as e:
            print(f"Error loading timepoints: {str(e)}")

    def load_graphs(self, timepoint_id: int) -> None:
        """Load graphs for a specific timepoint"""
        try:
            timepoint_info = self.timepoints.get(timepoint_id)
            if not timepoint_info:
                raise ValueError(f"Timepoint {timepoint_id} not found")

            timepoint_name = (
                timepoint_info.name.replace("_TSS", "")
                if timepoint_info.name.endswith("_TSS")
                else timepoint_info.name
            )

            original_graph_file, split_graph_file = self.get_graph_paths(timepoint_name)

            # Load original graph
                if os.path.exists(original_graph_file):
                    try:
                        self.original_graphs[timepoint_id] = read_bipartite_graph(  # Use timepoint_id as key
                            original_graph_file, 
                            timepoint_name,
                            dmr_id_offset=timepoint.dmr_id_offset or 0
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
                            timepoint_name,
                            dmr_id_offset=timepoint.dmr_id_offset or 0
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

    def get_timepoint_name(self, timepoint_id: int) -> str:
        """Get timepoint name from cached mapping."""
        if timepoint_id not in self.timepoints:
            raise ValueError(f"Timepoint {timepoint_id} not found in cache")
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
