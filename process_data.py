# File : process_data.py
# Author: Peter Shaw

# Author: Peter Shaw
#
# This file handles all data processing logic separate from web presentation.
# It serves as the main orchestrator for data analysis and visualization preparation.
#
# Responsibilities:
# - Read and process Excel data files
# - Create and analyze bipartite graphs
# - Process bicliques and their components
# - Generate visualization data
# - Create metadata for nodes
# - Calculate statistics
#
# Note: This separation allows the data processing logic to be used independently
# of the web interface, making it more maintainable and testable.

import os
import json
from flask import Flask, render_template

from processDMR import read_excel_file, create_bipartite_graph
from biclique_analysis import (
    processor,
    process_bicliques,
    process_enhancer_info,
    create_node_metadata,
    process_components,
    reporting,  # Add this import
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

        # Process DSS1 dataset
        df = read_excel_file(DSS1_FILE)
        df["Processed_Enhancer_Info"] = df[
            "ENCODE_Enhancer_Interaction(BingRen_Lab)"
        ].apply(process_enhancer_info)

        # Create gene ID mapping
        all_genes = set()
        # First pass: Collect and normalize all gene names
        all_genes = set()
        
        # Add genes from gene column (case-insensitive)
        gene_names = df["Gene_Symbol_Nearby"].dropna().str.strip().str.lower()
        all_genes.update(gene_names)
        
        # Add genes from enhancer info (case-insensitive)
        for genes in df["Processed_Enhancer_Info"]:
            if genes:  # Check if not None/empty
                all_genes.update(g.strip().lower() for g in genes)
        
        # Sort genes alphabetically for deterministic assignment
        sorted_genes = sorted(all_genes)
        
        # Create gene mapping starting after max DMR number
        max_dmr = df["DMR_No."].max()
        gene_id_mapping = {
            gene: idx + max_dmr + 1 
            for idx, gene in enumerate(sorted_genes)
        }
        
        print("\nGene ID Mapping Statistics:")
        print(f"Total unique genes (case-insensitive): {len(all_genes)}")
        print(f"ID range: {max_dmr + 1} to {max(gene_id_mapping.values())}")
        print("\nFirst 5 gene mappings:")
        for gene in sorted_genes[:5]:
            print(f"{gene}: {gene_id_mapping[gene]}")

        # Create gene mapping starting after max DMR number
        max_dmr = df["DMR_No."].max()
        gene_id_mapping = {
            gene: idx + max_dmr + 1 
            for idx, gene in enumerate(sorted(all_genes))  # Sort for deterministic assignment
        }
    
        print("\nGene ID Mapping Statistics:")
        print(f"Total unique genes: {len(all_genes)}")
        print(f"ID range: {max_dmr + 1} to {max(gene_id_mapping.values())}")
        print("\nFirst 5 gene mappings:")
        for gene in sorted(list(all_genes))[:5]:
            print(f"{gene}: {gene_id_mapping[gene]}")

        bipartite_graph = create_bipartite_graph(df, gene_id_mapping)

        # Process bicliques
        print("Processing bicliques...")
        bicliques_result = process_bicliques(
            bipartite_graph, 
            BICLIQUES_FILE, 
            max(df["DMR_No."]), 
            "DSS1",
            gene_id_mapping=gene_id_mapping,
            file_format=app.config.get('BICLIQUE_FORMAT', 'gene_name')  # Get format from app config
        )

        # Create node_biclique_map
        node_biclique_map = create_node_biclique_map(bicliques_result["bicliques"])

        # Create metadata
        print("Creating metadata...")
        dmr_metadata, gene_metadata = create_node_metadata(
            df, gene_id_mapping, node_biclique_map
        )

        # Calculate positions
        node_positions = calculate_node_positions(
            bicliques_result["bicliques"], node_biclique_map
        )

        # Create node labels and metadata
        node_labels, dmr_metadata, gene_metadata = (
            reporting.create_node_labels_and_metadata(
                df, bicliques_result, gene_id_mapping, node_biclique_map
            )
        )

        # Process components
        print("Processing components...")
        interesting_components, simple_connections = process_components(
            bipartite_graph,
            bicliques_result,
            dmr_metadata=dmr_metadata,
            gene_metadata=gene_metadata,
            gene_id_mapping=gene_id_mapping,
        )

        # Add visualization to each component
        for component in interesting_components:
            if component.get("bicliques") and component.get("raw_bicliques"):
                print(f"\nProcessing visualization for component {component['id']}:")
                print(f"Number of bicliques: {len(component['bicliques'])}")
                try:
                    # Extract proper biclique sets
                    processed_bicliques = extract_biclique_sets(component['bicliques'])
                    print(f"Processed bicliques: {len(processed_bicliques)}")
                    print("First biclique sizes:")
                    if processed_bicliques:
                        dmrs, genes = processed_bicliques[0]
                        print(f"DMRs: {len(dmrs)}, Genes: {len(genes)}")
    
                    component_viz = create_biclique_visualization(
                        processed_bicliques,  # Use processed bicliques instead of raw
                        node_labels,
                        node_positions,
                        node_biclique_map,
                        dmr_metadata=dmr_metadata,
                        gene_metadata=gene_metadata,
                        gene_id_mapping=gene_id_mapping,
                        bipartite_graph=bipartite_graph,
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

        # Create summary statistics
        stats = {
            "total_components": len(interesting_components),
            "components_with_bicliques": len(
                [comp for comp in interesting_components if comp.get("bicliques")]
            ),
            "total_bicliques": len(bicliques_result["bicliques"]),
            "non_trivial_bicliques": sum(
                1
                for comp in interesting_components
                if comp.get("bicliques")
                for bic in comp["bicliques"]
            ),
        }

        return {
            "stats": stats,
            "interesting_components": interesting_components,
            "simple_connections": simple_connections,
            "coverage": bicliques_result.get("coverage", {}),
            "dmr_metadata": dmr_metadata,
            "gene_metadata": gene_metadata,
            "gene_id_mapping": gene_id_mapping,
            "node_positions": node_positions,
            "node_labels": node_labels,
        }
    except Exception as e:
        print(f"Error in process_data: {str(e)}")
        import traceback

        traceback.print_exc()
        return {"error": str(e)}
