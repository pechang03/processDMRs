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
    """
    Add nodes from original graph to split graph, preserving bipartite structure.

    Args:
        original_graph: Source graph with bipartite node attributes
        split_graph: Target graph to add nodes to

    Returns:
        Tuple[int, int]: Count of (dmr_nodes, gene_nodes) added
    """
    try:
        print("\nAdding nodes to split graph...")

        # Get nodes by type using bipartite attribute
        dmr_nodes = set()
        gene_nodes = set()

        for node, data in original_graph.nodes(data=True):
            bipartite_value = data.get("bipartite")
            if bipartite_value == 0:
                dmr_nodes.add(node)
            elif bipartite_value == 1:
                gene_nodes.add(node)
            else:
                print(
                    f"Warning: Node {node} has invalid bipartite value: {bipartite_value}"
                )

        # Add nodes with their attributes
        if dmr_nodes:
            split_graph.add_nodes_from(dmr_nodes, bipartite=0)
        if gene_nodes:
            split_graph.add_nodes_from(gene_nodes, bipartite=1)

        print(f"Added {len(dmr_nodes)} DMR nodes and {len(gene_nodes)} gene nodes")
        return len(dmr_nodes), len(gene_nodes)

    except Exception as e:
        print(f"Error adding nodes to split graph:")
        print(f"- Type: {type(e).__name__}")
        print(f"- Details: {str(e)}")
        import traceback

        print("- Stack trace:")
        traceback.print_exc()
        return 0, 0  # Return zeros to indicate failure


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
    timepoint_name: str,
    original_graph_file: str,
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
    print("Loading original graph...")
    original_graph = read_bipartite_graph(original_graph_file, timepoint=timepoint_name)
    print(
        f"Original graph: {len(original_graph.nodes())} nodes, {len(original_graph.edges())} edges"
    )

    # Process connected components in original graph first
    print("\nProcessing connected components in original graph...")
    for comp_idx, component in enumerate(nx.connected_components(original_graph)):
        comp_subgraph = original_graph.subgraph(component)
        
        # Insert component
        comp_id = insert_component(
            session=session,
            timepoint_id=timepoint_id,
            graph_type='original',
            size=len(component),
            dmr_count=len([n for n in component if original_graph.nodes[n]['bipartite'] == 0]),
            gene_count=len([n for n in component if original_graph.nodes[n]['bipartite'] == 1]),
            edge_count=comp_subgraph.number_of_edges(),
            density=2.0 * comp_subgraph.number_of_edges() / (len(component) * (len(component) - 1)) if len(component) > 1 else 0
        )

        # Tag nodes with component ID
        for node in component:
            original_graph.nodes[node]['component_id'] = comp_id

        # Process triconnected components for this component
        process_triconnected_components(
            session=session,
            timepoint_id=timepoint_id,
            original_graph=original_graph,
            component_id=comp_id,
            df=df
        )

    # Continue with biclique processing...
    from database.biclique_processor import process_bicliques_db
    bicliques_result = process_bicliques_db(
        session=session,
        timepoint_id=timepoint_id,
        timepoint_name=timepoint_name,
        original_graph=original_graph,
        bicliques_file=bicliques_file,
        df=df,
        gene_id_mapping=gene_id_mapping,
        file_format=file_format,
    )

    print(f"Processed {len(bicliques_result.get('bicliques', []))} bicliques")
def process_triconnected_components(
    session: Session,
    timepoint_id: int,
    original_graph: nx.Graph,
    component_id: int,
    df: pd.DataFrame
) -> None:
    """Process and store triconnected components for the original graph."""
    from biclique_analysis.triconnected import analyze_triconnected_components
    from biclique_analysis.edge_classification import classify_edges
    from .operations import insert_triconnected_component

    print(f"\nAnalyzing triconnected components for component {component_id}...")
    
    # Get component subgraph
    component_nodes = {
        node for node in original_graph.nodes() 
        if original_graph.nodes[node].get('component_id') == component_id
    }
    subgraph = original_graph.subgraph(component_nodes)
    
    # Analyze triconnected components
    tricomps, stats, avg_dmrs, avg_genes, is_simple = analyze_triconnected_components(subgraph)
    
    print(f"Found {len(tricomps)} triconnected components")
    print(f"Stats: {stats}")

    # Process each triconnected component
    for idx, nodes in enumerate(tricomps):
        # Get component subgraph
        tri_subgraph = original_graph.subgraph(nodes)
        
        # Calculate basic metrics
        dmr_nodes = {n for n in nodes if original_graph.nodes[n]['bipartite'] == 0}
        gene_nodes = {n for n in nodes if original_graph.nodes[n]['bipartite'] == 1}
        
        # Find separation pairs and convert to list format
        from biclique_analysis.triconnected import find_separation_pairs
        separation_pairs = find_separation_pairs(tri_subgraph)
        separation_pairs_list = [sorted(list(pair)) for pair in separation_pairs] if separation_pairs else []
        
        # Convert all sets to sorted lists for database storage
        nodes_list = sorted(list(nodes))
        dmr_ids_list = sorted(list(dmr_nodes))
        gene_ids_list = sorted(list(gene_nodes))
        
        # Determine category based on composition
        from biclique_analysis.classifier import classify_component
        category = classify_component(dmr_nodes, gene_nodes, []).name.lower()

        # Insert triconnected component with properly formatted data
        tri_id = insert_triconnected_component(
            session=session,
            timepoint_id=timepoint_id,
            component_id=component_id,
            size=len(nodes),
            dmr_count=len(dmr_nodes),
            gene_count=len(gene_nodes),
            edge_count=tri_subgraph.number_of_edges(),
            density=2.0 * tri_subgraph.number_of_edges() / (len(nodes) * (len(nodes) - 1)) if len(nodes) > 1 else 0,
            category=category,
            separation_pairs=separation_pairs_list,
            nodes=nodes_list,
            avg_dmrs=avg_dmrs,
            avg_genes=avg_genes,
            is_simple=is_simple,
            dmr_ids=dmr_ids_list,
            gene_ids=gene_ids_list
        )

        # Update node annotations with triconnected component ID
        from database.operations import upsert_dmr_timepoint_annotation, upsert_gene_timepoint_annotation
        for node in nodes:
            if original_graph.nodes[node]['bipartite'] == 0:
                upsert_dmr_timepoint_annotation(
                    session=session,
                    timepoint_id=timepoint_id,
                    dmr_id=node,
                    triconnected_id=tri_id
                )
            else:
                upsert_gene_timepoint_annotation(
                    session=session,
                    timepoint_id=timepoint_id,
                    gene_id=node,
                    triconnected_id=tri_id
                )

    session.commit()
