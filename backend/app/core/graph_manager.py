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
        if timepoint_name == "DSS_Time_Series":
            # Special case for time series
            original_graph_file = os.path.join(
                self.data_dir, "bipartite_graph_output_DSS_overall.txt"
            )
            split_graph_file = os.path.join(
                self.data_dir,
                "bipartite_graph_output.txt",  # Only available for first timepoint
            )
        else:
            # Regular timepoint
            original_graph_file = os.path.join(
                self.data_dir, f"bipartite_graph_output_{timepoint_name}_TSS.txt"
            )
            split_graph_file = os.path.join(
                self.data_dir, f"bipartite_graph_output_{timepoint_name}.txt.bicluster"
            )

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

                timepoint_data = TimePointSchema.model_validate(timepoint)
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
