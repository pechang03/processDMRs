# File graph_manager.py
# Author: Peter Shaw
# Started 8 Jan 2025
#

import os
import networkx as nx
from pathlib import Path
from typing import Dict, Optional, Tuple
from sqlalchemy.orm import Session
from flask import current_app

from backend.app.utils.graph_io import read_bipartite_graph
from backend.app.core.data_loader import create_bipartite_graph
from backend.app.database.connection import get_db_engine
from backend.app.database.models import Timepoint
from backend.app.schemas import TimePointSchema
from backend.app.core.data_loader import read_gene_mapping


import logging

logger = logging.getLogger(__name__)


class GraphManager:
    def __init__(self, config=None):
        logger.info("Initializing GraphManager")
        self.original_graphs: Dict[str, nx.Graph] = {}
        self.split_graphs: Dict[str, nx.Graph] = {}
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

                for timepoint in timepoints:
                    try:
                        self.load_graphs(timepoint.id)
                    except Exception as e:
                        print(
                            f"Error loading graphs for timepoint {timepoint.name}: {str(e)}"
                        )
                        continue
        except Exception as e:
            print(f"Error loading timepoints: {str(e)}")

    def load_graphs(self, timepoint_id: int) -> None:
        """Load graphs for a specific timepoint"""
        try:
            engine = get_db_engine()
            with Session(engine) as session:
                timepoint = session.query(Timepoint).filter(Timepoint.id == timepoint_id).first()
                if not timepoint:
                    raise ValueError(f"Timepoint {timepoint_id} not found")

                # Convert SQLAlchemy model to dict before validation
                timepoint_dict = {
                    "id": timepoint.id,
                    "name": timepoint.name,
                    "components": []  # Empty list since we don't need components here
                }
                
                timepoint_data = TimePointSchema.model_validate(timepoint_dict)
                timepoint_name = (
                    timepoint_data.name.replace("_TSS", "")
                    if timepoint_data.name.endswith("_TSS")
                    else timepoint_data.name
                )

                original_graph_file, split_graph_file = self.get_graph_paths(timepoint_name)

                # Load original graph
                if os.path.exists(original_graph_file):
                    try:
                        self.original_graphs[timepoint_name] = read_bipartite_graph(
                            original_graph_file, 
                            timepoint_name,
                            dmr_id_offset=timepoint.dmr_id_offset or 0
                        )
                        logger.info(f"Loaded original graph for {timepoint_name}")
                    except Exception as e:
                        logger.error(f"Error loading original graph for {timepoint_name}: {str(e)}")
                        return

                # Handle split graph
                if os.path.exists(split_graph_file):
                    try:
                        self.split_graphs[timepoint_name] = read_bipartite_graph(
                            split_graph_file, 
                            timepoint_name,
                            dmr_id_offset=timepoint.dmr_id_offset or 0
                        )
                        logger.info(f"Loaded split graph for {timepoint_name}")
                    except Exception as e:
                        logger.warning(f"Error loading split graph for {timepoint_name}: {str(e)}")
                        if timepoint_name in self.original_graphs:
                            logger.info(f"Creating empty split graph for {timepoint_name}")
                            # Create empty graph with same nodes but no edges
                            self.split_graphs[timepoint_name] = nx.Graph()
                            self.split_graphs[timepoint_name].add_nodes_from(
                                self.original_graphs[timepoint_name].nodes()
                            )
                else:
                    logger.warning(f"Split graph file not found: {split_graph_file}")
                    if timepoint_name in self.original_graphs:
                        logger.info(f"Creating empty split graph for {timepoint_name}")
                        # Create empty graph with same nodes but no edges
                        self.split_graphs[timepoint_name] = nx.Graph()
                        self.split_graphs[timepoint_name].add_nodes_from(
                            self.original_graphs[timepoint_name].nodes()
                        )

        except Exception as e:
            logger.error(f"Error in load_graphs for timepoint {timepoint_id}: {str(e)}")
            raise

    def get_original_graph(self, timepoint: str) -> Optional[nx.Graph]:
        """Get the original graph for a timepoint"""
        if timepoint not in self.original_graphs:
            try:
                # Find timepoint ID from name
                engine = get_db_engine()
                with Session(engine) as session:
                    tp = (
                        session.query(Timepoint)
                        .filter(Timepoint.name == timepoint)
                        .first()
                    )
                    if tp:
                        self.load_graphs(tp.id)
            except Exception as e:
                print(f"Error loading graphs for timepoint {timepoint}: {str(e)}")
                return None
        return self.original_graphs.get(timepoint)

    def get_split_graph(self, timepoint: str) -> Optional[nx.Graph]:
        """Get the split graph for a timepoint"""
        if timepoint not in self.split_graphs:
            try:
                # Find timepoint ID from name
                engine = get_db_engine()
                with Session(engine) as session:
                    tp = (
                        session.query(Timepoint)
                        .filter(Timepoint.name == timepoint)
                        .first()
                    )
                    if tp:
                        self.load_graphs(tp.id)
            except Exception as e:
                print(f"Error loading graphs for timepoint {timepoint}: {str(e)}")
                return None
        return self.split_graphs.get(timepoint)

    def clear_graphs(self):
        """Clear all loaded graphs"""
        self.original_graphs.clear()
        self.split_graphs.clear()

    def get_timepoint_name(self, timepoint_id: int) -> str:
        """Get timepoint name from ID."""
        engine = get_db_engine()
        with Session(engine) as session:
            timepoint = session.query(Timepoint).filter_by(id=timepoint_id).first()
            if not timepoint:
                raise ValueError(f"Timepoint {timepoint_id} not found")
            return timepoint.name

    def get_original_graph_component(self, timepoint_id: int, component_nodes: set) -> nx.Graph:
        """Get component subgraph from original graph."""
        try:
            timepoint_name = self.get_timepoint_name(timepoint_id)
            original_graph = self.get_original_graph(timepoint_name)
            if not original_graph:
                logger.error(f"No original graph found for timepoint {timepoint_name}")
                return None
            return original_graph.subgraph(component_nodes).copy()
        except Exception as e:
            logger.error(f"Error getting original graph component: {str(e)}")
            return None

    def get_split_graph_component(self, timepoint_id: int, component_nodes: set) -> nx.Graph:
        """Get component subgraph from split graph."""
        try:
            timepoint_name = self.get_timepoint_name(timepoint_id)
            split_graph = self.get_split_graph(timepoint_name)
            if not split_graph:
                logger.error(f"No split graph found for timepoint {timepoint_name}")
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
