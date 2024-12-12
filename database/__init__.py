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
    create_tables
)

from .connection import (
    get_db_engine,
    get_db_session
)

from .cleanup import clean_database

from .operations import (
    # Core insert operations
    insert_timepoint,
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
    update_biclique_category,
    
    # Bulk population operations
    populate_dmrs,
    populate_genes,
    populate_timepoints,
    populate_statistics,
    populate_metadata,
    populate_relationships,
    
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
    process_gene_sources
)

__all__ = [
    # Classes
    'Base',
    'Timepoint',
    'Gene', 
    'DMR',
    'Biclique',
    'Component',
    'ComponentBiclique',
    'Statistic',
    'Metadata',
    'Relationship',
    'MasterGeneID',
    'GeneTimepointAnnotation',
    'DMRTimepointAnnotation',
    'TriconnectedComponent',
    
    # Connection functions
    'get_db_engine',
    'get_db_session',
    'create_tables',
    'clean_database',
    
    # Core insert operations
    'insert_timepoint',
    'insert_gene',
    'insert_dmr', 
    'insert_biclique',
    'insert_component',
    'insert_triconnected_component',
    'insert_statistics',
    'insert_metadata',
    'insert_relationship',
    'insert_component_biclique',
    
    # Annotation operations
    'upsert_gene_timepoint_annotation',
    'upsert_dmr_timepoint_annotation', 
    'update_gene_metadata',
    'update_gene_hub_status',
    'update_biclique_category',
    
    # Bulk population operations
    'populate_dmrs',
    'populate_genes',
    'populate_timepoints',
    'populate_statistics',
    'populate_metadata',
    'populate_relationships',
    
    # Query operations
    'query_timepoints',
    'query_genes',
    'query_dmrs',
    'query_bicliques', 
    'query_components',
    'query_statistics',
    'query_metadata',
    'query_relationships',
    
    # Utility operations
    'get_or_create_gene',
    'process_gene_sources'
]
