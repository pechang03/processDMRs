"""Script to initialize the database for DMR analysis system."""

import os
import sys
from typing import Dict, List, Set, Tuple
import pandas as pd
import networkx as nx
from dotenv import load_dotenv
from pandas.core.api import DataFrame
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base

# from utils.constants import DSS1_FILE, DSS_PAIRWISE_FILE, BIPARTITE_GRAPH_TEMPLATE
from utils import id_mapping, constants
from utils import node_info, edge_info
from utils.graph_io import write_gene_mappings
from utils import process_enhancer_info

# from data_loader import create_bipartite_graph
# from biclique_analysis import process_timepoint_data
# from biclique_analysis import reader
# from biclique_analysis.processor import create_node_metadata
# from biclique_analysis.component_analyzer import ComponentAnalyzer
# from biclique_analysis.classifier import classify_component
# from biclique_analysis.triconnected import (
#    analyze_triconnected_components,
#    find_separation_pairs,
# )
# from biclique_analysis.component_analyzer import Analyzer, ComponentAnalyzer

from data_loader import (
    get_excel_sheets,
    read_excel_file,
    create_bipartite_graph,
    create_gene_mapping,
    # validate_original_graph,
)

from database import models, connection, operations, clean_database
from database.models import Base
from database.models import (
    ComponentBiclique,
    Relationship,
    Metadata,
    Statistic,
    Biclique,
    Component,
    DMR,
    Gene,
    Timepoint,
)
from database.populate_tables import (
    populate_timepoints,
    populate_core_genes,
    populate_dmrs,
    populate_dmr_annotations,
    populate_gene_annotations,
    populate_bicliques,
)

from database.process_timepoints import (
    process_bicliques_for_timepoint,
    get_genes_from_df,
)

Base = declarative_base()

# Load environment variables
load_dotenv()


def main():
    """Main entry point for initializing the database."""
    try:
        engine = connection.get_db_engine()
        Base.metadata.create_all(engine)
        models.create_tables(engine)
        with Session(engine) as session:
            # Clean and recreate database
            clean_database(session)
            # """
            print("\nCollecting all unique genes across timepoints...")

            # Read sheets from pairwise file
            pairwise_sheets = get_excel_sheets(constants.DSS_PAIRWISE_FILE)
            all_genes = set()
            max_dmr_id = None

            # Process DSStimeseries first
            print("\nProcessing DSStimeseries data...")
            df_DSStimeseries = read_excel_file(constants.DSS1_FILE)
            if df_DSStimeseries is not None:
                all_genes.update(get_genes_from_df(df_DSStimeseries))
                max_dmr_id = len(df_DSStimeseries) - 1

            # Process pairwise sheets
            pairwise_dfs = {}
            for sheet in pairwise_sheets:
                print(f"\nProcessing sheet: {sheet}")
                df = read_excel_file(constants.DSS_PAIRWISE_FILE, sheet_name=sheet)
                if df is not None:
                    pairwise_dfs[sheet] = df
                    all_genes.update(get_genes_from_df(df))

            # Create and write gene mapping
            gene_id_mapping = create_gene_mapping(all_genes)
            write_gene_mappings(
                gene_id_mapping, "master_gene_ids.csv", "All_Timepoints"
            )

            # Populate timepoints
            print("\nPopulating timepoints...")
            populate_timepoints(session)
            session.commit()

            # Populate genes with initial data
            print("\nPopulating genes table...")
            populate_core_genes(session, gene_id_mapping, df_DSStimeseries)
            session.commit()

            # Process DSStimeseries timepoint
            if df_DSStimeseries is not None:
                process_timepoint_data(
                    session=session,
                    df=df_DSStimeseries,
                    timepoint_name="DSStimeseries",
                    gene_id_mapping=gene_id_mapping,
                )

            # Process pairwise timepoints
            for sheet_name, df in pairwise_dfs.items():
                process_timepoint_data(
                    session=session,
                    df=df,
                    timepoint_name=sheet_name,
                    gene_id_mapping=gene_id_mapping,
                )
            # """
            print("\nDatabase initialization completed successfully")

    except Exception as e:
        print(f"An error occurred during database initialization: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
