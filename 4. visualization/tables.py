"""Table creation functionality"""

from typing import Dict, List
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
