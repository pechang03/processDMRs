# file rb_domination.py

import os
import json
from typing import Set, Dict
import networkx as nx
from heapq import heapify, heappush, heappop
import pandas as pd

class RBDominationCache:
    def __init__(self, cache_dir: str = "cache/rb_domination"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_cache_path(self, timepoint: str) -> str:
        """Get cache file path for a timepoint's RB dominating set."""
        return os.path.join(self.cache_dir, f"rb_dominating_set_{timepoint}.json")
    
    def load_dominating_set(self, timepoint: str) -> Set[int]:
        """Load cached RB dominating set for timepoint."""
        cache_path = self.get_cache_path(timepoint)
        try:
            if os.path.exists(cache_path):
                print(f"Loading cached RB dominating set for {timepoint}")
                with open(cache_path, 'r') as f:
                    return set(json.load(f))
        except Exception as e:
            print(f"Error loading RB dominating set cache for {timepoint}: {e}")
        return None
    
    def save_dominating_set(self, timepoint: str, dominating_set: Set[int]):
        """Save RB dominating set to cache."""
        cache_path = self.get_cache_path(timepoint)
        try:
            print(f"Caching RB dominating set for {timepoint}")
            with open(cache_path, 'w') as f:
                json.dump(list(dominating_set), f)
        except Exception as e:
            print(f"Error saving RB dominating set cache for {timepoint}: {e}")


def greedy_rb_domination(graph, df, area_col=None):
    """Calculate a red-blue dominating set using a greedy approach with heap"""
    # Initialize the dominating set
    dominating_set = set()

    # Get all gene nodes (bipartite=1)
    gene_nodes = {
        node for node, data in graph.nodes(data=True) if data["bipartite"] == 1
    }

    # Keep track of dominated genes
    dominated_genes = set()

    # Process all degree-1 genes in a single pass
    degree_one_genes = {gene for gene in gene_nodes if graph.degree(gene) == 1}
    if degree_one_genes:
        print(f"\nProcessing {len(degree_one_genes)} degree-1 genes")
        for gene in degree_one_genes:
            if gene not in dominated_genes:
                dmr = list(graph.neighbors(gene))[0]
                dominating_set.add(dmr)
                dominated_genes.update(graph.neighbors(dmr))

        print(f"After processing degree-1 genes:")
        print(f"Dominating set size: {len(dominating_set)}")
        print(f"Dominated genes: {len(dominated_genes)}")

    # Initialize utility heap
    # Using negative utility for max-heap behavior
    utility_heap = []
    utility_map = {}  # Keep track of current utility for each DMR

    # Initialize utilities for remaining DMRs
    for dmr, data in graph.nodes(data=True):
        if data["bipartite"] == 0 and dmr not in dominating_set:
            new_genes = set(graph.neighbors(dmr)) - dominated_genes
            if new_genes:  # Only consider DMRs that would dominate new genes
                area = (
                    df.loc[df["DMR_No."] == dmr + 1, area_col].iloc[0]
                    if area_col
                    else 1.0
                )
                utility = len(new_genes)
                entry = (-utility, -area, dmr)
                utility_map[dmr] = entry
                heappush(utility_heap, entry)

    # While there are still undominated genes and DMRs to choose from
    while utility_heap and dominated_genes < gene_nodes:
        # Get DMR with highest utility
        neg_utility, neg_area, best_dmr = heappop(utility_heap)

        # Skip if this DMR is no longer in utility_map (already processed)
        if best_dmr not in utility_map:
            continue

        # Skip if utility has changed
        current_entry = utility_map[best_dmr]
        if current_entry != (neg_utility, neg_area, best_dmr):
            if (
                current_entry[0] > neg_utility
            ):  # If utility improved, re-add with new value
                heappush(utility_heap, current_entry)
            continue

        # Add to dominating set
        dominating_set.add(best_dmr)
        new_dominated = set(graph.neighbors(best_dmr)) - dominated_genes
        dominated_genes.update(new_dominated)

        # Remove the used DMR from utility tracking
        del utility_map[best_dmr]

        # Update utilities for affected DMRs
        affected_dmrs = set()
        for gene in new_dominated:
            affected_dmrs.update(
                dmr
                for dmr in graph.neighbors(gene)
                if dmr not in dominating_set and dmr in utility_map
            )

        for dmr in affected_dmrs:
            new_genes = set(graph.neighbors(dmr)) - dominated_genes
            if new_genes:  # Only keep DMRs that would dominate new genes
                area = (
                    df.loc[df["DMR_No."] == dmr + 1, area_col].iloc[0]
                    if area_col
                    else 1.0
                )
                utility = len(new_genes)
                new_entry = (-utility, -area, dmr)
                utility_map[dmr] = new_entry
                heappush(utility_heap, new_entry)
            else:
                del utility_map[dmr]  # Remove DMRs that wouldn't dominate any new genes

    # Minimize the dominating set
    print("\nMinimizing dominating set...")
    print(f"Initial dominating set size: {len(dominating_set)}")
    original_size = len(dominating_set)
    minimal_dominating_set = minimize_dominating_set(graph, dominating_set)

    print(f"Original size: {original_size}")
    print(f"Minimal size: {len(minimal_dominating_set)}")
    print(f"Removed {original_size - len(minimal_dominating_set)} redundant DMRs")

    # Verify minimality
    for dmr in sorted(minimal_dominating_set):
        remaining = minimal_dominating_set - {dmr}
        if all(
            any(d in graph.neighbors(gene) for d in remaining)
            for gene in graph.neighbors(dmr)
        ):
            print(f"Warning: DMR {dmr} could be removed while maintaining coverage")

    return minimal_dominating_set


def calculate_dominating_sets(graph: nx.Graph, df: pd.DataFrame, timepoint: str = "DSStimeseries") -> Set[int]:
    """Calculate or load cached RB dominating set for the graph."""
    cache = RBDominationCache()
    
    # Try to load from cache first
    cached_set = cache.load_dominating_set(timepoint)
    if cached_set is not None:
        print(f"Using cached RB dominating set for {timepoint}")
        return cached_set
    
    # Calculate new dominating set
    print(f"Calculating new RB dominating set for {timepoint}")
    dominating_set = greedy_rb_domination(graph, df, area_col="Area_Stat")
    
    # Cache the result
    cache.save_dominating_set(timepoint, dominating_set)
    
    return dominating_set


def is_still_dominated(graph, dominating_set, dmr_to_remove):
    """Check if removing a DMR from dominating set maintains coverage"""
    # Get all genes currently dominated by this DMR
    genes_dominated_by_dmr = set(graph.neighbors(dmr_to_remove))

    # Check if these genes are still dominated by other DMRs in the set
    remaining_dmrs = dominating_set - {dmr_to_remove}
    for gene in genes_dominated_by_dmr:
        if not any(dmr in graph.neighbors(gene) for dmr in remaining_dmrs):
            return False
    return True


"""
THIS IS A poor implementation as it doesn't use utility"""


def minimize_dominating_set(graph, dominating_set):
    """Remove redundant DMRs while maintaining coverage"""
    redundant_dmrs = set()

    # Check each DMR in the dominating set
    for dmr in sorted(dominating_set):  # Sort for deterministic behavior
        if is_still_dominated(graph, dominating_set, dmr):
            redundant_dmrs.add(dmr)

    # Remove all redundant DMRs
    minimal_dominating_set = dominating_set - redundant_dmrs

    if redundant_dmrs:
        print(f"\nRemoved {len(redundant_dmrs)} redundant DMRs from dominating set")
        print(f"Original size: {len(dominating_set)}")
        print(f"Minimal size: {len(minimal_dominating_set)}")

    return minimal_dominating_set


def print_domination_statistics(
    dominating_set: set, graph: nx.Graph, df: pd.DataFrame
) -> None:
    """
    Print statistics about a dominating set.

    Args:
        dominating_set: Set of DMR nodes in the dominating set
        graph: The bipartite graph
        df: DataFrame containing DMR metadata
    """
    # Get node sets
    gene_nodes = {n for n, d in graph.nodes(data=True) if d["bipartite"] == 1}
    dmr_nodes = {n for n, d in graph.nodes(data=True) if d["bipartite"] == 0}

    # Calculate dominated genes
    dominated_genes = set()
    for dmr in dominating_set:
        dominated_genes.update(graph.neighbors(dmr))

    # Print statistics
    print("\nDominating Set Statistics:")
    print(f"Size of dominating set: {len(dominating_set)} DMRs")
    print(
        f"Percentage of DMRs in dominating set: {(len(dominating_set)/len(dmr_nodes))*100:.2f}%"
    )
    print(f"Number of genes dominated: {len(dominated_genes)} / {len(gene_nodes)}")
    print(
        f"Percentage of genes dominated: {(len(dominated_genes)/len(gene_nodes))*100:.2f}%"
    )

    # Print sample DMRs
    print("\nSample DMRs from dominating set:")
    sample_size = min(5, len(dominating_set))
    for dmr in list(dominating_set)[:sample_size]:
        area = df.loc[df["DMR_No."] == dmr + 1, "Area_Stat"].iloc[0]
        num_dominated = len(list(graph.neighbors(dmr)))
        print(f"DMR_{dmr + 1}: Area={area}, Dominates {num_dominated} genes")


from typing import Set, Dict


def copy_dominating_set(
    source_graph: nx.Graph, target_graph: nx.Graph, dominating_set: Set[int]
) -> Set[int]:
    """
    Copy dominating set between graphs with same node IDs.

    Args:
        source_graph: Original graph containing the dominating set
        target_graph: Target graph to verify dominating set
        dominating_set: Set of node IDs in the dominating set

    Returns:
        Verified dominating set for target graph
    """
    # Verify nodes exist in target graph
    if not all(node in target_graph for node in dominating_set):
        raise ValueError("Some dominating set nodes not found in target graph")

    return dominating_set
