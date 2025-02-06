# File: tables.py
# Author: Peter Shaw
#
"""Table creation functionality"""

from typing import Dict, List, Set, Tuple
import plotly.graph_objs as go


def create_dmr_table(dmr_metadata: Dict[str, Dict]) -> go.Table:
    """Create a Plotly table for DMR metadata."""
    headers = ["DMR", "Area", "Bicliques"]
    rows = [
        [
            dmr,
            metadata.get("area", "N/A"),
            ", ".join(map(str, metadata.get("bicliques", []))),
        ]
        for dmr, metadata in dmr_metadata.items()
    ]
    return go.Table(header=dict(values=headers), cells=dict(values=list(zip(*rows))))


def create_gene_table(
    gene_metadata: Dict[str, Dict],
    gene_id_mapping: Dict[str, int],
    node_biclique_map: Dict[int, List[int]],
) -> go.Table:
    """Create a Plotly table for gene metadata."""
    headers = ["Gene", "Description", "Bicliques"]
    rows = [
        [
            gene,
            metadata.get("description", "N/A"),
            ", ".join(map(str, node_biclique_map.get(gene_id_mapping[gene], []))),
        ]
        for gene, metadata in gene_metadata.items()
    ]
    return go.Table(header=dict(values=headers), cells=dict(values=list(zip(*rows))))
def create_statistics_table(
    statistics: Dict,
    false_positive_edges: Set[Tuple[int, int]] = None,
    false_negative_edges: Set[Tuple[int, int]] = None
) -> go.Table:
    """Create a Plotly table for statistics summary."""
    headers = ["Metric", "Value"]
    rows = []
    
    # Coverage statistics
    dmr_cov = statistics["coverage"]["dmrs"]
    gene_cov = statistics["coverage"]["genes"]
    edge_cov = statistics["coverage"]["edges"]
    
    rows.extend([
        ["DMR Coverage", f"{dmr_cov['covered']}/{dmr_cov['total']} ({dmr_cov['percentage']:.1%})"],
        ["Gene Coverage", f"{gene_cov['covered']}/{gene_cov['total']} ({gene_cov['percentage']:.1%})"],
        ["Single Edge Coverage", f"{edge_cov['single_coverage']} ({edge_cov['single_percentage']:.1%})"],
        ["Multiple Edge Coverage", f"{edge_cov['multiple_coverage']} ({edge_cov['multiple_percentage']:.1%})"],
        ["Uncovered Edges", f"{edge_cov['uncovered']} ({edge_cov['uncovered_percentage']:.1%})"],
        ["False Positive Edges", str(len(false_positive_edges)) if false_positive_edges else "0"],
        ["False Negative Edges", str(len(false_negative_edges)) if false_negative_edges else "0"]
    ])
    
    # Size distribution summary
    size_dist = statistics["coverage"]["size_distribution"]
    if size_dist:
        rows.append(["", ""])  # Blank row for spacing
        rows.append(["Biclique Sizes", "Count"])
        for (dmrs, genes), count in sorted(size_dist.items()):
            rows.append([f"{dmrs} DMRs × {genes} genes", str(count)])
    
    return go.Table(
        header=dict(values=headers),
        cells=dict(values=list(zip(*rows)))
    )
