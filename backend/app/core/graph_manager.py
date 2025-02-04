# File graph_manager.py
# Author: Peter Shaw
# Started 8 Jan 2025
#

import os
import networkx as nx
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Set
from sqlalchemy.orm import Session
from sqlalchemy import text
from flask import current_app
from dataclasses import dataclass

from backend.app.utils.graph_io import read_bipartite_graph
from backend.app.core.data_loader import create_bipartite_graph, read_gene_mapping
from backend.app.database.connection import get_db_engine
from backend.app.database.operations import update_component_edge_classification
from backend.app.database.models import Timepoint
from backend.app.schemas import TimePointSchema


import logging

logger = logging.getLogger(__name__)


class ComponentMapping:
    """Maps components between original and split graphs"""

    def __init__(self, original_graph: nx.Graph, split_graph: nx.Graph):
        self.original_components: Dict[int, Set[int]] = {}  # component_id -> node_ids
        self.split_components: Dict[int, Set[int]] = {}  # component_id -> node_ids
        self.split_to_original: Dict[
            int, int
        ] = {}  # split_component_id -> original_component_id

        # Remove isolated nodes from both graphs
        self.original_graph = original_graph.subgraph(
            [n for n, d in original_graph.degree() if d > 0]
        )
        self.split_graph = split_graph.subgraph(
            [n for n, d in split_graph.degree() if d > 0]
        )

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

    def get_component_graphs(
        self, split_component_id: int
    ) -> Tuple[nx.Graph, nx.Graph]:
        """Get subgraphs for a component pair"""
        split_nodes = self.split_components[split_component_id]
        orig_nodes = self.get_original_component(split_component_id)

        return (
            self.original_graph.subgraph(orig_nodes),
            self.split_graph.subgraph(split_nodes),
        )


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
        self.component_mappings = {}  # Add this to store mappings per timepoint
        self.data_dir = config.get("DATA_DIR", "./data") if config else "./data"
        logger.info(f"Using data directory: {self.data_dir}")
        self.load_all_timepoints()

    def initialize_timepoint_mapping(self, timepoint_id: int) -> ComponentMapping:
        """Initialize component mapping when timepoint is selected"""
        logger.info(f"Initializing component mapping for timepoint {timepoint_id}")

        # Ensure graphs are loaded first
        self.load_graphs(timepoint_id)

        # Get the full graphs for this timepoint
        original_graph = self.get_original_graph(timepoint_id)
        split_graph = self.get_split_graph(timepoint_id)

        if not original_graph or not split_graph:
            logger.error(f"Could not load graphs for timepoint {timepoint_id}")
            raise ValueError(f"Failed to load graphs for timepoint {timepoint_id}")

        # Add detailed graph validation
        if len(original_graph.edges()) == 0:
            logger.error(f"Original graph for timepoint {timepoint_id} has no edges!")
            raise ValueError(
                f"Original graph has no edges for timepoint {timepoint_id}"
            )

        if len(split_graph.edges()) == 0:
            logger.error(f"Split graph for timepoint {timepoint_id} has no edges!")
            raise ValueError(f"Split graph has no edges for timepoint {timepoint_id}")

        logger.info(f"Creating component mapping for timepoint {timepoint_id}")
        logger.info(
            f"Original graph: {len(original_graph.nodes())} nodes, {len(original_graph.edges())} edges"
        )
        logger.info(
            f"Split graph: {len(split_graph.nodes())} nodes, {len(split_graph.edges())} edges"
        )

        # Create and store the mapping
        try:
            mapping = ComponentMapping(original_graph, split_graph)
            self.component_mappings[timepoint_id] = mapping
            logger.info(f"Component mapping created for timepoint {timepoint_id}")

            # Validate the mapping
            if not mapping.original_components or not mapping.split_components:
                logger.error(
                    f"Component mapping contains no components for timepoint {timepoint_id}"
                )
                raise ValueError(
                    f"No components found in mapping for timepoint {timepoint_id}"
                )

            logger.info(f"Found {len(mapping.original_components)} original components")
            logger.info(f"Found {len(mapping.split_components)} split components")

            return mapping

        except Exception as e:
            logger.error(f"Error creating component mapping: {str(e)}")
            raise ValueError(f"Failed to create component mapping: {str(e)}")

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
                self.data_dir,
                "bipartite_graph_output_DSS.txt.bicluster",  # Changed from DSS1 to DSS
            )
        else:
            original_graph_file = os.path.join(
                self.data_dir, f"bipartite_graph_output_{graph_name}.txt"
            )
            split_graph_file = os.path.join(
                self.data_dir,
                f"bipartite_graph_output_{timepoint_info.name}.txt.bicluster",  # Use base name for bicluster file
            )

        logger.info(
            f"Looking for graphs at:\nOriginal: {original_graph_file}\nSplit: {split_graph_file}"
        )
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
                logger.info(
                    f"Found timepoints: {[(tp.id, tp.name) for tp in timepoints]}"
                )

                # Cache timepoint data first
                for timepoint in timepoints:
                    timepoint_info = TimepointInfo(
                        id=int(timepoint.id),
                        name=timepoint.name,
                        dmr_id_offset=timepoint.dmr_id_offset or 0,
                        description=timepoint.description,
                        sheet_name=(
                            timepoint.sheet_name
                            if hasattr(timepoint, "sheet_name")
                            else None
                        ),
                    )
                    self.timepoints[int(timepoint.id)] = timepoint_info
                    logger.info(f"Cached timepoint {timepoint.id}: {timepoint.name}")

                    try:
                        self.load_graphs(int(timepoint.id))
                    except Exception as e:
                        logger.error(
                            f"Error loading graphs for timepoint {timepoint.name} (ID: {timepoint.id}): {str(e)}"
                        )
                        continue

                    # Initialize component mapping
                    try:
                        component_mapping = self.initialize_timepoint_mapping(
                            timepoint.id
                        )
                        if not component_mapping:
                            raise ValueError("Component mapping initialization failed")

                        logger.info(
                            f"Successfully initialized component mapping for timepoint {timepoint.id}"
                        )
                        logger.info(
                            f"Found {len(component_mapping.original_components)} original components"
                        )
                        logger.info(
                            f"Found {len(component_mapping.split_components)} split components"
                        )

                        # Validate the mapping
                        if (
                            not component_mapping.original_components
                            or not component_mapping.split_components
                        ):
                            raise ValueError("Component mapping contains no components")

                    except Exception as e:
                        logger.error(f"Error initializing component mapping: {str(e)}")
                        return {
                            "status": "error",
                            "message": f"Failed to initialize component mapping: {str(e)}",
                        }

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

            # Load edge details for DMRs
            engine = get_db_engine()
            with Session(engine) as session:
                # Query edge details for all DMRs in this timepoint
                edge_details = session.execute(
                    text("""
                        SELECT ed.dmr_id, ed.gene_id, g.symbol as gene_name,
                               ed.edge_type, ed.edit_type, ed.distance_from_tss
                        FROM edge_details ed
                        JOIN genes g ON ed.gene_id = g.id
                        WHERE ed.timepoint_id = :timepoint_id
                    """),
                    {"timepoint_id": timepoint_id},
                ).fetchall()

                # Group edge details by DMR
                self.dmr_edge_details = {}
                for detail in edge_details:
                    dmr_id = detail.dmr_id
                    if dmr_id not in self.dmr_edge_details:
                        self.dmr_edge_details[dmr_id] = {"edge_details": []}

                    self.dmr_edge_details[dmr_id]["edge_details"].append(
                        {
                            "gene_id": detail.gene_id,
                            "gene_name": detail.gene_name,
                            "edge_type": detail.edge_type,
                            "distance_from_tss": detail.distance_from_tss,
                            "edit_type": detail.edit_type,
                        }
                    )

            original_graph_file, split_graph_file = self.get_graph_paths(timepoint_info)

            logger.info(f"Loading graphs for timepoint {timepoint_id}")
            logger.info(f"Original graph file: {original_graph_file}")
            logger.info(f"Split graph file: {split_graph_file}")

            # Load original graph using read_bipartite_graph
            if os.path.exists(original_graph_file):
                try:
                    self.original_graphs[timepoint_id] = read_bipartite_graph(
                        original_graph_file,
                        timepoint_info.name,
                        dmr_id_offset=timepoint_info.dmr_id_offset or 0,
                    )
                    logger.info(
                        f"Loaded original graph for timepoint_id={timepoint_id}"
                    )
                    logger.info(
                        f"Original graph has {len(self.original_graphs[timepoint_id].edges())} edges"
                    )
                except Exception as e:
                    logger.error(
                        f"Error loading original graph for timepoint_id={timepoint_id}: {str(e)}"
                    )
                    return
            else:
                logger.error(f"Original graph file not found: {original_graph_file}")
                return

            # Get gene mapping from database
            engine = get_db_engine()
            with Session(engine) as session:
                from ..database.models import MasterGeneID
                from ..schemas import MasterGeneIDSchema

                # Query using SQLAlchemy model
                gene_mapping_results = session.query(MasterGeneID).all()

                # Convert to Pydantic models and create mapping
                gene_id_mapping = {
                    gene.gene_symbol.lower(): gene.id for gene in gene_mapping_results
                }

                logger.info(f"Loaded gene mapping with {len(gene_id_mapping)} entries")
                logger.info(
                    f"Sample gene mappings: {list(gene_id_mapping.items())[:5]}"
                )

            # Load split graph using read_bicliques_file
            if os.path.exists(split_graph_file):
                try:
                    from backend.app.biclique_analysis.reader import read_bicliques_file

                    bicliques_result = read_bicliques_file(
                        split_graph_file,
                        self.original_graphs[timepoint_id],
                        gene_id_mapping=gene_id_mapping,  # Pass the database gene mapping
                        file_format="gene_name",
                    )

                    # Debug logging
                    logger.info(
                        f"Read bicliques result keys: {bicliques_result.keys()}"
                    )
                    logger.info(
                        f"Found {len(bicliques_result.get('bicliques', []))} bicliques"
                    )
                    logger.info(
                        f"Bicliques result structure: {list(bicliques_result.keys()) if 'bicliques_result' in locals() else 'No result'}"
                    )

                    # Create graph from bicliques
                    split_graph = nx.Graph()
                    # Add all nodes from original graph to maintain node set consistency
                    split_graph.add_nodes_from(
                        self.original_graphs[timepoint_id].nodes(data=True)
                    )

                    # Get bicliques from the result
                    bicliques = bicliques_result["bicliques"]

                    # Add edges from bicliques with validation
                    edge_count = 0
                    for dmr_nodes, gene_nodes in bicliques:
                        # Log first few bicliques for debugging
                        if edge_count == 0:
                            logger.info(
                                f"Sample biclique - DMRs: {list(dmr_nodes)[:5]}, Genes: {list(gene_nodes)[:5]}"
                            )

                        for dmr in dmr_nodes:
                            for gene in gene_nodes:
                                split_graph.add_edge(dmr, gene)
                                edge_count += 1

                        if edge_count % 1000 == 0:
                            logger.info(f"Added {edge_count} edges so far...")

                    # Calculate and store degrees for DMR nodes
                    min_gene_id = (
                        min(gene_id_mapping.values()) if gene_id_mapping else 0
                    )

                    for node in split_graph.nodes():
                        # Only process DMR nodes (assuming DMR IDs < gene IDs)
                        if node < min_gene_id:
                            degree = split_graph.degree(node)
                            session.execute(
                                text(
                                    """
                                    UPDATE dmr_timepoint_annotations
                                    SET degree = :degree
                                    WHERE dmr_id = :dmr_id
                                    AND timepoint_id = :timepoint_id
                                """
                                ),
                                {
                                    "degree": degree,
                                    "dmr_id": node,
                                    "timepoint_id": timepoint_id,
                                },
                            )
                    session.commit()

                    self.split_graphs[timepoint_id] = split_graph
                    logger.info(f"Loaded split graph for timepoint_id={timepoint_id}")
                    logger.info(f"Split graph has {len(split_graph.edges())} edges")
                    logger.info(f"Split graph has {len(split_graph.nodes())} nodes")
                    logger.info(
                        f"Bicliques coverage: {bicliques_result.get('coverage', {})}"
                    )

                    # Validate the graph is non-empty
                    if len(split_graph.edges()) == 0:
                        raise ValueError(
                            "Split graph has no edges after processing bicliques"
                        )

                except Exception as e:
                    logger.error(
                        f"Error loading split graph for timepoint_id={timepoint_id}: {str(e)}"
                    )
                    return
            else:
                logger.error(f"Split graph file not found: {split_graph_file}")
                return

        except Exception as e:
            logger.error(f"Error in load_graphs for timepoint {timepoint_id}: {str(e)}")
            raise

    def get_original_graph(self, timepoint_id: int) -> Optional[nx.Graph]:
        """Get the original graph for a timepoint"""
        if timepoint_id not in self.original_graphs:
            try:
                self.load_graphs(timepoint_id)
            except Exception as e:
                logger.error(
                    f"Error loading graphs for timepoint_id={timepoint_id}: {str(e)}"
                )
                return None
        return self.original_graphs.get(timepoint_id)

    def get_split_graph(self, timepoint_id: int) -> Optional[nx.Graph]:
        """Get the split graph for a timepoint"""
        if timepoint_id not in self.split_graphs:
            try:
                self.load_graphs(timepoint_id)
            except Exception as e:
                logger.error(
                    f"Error loading graphs for timepoint_id={timepoint_id}: {str(e)}"
                )
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

    def get_dmr_metadata(self, timepoint_id: int) -> Dict:
        """Get DMR metadata including edge details."""
        if not hasattr(self, "dmr_edge_details"):
            return {}
        return self.dmr_edge_details

    def get_timepoint_name(self, timepoint_id: int) -> str:
        """Get timepoint name from cached mapping."""
        timepoint_id = int(timepoint_id)  # Ensure integer type
        logger.debug(f"Getting name for timepoint_id {timepoint_id}")
        logger.debug(f"Available timepoints: {list(self.timepoints.keys())}")

        if timepoint_id not in self.timepoints:
            available_ids = list(self.timepoints.keys())
            raise ValueError(
                f"Timepoint {timepoint_id} not found in cache. Available IDs: {available_ids}"
            )

        return self.timepoints[timepoint_id].name

    def get_original_graph_component(
        self, timepoint_id: int, component_nodes: set
    ) -> nx.Graph:
        """Get component subgraph from original graph."""
        try:
            original_graph = self.get_original_graph(timepoint_id)
            if not original_graph:
                logger.error(f"No original graph found for timepoint_id={timepoint_id}")
                return None

            # Create subgraph of the component nodes
            subgraph = original_graph.subgraph(component_nodes)

            # Create a new graph and copy both nodes AND edges
            component_graph = nx.Graph()
            component_graph.add_nodes_from(subgraph.nodes())
            component_graph.add_edges_from(subgraph.edges())  # This line was missing!

            logger.info(
                f"Created original graph component with {len(component_graph.nodes())} nodes and {len(component_graph.edges())} edges"
            )
            return component_graph

        except Exception as e:
            logger.error(f"Error getting original graph component: {str(e)}")
            return None

    def get_split_graph_component(
        self, timepoint_id: int, component_nodes: set
    ) -> nx.Graph:
        """Get component subgraph from split graph."""
        try:
            split_graph = self.get_split_graph(timepoint_id)
            if not split_graph:
                logger.error(f"No split graph found for timepoint_id={timepoint_id}")
                return None

            # Log full split graph stats
            logger.info(
                f"Full split graph has {len(split_graph.nodes())} nodes and {len(split_graph.edges())} edges"
            )

            # Create subgraph of the component nodes
            subgraph = split_graph.subgraph(component_nodes)

            # Log subgraph stats
            logger.info(
                f"Subgraph has {len(subgraph.nodes())} nodes and {len(subgraph.edges())} edges"
            )

            # Create a new graph and copy both nodes AND edges
            component_graph = nx.Graph()
            component_graph.add_nodes_from(subgraph.nodes())
            component_graph.add_edges_from(subgraph.edges())

            # Log final component graph stats
            logger.info(
                f"Final component graph has {len(component_graph.nodes())} nodes and {len(component_graph.edges())} edges"
            )

            return component_graph

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
