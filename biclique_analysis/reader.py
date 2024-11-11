# File reader.py
# Authoer: Peter Shaw
#


def read_bicliques_file(
    filename: str, max_DMR_id: int, original_graph: nx.Graph
) -> Dict:
    """Read and process bicliques from a .biclusters file."""
    statistics = {}
    bicliques = []
    dmr_coverage = set()
    gene_coverage = set()
    edge_distribution = {}

    with open(filename, "r") as f:
        lines = f.readlines()
        statistics = _parse_header_statistics(lines)
        bicliques = _parse_bicliques(lines, max_DMR_id)

    coverage_stats = _calculate_coverage(bicliques, original_graph)
    edge_distribution = _track_edge_distribution(bicliques, original_graph)

    return {
        "bicliques": bicliques,
        "statistics": statistics,
        "coverage": coverage_stats,
        "edge_distribution": edge_distribution,
    }


def _parse_header_statistics(lines: List[str]) -> Dict:
    """Parse header statistics from file lines."""
    statistics = {}
    for line in lines:
        if not line.startswith("- "):
            continue
        line = line[2:]
        if ":" in line:
            key, value = line.split(":", 1)
            statistics[key.strip()] = _convert_statistic_value(
                key.strip(), value.strip()
            )
    return statistics


def _convert_statistic_value(key: str, value: str) -> Union[int, str]:
    """Convert statistic value to appropriate type."""
    if key in ["Nb operations", "Nb splits", "Nb deletions", "Nb additions"]:
        return int(value)
    return value


# Add other helper functions...
