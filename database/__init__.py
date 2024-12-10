"""Database module for DMR analysis system."""

from .schema import create_tables
from .connection import get_db_engine
from .operations import (
    insert_timepoint,
    insert_gene,
    insert_dmr,
    insert_biclique,
    insert_component,
    insert_statistics,
    insert_metadata,
    insert_relationship,
    populate_dmrs,  # Add this
    populate_genes,  # Add this
    query_timepoints,
    query_genes,
    query_dmrs,
    query_bicliques,
    query_components,
    query_statistics,
    query_metadata,
    query_relationships,
)
