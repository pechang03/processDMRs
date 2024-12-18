"""Component analysis functionality."""

from typing import Dict, List, Set, Tuple
import networkx as nx
from collections import defaultdict

from .statistics import analyze_components
from .edge_classification import classify_edges
from .classifier import BicliqueSizeCategory, classify_component
from utils.edge_info import EdgeInfo


class ComponentAnalyzer:
    """Handles analysis of graph components."""

    def __init__(self, bipartite_graph: nx.Graph, bicliques_result: Dict, biclique_graph: nx.Graph = None):
        """Initialize with graphs and biclique data."""
        self.bipartite_graph = bipartite_graph
        self.bicliques_result = bicliques_result
        # Use provided biclique graph or create new one
        self.biclique_graph = biclique_graph if biclique_graph is not None else self._create_biclique_graph()

    def _create_biclique_graph(self) -> nx.Graph:
        """Create graph from bicliques."""
        G = nx.Graph()
        for dmr_nodes, gene_nodes in self.bicliques_result["bicliques"]:
            G.add_nodes_from(dmr_nodes, bipartite=0)
            G.add_nodes_from(gene_nodes, bipartite=1)
            G.add_edges_from((d, g) for d in dmr_nodes for g in gene_nodes)
        return G

    def analyze_components(self, dominating_set: Set[int] = None) -> Dict:
        """Analyze all component types."""
        return {
            "components": {
                "original": self._analyze_graph_components(self.bipartite_graph),
                "biclique": self._analyze_graph_components(self.biclique_graph),
            },
            "dominating_set": self._analyze_dominating_set(dominating_set)
            if dominating_set
            else {},
        }

    def _analyze_graph_components(self, graph: nx.Graph) -> Dict:
        """Analyze components of a single graph."""
        # First check if this is the biclique graph
        is_biclique_graph = graph == self.biclique_graph
        
        if is_biclique_graph:
            # For biclique graph, use biclique classification
            components = list(nx.connected_components(graph))
            biclique_stats = {
                "empty": 0,
                "simple": 0,
                "interesting": 0,
                "complex": 0
            }
            
            for comp in components:
                # Get bicliques for this component
                comp_bicliques = [b for b in self.bicliques_result.get("bicliques", [])
                                if any(node in comp for node in b[0] | b[1])]
                
                # Classify the component
                dmr_nodes = {n for n in comp if graph.nodes[n].get("bipartite") == 0}
                gene_nodes = {n for n in comp if graph.nodes[n].get("bipartite") == 1}
                category = classify_component(dmr_nodes, gene_nodes, comp_bicliques)
                biclique_stats[category.name.lower()] += 1
                
            return {"biclique_components": biclique_stats}
        else:
            # Original graph analysis with proper triconnected component handling
            connected_comps = list(nx.connected_components(graph))
            connected_stats = analyze_components(connected_comps, graph)
            biconn_comps = list(nx.biconnected_components(graph))
            biconn_stats = analyze_components(biconn_comps, graph)
            
            # Get triconnected components properly
            triconn_stats = self._analyze_triconnected_components(graph)
            
            return {
                "connected": connected_stats,
                "biconnected": biconn_stats,
                "triconnected": triconn_stats
            }

    def _analyze_dominating_set(self, dominating_set: Set[int]) -> Dict:
        """Calculate statistics about the dominating set."""
        dmr_nodes = {
            n for n, d in self.bipartite_graph.nodes(data=True) if d["bipartite"] == 0
        }
        gene_nodes = {
            n for n, d in self.bipartite_graph.nodes(data=True) if d["bipartite"] == 1
        }

        # Calculate dominated genes
        dominated_genes = set()
        for dmr in dominating_set:
            dominated_genes.update(self.bipartite_graph.neighbors(dmr))

        return {
            "size": len(dominating_set),
            "percentage": len(dominating_set) / len(dmr_nodes) if dmr_nodes else 0,
            "genes_dominated": len(dominated_genes),
            "genes_dominated_percentage": len(dominated_genes) / len(gene_nodes)
            if gene_nodes
            else 0,
            "components_with_ds": self._count_components_with_dominating_nodes(
                dominating_set
            ),
            "avg_size_per_component": self._calculate_avg_size_per_component(
                dominating_set
            ),
        }

    def _count_components_with_dominating_nodes(self, dominating_set: Set[int]) -> int:
        """Count components containing dominating nodes."""
        components = nx.connected_components(self.bipartite_graph)
        return sum(1 for comp in components if comp & dominating_set)

    def _calculate_avg_size_per_component(self, dominating_set: Set[int]) -> float:
        """Calculate average dominating set size per component."""
        components = list(nx.connected_components(self.bipartite_graph))
        if not components:
            return 0.0
        return len(dominating_set) / len(components)

    def get_edge_classifications(self) -> Dict[str, List[EdgeInfo]]:
        """Get edge classifications between original and biclique graphs."""
        return classify_edges(
            self.bipartite_graph,
            self.biclique_graph,
            self.bipartite_graph.graph.get("edge_sources", {}),
        )

    def find_redundant_dominating_nodes(
        self, dominating_set: Set[int]
    ) -> List[Tuple[int, Set[int]]]:
        """
        Find bicliques where multiple DMRs are in the dominating set.

        Returns:
            List of (biclique_id, set of DMRs from dominating set) tuples
            where the biclique has more than one DMR in the dominating set
        """
        redundant_opportunities = []

        for idx, (dmr_nodes, _) in enumerate(self.bicliques_result["bicliques"]):
            dmrs_in_ds = dmr_nodes & dominating_set
            if len(dmrs_in_ds) > 1:
                # Found a biclique with multiple dominating DMRs
                redundant_opportunities.append((idx, dmrs_in_ds))

        return redundant_opportunities

    def validate_dominating_set(self, dominating_set: Set[int]) -> bool:
        """
        Validate that the dominating set properly dominates all components.
        """
        biclique_ds_nodes = defaultdict(set)

        components = list(nx.connected_components(self.bipartite_graph))
        for idx, comp in enumerate(components):
            ds_nodes = comp & dominating_set
            if not ds_nodes:
                raise ValueError(
                    f"Component {idx} (size {len(comp)}) has no dominating nodes"
                )

            # Check if component has multiple dominating nodes in same biclique
            for dmr in ds_nodes:
                for bic_idx, (dmr_nodes, _) in enumerate(
                    self.bicliques_result["bicliques"]
                ):
                    if dmr in dmr_nodes:
                        biclique_ds_nodes[bic_idx].add(dmr)

            # Report potential optimizations
            for bic_idx, dmrs in biclique_ds_nodes.items():
                if len(dmrs) > 1:
                    print(
                        f"Warning: Biclique {bic_idx} in component {idx} has "
                        f"{len(dmrs)} dominating nodes: {dmrs}"
                    )
                    print("Consider removing redundant dominating nodes")

        return True

    def get_node_biclique_map(self) -> Dict[int, List[int]]:
        """
        Create a mapping of nodes to their biclique indices.
        
        Returns:
            Dict mapping node IDs to list of biclique indices they belong to
        """
        node_biclique_map = defaultdict(list)
        
        # Iterate through bicliques and track which nodes appear in each
        for idx, (dmr_nodes, gene_nodes) in enumerate(self.bicliques_result["bicliques"]):
            for node in dmr_nodes | gene_nodes:  # Union of both node sets
                node_biclique_map[node].append(idx)
                
        return dict(node_biclique_map)  # Convert defaultdict to regular dict

    def optimize_dominating_set(self, dominating_set: Set[int]) -> Set[int]:
        """
        Try to reduce dominating set size by removing redundant nodes.

        Strategy:
        1. Find bicliques with multiple dominating nodes
        2. For each such biclique, try removing DMRs one at a time
        3. Keep removal if remaining set still dominates all genes

        Returns:
            Optimized dominating set with redundant nodes removed
        """
        optimized_ds = dominating_set.copy()
        redundant = self.find_redundant_dominating_nodes(optimized_ds)

        for _, dmrs_in_ds in redundant:
            for dmr in dmrs_in_ds:
                # Try removing this DMR
                test_ds = optimized_ds - {dmr}
                dominated_genes = set()
                for d in test_ds:
                    dominated_genes.update(self.bipartite_graph.neighbors(d))

                # If we still dominate all genes, keep the reduction
                all_genes = {
                    n
                    for n, d in self.bipartite_graph.nodes(data=True)
                    if d["bipartite"] == 1
                }
                if dominated_genes == all_genes:
                    optimized_ds.remove(dmr)
                    print(f"Removed redundant DMR {dmr} from dominating set")

        return optimized_ds

    def get_dominating_set_stats(self, dominating_set: Set[int]) -> Dict:
        """
        Get comprehensive statistics about the dominating set.

        Returns:
            Dictionary containing:
            - Basic stats (size, coverage)
            - Redundancy analysis
            - Optimization opportunities
        """
        dmr_nodes = {
            n for n, d in self.bipartite_graph.nodes(data=True) if d["bipartite"] == 0
        }
        gene_nodes = {
            n for n, d in self.bipartite_graph.nodes(data=True) if d["bipartite"] == 1
        }

        # Find redundancies
        redundant = self.find_redundant_dominating_nodes(dominating_set)

        # Calculate dominated genes
        dominated_genes = set()
        for dmr in dominating_set:
            dominated_genes.update(self.bipartite_graph.neighbors(dmr))

        return {
            "size": len(dominating_set),
            "percentage": len(dominating_set) / len(dmr_nodes) if dmr_nodes else 0,
            "genes_dominated": len(dominated_genes),
            "genes_dominated_percentage": len(dominated_genes) / len(gene_nodes)
            if gene_nodes
            else 0,
            "redundancy_analysis": {
                "bicliques_with_multiple_ds": len(redundant),
                "potential_reductions": sum(len(dmrs) - 1 for _, dmrs in redundant),
                "details": [
                    {
                        "biclique_id": bic_id,
                        "dmrs_in_ds": list(dmrs),
                        "potential_savings": len(dmrs) - 1,
                    }
                    for bic_id, dmrs in redundant
                ],
            },
        }
    def _analyze_triconnected_components(self, graph: nx.Graph) -> Dict:
        """Analyze triconnected components properly."""
        from biclique_analysis.triconnected import find_separation_pairs
        
        # Get triconnected components
        separation_pairs = find_separation_pairs(graph)
        if not separation_pairs:
            return {"total": 0, "single_node": 0, "small": 0, "interesting": 0}
            
        # Analyze the components
        return analyze_components(separation_pairs, graph)
