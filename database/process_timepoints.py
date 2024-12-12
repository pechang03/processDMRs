# file process_timepoints.py
# Author: Peter Shaw
#
import os
import sys
from typing import Dict, List, Set, Tuple
import pandas as pd
import networkx as nx
import numpy as np

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base

# from utils.constants import DSS1_FILE, DSS_PAIRWISE_FILE, BIPARTITE_GRAPH_TEMPLATE
from database.operations import insert_component
from utils import id_mapping, constants
from utils import node_info, edge_info
from utils.graph_io import write_gene_mappings
from utils import process_enhancer_info

from data_loader import create_bipartite_graph
from biclique_analysis import process_timepoint_data
from biclique_analysis import reader
from biclique_analysis.processor import create_node_metadata
from biclique_analysis.component_analyzer import ComponentAnalyzer
from biclique_analysis.classifier import classify_component
from biclique_analysis.triconnected import (
    analyze_triconnected_components,
    find_separation_pairs,
)
# from biclique_analysis.component_analyzer import Analyzer, ComponentAnalyzer

from database.models import (
    ComponentBiclique,
    Relationship,
    Metadata,
    Statistic,
    Biclique,
    Component,
    DMR,
    Gene,
    Timepoint,
)
from .operations import insert_component

from database.populate_tables import (
    populate_timepoints,
    populate_genes,
    populate_dmrs,
    populate_dmr_annotations,
    populate_gene_annotations,
    populate_bicliques,
)

def add_split_graph_nodes(original_graph: nx.Graph, split_graph: nx.Graph):
    """Split graph into DMRs and genes."""
    # For a given timepoint the dmr_nodes and gene_nodes are the same.
    dmr_nodes = [node for node in original_graph.nodes if node in original_graph[0]]
    gene_nodes = [node for node in original_graph.nodes if node in original_graph[1]]
    split_graph.add_nodes_from(dmr_nodes, bipartite=0)
    split_graph.add_nodes_from(gene_nodes, bipartite=:np.who()1)
    ## We don't add the edge yet as the are not the same between original and split graphs

def process_bicliques_for_timepoint(
    session: Session,
    timepoint_id: int,
    bicliques_file: str,
    df: pd.DataFrame,
    gene_id_mapping: dict,
):
    """Process bicliques for a timepoint and store results in database."""

    # Create graphs
    original_graph = create_bipartite_graph(df, gene_id_mapping)
    split_graph = nx.Graph()
    add_split_graph_nodes(original_graph, split_graph)

    # Process bicliques
    bicliques_result = reader.read_bicliques_file(
        bicliques_file,
        original_graph,
        gene_id_mapping=gene_id_mapping,
        file_format="gene_name",
    )

    # Create analyzer
    analyzer = ComponentAnalyzer(original_graph, bicliques_result, split_graph)

    # First pass: Process original graph components
    for component in nx.connected_components(original_graph):
        comp_subgraph = original_graph.subgraph(component)
        comp_id = operations.insert_component(
            session,
            timepoint_id=timepoint_id,
            graph_type="original",
            # ... other component fields ...
        )

        # Populate annotations for this component
        populate_dmr_annotations(
            session=session,
            timepoint_id=timepoint_id,
            component_id=comp_id,
            graph=comp_subgraph,
            df=df,
            is_original=True,
        )

        populate_gene_annotations(
            session=session,
            timepoint_id=timepoint_id,
            component_id=comp_id,
            graph=comp_subgraph,
            df=df,
            is_original=True,
        )

    # Second pass: Process split graph components and bicliques
    for component in nx.connected_components(split_graph):
        comp_subgraph = split_graph.subgraph(component)
        comp_bicliques = [
            b
            for b in bicliques_result["bicliques"]
            if any(n in component for n in b[0] | b[1])
        ]

        comp_id = operations.insert_component(
            session,
            timepoint_id=timepoint_id,
            graph_type="split",
            # ... other component fields ...
        )

        # Populate bicliques for this component
        for biclique in comp_bicliques:
            biclique_id = populate_bicliques(
                session,
                timepoint_id=timepoint_id,
                component_id=comp_id,
                dmr_nodes=biclique[0],
                gene_nodes=biclique[1],
            )

        # Update annotations with biclique information
        populate_dmr_annotations(
            session=session,
            timepoint_id=timepoint_id,
            component_id=comp_id,
            graph=comp_subgraph,
            bicliques=comp_bicliques,
            df=df,
            is_original=False,
        )

        populate_gene_annotations(
            session=session,
            timepoint_id=timepoint_id,
            component_id=comp_id,
            graph=comp_subgraph,
            bicliques=comp_bicliques,
            df=df,
            is_original=False,
        )
