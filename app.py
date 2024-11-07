from flask import Flask, render_template
import pandas as pd
import networkx as nx
import json
import plotly
import plotly.graph_objs as go

# Import functions from processDMR
from processDMR import (
    read_excel_file,
    create_bipartite_graph,
)

# Import functions from process_bicliques
from process_bicliques import (
    read_bicliques_file,
    print_bicliques_summary,
    print_bicliques_detail,
)

# Import utility functions from graph_utils
from graph_visualize import create_biclique_visualization, create_node_biclique_map
from graph_layout import calculate_node_positions
from graph_utils import (
    process_enhancer_info,
    # validate_bipartite_graph,
    # read_and_prepare_data,
    # create_metadata,
)

app = Flask(__name__)


def process_data():
    """Process the DMR data and return results"""
    try:
        df, gene_id_mapping = read_and_prepare_data()
        bipartite_graph = create_bipartite_graph(df, gene_id_mapping)
        bicliques_result = process_bicliques(bipartite_graph, df)
        component_data = process_components(bipartite_graph, bicliques_result)
        dmr_metadata, gene_metadata = create_metadata(df, gene_id_mapping)

        # Create summary statistics
        stats = {
            "total_components": len(component_data),
            "components_with_bicliques": len(
                [comp for comp in component_data if comp["bicliques"]]
            ),
            "total_bicliques": len(bicliques_result["bicliques"]),
            "non_trivial_bicliques": sum(
                1 for comp in component_data for bic in comp["bicliques"]
            ),
        }

        return {
            "stats": stats,
            "components": component_data,
            "coverage": bicliques_result["coverage"],
            "dmr_metadata": dmr_metadata,
            "gene_metadata": gene_metadata,
        }
    except Exception as e:
        return {"error": str(e)}


def read_and_prepare_data():
    """Read and prepare the data from the Excel file"""
    df = read_excel_file("./data/DSS1.xlsx")
    df["Processed_Enhancer_Info"] = df[
        "ENCODE_Enhancer_Interaction(BingRen_Lab)"
    ].apply(process_enhancer_info)
    all_genes = set(df["Gene_Symbol_Nearby"].dropna())
    all_genes.update([g for genes in df["Processed_Enhancer_Info"] for g in genes])
    gene_id_mapping = {
        gene: idx + len(df) for idx, gene in enumerate(sorted(all_genes))
    }
    return df, gene_id_mapping


def process_bicliques(bipartite_graph, df):
    """Read and process bicliques from the file"""
    max_dmr_id = max(df["DMR_No."])
    return read_bicliques_file(
        "./data/bipartite_graph_output.txt.biclusters", max_dmr_id, bipartite_graph
    )


def process_components(bipartite_graph, bicliques_result):
    """Process connected components of the graph"""
    components = list(nx.connected_components(bipartite_graph))
    component_data = []

    for idx, component in enumerate(components):
        subgraph = bipartite_graph.subgraph(component)
        component_bicliques = [
            {
                "dmrs": sorted(list(dmr_nodes)),
                "genes": sorted(list(gene_nodes)),
                "size": f"{len(dmr_nodes)}×{len(gene_nodes)}",
            }
            for dmr_nodes, gene_nodes in bicliques_result["bicliques"]
            if any(node in component for node in dmr_nodes)
            and (len(dmr_nodes) > 1 or len(gene_nodes) > 1)
        ]

        if component_bicliques:
            component_data.append(
                {
                    "id": idx + 1,
                    "size": len(component),
                    "dmrs": len(
                        [
                            n
                            for n in subgraph.nodes()
                            if bipartite_graph.nodes[n]["bipartite"] == 0
                        ]
                    ),
                    "genes": len(
                        [
                            n
                            for n in subgraph.nodes()
                            if bipartite_graph.nodes[n]["bipartite"] == 1
                        ]
                    ),
                    "bicliques": component_bicliques,
                }
            )

    return component_data


def create_metadata(df, gene_id_mapping):
    """Create metadata dictionaries for DMRs and genes"""
    dmr_metadata = {
        f"DMR_{row['DMR_No.']}": {
            "area": row["Area_Stat"] if "Area_Stat" in df.columns else "N/A"
        }
        for _, row in df.iterrows()
    }

    gene_metadata = {
        gene: {
            "description": df[df["Gene_Symbol_Nearby"] == gene].iloc[0][
                "Gene_Description"
            ]
            if len(df[df["Gene_Symbol_Nearby"] == gene]) > 0
            else "N/A"
        }
        for gene in gene_id_mapping
    }

    return dmr_metadata, gene_metadata


def create_plotly_graph(
    component_data,
    node_labels,
    node_positions,
    node_biclique_map,
    dmr_metadata,
    gene_metadata,
):
    """Create Plotly graph for a component using the visualization function"""
    bicliques = [
        (
            set(component["dmrs"])
            if isinstance(component["dmrs"], (list, set))
            else {component["dmrs"]},
            set(component["genes"])
            if isinstance(component["genes"], (list, set))
            else {component["genes"]},
        )
        for component in results["components"]
    ]
    # Use the create_biclique_visualization function
    return create_biclique_visualization(
        bicliques,
        node_labels,
        node_positions,
        node_biclique_map,
        dmr_metadata=dmr_metadata,
        gene_metadata=gene_metadata,
    )


@app.route("/")
def index():
    results = process_data()

    # Debugging output to check the contents of results
    print("Results:", results)

    if "error" in results:
        return f"Error: {results['error']}"

    # Check if 'dmr_metadata' and other keys are present
    if "dmr_metadata" not in results or "gene_metadata" not in results:
        return "Error: Missing metadata in results"

    # Prepare node labels and positions
    node_labels = {}
    for component in results["components"]:
        # Check if "dmrs" and "genes" are lists or single integers
        dmrs = (
            component["dmrs"]
            if isinstance(component["dmrs"], (list, set))
            else [component["dmrs"]]
        )
        genes = (
            component["genes"]
            if isinstance(component["genes"], (list, set))
            else [component["genes"]]
        )

        for node_id in dmrs:
            node_labels[node_id] = f"DMR_{node_id}"
        for node_id in genes:
            node_labels[node_id] = f"Gene_{node_id}"
    node_positions = calculate_node_positions(
        bicliques, create_node_biclique_map(bicliques)
    )

    for component in results["components"]:
        component["plotly_graph"] = create_biclique_visualization(
            [
                (set(biclique["dmrs"]), set(biclique["genes"]))
                for biclique in component["bicliques"]
            ],
            node_labels,
            node_positions,
            create_node_biclique_map(
                [
                    (set(biclique["dmrs"]), set(biclique["genes"]))
                    for biclique in component["bicliques"]
                ]
            ),
            dmr_metadata=results["dmr_metadata"],
            gene_metadata=results["gene_metadata"],
        )

    return render_template(
        "index.html",
        results=results,
        dmr_metadata=results["dmr_metadata"],
        gene_metadata=results["gene_metadata"],
    )


if __name__ == "__main__":
    app.run(debug=True)
