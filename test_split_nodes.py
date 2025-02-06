import plotly.graph_objects as go
import networkx as nx

# Create a sample graph
G = nx.random_geometric_graph(10, 0.5, seed=42)

# Get node positions
pos = nx.spring_layout(G)

# Create edge trace
edge_x = []
edge_y = []
for edge in G.edges():
    x0, y0 = pos[edge[0]]
    x1, y1 = pos[edge[1]]
    edge_x.extend([x0, x1, None])
    edge_y.extend([y0, y1, None])

edge_trace = go.Scatter(
    x=edge_x,
    y=edge_y,
    line=dict(width=0.5, color="#888"),
    hoverinfo="none",
    mode="lines",
)

# Create node traces
node_x = []
node_y = []
for node in G.nodes():
    x, y = pos[node]
    node_x.append(x)
    node_y.append(y)

# Create two overlapping circles with a diagonal line to create split effect
# First half (red)
node_trace1 = go.Scatter(
    x=node_x,
    y=node_y,
    mode="markers",
    hoverinfo="text",
    marker=dict(size=20, color="red", line=dict(width=1, color="white")),
)

# Second half (blue)
node_trace2 = go.Scatter(
    x=node_x,
    y=node_y,
    mode="markers",
    hoverinfo="text",
    marker=dict(size=20, color="blue", line=dict(width=1, color="white")),
)

# Create diagonal lines to split the nodes
split_lines = []
for x, y in zip(node_x, node_y):
    # Create a diagonal line through each node
    split_lines.append(
        go.Scatter(
            x=[x - 0.02, x + 0.02],
            y=[y - 0.02, y + 0.02],
            mode="lines",
            line=dict(color="white", width=2),
            hoverinfo="none",
            showlegend=False,
        )
    )

# Combine all traces
all_traces = [edge_trace, node_trace2, node_trace1] + split_lines

# Create the figure
fig = go.Figure(
    data=all_traces,
    layout=go.Layout(
        showlegend=False,
        hovermode="closest",
        margin=dict(b=0, l=0, r=0, t=0),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    ),
)

# Adjust the plot size and background
fig.update_layout(plot_bgcolor="white", width=800, height=800)

# Show the plot
fig.show()
