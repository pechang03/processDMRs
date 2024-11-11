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
from biclique_analysis.processor import process_bicliques
from biclique_analysis.components import process_components
import math
from flask import Flask

# Import utility functions from graph_utils
from visualization import (
    create_biclique_visualization,
    create_component_visualization,
    create_node_biclique_map
)

# Import the calculate_node_positions function
from graph_layout import calculate_node_positions, NodeInfo
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
        bicliques_result = process_bicliques(bipartite_graph, df, gene_id_mapping)
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
            "gene_id_mapping": gene_id_mapping,  # Add this line
        }
    except Exception as e:
        return render_template("error.html", message=str(e))


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
        for component in component_data
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
@app.route("/")
def index():
    try:
        results = process_data()
    except Exception as e:
        return render_template("error.html", message=str(e))

    # Prepare node labels and positions
    node_labels = {}
    all_nodes = set()  # Track all nodes that need positions

    # First pass: collect all nodes
    for component in results["components"]:
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

        if isinstance(dmrs, int):
            node_labels[dmrs] = f"DMR_{dmrs}"
            all_nodes.add(dmrs)
        elif isinstance(dmrs, (list, set)):
            for node_id in dmrs:
                node_labels[node_id] = f"DMR_{node_id}"
                all_nodes.add(node_id)
        if isinstance(genes, int):
            node_labels[genes] = f"Gene_{genes}"
            all_nodes.add(genes)
        elif isinstance(genes, (list, set)):
            for node_id in genes:
                node_labels[node_id] = f"Gene_{node_id}"
                all_nodes.add(node_id)

        # Add nodes from bicliques
        for biclique in component["bicliques"]:
            all_nodes.update(biclique["dmrs"])
            all_nodes.update(biclique["genes"])

    # Create bicliques list with all nodes
    bicliques = []
    # Create bicliques list
    bicliques = []
    for component in results["components"]:
        for biclique in component["bicliques"]:
            dmr_nodes = set(biclique["dmrs"])
            gene_nodes = set(biclique["genes"])
            bicliques.append((dmr_nodes, gene_nodes))

    # Use the imported function to create node_biclique_map
    node_biclique_map = create_node_biclique_map(bicliques)

    # Calculate positions for all nodes
    node_positions = calculate_node_positions(bicliques, node_biclique_map)

    # Verify all nodes have positions
    missing_nodes = all_nodes - set(node_positions.keys())
    if missing_nodes:
        print(f"Warning: Missing positions for nodes: {missing_nodes}")
        # Assign default positions for missing nodes
        for node in missing_nodes:
            # Check if node is a DMR by checking if it's less than the minimum gene ID
            min_gene_id = min(
                gene_id
                for comp in results["components"]
                for biclique in comp["bicliques"]
                for gene_id in biclique["genes"]
            )
            is_dmr = node < min_gene_id
            node_positions[node] = (0, 0.5) if is_dmr else (1, 0.5)

    # Create visualizations for each component
    for component in results["components"]:
        # Create bicliques list for this component
        component_bicliques = [
            (set(biclique["dmrs"]), set(biclique["genes"]))
            for biclique in component["bicliques"]
        ]

        # Create NodeInfo object
        all_nodes = set()
        dmr_nodes = set()
        gene_nodes = set()
        for dmrs, genes in component_bicliques:
            all_nodes.update(dmrs)
            all_nodes.update(genes)
            dmr_nodes.update(dmrs)
            gene_nodes.update(genes)

        # Calculate node degrees
        node_degrees = {}
        for node in all_nodes:
            node_degrees[node] = len(node_biclique_map.get(node, []))

        # Find min gene id to separate DMRs from genes
        min_gene_id = min(gene_nodes) if gene_nodes else float('inf')

        node_info = NodeInfo(
            all_nodes=all_nodes,
            dmr_nodes=dmr_nodes,
            regular_genes={n for n in gene_nodes if node_degrees[n] == 1},
            split_genes={n for n in gene_nodes if node_degrees[n] > 1},
            node_degrees=node_degrees,
            min_gene_id=min_gene_id
        )

        # Calculate false positive edges
        false_positive_edges = set()
        # Add edges that exist in the graph but not in any biclique
        for dmr in dmr_nodes:
            for gene in gene_nodes:
                edge_in_biclique = any(
                    dmr in dmrs and gene in genes 
                    for dmrs, genes in component_bicliques
                )
                if not edge_in_biclique:
                    false_positive_edges.add((dmr, gene))

        component["plotly_graph"] = json.loads(
            create_component_visualization(
                bicliques=component_bicliques,
                node_labels=node_labels,
                node_positions=node_positions,
                node_biclique_map=node_biclique_map,
                false_positive_edges=false_positive_edges,  # Add this
                node_info=node_info,  # Add this
                dmr_metadata=results["dmr_metadata"],
                gene_metadata=results["gene_metadata"],
                gene_id_mapping=results["gene_id_mapping"],
            )
        )

    return render_template(
        "index.html",
        results=results,
        dmr_metadata=results["dmr_metadata"],
        gene_metadata=results["gene_metadata"],
    )

@app.route("/statistics")
def statistics():
    try:
        results = process_data()
        df, gene_id_mapping = read_and_prepare_data()
        bipartite_graph = create_bipartite_graph(df, gene_id_mapping)
        
        # Get detailed statistics
        bicliques_result = process_bicliques(bipartite_graph, df, gene_id_mapping)
        statistics = calculate_biclique_statistics(
            bicliques_result["bicliques"],
            bipartite_graph
        )
        
        return render_template(
            "statistics.html",
            statistics=statistics,
            bicliques_result=bicliques_result
        )
    except Exception as e:
        return render_template("error.html", message=str(e))


if __name__ == "__main__":
    app.run(debug=True)
