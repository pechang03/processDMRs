from typing import Dict, List, Set, Tuple
import networkx as nx
import plotly.graph_objects as go
from .base import GraphVisualization
from backend.app.utils.node_info import NodeInfo


class TriconnectedVisualization(GraphVisualization):
    """Visualization specifically for triconnected components."""

    def create_visualization(
        self,
        graph: nx.Graph,
        node_labels: Dict[int, str],
        node_positions: Dict[int, Tuple[float, float]],
        node_metadata: Dict[int, Dict] = None,
        edge_classifications: Dict[str, Set[Tuple[int, int]]] = None,
        **kwargs,
    ) -> str:
        """
        Create triconnected component visualization.

        Args:
            graph: NetworkX graph of the component
            node_labels: Mapping of node IDs to display labels
            node_positions: Node position coordinates
            node_metadata: Additional node information for hover text
            edge_classifications: Edge classification information
            **kwargs: Additional arguments including:
                - components: List of node sets for each triconnected component
                - component_colors: Dict mapping component indices to colors

        Returns:
            JSON string containing the Plotly figure
        """
        fig = go.Figure()

        # Get components and colors from kwargs
        components = kwargs.get("components", [set(graph.nodes())])
        component_colors = kwargs.get("component_colors", {})

        # Draw edges first
        if edge_classifications:
            # Draw classified edges with different styles
            for edge_type, edges in edge_classifications.items():
                edge_x, edge_y = self._get_edge_traces(edges, node_positions)

                # Set edge style based on type
                if edge_type == "permanent":
                    line_style = dict(color="black", width=1)
                elif edge_type == "separation_pair":
                    line_style = dict(color="red", width=2, dash="dash")
                else:
                    line_style = dict(color="gray", width=1)

                fig.add_trace(
                    go.Scatter(
                        x=edge_x,
                        y=edge_y,
                        mode="lines",
                        line=line_style,
                        name=f"{edge_type.replace('_', ' ').title()} Edges",
                        hoverinfo="none",
                    )
                )
        else:
            # Draw all edges as regular if no classification provided
            edge_x, edge_y = self._get_edge_traces(set(graph.edges()), node_positions)
            fig.add_trace(
                go.Scatter(
                    x=edge_x,
                    y=edge_y,
                    mode="lines",
                    line=dict(color="black", width=1),
                    name="Edges",
                    hoverinfo="none",
                )
            )

        # Draw nodes by component
        for idx, component in enumerate(components):
            node_x = []
            node_y = []
            hover_text = []

            for node in component:
                if node in node_positions:
                    x, y = node_positions[node]
                    node_x.append(x)
                    node_y.append(y)

                    # Create hover text with metadata
                    label = node_labels.get(node, str(node))
                    meta = node_metadata.get(node, {})
                    hover = f"{label}<br>" + "<br>".join(
                        f"{k}: {v}" for k, v in meta.items()
                    )
                    hover_text.append(hover)

            # Get color for this component
            color = component_colors.get(idx, f"hsl({(idx * 77) % 360}, 70%, 50%)")

            # Add node trace
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
                    hovertext=hover_text,
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

    def _get_edge_traces(
        self,
        edges: Set[Tuple[int, int]],
        node_positions: Dict[int, Tuple[float, float]],
    ) -> Tuple[List[float], List[float]]:
        """Helper method to create edge trace coordinates."""
        edge_x = []
        edge_y = []

        for edge in edges:
            if edge[0] in node_positions and edge[1] in node_positions:
                x0, y0 = node_positions[edge[0]]
                x1, y1 = node_positions[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])

        return edge_x, edge_y
