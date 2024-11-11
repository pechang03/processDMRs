from typing import Dict
import pandas as pd
import networkx as nx

from biclique_analysis.classifier import classify_biclique


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
    print(f"Single coverage: {edge_cov['single_coverage']} edges")
    print(f"Multiple coverage: {edge_cov['multiple_coverage']} edges")
    print(
        f"Uncovered: {edge_cov['uncovered']} edges ({edge_cov['uncovered']/edge_cov['total']:.1%})"
    )

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
    for biclique in bicliques_result["bicliques"]:
        dmr_nodes, gene_nodes = biclique
        for dmr in dmr_nodes:
            for gene in gene_nodes:
                if not original_graph.has_edge(dmr, gene):
                    total_false_negatives += 1
    print(f"Total false negative edges across all bicliques: {total_false_negatives}")
    print(f"Total false positive edges (deletions): {header_stats['Nb deletions']}")

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

    print(f"\nTotal false negative edges across all bicliques: {total_false_negatives}")
    print(
        "Note: False negative edges indicate hypothesized biclique connections that don't exist in the original graph"
    )
