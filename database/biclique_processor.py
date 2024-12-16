"""Database operations for biclique processing."""

from typing import Dict, List, Set, Tuple
import networkx as nx
import pandas as pd
from collections import defaultdict
import json
from sqlalchemy.orm import Session
from database import operations
from database.populate_tables import populate_dmr_annotations, populate_gene_annotations, populate_bicliques, insert_metadata
from biclique_analysis.classifier import BicliqueSizeCategory, classify_biclique, classify_component

def process_bicliques_db(
    session: Session,
    timepoint_id: int,
    timepoint_name: str,
    original_graph: nx.Graph,
    bicliques_file: str,
    df: pd.DataFrame,
    gene_id_mapping: Dict[str, int],
    file_format: str = "gene_name",
) -> Dict:
    """Process bicliques with database integration and rich metadata."""
    print(f"\nProcessing bicliques for {timepoint_name}")
    
    # Create split graph
    split_graph = nx.Graph()
    
    # Read bicliques using existing function
    from biclique_analysis.reader import read_bicliques_file
    bicliques_result = read_bicliques_file(
        bicliques_file,
        original_graph,
        gene_id_mapping=gene_id_mapping,
        file_format=file_format,
    )
    
    if not bicliques_result or not bicliques_result.get("bicliques"):
        print(f"No bicliques found in {bicliques_file}")
        return bicliques_result

    # First pass: Process original graph components
    print("\nProcessing original graph components...")
    for component in nx.connected_components(original_graph):
        _process_original_graph_component(
            session,
            timepoint_id,
            component,
            original_graph,
            df
        )

    # Second pass: Process split graph components
    print("\nProcessing split graph components...")
    for component in nx.connected_components(split_graph):
        _process_split_graph_component(
            session,
            timepoint_id,
            component,
            split_graph,
            bicliques_result,
            df,
            gene_id_mapping
        )

    return bicliques_result

def _process_original_graph_component(
    session: Session,
    timepoint_id: int,
    component: Set[int],
    original_graph: nx.Graph,
    df: pd.DataFrame
) -> int:
    """Process a single component from the original graph."""
    comp_subgraph = original_graph.subgraph(component)
    
    # Use classifier to categorize component
    dmr_nodes = {n for n in component if original_graph.nodes[n]["bipartite"] == 0}
    gene_nodes = {n for n in component if original_graph.nodes[n]["bipartite"] == 1}
    
    category = classify_component(
        dmr_nodes, 
        gene_nodes,
        []  # Original graph components don't have bicliques
    )
    
    # Insert component with classification
    comp_id = operations.insert_component(
        session,
        timepoint_id=timepoint_id,
        graph_type="original",
        category=category.name.lower(),
        size=len(component),
        dmr_count=len(dmr_nodes),
        gene_count=len(gene_nodes),
        edge_count=len(comp_subgraph.edges()),
        density=2 * len(comp_subgraph.edges()) / (len(component) * (len(component) - 1))
    )

    # Populate annotations
    populate_dmr_annotations(
        session=session,
        timepoint_id=timepoint_id,
        component_id=comp_id,
        graph=comp_subgraph,
        df=df,
        is_original=True
    )
    
    populate_gene_annotations(
        session=session,
        timepoint_id=timepoint_id,
        component_id=comp_id,
        graph=comp_subgraph,
        df=df,
        is_original=True
    )
    
    return comp_id

def _process_split_graph_component(
    session: Session,
    timepoint_id: int,
    component: Set[int],
    split_graph: nx.Graph,
    bicliques_result: Dict,
    df: pd.DataFrame,
    gene_id_mapping: Dict[str, int]
) -> int:
    """Process a single component from the split graph."""
    comp_subgraph = split_graph.subgraph(component)
    
    # Get bicliques for this component
    comp_bicliques = [
        b for b in bicliques_result["bicliques"]
        if any(n in component for n in b[0] | b[1])
    ]
    
    # Use classifier for split graph component
    dmr_nodes = {n for n in component if split_graph.nodes[n]["bipartite"] == 0}
    gene_nodes = {n for n in component if split_graph.nodes[n]["bipartite"] == 1}
    
    category = classify_component(dmr_nodes, gene_nodes, comp_bicliques)
    
    # Create node-biclique mapping
    node_biclique_map = defaultdict(list)
    for idx, (dmr_nodes, gene_nodes) in enumerate(comp_bicliques):
        for node in dmr_nodes | gene_nodes:
            node_biclique_map[node].append(idx)
    
    # Get detailed biclique information
    biclique_details = _add_biclique_details(
        comp_bicliques,
        df,
        gene_id_mapping,
        node_biclique_map
    )
    
    comp_id = operations.insert_component(
        session,
        timepoint_id=timepoint_id,
        graph_type="split",
        category=category.name.lower(),
        size=len(component),
        dmr_count=len(dmr_nodes),
        gene_count=len(gene_nodes),
        edge_count=len(comp_subgraph.edges()),
        density=2 * len(comp_subgraph.edges()) / (len(component) * (len(component) - 1))
    )

    # Process bicliques for this component
    for biclique_info in biclique_details:
        biclique = comp_bicliques[biclique_info["id"]-1]
        biclique_id = populate_bicliques(
            session,
            timepoint_id=timepoint_id,
            component_id=comp_id,
            dmr_nodes=biclique[0],
            gene_nodes=biclique[1]
        )
        
        # Store detailed metadata
        for key, value in biclique_info.items():
            if key not in ["id", "dmrs", "genes", "split_genes"]:
                insert_metadata(
                    session,
                    "biclique",
                    biclique_id,
                    key,
                    json.dumps(value)
                )
        
        # Update annotations with rich metadata
        for dmr_info in biclique_info["dmrs"]:
            operations.upsert_dmr_timepoint_annotation(
                session,
                timepoint_id=timepoint_id,
                dmr_id=dmr_info["id"],
                component_id=comp_id,
                biclique_ids=[biclique_id]
            )
        
        for gene_info in biclique_info["genes"] + biclique_info["split_genes"]:
            operations.upsert_gene_timepoint_annotation(
                session,
                timepoint_id=timepoint_id,
                gene_id=gene_info["id"],
                component_id=comp_id,
                biclique_ids=[biclique_id],
                interaction_source=gene_info["interaction_source"],
                description=gene_info["description"]
            )
    
    return comp_id

