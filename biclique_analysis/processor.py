# File: Processor.py
# Author: Peter Shaw
#
from typing import Dict, List, Set, Tuple
import networkx as nx
import pandas as pd
from collections import defaultdict
from sqlalchemy.orm import Session

# Removed data_loader import
from utils.node_info import NodeInfo
from utils import process_enhancer_info
from .reader import read_bicliques_file
from .components import process_components
from database import operations
from database.populate_tables import populate_dmr_annotations, populate_gene_annotations, populate_bicliques
import json
from .classifier import BicliqueSizeCategory, classify_biclique, classify_component


def process_bicliques(
    bipartite_graph: nx.Graph,
    bicliques_file: str,
    dataset_name: str,
    gene_id_mapping: Dict[str, int] = None,
    file_format: str = "gene_name",
    biclique_graph: nx.Graph = None,  # Add parameter to receive the graph
) -> Dict:
    """
    Call stack:
    1. process_timepoint
    2. [process_bicliques] (YOU ARE HERE)
    3. read_bicliques_file
    4. process_components
    
    Process bicliques and add detailed information.
    """
    print(f"\nProcessing bicliques for {dataset_name}")
    print(f"Using format: {file_format}")

    try:
        # Use the passed biclique_graph instead of creating a new one
        if biclique_graph is None:
            print("Warning: No biclique graph provided, creating new one")
            biclique_graph = nx.Graph()

        # Read bicliques using reader.py
        bicliques_result = read_bicliques_file(
            bicliques_file,
            bipartite_graph,
            gene_id_mapping=gene_id_mapping,
            file_format=file_format,
        )

        if not bicliques_result or not bicliques_result.get("bicliques"):
            print(f"No bicliques found in {bicliques_file}")
            return {
                "bicliques": [],
                "components": [],
                "statistics": {},
                "graph_info": {
                    "name": dataset_name,
                    "total_dmrs": sum(
                        1
                        for n, d in bipartite_graph.nodes(data=True)
                        if d["bipartite"] == 0
                    ),
                    "total_genes": sum(
                        1
                        for n, d in bipartite_graph.nodes(data=True)
                        if d["bipartite"] == 1
                    ),
                    "total_edges": len(bipartite_graph.edges()),
                },
            }

        # Process components using components.py
        # Update this line to match the 6 return values from process_components
        (
            complex_components,
            interesting_components,
            simple_components,  # Add this variable
            non_simple_components,
            component_stats,
            statistics,
        ) = process_components(
            bipartite_graph=bipartite_graph,
            bicliques_result=bicliques_result,
            biclique_graph=biclique_graph,  # Pass the existing biclique graph
            dominating_set=None,  # Add dominating set if needed
        )

        # Add component information to result
        bicliques_result.update(
            {
                "complex_components": complex_components,
                "interesting_components": interesting_components,
                "non_simple_components": non_simple_components,
                "component_stats": component_stats,
                "statistics": statistics,
            }
        )

        print(f"\nProcessed bicliques result:")
        print(f"Total bicliques: {len(bicliques_result.get('bicliques', []))}")
        print(f"Complex components: {len(complex_components)}")
        print(f"Interesting components: {len(interesting_components)}")

        return bicliques_result

    except FileNotFoundError:
        print(f"Warning: Bicliques file not found: {bicliques_file}")
        return {
            "bicliques": [],
            "components": [],
            "statistics": {},
            "graph_info": {
                "name": dataset_name,
                "total_dmrs": sum(
                    1
                    for n, d in bipartite_graph.nodes(data=True)
                    if d["bipartite"] == 0
                ),
                "total_genes": sum(
                    1
                    for n, d in bipartite_graph.nodes(data=True)
                    if d["bipartite"] == 1
                ),
                "total_edges": len(bipartite_graph.edges()),
            },
        }
    except Exception as e:
        print(f"Error processing bicliques: {str(e)}")
        raise


def _get_dmr_details(dmr_nodes: Set[int], df: pd.DataFrame) -> List[Dict]:
    """Get detailed information for DMR nodes."""
    dmr_details = []
    for dmr_id in dmr_nodes:
        dmr_row = df[df["DMR_No."] == dmr_id + 1].iloc[0]
        dmr_details.append(
            {
                "id": dmr_id,
                "area": dmr_row["Area_Stat"] if "Area_Stat" in df.columns else "N/A",
                "description": dmr_row["DMR_Description"]
                if "DMR_Description" in df.columns
                else "N/A",
            }
        )
    return dmr_details


def _get_gene_details(
    gene_nodes: Set[int], df: pd.DataFrame, gene_id_mapping: Dict
) -> List[Dict]:
    """Get detailed information for gene nodes."""
    gene_details = []
    reverse_gene_mapping = {v: k for k, v in gene_id_mapping.items()}
    for gene_id in gene_nodes:
        gene_name = reverse_gene_mapping.get(gene_id, f"Unknown_{gene_id}")
        matching_rows = df[df["Gene_Symbol_Nearby"].str.lower() == gene_name.lower()]
        if not matching_rows.empty:
            gene_desc = matching_rows.iloc[0]["Gene_Description"]
            gene_details.append(
                {
                    "name": gene_name,
                    "description": gene_desc
                    if pd.notna(gene_desc) and gene_desc != "N/A"
                    else "N/A",
                }
            )
        else:
            gene_details.append({"name": gene_name, "description": "N/A"})
    return gene_details


def _add_biclique_details(
    bicliques: List, df: pd.DataFrame, gene_id_mapping: Dict
) -> Dict:
    """Add detailed information for each biclique."""
    detailed_info = {}
    for idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        detailed_info[f"biclique_{idx+1}_details"] = {
            "dmrs": _get_dmr_details(dmr_nodes, df),
            "genes": _get_gene_details(gene_nodes, df, gene_id_mapping),
        }
    return detailed_info


def process_dataset(
    df: pd.DataFrame, bipartite_graph: nx.Graph, gene_id_mapping: Dict[str, int]
):
    """Process a dataset with pre-loaded graph and dataframe.

    Args:
        df: Loaded dataframe
        bipartite_graph: Pre-created bipartite graph
        gene_id_mapping: Gene name to ID mapping

    Returns:
        Tuple of (bipartite_graph, dataframe, gene_id_mapping)
    """
    # Process enhancer information if not already processed
    if "Processed_Enhancer_Info" not in df.columns:
        df["Processed_Enhancer_Info"] = df[
            "ENCODE_Enhancer_Interaction(BingRen_Lab)"
        ].apply(process_enhancer_info)

    return bipartite_graph, df, gene_id_mapping


# Add other helper functions...
def create_node_metadata(
    df: pd.DataFrame,
    gene_id_mapping: Dict[str, int],
    node_biclique_map: Dict[int, List[int]],
    graph: nx.Graph = None,
) -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
    """
    Create metadata dictionaries for DMRs and genes.

    Args:
        df: DataFrame containing DMR and gene information
        gene_id_mapping: Mapping of gene names to IDs
        node_biclique_map: Mapping of nodes to their bicliques
        graph: Optional NetworkX graph for additional node information

    Returns:
        Tuple of (dmr_metadata, gene_metadata)
    """
    # Create node info if graph is provided
    node_info = None
    if graph:
        node_info = NodeInfo(
            all_nodes=set(graph.nodes()),
            dmr_nodes={n for n, d in graph.nodes(data=True) if d["bipartite"] == 0},
            regular_genes={n for n, d in graph.nodes(data=True) if d["bipartite"] == 1},
            split_genes=set(),
            node_degrees={n: graph.degree(n) for n in graph.nodes()},
            min_gene_id=min(gene_id_mapping.values(), default=0),
        )

    # Create DMR metadata
    dmr_metadata = {}
    for _, row in df.iterrows():
        dmr_id = row["DMR_No."] - 1  # Convert to 0-based index
        dmr_metadata[f"DMR_{row['DMR_No.']}"] = {
            "area": str(row["Area_Stat"]) if "Area_Stat" in df.columns else "N/A",
            "description": str(row["Gene_Description"])
            if "Gene_Description" in df.columns
            else "N/A",
            "name": f"DMR_{row['DMR_No.']}",
            "bicliques": node_biclique_map.get(dmr_id, []),
            "node_type": node_info.get_node_type(dmr_id) if node_info else "DMR",
            "degree": node_info.get_node_degree(dmr_id) if node_info else 0,
        }

    # Create gene metadata
    gene_metadata = {}
    for gene_name, gene_id in gene_id_mapping.items():
        gene_matches = df[df["Gene_Symbol_Nearby"].str.lower() == gene_name.lower()]
        description = "N/A"
        if not gene_matches.empty and "Gene_Description" in gene_matches.columns:
            description = str(gene_matches.iloc[0]["Gene_Description"])

        gene_metadata[gene_name] = {
            "description": description,
            "id": gene_id,
            "bicliques": node_biclique_map.get(gene_id, []),
            "name": gene_name,
            "node_type": node_info.get_node_type(gene_id) if node_info else "gene",
            "degree": node_info.get_node_degree(gene_id) if node_info else 0,
        }

    return dmr_metadata, gene_metadata


def create_biclique_metadata(
    bicliques: List[Tuple[Set[int], Set[int]]], node_info: NodeInfo = None
) -> List[Dict]:
    """
    Create detailed metadata for each biclique.

    Args:
        bicliques: List of (dmr_nodes, gene_nodes) tuples
        node_info: Optional NodeInfo object for additional node details

    Returns:
        List of dictionaries containing metadata for each biclique
    """
    from .classifier import classify_biclique
    from collections import defaultdict
    from utils.json_utils import convert_for_json

    metadata = []

    # Track nodes across all bicliques for overlap calculations
    all_dmrs = set()
    all_genes = set()
    node_to_bicliques = defaultdict(set)

    # First pass - collect basic info and track nodes
    for idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        all_dmrs.update(dmr_nodes)
        all_genes.update(gene_nodes)

        # Track which bicliques each node belongs to
        for node in dmr_nodes | gene_nodes:
            node_to_bicliques[node].add(idx)

    # Second pass - create detailed metadata
    for idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        # Calculate basic metrics
        size = len(dmr_nodes) + len(gene_nodes)
        density = len(dmr_nodes) * len(gene_nodes) / (size * size) if size > 0 else 0

        # Calculate overlap with other bicliques
        overlapping_bicliques = set()
        for node in dmr_nodes | gene_nodes:
            overlapping_bicliques.update(node_to_bicliques[node])
        overlapping_bicliques.discard(idx)  # Remove self

        # Calculate shared nodes with overlapping bicliques
        shared_nodes = {
            str(other_idx): len(
                (dmr_nodes | gene_nodes)
                & (bicliques[other_idx][0] | bicliques[other_idx][1])
            )
            for other_idx in overlapping_bicliques
        }

        # Get biclique classification
        category = classify_biclique(dmr_nodes, gene_nodes)

        # Create metadata dictionary
        biclique_metadata = {
            "id": idx,
            "size": {"total": size, "dmrs": len(dmr_nodes), "genes": len(gene_nodes)},
            "nodes": {
                "dmrs": sorted(str(n) for n in dmr_nodes), 
                "genes": sorted(str(n) for n in gene_nodes)
            },
            "metrics": {
                "density": density,
                "dmr_ratio": len(dmr_nodes) / len(all_dmrs) if all_dmrs else 0,
                "gene_ratio": len(gene_nodes) / len(all_genes) if all_genes else 0,
                "edge_count": len(dmr_nodes) * len(gene_nodes),
            },
            "classification": {
                "category": category.name.lower(),
                "is_interesting": classify_biclique(dmr_nodes, gene_nodes)
                == BicliqueSizeCategory.INTERESTING,
            },
            "relationships": {
                "overlapping_bicliques": len(overlapping_bicliques),
                "shared_nodes": shared_nodes,
                "max_overlap": max(shared_nodes.values()) if shared_nodes else 0,
            },
            "node_details": {
                "dmrs": {
                    "types": [
                        node_info.get_node_type(n) if node_info else "DMR"
                        for n in dmr_nodes
                    ],
                    "degrees": [
                        node_info.get_node_degree(n) if node_info else 0
                        for n in dmr_nodes
                    ],
                },
                "genes": {
                    "types": [
                        node_info.get_node_type(n) if node_info else "gene"
                        for n in gene_nodes
                    ],
                    "degrees": [
                        node_info.get_node_degree(n) if node_info else 0
                        for n in gene_nodes
                    ],
                },
            },
        }

        metadata.append(biclique_metadata)

    # Convert to JSON-safe format
    return convert_for_json(metadata)
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
