from typing import Dict, List, Tuple
import pandas as pd
import networkx as nx
from .classifier import classify_biclique, BicliqueSizeCategory



def print_bicliques_summary(bicliques_result: Dict, original_graph: nx.Graph) -> None:
    """Print detailed summary of bicliques analysis."""
    graph_name = bicliques_result["graph_info"]["name"]
    print(f"\n=== Bicliques Analysis for {graph_name} ===")

    # Basic statistics
    print(f"\nGraph Statistics:")
    print(f"DMRs: {bicliques_result['graph_info']['total_dmrs']}")
    print(f"Genes: {bicliques_result['graph_info']['total_genes']}")
    print(f"Total edges: {bicliques_result['graph_info']['total_edges']}")
    print(f"Total bicliques found: {len(bicliques_result['bicliques'])}")

    # Coverage statistics
    print(f"\nNode Coverage:")
    dmr_cov = bicliques_result["coverage"]["dmrs"]
    gene_cov = bicliques_result["coverage"]["genes"]
    print(
        f"DMRs: {dmr_cov['covered']}/{dmr_cov['total']} ({dmr_cov['percentage']:.1%})"
    )
    print(
        f"Genes: {gene_cov['covered']}/{gene_cov['total']} ({gene_cov['percentage']:.1%})"
    )

    # Edge coverage
    edge_cov = bicliques_result["coverage"]["edges"]
    print(f"\nEdge Coverage:")
    print(f"Single coverage: {edge_cov['single_coverage']} edges ({edge_cov['single_percentage']:.1%})")
    print(f"Multiple coverage: {edge_cov['multiple_coverage']} edges ({edge_cov['multiple_percentage']:.1%})")
    print(f"Uncovered: {edge_cov['uncovered']} edges ({edge_cov['uncovered_percentage']:.1%})")

    if edge_cov["uncovered"] > 0:
        print("\nSample of uncovered edges:")
        for edge in bicliques_result["debug"]["uncovered_edges"]:
            print(f"  {edge}")
        print(
            f"Total nodes involved in uncovered edges: {bicliques_result['debug']['uncovered_nodes']}"
        )

    # Validate header statistics
    header_stats = bicliques_result["debug"]["header_stats"]
    print("\nValidation of Header Statistics:")
    print(f"Nb operations: {header_stats['Nb operations']}")
    print(f"Nb splits: {header_stats['Nb splits']}")
    print(f"Nb deletions: {header_stats['Nb deletions']}")
    print(f"Nb additions: {header_stats['Nb additions']}")
    total_false_negatives = 0
    # Removed problematic code block
    pass

    # Validate statistics from header if present
    if "statistics" in bicliques_result and bicliques_result["statistics"]:
        print("\nValidation of Header Statistics:")
        for key, value in bicliques_result["statistics"].items():
            print(f"  {key}: {value}")


def print_bicliques_detail(
    bicliques_result: Dict, df: pd.DataFrame, gene_id_mapping: Dict
) -> None:
    """Print detailed information about each biclique."""
    reverse_gene_mapping = {v: k for k, v in gene_id_mapping.items()}

    # Classify all bicliques and track interesting ones
    biclique_classifications = []
    interesting_bicliques = []
    for i, (dmr_nodes, gene_nodes) in enumerate(bicliques_result["bicliques"]):
        classification = classify_biclique(dmr_nodes, gene_nodes)
        biclique_classifications.append(classification)
        if classification == "interesting":
            interesting_bicliques.append(i)

    # Track genes in interesting bicliques only
    gene_to_interesting_bicliques = {}
    for i in interesting_bicliques:
        _, gene_nodes = bicliques_result["bicliques"][i]
        for gene_id in gene_nodes:
            if gene_id not in gene_to_interesting_bicliques:
                gene_to_interesting_bicliques[gene_id] = []
            gene_to_interesting_bicliques[gene_id].append(i)

    # Find split genes (only those appearing in multiple interesting bicliques)
    split_genes = {
        gene_id: biclique_list
        for gene_id, biclique_list in gene_to_interesting_bicliques.items()
        if len(biclique_list) > 1
    }

    # Print statistics
    total_bicliques = len(bicliques_result["bicliques"])
    trivial_count = biclique_classifications.count("trivial")
    small_count = biclique_classifications.count("small")
    interesting_count = len(interesting_bicliques)

    print("\nBiclique Classification Summary:")
    print(f"Total bicliques: {total_bicliques}")
    print(f"Trivial bicliques (1 DMR, 1 gene): {trivial_count}")
    print(f"Small bicliques: {small_count}")
    print(f"Interesting bicliques (≥3 DMRs, ≥3 genes): {interesting_count}")

    # Print interesting bicliques
    print("\nBiclique Size Distribution:")
    size_distribution = {}
    for dmr_nodes, gene_nodes in bicliques_result["bicliques"]:
        size_key = (len(dmr_nodes), len(gene_nodes))
        size_distribution[size_key] = size_distribution.get(size_key, 0) + 1

    print("\nSize distribution (DMRs × Genes: Count):")
    for (dmr_count, gene_count), count in sorted(size_distribution.items()):
        print(f"{dmr_count}×{gene_count}: {count}")

    print("\nInteresting Bicliques:")
    total_false_negatives = 0
    expected_edges = len(bicliques_result["debug"]["edge_distribution"])

    for i in interesting_bicliques:  # Show all interesting bicliques
        dmr_nodes, gene_nodes = bicliques_result["bicliques"][i]

        # Only print details if it's truly interesting (≥3 DMRs and ≥3 genes)
        if classify_biclique(dmr_nodes, gene_nodes) == BicliqueSizeCategory.INTERESTING:
            print(f"\nBiclique {i+1} ({len(dmr_nodes)} DMRs, {len(gene_nodes)} genes):")

            print("  DMRs:")
            for dmr_id in sorted(dmr_nodes):
                dmr_row = df[df["DMR_No."] == dmr_id + 1].iloc[0]
                area_stat = float(dmr_row["Area_Stat"])  # Ensure it's a float
                area_stat = float(f"{area_stat:.5g}")  # Round to 5 significant figures
                dmr_name = dmr_row["DMR_Name"]
                gene_desc = dmr_row["Gene_Description"]
                desc_text = (
                    f" - {gene_desc}"
                    if pd.notna(gene_desc) and gene_desc != "N/A"
                    else ""
                )
                print(
                    f"    DMR_{dmr_id + 1} - {dmr_name} (Area: {area_stat}){desc_text}"
                )

            print("  Genes:")
            for gene_id in sorted(gene_nodes):
                gene_name = reverse_gene_mapping.get(gene_id, f"Unknown_{gene_id}")
                matching_rows = df[
                    df["Gene_Symbol_Nearby"].str.lower() == gene_name.lower()
                ]
                if not matching_rows.empty:
                    gene_desc = matching_rows.iloc[0]["Gene_Description"]
                    if pd.notna(gene_desc) and gene_desc != "N/A":
                        print(f"    {gene_name}: {gene_desc}")
                    else:
                        print(f"    {gene_name}")
                else:
                    # Print gene even if no description found
                    print(f"    {gene_name}")

    print(f"\nTotal false negative edges across all bicliques: {total_false_negatives}")
    print(
        "Note: False negative edges indicate hypothesized biclique connections that don't exist in the original graph"
    )


def create_node_labels_and_metadata(df: pd.DataFrame, 
                                  bicliques_result: Dict, 
                                  gene_id_mapping: Dict[str, int],
                                  node_biclique_map: Dict[int, List[int]]) -> Tuple[Dict, Dict, Dict]:
    """
    Create node labels and metadata for visualization.
    
    Returns:
        Tuple of (node_labels, dmr_metadata, gene_metadata)
    """
    node_labels = {}
    dmr_metadata = {}
    gene_metadata = {}
    
    print("\nDebugging node label creation:")
    
    # Process DMR metadata and labels
    print("\nProcessing DMR labels:")
    for _, row in df.iterrows():
        dmr_id = row["DMR_No."] - 1  # Convert to 0-based index
        dmr_label = f"DMR_{row['DMR_No.']}"
        
        # Debug output for first few DMRs
        if dmr_id < 5:
            print(f"Creating label for DMR {dmr_id}: {dmr_label}")
            print(f"  Area: {row['Area_Stat'] if 'Area_Stat' in df.columns else 'N/A'}")
            print(f"  Description: {row['Gene_Description'] if 'Gene_Description' in df.columns else 'N/A'}")
        
        dmr_metadata[dmr_label] = {
            "area": row["Area_Stat"] if "Area_Stat" in df.columns else "N/A",
            "description": row["Gene_Description"] if "Gene_Description" in df.columns else "N/A",
            "bicliques": node_biclique_map.get(dmr_id, [])
        }
        node_labels[dmr_id] = dmr_label

    # Process gene metadata and labels
    print("\nProcessing gene labels:")
    reverse_gene_mapping = {v: k for k, v in gene_id_mapping.items()}
    
    # Debug gene mapping
    print(f"\nGene mapping sample (first 5):")
    sample_genes = list(gene_id_mapping.items())[:5]
    for gene_name, gene_id in sample_genes:
        print(f"Gene '{gene_name}' mapped to ID {gene_id}")
    
    # Get all genes from bicliques
    all_biclique_genes = set()
    for _, genes in bicliques_result["bicliques"]:
        all_biclique_genes.update(genes)
    
    print(f"\nTotal genes in bicliques: {len(all_biclique_genes)}")
    print(f"Sample biclique genes (first 5): {sorted(list(all_biclique_genes))[:5]}")
    
    for gene_id in all_biclique_genes:
        gene_name = reverse_gene_mapping.get(gene_id, f"Gene_{gene_id}")
        
        # Debug output for first few genes
        if len(gene_metadata) < 5:
            print(f"\nProcessing gene {gene_id}:")
            print(f"  Mapped name: {gene_name}")
            
        gene_desc = "N/A"
        gene_matches = df[df["Gene_Symbol_Nearby"].str.lower() == gene_name.lower()]
        if len(gene_matches) > 0 and "Gene_Description" in gene_matches.columns:
            gene_desc = gene_matches.iloc[0]["Gene_Description"]
        
        gene_metadata[gene_name] = {
            "description": gene_desc,
            "bicliques": node_biclique_map.get(gene_id, [])
        }
        node_labels[gene_id] = gene_name
        
        # Debug output for first few genes
        if len(gene_metadata) < 5:
            print(f"  Description: {gene_desc}")
            print(f"  Bicliques: {node_biclique_map.get(gene_id, [])}")
    
    # Validation summary
    print("\nLabel creation summary:")
    print(f"Total node labels created: {len(node_labels)}")
    print(f"Total DMR metadata entries: {len(dmr_metadata)}")
    print(f"Total gene metadata entries: {len(gene_metadata)}")
    
    # Sample of created labels
    print("\nSample of created labels (first 5):")
    sample_labels = list(node_labels.items())[:5]
    for node_id, label in sample_labels:
        print(f"Node {node_id}: '{label}'")
        
    return node_labels, dmr_metadata, gene_metadata


from utils.edge_info import EdgeInfo

def create_statistics_summary(
    bicliques_result: Dict,
    edge_classification: Dict[str, List[EdgeInfo]] = None
) -> Dict:
    """
    Create a summary of statistics in a structured format.
    
    Args:
        bicliques_result: Dictionary containing bicliques analysis results
        edge_classification: Optional edge classification results from classify_edges()
        
    Returns:
        Dictionary containing formatted statistics
    """
    coverage = bicliques_result.get("coverage", {})
    dmr_cov = coverage.get("dmrs", {})
    gene_cov = coverage.get("genes", {})
    
    # Initialize edge classification counts
    edge_counts = {label: 0 for label in EdgeInfo.VALID_LABELS}
    
    # Count edges by classification if available
    if edge_classification:
        # Count regular classifications
        for label in EdgeInfo.VALID_LABELS:
            if label in edge_classification:
                edge_counts[label] = len(edge_classification[label])
        
        # Add bridge edge counts if present
        if "bridge_edges" in edge_classification:
            edge_counts["bridge_false_positive"] = len(edge_classification["bridge_edges"]["false_positives"])
            edge_counts["potential_true_bridge"] = len(edge_classification["bridge_edges"]["potential_true_bridges"])
    
    # Create summary structure
    summary = {
        "coverage": {
            "dmrs": {
                "covered": dmr_cov.get("covered", 0),
                "total": dmr_cov.get("total", 0),
                "percentage": dmr_cov.get("percentage", 0),
                "participation": dmr_cov.get("participation", {})
            },
            "genes": {
                "covered": gene_cov.get("covered", 0),
                "total": gene_cov.get("total", 0),
                "percentage": gene_cov.get("percentage", 0),
                "participation": gene_cov.get("participation", {})
            },
            "edges": {
                "classification": edge_counts,
                "total": sum(edge_counts.values()),
                "percentages": {
                    label: count / sum(edge_counts.values()) if sum(edge_counts.values()) > 0 else 0
                    for label, count in edge_counts.items()
                }
            }
        },
        "size_distribution": calculate_size_distribution(bicliques_result.get("bicliques", [])),
        "classifications": classify_biclique_types(bicliques_result.get("bicliques", []))
    }
    
    return summary


def print_bicliques_detail(
    bicliques_result: Dict, df: pd.DataFrame, gene_id_mapping: Dict
) -> None:
    """Print detailed information about each biclique."""
    reverse_gene_mapping = {v: k for k, v in gene_id_mapping.items()}

    # Classify all bicliques and track interesting ones
    biclique_classifications = []
    interesting_bicliques = []
    for i, (dmr_nodes, gene_nodes) in enumerate(bicliques_result["bicliques"]):
        classification = classify_biclique(dmr_nodes, gene_nodes)
        biclique_classifications.append(classification)
        if classification == "interesting":
            interesting_bicliques.append(i)

    # Track genes in interesting bicliques only
    gene_to_interesting_bicliques = {}
    for i in interesting_bicliques:
        _, gene_nodes = bicliques_result["bicliques"][i]
        for gene_id in gene_nodes:
            if gene_id not in gene_to_interesting_bicliques:
                gene_to_interesting_bicliques[gene_id] = []
            gene_to_interesting_bicliques[gene_id].append(i)

    # Find split genes (only those appearing in multiple interesting bicliques)
    split_genes = {
        gene_id: biclique_list
        for gene_id, biclique_list in gene_to_interesting_bicliques.items()
        if len(biclique_list) > 1
    }

    # Print statistics
    total_bicliques = len(bicliques_result["bicliques"])
    trivial_count = biclique_classifications.count("trivial")
    small_count = biclique_classifications.count("small")
    interesting_count = len(interesting_bicliques)

    print("\nBiclique Classification Summary:")
    print(f"Total bicliques: {total_bicliques}")
    print(f"Trivial bicliques (1 DMR, 1 gene): {trivial_count}")
    print(f"Small bicliques: {small_count}")
    print(f"Interesting bicliques (≥3 DMRs, ≥3 genes): {interesting_count}")

    # Print interesting bicliques
    print("\nBiclique Size Distribution:")
    size_distribution = {}
    for dmr_nodes, gene_nodes in bicliques_result["bicliques"]:
        size_key = (len(dmr_nodes), len(gene_nodes))
        size_distribution[size_key] = size_distribution.get(size_key, 0) + 1

    print("\nSize distribution (DMRs × Genes: Count):")
    for (dmr_count, gene_count), count in sorted(size_distribution.items()):
        print(f"{dmr_count}×{gene_count}: {count}")

    print("\nInteresting Bicliques:")
    total_false_negatives = 0
    expected_edges = len(bicliques_result["debug"]["edge_distribution"])

    for i in interesting_bicliques:  # Show all interesting bicliques
        dmr_nodes, gene_nodes = bicliques_result["bicliques"][i]

        # Only print details if it's truly interesting (≥3 DMRs and ≥3 genes)
        if len(dmr_nodes) >= 3 and len(gene_nodes) >= 3:
            print(f"\nBiclique {i+1} ({len(dmr_nodes)} DMRs, {len(gene_nodes)} genes):")

            print("  DMRs:")
            for dmr_id in sorted(dmr_nodes):
                dmr_row = df[df["DMR_No."] == dmr_id + 1].iloc[0]
                area_stat = float(dmr_row["Area_Stat"])  # Ensure it's a float
                area_stat = float(f"{area_stat:.5g}")  # Round to 5 significant figures
                dmr_name = dmr_row["DMR_Name"]
                gene_desc = dmr_row["Gene_Description"]
                desc_text = (
                    f" - {gene_desc}"
                    if pd.notna(gene_desc) and gene_desc != "N/A"
                    else ""
                )
                print(
                    f"    DMR_{dmr_id + 1} - {dmr_name} (Area: {area_stat}){desc_text}"
                )

            print("  Genes:")
            for gene_id in sorted(gene_nodes):
                gene_name = reverse_gene_mapping.get(gene_id, f"Unknown_{gene_id}")
                matching_rows = df[
                    df["Gene_Symbol_Nearby"].str.lower() == gene_name.lower()
                ]
                if not matching_rows.empty:
                    gene_desc = matching_rows.iloc[0]["Gene_Description"]
                    if pd.notna(gene_desc) and gene_desc != "N/A":
                        print(f"    {gene_name}: {gene_desc}")
                    else:
                        print(f"    {gene_name}")
                else:
                    # Print gene even if no description found
                    print(f"    {gene_name}")

    print(f"\nTotal false negative edges across all bicliques: {total_false_negatives}")
    print(
        "Note: False negative edges indicate hypothesized biclique connections that don't exist in the original graph"
    )
def create_node_labels_and_metadata(df: pd.DataFrame, 
                                  bicliques_result: Dict, 
                                  gene_id_mapping: Dict[str, int],
                                  node_biclique_map: Dict[int, List[int]]) -> Tuple[Dict, Dict, Dict]:
    """
    Create node labels and metadata for visualization.
    
    Returns:
        Tuple of (node_labels, dmr_metadata, gene_metadata)
    """
    node_labels = {}
    dmr_metadata = {}
    gene_metadata = {}
    
    print("\nDebugging node label creation:")
    
    # Process DMR metadata and labels
    print("\nProcessing DMR labels:")
    for _, row in df.iterrows():
        dmr_id = row["DMR_No."] - 1  # Convert to 0-based index
        dmr_label = f"DMR_{row['DMR_No.']}"
        
        # Debug output for first few DMRs
        if dmr_id < 5:
            print(f"Creating label for DMR {dmr_id}: {dmr_label}")
            print(f"  Area: {row['Area_Stat'] if 'Area_Stat' in df.columns else 'N/A'}")
            print(f"  Description: {row['Gene_Description'] if 'Gene_Description' in df.columns else 'N/A'}")
        
        dmr_metadata[dmr_label] = {
            "area": row["Area_Stat"] if "Area_Stat" in df.columns else "N/A",
            "description": row["Gene_Description"] if "Gene_Description" in df.columns else "N/A",
            "bicliques": node_biclique_map.get(dmr_id, [])
        }
        node_labels[dmr_id] = dmr_label

    # Process gene metadata and labels
    print("\nProcessing gene labels:")
    reverse_gene_mapping = {v: k for k, v in gene_id_mapping.items()}
    
    # Debug gene mapping
    print(f"\nGene mapping sample (first 5):")
    sample_genes = list(gene_id_mapping.items())[:5]
    for gene_name, gene_id in sample_genes:
        print(f"Gene '{gene_name}' mapped to ID {gene_id}")
    
    # Get all genes from bicliques
    all_biclique_genes = set()
    for _, genes in bicliques_result["bicliques"]:
        all_biclique_genes.update(genes)
    
    print(f"\nTotal genes in bicliques: {len(all_biclique_genes)}")
    print(f"Sample biclique genes (first 5): {sorted(list(all_biclique_genes))[:5]}")
    
    for gene_id in all_biclique_genes:
        gene_name = reverse_gene_mapping.get(gene_id, f"Gene_{gene_id}")
        
        # Debug output for first few genes
        if len(gene_metadata) < 5:
            print(f"\nProcessing gene {gene_id}:")
            print(f"  Mapped name: {gene_name}")
            
        gene_desc = "N/A"
        gene_matches = df[df["Gene_Symbol_Nearby"].str.lower() == gene_name.lower()]
        if len(gene_matches) > 0 and "Gene_Description" in gene_matches.columns:
            gene_desc = gene_matches.iloc[0]["Gene_Description"]
        
        gene_metadata[gene_name] = {
            "description": gene_desc,
            "bicliques": node_biclique_map.get(gene_id, [])
        }
        node_labels[gene_id] = gene_name
        
        # Debug output for first few genes
        if len(gene_metadata) < 5:
            print(f"  Description: {gene_desc}")
            print(f"  Bicliques: {node_biclique_map.get(gene_id, [])}")
    
    # Validation summary
    print("\nLabel creation summary:")
    print(f"Total node labels created: {len(node_labels)}")
    print(f"Total DMR metadata entries: {len(dmr_metadata)}")
    print(f"Total gene metadata entries: {len(gene_metadata)}")
    
    # Sample of created labels
    print("\nSample of created labels (first 5):")
    sample_labels = list(node_labels.items())[:5]
    for node_id, label in sample_labels:
        print(f"Node {node_id}: '{label}'")
        
    return node_labels, dmr_metadata, gene_metadata
