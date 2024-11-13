# file App.py
# Author: Peter Shaw

import os
import json
from flask import Flask, render_template

from processDMR import read_excel_file, create_bipartite_graph
from biclique_analysis import reporting
from biclique_analysis.processor import (
    process_bicliques,
    process_enhancer_info,
    create_node_metadata,  # Add this import
)
from biclique_analysis import (
    process_bicliques,
    process_components,
    calculate_biclique_statistics,
)
from visualization import (
    create_node_biclique_map,
    create_biclique_visualization,
    calculate_node_positions,
)
from visualization.node_info import NodeInfo

app = Flask(__name__)

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DSS1_FILE = os.path.join(DATA_DIR, "DSS1.xlsx")
HOME1_FILE = os.path.join(DATA_DIR, "HOME1.xlsx")
BICLIQUES_FILE = os.path.join(DATA_DIR, "bipartite_graph_output.txt.biclusters")


def process_data():
    """Process the DMR data and return results"""
    try:
        print("Starting data processing...")
        print(f"Using data directory: {DATA_DIR}")

        # Process DSS1 dataset using the new function
        df = read_excel_file(DSS1_FILE)
        df["Processed_Enhancer_Info"] = df[
            "ENCODE_Enhancer_Interaction(BingRen_Lab)"
        ].apply(process_enhancer_info)

        # Create gene ID mapping
        all_genes = set()
        all_genes.update(df["Gene_Symbol_Nearby"].dropna())
        all_genes.update([g for genes in df["Processed_Enhancer_Info"] for g in genes])

        # Create gene mapping starting after max DMR number
        max_dmr = df["DMR_No."].max()
        gene_id_mapping = {
            gene: idx + max_dmr + 1 for idx, gene in enumerate(sorted(all_genes))
        }

        # Create reverse mapping for labels
        reverse_gene_mapping = {v: k for k, v in gene_id_mapping.items()}

        bipartite_graph = create_bipartite_graph(df, gene_id_mapping)

        # Process bicliques
        print("Processing bicliques...")
        bicliques_result = process_bicliques(
            bipartite_graph, BICLIQUES_FILE, max(df["DMR_No."]), "DSS1"
        )

        # Create node_biclique_map before creating metadata
        node_biclique_map = create_node_biclique_map(bicliques_result["bicliques"])

        # Create metadata BEFORE processing components
        print("Creating metadata...")
        dmr_metadata = {}
        for _, row in df.iterrows():
            dmr_id = row["DMR_No."] - 1  # Convert to 0-based index
            dmr_metadata[f"DMR_{row['DMR_No.']}"] = {
                "area": str(row["Area_Stat"]) if "Area_Stat" in df.columns else "N/A",
                "description": str(row["Gene_Description"])
                if "Gene_Description" in df.columns
                else "N/A",
                "name": f"DMR_{row['DMR_No.']}",
                "bicliques": node_biclique_map.get(dmr_id, []),
            }

        gene_metadata = {}
        for gene_name, gene_id in gene_id_mapping.items():
            gene_matches = df[df["Gene_Symbol_Nearby"].str.lower() == gene_name.lower()]
            description = "N/A"
            if not gene_matches.empty and "Gene_Description" in gene_matches.columns:
                description = str(gene_matches.iloc[0]["Gene_Description"])

            gene_metadata[gene_name] = {
                "description": description,
                "id": gene_id,
                "bicliques": node_biclique_map.get(gene_id, []),
                "name": gene_name,
            }

        # Now process components with the metadata
        print("Processing components...")
        component_data = process_components(
            bipartite_graph,
            bicliques_result,
            dmr_metadata=dmr_metadata,
            gene_metadata=gene_metadata,
            gene_id_mapping=gene_id_mapping,
        )
        # Create node_biclique_map before creating metadata
        node_biclique_map = create_node_biclique_map(bicliques_result["bicliques"])

        # Create metadata using the new function
        print("Creating metadata...")
        dmr_metadata, gene_metadata = create_node_metadata(
            df, gene_id_mapping, node_biclique_map
        )

        # Before calculating positions, let's add debug logging
        print("\nDebugging node positions:")
        print(f"Number of bicliques: {len(bicliques_result['bicliques'])}")
        print(f"Sample biclique: {list(bicliques_result['bicliques'])[0]}")

        # Create node_biclique_map
        node_biclique_map = create_node_biclique_map(bicliques_result["bicliques"])
        print(f"Number of nodes in biclique map: {len(node_biclique_map)}")

        # Get all nodes that should have positions
        all_nodes = set()
        for dmr_nodes, gene_nodes in bicliques_result["bicliques"]:
            all_nodes.update(dmr_nodes)
            all_nodes.update(gene_nodes)
        print(f"Total unique nodes: {len(all_nodes)}")

        # Calculate positions
        node_positions = calculate_node_positions(
            bicliques_result["bicliques"], node_biclique_map
        )

        # Create node labels and metadata using the reporting function
        node_labels, dmr_metadata, gene_metadata = (
            reporting.create_node_labels_and_metadata(
                df, bicliques_result, gene_id_mapping, node_biclique_map
            )
        )

        # Debug output
        print("\nVisualization preparation:")
        print(f"Number of node labels: {len(node_labels)}")
        print(f"Number of node positions: {len(node_positions)}")
        print(f"Sample node labels: {list(node_labels.items())[:5]}")
        print(f"Sample DMR metadata: {list(dmr_metadata.items())[:2]}")
        print(f"Sample gene metadata: {list(gene_metadata.items())[:2]}")

        # Create node labels and metadata using the reporting function
        node_labels, dmr_metadata, gene_metadata = (
            reporting.create_node_labels_and_metadata(
                df, bicliques_result, gene_id_mapping, node_biclique_map
            )
        )

        # Debug output
        print("\nVisualization preparation:")
        print(f"Number of node labels: {len(node_labels)}")
        print(f"Number of node positions: {len(node_positions)}")
        print(f"Sample node labels: {list(node_labels.items())[:5]}")
        print(f"Sample DMR metadata: {list(dmr_metadata.items())[:2]}")
        print(f"Sample gene metadata: {list(gene_metadata.items())[:2]}")

        # Create visualization
        viz_json = create_biclique_visualization(
            bicliques_result["bicliques"],
            node_labels,
            node_positions,
            node_biclique_map,
            dmr_metadata=dmr_metadata,
            gene_metadata=gene_metadata,
            gene_id_mapping=gene_id_mapping,
        )

        # Add visualization to each component
        for component in component_data:
            if component.get("bicliques"):
                print(f"\nProcessing visualization for component {component['id']}:")
                print(f"Number of bicliques: {len(component['bicliques'])}")
                try:
                    component_viz = create_biclique_visualization(
                        formatted_bicliques,
                        node_labels,
                        node_positions,
                        node_biclique_map,
                        dmr_metadata=dmr_metadata,
                        gene_metadata=gene_metadata,
                    )
                    component["plotly_graph"] = json.loads(component_viz)
                    print(
                        f"Successfully created visualization for component {component['id']}"
                    )
                except Exception as e:
                    print(
                        f"Error creating visualization for component {component['id']}: {str(e)}"
                    )
                    import traceback

                    traceback.print_exc()

        # Update the full visualization creation
        full_viz = create_biclique_visualization(
            bicliques_result["bicliques"],
            node_labels,
            node_positions,
            node_biclique_map,
            dmr_metadata=dmr_metadata,
            gene_metadata=gene_metadata,
            bipartite_graph=bipartite_graph,  # Add this parameter
        )

        # Save full visualization
        with open("biclique_visualization.json", "w") as f:
            f.write(full_viz)

        # Create summary statistics
        stats = {
            "total_components": len(component_data),
            "components_with_bicliques": len(
                [comp for comp in component_data if comp.get("bicliques")]
            ),
            "total_bicliques": len(bicliques_result["bicliques"]),
            "non_trivial_bicliques": sum(
                1
                for comp in component_data
                if comp.get("bicliques")
                for bic in comp["bicliques"]
            ),
        }

        return {
            "stats": stats,
            "components": component_data,  # This should be a list of component dictionaries
            "coverage": bicliques_result.get("coverage", {}),
            "dmr_metadata": dmr_metadata,
            "gene_metadata": gene_metadata,
            "gene_id_mapping": gene_id_mapping,
            "node_positions": node_positions,
        }
    except Exception as e:
        print(f"Error in process_data: {str(e)}")
        import traceback

        traceback.print_exc()
        return {"error": str(e)}


def read_and_prepare_data(dss1_path=None):
    """Read and prepare the data from the Excel files"""
    try:
        print(f"Reading Excel file: {dss1_path}")
        df = read_excel_file(dss1_path or DSS1_FILE)
        print(f"Successfully read DSS1 file with {len(df)} rows")

        print("Processing enhancer info...")
        df["Processed_Enhancer_Info"] = df[
            "ENCODE_Enhancer_Interaction(BingRen_Lab)"
        ].apply(process_enhancer_info)

        print("Creating gene ID mapping...")
        all_genes = set(df["Gene_Symbol_Nearby"].dropna())
        all_genes.update([g for genes in df["Processed_Enhancer_Info"] for g in genes])

        print(f"Found {len(all_genes)} unique genes")

        gene_id_mapping = {
            gene: idx + len(df) for idx, gene in enumerate(sorted(all_genes))
        }
        print(f"Created mapping for {len(gene_id_mapping)} genes")

        return df, gene_id_mapping
    except Exception as e:
        print(f"Error in read_and_prepare_data: {str(e)}")
        import traceback

        traceback.print_exc()
        raise


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
        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Print results for debugging
        print("Results structure:", results.keys())
        print("Number of components:", len(results.get("components", [])))

        # Ensure we have all required data
        for component in results.get("components", []):
            if "plotly_graph" not in component:
                print(f"Warning: Component {component.get('id')} missing plotly_graph")

        return render_template(
            "index.html",
            results=results,
            dmr_metadata=results.get("dmr_metadata", {}),
            gene_metadata=results.get("gene_metadata", {}),
            statistics=results.get("stats", {}),
            coverage=results.get("coverage", {}),
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        return render_template("error.html", message=str(e))


@app.route("/statistics")
def statistics():
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Calculate additional statistics if needed
        detailed_stats = {
            "size_distribution": results.get("size_distribution", {}),
            "coverage": results.get("coverage", {}),
            "node_participation": results.get("node_participation", {}),
            "edge_coverage": results.get("edge_coverage", {}),
        }

        return render_template(
            "statistics.html", statistics=detailed_stats, bicliques_result=results
        )
    except Exception as e:
        return render_template("error.html", message=str(e))


if __name__ == "__main__":
    app.run(debug=True)


@app.route("/component/<int:component_id>")
def component_detail(component_id):
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        component = next(
            (c for c in results["components"] if c["id"] == component_id), None
        )

        if not component:
            return render_template(
                "error.html", message=f"Component {component_id} not found"
            )

        return render_template(
            "components.html",
            component=component,
            dmr_metadata=results["dmr_metadata"],
            gene_metadata=results["gene_metadata"],
        )
    except Exception as e:
        return render_template("error.html", message=str(e))


from biclique_analysis.processor import create_node_metadata
from processDMR import read_excel_file
