# file rb_domination.py

from networkx import bipartite
import networkx as nx


def validate_bipartite_graph(B):
    """Validate the bipartite graph properties"""
    # Check for isolated nodes
    isolated = list(nx.isolates(B))
    if isolated:
        print(f"Warning: Found {len(isolated)} isolated nodes: {isolated[:5]}")

    # Check node degrees
    degrees = dict(B.degree())
    if min(degrees.values()) == 0:
        zero_degree_nodes = [n for n, d in degrees.items() if d == 0]
        print(f"Warning: Graph contains {len(zero_degree_nodes)} nodes with degree 0")
        print(f"First 5 zero-degree nodes: {zero_degree_nodes[:5]}")

    # Verify bipartite property
    if not nx.is_bipartite(B):
        print("Warning: Graph is not bipartite")


def greedy_rb_domination(graph, df, area_col=None):
    # Initialize the dominating set
    dominating_set = set()

    # Get all gene nodes (bipartite=1)
    gene_nodes = set(
        node for node, data in graph.nodes(data=True) if data["bipartite"] == 1
    )

    # Keep track of dominated genes
    dominated_genes = set()

    # First, handle degree-1 genes that aren't already dominated
    for gene in gene_nodes:
        if graph.degree(gene) == 1 and gene not in dominated_genes:
            # Get the single neighbor (DMR) of this gene
            dmr = list(graph.neighbors(gene))[0]
            dominating_set.add(dmr)
            # Update dominated genes
            dominated_genes.update(graph.neighbors(dmr))

    # Get remaining undominated subgraph
    remaining_graph = graph.copy()
    remaining_graph.remove_nodes_from(dominating_set)
    remaining_graph.remove_nodes_from(dominated_genes)

    # Handle remaining components
    for component in nx.connected_components(remaining_graph):
        # Skip if component has no genes to dominate
        if not any(remaining_graph.nodes[n]["bipartite"] == 1 for n in component):
            continue

        # Get DMR nodes in this component
        dmr_nodes = [
            node for node in component if remaining_graph.nodes[node]["bipartite"] == 0
        ]

        if dmr_nodes:  # If there are DMR nodes in this component
            # Add weight-based selection
            def get_node_weight(node):
                degree = len(set(graph.neighbors(node)))
                area = df.loc[node, area_col] if area_col else 1.0
                return degree * area

            # Modify selection strategy
            best_dmr = max(
                dmr_nodes,
                key=lambda x: (
                    len(set(remaining_graph.neighbors(x))),
                    get_node_weight(x),
                ),
            )
            dominating_set.add(best_dmr)

    return dominating_set


def process_components(graph, df):
    # Process larger components first
    components = sorted(nx.connected_components(graph), key=len, reverse=True)
    dominating_sets = []

    for component in components:
        if len(component) > 1:  # Skip isolated nodes
            subgraph = graph.subgraph(component)
            dom_set = greedy_rb_domination(subgraph, df)
            dominating_sets.extend(dom_set)

    return dominating_sets
