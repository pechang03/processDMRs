from typing import Dict, List, Set, Tuple
import networkx as nx
import plotly.graph_objects as go
from .base import GraphVisualization
from ..utils import get_node_position  # Add this import


class BiconnectedVisualization(GraphVisualization):
    """Visualization specifically for bi-edge-connected components."""

    def create_visualization(
        self,
        graph: nx.Graph,
        node_labels: Dict[int, str],
        node_positions: Dict[int, Tuple[float, float]],
        edge_classifications: Dict[str, Set[Tuple[int, int]]] = None,
        node_metadata: Dict[int, Dict] = None,
        **kwargs,
    ) -> str:
        """
        Create bi-edge-connected component visualization.

        Additional kwargs:
            components: List of node sets representing bi-edge-connected components
            spring_layout: Boolean to use spring layout instead of fixed positions
            component_colors: Dict mapping component IDs to colors

        Returns:
            JSON string containing the Plotly figure
        """
        fig = go.Figure()

        # Use spring layout if requested or if positions not provided
        if kwargs.get("spring_layout", False) or not node_positions:
            node_positions = nx.spring_layout(graph)

        # Get components if provided
        components = kwargs.get("components", [set(graph.nodes())])
        component_colors = kwargs.get("component_colors", {})

        # Draw edges with different styles based on classification
        if edge_classifications:
            # Permanent edges (solid black)
            permanent_edges = edge_classifications.get("permanent", set())
            edge_x, edge_y = self._get_edge_traces(permanent_edges, node_positions)
            fig.add_trace(
                go.Scatter(
                    x=edge_x,
                    y=edge_y,
                    mode="lines",
                    line=dict(color="black", width=1),
                    hoverinfo="none",
                    name="Permanent Edges",
                )
            )

            # False positive edges (dashed red)
            false_pos_edges = edge_classifications.get("false_positive", set())
            edge_x, edge_y = self._get_edge_traces(false_pos_edges, node_positions)
            fig.add_trace(
                go.Scatter(
                    x=edge_x,
                    y=edge_y,
                    mode="lines",
                    line=dict(color="red", width=1, dash="dash"),
                    name="False Positive Edges",
                )
            )

            # False negative edges (dotted blue)
            false_neg_edges = edge_classifications.get("false_negative", set())
            edge_x, edge_y = self._get_edge_traces(false_neg_edges, node_positions)
            fig.add_trace(
                go.Scatter(
                    x=edge_x,
                    y=edge_y,
                    mode="lines",
                    line=dict(color="blue", width=1, dash="dot"),
                    name="False Negative Edges",
                )
            )
        else:
            # Draw all edges as permanent if no classification provided
            edge_x, edge_y = self._get_edge_traces(set(graph.edges()), node_positions)
            fig.add_trace(
                go.Scatter(
                    x=edge_x,
                    y=edge_y,
                    mode="lines",
                    line=dict(color="black", width=1),
                    hoverinfo="none",
                    name="Edges",
                )
            )

        # Draw nodes by component
        for idx, component in enumerate(components):
            node_x = []
            node_y = []
            node_text = []
            for node in component:
                if node in node_positions:
                    x, y = node_positions[node]
                    node_x.append(x)
                    node_y.append(y)

                    # Create hover text
                    label = node_labels.get(node, str(node))
                    metadata = node_metadata.get(node, {})
                    hover_text = f"{label}<br>" + "<br>".join(
                        f"{k}: {v}" for k, v in metadata.items()
                    )
                    node_text.append(hover_text)

            # Get color for component
            color = component_colors.get(idx, f"hsl({(idx * 77) % 360}, 70%, 50%)")

            fig.add_trace(
                go.Scatter(
                    x=node_x,
                    y=node_y,
                    mode="markers+text",
                    marker=dict(
                        size=10, color=color, line=dict(color="black", width=1)
                    ),
                    text=[
                        node_labels.get(n, str(n))
                        for n in component
                        if n in node_positions
                    ],
                    textposition="top center",
                    hovertext=node_text,
                    hoverinfo="text",
                    name=f"Component {idx+1}",
                )
            )

        # Update layout
        fig.update_layout(
            showlegend=True,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor="white",
        )

        return fig.to_json()

    def get_component_colors(self, num_components: int) -> Dict[int, str]:
        """Generate distinct colors for components."""
        return {i: f"hsl({(i * 77) % 360}, 70%, 50%)" for i in range(num_components)}
