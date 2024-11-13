# file App.py
# Author: Peter Shaw

import os
from flask import Flask, render_template
from process_data import process_data
from processDMR import read_excel_file  # Add this import
from biclique_analysis.processor import process_enhancer_info  # Add this import

app = Flask(__name__)

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DSS1_FILE = os.path.join(DATA_DIR, "DSS1.xlsx")
HOME1_FILE = os.path.join(DATA_DIR, "HOME1.xlsx")
BICLIQUES_FILE = os.path.join(DATA_DIR, "bipartite_graph_output.txt.biclusters")


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




@app.route("/")
@app.route("/")
def index():
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Print results for debugging
        print("Results structure:", results.keys())
        print(
            "Number of interesting components:",
            len(results.get("interesting_components", [])),
        )
        print(
            "Number of simple connections:", len(results.get("simple_connections", []))
        )

        # Ensure we have all required data
        for component in results.get("interesting_components", []):
            if "plotly_graph" not in component:
                print(f"Warning: Component {component.get('id')} missing plotly_graph")

        return render_template(
            "index.html",
            results=results,
            dmr_metadata=results.get("dmr_metadata", {}),
            gene_metadata=results.get("gene_metadata", {}),
            statistics=results.get("stats", {}),
            coverage=results.get("coverage", {}),
            node_labels=results.get(
                "node_labels", {}
            ),  # Pass node_labels to the template
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
            (
                c for c in results["interesting_components"] if c["id"] == component_id
            ),  # Changed from components
            None,
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
