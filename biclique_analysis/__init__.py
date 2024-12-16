# File : __init__.py
#

from .reader import read_bicliques_file
from .components import process_components
from .classifier import classify_biclique, classify_biclique_types, BicliqueSizeCategory
from .statistics import (
    calculate_biclique_statistics,
    calculate_coverage_statistics,
    calculate_size_distribution,
)
from .reporting import print_bicliques_summary, print_bicliques_detail
from .analyzer import analyze_bicliques
from .processor import process_dataset
from .edge_classification import classify_edges
from .writer import write_bicliques, write_analysis_results, write_component_details
from utils.metadata import create_node_labels_and_metadata

# Use a set to ensure uniqueness and then convert back to a list
__all__ = list(
    set(
        [
            # Reader exports
            "read_bicliques_file",
            # Analyzer exports
            "analyze_bicliques",
            # Processor exports
            "process_dataset",
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
            # Metadata exports
            "create_node_labels_and_metadata",
            # Timepoint processing
            "process_timepoint",
        ]
    )
)
