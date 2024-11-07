from flask import Flask, render_template
import pandas as pd
import networkx as nx
from processDMR import (
    read_excel_file,
    create_bipartite_graph,
    process_enhancer_info,
    validate_bipartite_graph
)
from process_bicliques import (
    read_bicliques_file,
    print_bicliques_summary,
    print_bicliques_detail
)
import json
import plotly
import plotly.graph_objs as go

app = Flask(__name__)

def process_data():
    """Process the DMR data and return results"""
    try:
        # Read DSS1 data
        df = read_excel_file("./data/DSS1.xlsx")
        df["Processed_Enhancer_Info"] =
df["ENCODE_Enhancer_Interaction(BingRen_Lab)"].apply(process_enhancer_info)

        # Create gene ID mapping
        all_genes = set()
        all_genes.update(df["Gene_Symbol_Nearby"].dropna())
        all_genes.update([g for genes in df["Processed_Enhancer_Info"] for g in
genes])
        gene_id_mapping = {gene: idx + len(df) for idx, gene in
enumerate(sorted(all_genes))}

        # Create bipartite graph
        bipartite_graph = create_bipartite_graph(df, gene_id_mapping)

        # Read bicliques
        max_dmr_id = max(df["DMR_No."])
        bicliques_result = read_bicliques_file(
            "./data/bipartite_graph_output.txt.biclusters",
            max_dmr_id,
            bipartite_graph
        )

        # Process connected components
        components = list(nx.connected_components(bipartite_graph))
        component_data = []

        for idx, component in enumerate(components):
            subgraph = bipartite_graph.subgraph(component)

            # Get bicliques for this component
            component_bicliques = []
            for dmr_nodes, gene_nodes in bicliques_result['bicliques']:
                if any(node in component for node in dmr_nodes):
                    # Only include non-trivial bicliques
                    if len(dmr_nodes) > 1 or len(gene_nodes) > 1:
                        component_bicliques.append({
                            'dmrs': sorted(list(dmr_nodes)),
                            'genes': sorted(list(gene_nodes)),
                            'size': f"{len(dmr_nodes)}×{len(gene_nodes)}"
                        })

            if component_bicliques:  # Only include components with non-trivial
bicliques
                component_data.append({
                    'id': idx + 1,
                    'size': len(component),
                    'dmrs': len([n for n in subgraph.nodes() if
bipartite_graph.nodes[n]['bipartite'] == 0]),
                    'genes': len([n for n in subgraph.nodes() if
bipartite_graph.nodes[n]['bipartite'] == 1]),
                    'bicliques': component_bicliques
                })

        # Create summary statistics
        stats = {
            'total_components': len(components),
            'components_with_bicliques': len(component_data),
            'total_bicliques': len(bicliques_result['bicliques']),
            'non_trivial_bicliques': sum(1 for comp in component_data for bic in
comp['bicliques'])
        }

        return {
            "stats": stats,
            "components": component_data,
            "coverage": bicliques_result['coverage']
        }
    except Exception as e:
        return {"error": str(e)}

def create_plotly_graph(component_data):
    """Create Plotly graph for a component"""
    edge_trace = []
    node_trace = []

    for biclique in component_data['bicliques']:
        dmr_nodes = biclique['dmrs']
        gene_nodes = biclique['genes']

        # Create edges for this biclique
        for dmr in dmr_nodes:
            for gene in gene_nodes:
                edge_trace.append(
                    go.Scatter(
                        x=[dmr, gene],
                        y=[0, 1],
                        mode='lines',
                        line=dict(width=1),
                        hoverinfo='none'
                    )
                )

        # Create nodes for this biclique
        node_trace.append(
            go.Scatter(
                x=dmr_nodes,
                y=[0] * len(dmr_nodes),
                mode='markers',
                marker=dict(size=10, color='blue'),
                text=[f"DMR_{d}" for d in dmr_nodes],
                hoverinfo='text'
            )
        )
        node_trace.append(
            go.Scatter(
                x=gene_nodes,
                y=[1] * len(gene_nodes),
                mode='markers',
                marker=dict(size=10, color='red'),
                text=[f"Gene_{g}" for g in gene_nodes],
                hoverinfo='text'
            )
        )

    layout = go.Layout(
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )

    return json.dumps(go.Figure(data=edge_trace + node_trace, layout=layout),
cls=plotly.utils.PlotlyJSONEncoder)

@app.route('/')
def index():
    results = process_data()
    if 'error' not in results:
        for component in results['components']:
            component['plotly_graph'] = create_plotly_graph(component)
    return render_template('index.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)
