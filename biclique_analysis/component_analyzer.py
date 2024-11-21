"""Component analysis functionality."""

from typing import Dict, List, Set, Tuple
import networkx as nx

from .statistics import analyze_components
from .edge_classification import classify_edges

class ComponentAnalyzer:
    """Handles analysis of graph components."""
    
    def __init__(self, bipartite_graph: nx.Graph, bicliques_result: Dict):
        """Initialize with graphs and biclique data."""
        self.bipartite_graph = bipartite_graph
        self.bicliques_result = bicliques_result
        self.biclique_graph = self._create_biclique_graph()
        
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
                "biclique": self._analyze_graph_components(self.biclique_graph)
            },
            "dominating_set": self._analyze_dominating_set(dominating_set) if dominating_set else {}
        }
        
    def _analyze_graph_components(self, graph: nx.Graph) -> Dict:
        """Analyze components of a single graph."""
        connected_comps = list(nx.connected_components(graph))
        connected_stats = analyze_components(connected_comps, graph)
        
        biconn_comps = list(nx.biconnected_components(graph))
        biconn_stats = analyze_components(biconn_comps, graph)
        
        return {
            "connected": connected_stats,
            "biconnected": biconn_stats,
            "triconnected": {
                "total": 0,
                "single_node": 0,
                "small": 0,
                "interesting": 0
            }
        }

    def _analyze_dominating_set(self, dominating_set: Set[int]) -> Dict:
        """Calculate statistics about the dominating set."""
        dmr_nodes = {n for n, d in self.bipartite_graph.nodes(data=True) if d['bipartite'] == 0}
        gene_nodes = {n for n, d in self.bipartite_graph.nodes(data=True) if d['bipartite'] == 1}
        
        # Calculate dominated genes
        dominated_genes = set()
        for dmr in dominating_set:
            dominated_genes.update(self.bipartite_graph.neighbors(dmr))
        
        return {
            "size": len(dominating_set),
            "percentage": len(dominating_set) / len(dmr_nodes) if dmr_nodes else 0,
            "genes_dominated": len(dominated_genes),
            "genes_dominated_percentage": len(dominated_genes) / len(gene_nodes) if gene_nodes else 0,
            "components_with_ds": self._count_components_with_dominating_nodes(dominating_set),
            "avg_size_per_component": self._calculate_avg_size_per_component(dominating_set)
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

    def get_edge_classifications(self) -> Dict[str, List['EdgeInfo']]:
        """Get edge classifications between original and biclique graphs."""
        return classify_edges(
            self.bipartite_graph, 
            self.biclique_graph, 
            self.bipartite_graph.graph.get('edge_sources', {})
        )
