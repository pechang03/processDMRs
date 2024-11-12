# file App.py
# Author: Peter Shaw

import os
import json
from flask import Flask, render_template

from processDMR import read_excel_file, create_bipartite_graph, process_enhancer_info
from biclique_analysis import process_bicliques, process_components, calculate_biclique_statistics
from visualization import (
    create_node_biclique_map, 
    create_biclique_visualization, 
    create_component_visualization
)
from visualization.graph_layout import calculate_node_positions
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

        # Read and prepare data - only DSS1
        print("Reading Excel files...")
        df, gene_id_mapping = read_and_prepare_data(DSS1_FILE)
        bipartite_graph = create_bipartite_graph(df, gene_id_mapping)
        
        # Process bicliques
        print("Processing bicliques...")
        bicliques_result = process_bicliques(
            bipartite_graph, 
            BICLIQUES_FILE, 
            max(df["DMR_No."]), 
            "DSS1"
        )
        
        # Process components
        print("Processing components...")
        component_data = process_components(bipartite_graph, bicliques_result)
        
        # Create metadata
        print("Creating metadata...")
        dmr_metadata, gene_metadata = create_metadata(df, gene_id_mapping)

        # Calculate node positions
        node_biclique_map = create_node_biclique_map(bicliques_result["bicliques"])
        node_positions = calculate_node_positions(bicliques_result["bicliques"], node_biclique_map)

        # Create node labels
        node_labels = {}
        for dmr_id in range(len(df)):
            node_labels[dmr_id] = f"DMR_{dmr_id+1}"
        for gene_name, gene_id in gene_id_mapping.items():
            node_labels[gene_id] = gene_name

        # Add visualization to each component
        for component in component_data:
            if component.get("bicliques"):
                # Convert component bicliques to the expected format (dmr_nodes, gene_nodes) tuples
                formatted_bicliques = []
                # Create node labels mapping
                node_labels = {}
                # Add DMR labels
                for dmr_id in range(len(df)):
                    node_labels[dmr_id] = f"DMR_{dmr_id+1}"
            
                # Add gene labels using actual gene names
                for gene_name, gene_id in gene_id_mapping.items():
                    node_labels[gene_id] = gene_name  # Use gene name as label
            
                for biclique in component["bicliques"]:
                    if isinstance(biclique, dict):
                        # Extract DMR IDs
                        dmr_nodes = set(
                            dmr["id"] for dmr in biclique.get("details", {}).get("dmrs", [])
                            if isinstance(dmr, dict) and "id" in dmr
                        )
                
                        # Extract gene IDs while maintaining name mapping
                        gene_nodes = set()
                        for gene in biclique.get("details", {}).get("genes", []):
                            if isinstance(gene, dict) and "name" in gene:
                                gene_name = gene["name"]
                                if gene_name in gene_id_mapping:
                                    gene_id = gene_id_mapping[gene_name]
                                    gene_nodes.add(gene_id)
                                    # Ensure the label is set
                                    node_labels[gene_id] = gene_name
                
                        # Only add if we have valid nodes
                        if dmr_nodes and gene_nodes:
                            formatted_bicliques.append((dmr_nodes, gene_nodes))
                    elif isinstance(biclique, (list, tuple)) and len(biclique) == 2:
                        formatted_bicliques.append((set(biclique[0]), set(biclique[1])))
                    else:
                        print(f"Warning: Unexpected biclique format: {biclique}")
                        continue

                component_viz = create_biclique_visualization(
                    formatted_bicliques,  # Use the formatted bicliques
                    node_labels,  # Pass the node labels mapping
                    node_positions,
                    node_biclique_map,
                    dmr_metadata=dmr_metadata,
                    gene_metadata=gene_metadata,
                )
                component["plotly_graph"] = json.loads(component_viz)

        # Create full visualization
        full_viz = create_biclique_visualization(
            bicliques_result["bicliques"],
            node_labels,
            node_positions,
            node_biclique_map,
            dmr_metadata=dmr_metadata,
            gene_metadata=gene_metadata,
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
                1 for comp in component_data 
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
            coverage=results.get("coverage", {})
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
            "edge_coverage": results.get("edge_coverage", {})
        }

        return render_template(
            "statistics.html", 
            statistics=detailed_stats,
            bicliques_result=results
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
            (c for c in results["components"] if c["id"] == component_id), 
            None
        )
        
        if not component:
            return render_template("error.html", message=f"Component {component_id} not found")
            
        return render_template(
            "components.html",
            component=component,
            dmr_metadata=results["dmr_metadata"],
            gene_metadata=results["gene_metadata"]
        )
    except Exception as e:
        return render_template("error.html", message=str(e))
