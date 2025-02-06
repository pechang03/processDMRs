"""Database module for DMR analysis system."""

from .models import (
    Base,
    Timepoint,
    Gene,
    DMR,
    Biclique,
    Component,
    ComponentBiclique,
    Statistic,
    Metadata,
    Relationship,
    MasterGeneID,
    GeneTimepointAnnotation,
    DMRTimepointAnnotation,
    TriconnectedComponent,
    DominatingSet,
    GOEnrichmentDMR,
    GOEnrichmentBiclique,
    TopGOProcessesDMR,
    TopGOProcessesBiclique,
    EdgeDetails,
    GeneDetails,
    create_tables,
)

from .connection import get_db_engine, get_db_session

from .cleanup import clean_database

from .operations import (
    # Core operations
    get_or_create_timepoint,
    insert_gene,
    insert_dmr,
    insert_biclique,
    insert_component,
    insert_triconnected_component,
    insert_statistics,
    insert_metadata,
    insert_relationship,
    insert_component_biclique,
    # Annotation operations
    upsert_gene_timepoint_annotation,
    upsert_dmr_timepoint_annotation,
    update_gene_metadata,
    update_gene_hub_status,
    update_gene_source_metadata,
    # Query operations
    query_timepoints,
    query_genes,
    query_dmrs,
    query_bicliques,
    query_components,
    query_statistics,
    query_metadata,
    query_relationships,
    # Utility operations
    get_or_create_gene,
    store_dominating_set,
    get_dominating_set,
)

from .biclique_processor import process_bicliques_db
from .dominating_sets import calculate_dominating_sets
from .process_timepoints import (
    process_bicliques_for_timepoint,
    get_genes_from_df,
    process_timepoint_table_data,
)

__all__ = [
    # Classes
    "Base",
    "Timepoint",
    "Gene",
    "DMR",
    "Biclique",
    "Component",
    "ComponentBiclique",
    "Statistic",
    "Metadata",
    "Relationship",
    "MasterGeneID",
    "GeneTimepointAnnotation",
    "DMRTimepointAnnotation",
    "TriconnectedComponent",
    "DominatingSet",
    "GOEnrichmentDMR",
    "GOEnrichmentBiclique",
    "TopGOProcessesDMR",
    "TopGOProcessesBiclique",
    "EdgeDetails",
    "GeneDetails",
    # Connection functions
    "get_db_engine",
    "get_db_session",
    "create_tables",
    "clean_database",
    # Core operations
    "get_or_create_timepoint",
    "insert_gene",
    "insert_dmr",
    "insert_biclique",
    "insert_component",
    "insert_triconnected_component",
    "insert_statistics",
    "insert_metadata",
    "insert_relationship",
    "insert_component_biclique",
    # Annotation operations
    "upsert_gene_timepoint_annotation",
    "upsert_dmr_timepoint_annotation",
    "update_gene_metadata",
    "update_gene_hub_status",
    "update_gene_source_metadata",
    # Processing operations
    "process_bicliques_db",
    "process_bicliques_for_timepoint",
    "process_timepoint_table_data",
    "get_genes_from_df",
    # Query operations
    "query_timepoints",
    "query_genes",
    "query_dmrs",
    "query_bicliques",
    "query_components",
    "query_statistics",
    "query_metadata",
    "query_relationships",
    # Utility operations
    "get_or_create_gene",
    "store_dominating_set",
    "get_dominating_set",
    # Dominating set operations
    "calculate_dominating_sets",
]
