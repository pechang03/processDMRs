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
from utils.graph_io import read_bipartite_graph, write_gene_mappings
from utils import process_enhancer_info
from data_loader import create_bipartite_graph

# from biclique_analysis import process_timepoint_data
from biclique_analysis import reader
from biclique_analysis.reader import read_bicliques_file

# from biclique_analysis.processor import create_node_metadata
from biclique_analysis.component_analyzer import ComponentAnalyzer
# from biclique_analysis.classifier import classify_component
# from biclique_analysis.triconnected import (
#    analyze_triconnected_components,
#    find_separation_pairs,
# )
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
from . import operations

from database.populate_tables import (
    populate_timepoints,
    populate_core_genes,
    populate_timepoint_genes,
    populate_dmrs,
    populate_dmr_annotations,
    populate_gene_annotations,
    populate_bicliques,
)


def get_genes_from_df(df: pd.DataFrame) -> Set[str]:
    """Extract all genes from a dataframe."""
    genes = set()

    # Get gene column
    gene_column = next(
        (
            col
            for col in ["Gene_Symbol_Nearby", "Gene_Symbol", "Gene"]
            if col in df.columns
        ),
        None,
    )
    if gene_column:
        genes.update(df[gene_column].dropna().str.strip().str.lower())

    # Get genes from enhancer/promoter info
    if "Processed_Enhancer_Info" not in df.columns:
        interaction_col = next(
            (
                col
                for col in [
                    "ENCODE_Enhancer_Interaction(BingRen_Lab)",
                    "ENCODE_Promoter_Interaction(BingRen_Lab)",
                ]
                if col in df.columns
            ),
            None,
        )

        if interaction_col:
            df["Processed_Enhancer_Info"] = df[interaction_col].apply(
                process_enhancer_info
            )

    if "Processed_Enhancer_Info" in df.columns:
        for gene_list in df["Processed_Enhancer_Info"]:
            if gene_list:
                genes.update(g.strip().lower() for g in gene_list)

    return genes


def add_split_graph_nodes(original_graph: nx.Graph, split_graph: nx.Graph):
    """Split graph into DMRs and genes."""
    # For a given timepoint the dmr_nodes and gene_nodes are the same.
    dmr_nodes = [node for node in original_graph.nodes if node in original_graph[0]]
    gene_nodes = [node for node in original_graph.nodes if node in original_graph[1]]
    split_graph.add_nodes_from(dmr_nodes, bipartite=0)
    split_graph.add_nodes_from(gene_nodes, bipartite=1)
    ## We don't add the edge yet as the are not the same between original and split graphs


def process_timepoint_table_data(
    session: Session, timepoint_id: int, df: pd.DataFrame, gene_id_mapping: dict
):
    """Process file data for a timepoint and store results in database."""
    # First populate timepoint-specific gene data
    print("Populating timepoint-specific gene data...")
    print(f"\nProcessing timepoint ID: {timepoint_id}")
    print(f"DataFrame shape: {df.shape}")
    print(f"DataFrame columns: {df.columns}")
    populate_timepoint_genes(session, gene_id_mapping, df, timepoint_id)
    populate_dmrs(
        session, df, timepoint_id=timepoint_id, gene_id_mapping=gene_id_mapping
    )


def process_bicliques_for_timepoint(
    session: Session,
    timepoint_id: int,
    original_graph_file: str,  # Add parameter for original graph file
    bicliques_file: str,
    df: pd.DataFrame,
    gene_id_mapping: dict,
    file_format: str = "gene_name",
):
    """Process bicliques for a timepoint and store results in database."""
    print("Populating timepoint-specific graph data...")
    print(f"Original graph file: {original_graph_file}")
    print(f"Bicliques file: {bicliques_file}")
    print(f"Number of genes in mapping: {len(gene_id_mapping)}")

    if not os.path.exists(bicliques_file):
        print(f"Warning: Bicliques file not found at {bicliques_file}")
        return

    if not os.path.exists(original_graph_file):
        print(f"Warning: Original graph file not found at {original_graph_file}")
        return

    # Create graphs
    # print("Creating original graph...")
    # original_graph = create_bipartite_graph(df, gene_id_mapping)
    # AI we don't need the original graph as we have the graph already
    # AI we just need to read it in from this file
    original_graph = read_bipartite_graph(original_graph_file, timepoint_id)
    print(
        f"Original graph: {len(original_graph.nodes())} nodes, {len(original_graph.edges())} edges"
    )

    print("Creating split graph...")
    split_graph = nx.Graph()

    split_graph = read_bicliques_file(
        bicliques_file, original_graph, gene_id_mapping, file_format
    )

    add_split_graph_nodes(original_graph, split_graph)
    print(f"Split graph: {len(split_graph.nodes())} nodes")

    # Process bicliques
    print("Reading bicliques file...")
    from biclique_analysis import reader

    bicliques_result = reader.read_bicliques_file(
        bicliques_file,
        original_graph,
        gene_id_mapping=gene_id_mapping,
        file_format="gene_name",
    )
    print(f"Found {len(bicliques_result['bicliques'])} bicliques")

    # First pass: Process original graph components
    for component in nx.connected_components(original_graph):
        comp_subgraph = original_graph.subgraph(component)
        from . import operations

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

        # Now populate_gene_annotations will only update annotations, not create genes
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

            # Update DMR annotations
            for dmr_id in biclique[0]:
                operations.upsert_dmr_timepoint_annotation(
                    session,
                    timepoint_id=timepoint_id,
                    dmr_id=dmr_id,
                    component_id=comp_id,
                    biclique_ids=[biclique_id],  # Now using ArrayType
                )

            # Update Gene annotations
            for gene_id in biclique[1]:
                operations.upsert_gene_timepoint_annotation(
                    session,
                    timepoint_id=timepoint_id,
                    gene_id=gene_id,
                    component_id=comp_id,
                    biclique_ids=[biclique_id],  # Now using ArrayType
                )
