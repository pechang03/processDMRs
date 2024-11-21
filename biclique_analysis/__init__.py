from .reader import read_bicliques_file
from .edge_info import EdgeInfo  # Import EdgeInfo
from .components import process_components
from .classifier import classify_biclique, classify_biclique_types
from .statistics import (
    calculate_biclique_statistics,
    calculate_coverage_statistics,
    calculate_size_distribution,
)
from .reporting import print_bicliques_summary, print_bicliques_detail
from .processor import (
    process_bicliques,
    process_enhancer_info,
    process_dataset,
    create_node_metadata,
)

# Use a set to ensure uniqueness and then convert back to a list
__all__ = list(
    set(
        [
            # Reader exports
            "read_bicliques_file",
            # Processor exports
            "process_bicliques",
            "process_enhancer_info",
            "process_dataset",
            "create_node_metadata",
            # Component exports
            "process_components",
            # Classifier exports
            "classify_biclique",
            "classify_biclique_types",
            # Statistics exports
            "calculate_biclique_statistics",
            "calculate_coverage_statistics",
            "calculate_size_distribution",
            # Reporting exports
            "EdgeInfo",
            "print_bicliques_summary",
            "print_bicliques_detail",
        ]
    )
)
