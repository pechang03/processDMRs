# File : __init__.py
#

from .reader import read_bicliques_file
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
    process_dataset,
    create_node_metadata,
)
from .edge_classification import classify_edges
from .writer import write_bicliques, write_analysis_results, write_component_details

# Use a set to ensure uniqueness and then convert back to a list
__all__ = list(
    set(
        [
            # Reader exports
            "read_bicliques_file",
            # Processor exports
            "process_bicliques",
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
            "print_bicliques_summary",
            "print_bicliques_detail",
            # Edge classification exports
            "classify_edges",
            # Writer exports
            "write_bicliques",
            "write_analysis_results",
            "write_component_details",
        ]
    )
)
