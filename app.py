print("Server starting with updated templates...")

# file App.py
# Author: Peter Shaw

import os
from flask import Flask, render_template
from routes import index
from process_data import process_data

app = Flask(__name__)

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DSS1_FILE = os.path.join(DATA_DIR, "DSS1.xlsx")
HOME1_FILE = os.path.join(DATA_DIR, "HOME1.xlsx")
BICLIQUES_FILE = os.path.join(DATA_DIR, "bipartite_graph_output.txt.biclusters")


from processDMR import read_excel_file
from biclique_analysis.processor import process_enhancer_info

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


from flask import Flask
from routes import index_route, statistics_route, component_detail_route

app = Flask(__name__)

# Register routes
app.add_url_rule('/', 'index_route', index_route)
app.add_url_rule('/statistics', 'statistics_route', statistics_route)
app.add_url_rule('/component/<int:component_id>', 'component_detail', component_detail_route)

if __name__ == "__main__":
    app.run(debug=True)
