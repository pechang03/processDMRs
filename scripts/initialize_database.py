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

from data_loader import (
    get_excel_sheets,
    read_excel_file,
    read_gene_mapping,
    create_bipartite_graph,
    # create_gene_mapping, NO No NO
)

from database import models, connection, operations, clean_database
from database.models import Base
from database.operations import get_or_create_timepoint
from database.populate_tables import (
    populate_timepoints,
    populate_master_gene_ids,
    populate_core_genes,
)

from database.process_timepoints import (
    process_bicliques_for_timepoint,
    get_genes_from_df,
    process_timepoint_table_data,
)

Base = declarative_base()

# Load environment variables from sample.env
load_dotenv("sample.env")


def main():
    """Main entry point for initializing the database."""
    try:
        # Get paths from environment variables
        data_dir = os.getenv("DATA_DIR", "./data")
        dss1_file = os.getenv("DSS1_FILE", os.path.join(data_dir, "DSS1.xlsx"))

        dss_pairwise_file = os.getenv(
            "DSS_PAIRWISE_FILE", os.path.join(data_dir, "DSS_PAIRWISE.xlsx")
        )
        # Create engine and ensure tables exist
        engine = connection.get_db_engine()
        models.Base.metadata.drop_all(engine)  # Drop all existing tables
        models.Base.metadata.create_all(engine)  # Create fresh tables
        
        with Session(engine) as session:
            # Clean database (this will now just clear data, not schema)
            clean_database(session)

            print("\nCollecting all unique genes across timepoints...")

            # Read sheets from both files
            timeseries_sheet = "DSS_Time_Series"  # The sheet name from DSS1.xlsx
            pairwise_sheets = get_excel_sheets(dss_pairwise_file)
            
            print(f"Timeseries sheet: {timeseries_sheet}")
            print(f"Pairwise sheets: {pairwise_sheets}")
            
            # Populate timepoints with both timeseries and pairwise sheets
            print("\nPopulating timepoints...")
            populate_timepoints(session, timeseries_sheet, pairwise_sheets, start_gene_id)
            session.commit()

            gene_id_mapping = read_gene_mapping(
                os.path.join(data_dir, "master_gene_ids.csv")
            )

            populate_master_gene_ids(session, gene_id_mapping)

            # Populate genes with initial data
            print("\nPopulating genes table...")
            populate_core_genes(session, gene_id_mapping)
            session.commit()
            print(f"Debug: timeseries spreadshet file {dss1_file} ")

            if not os.path.exists(dss1_file):
                print(f"Warning: timeseries spreadshet file {dss1_file} not found")
                raise Exception("DSS1 file not found")
            df_DSS1 = read_excel_file(dss1_file, sheet_name="DSS_Time_Series")
            max_dmr_id = 0
            print("\nProcessing DSS1 data...")
            if df_DSS1 is not None:
                print(f"Successfully read DSS1 data with {len(df_DSS1)} rows")
                all_genes.update(get_genes_from_df(df_DSS1))
                max_dmr_id = len(df_DSS1) - 1
            else:
                print(f"Unable to read DSS1 from path {dss1_file}")
                raise Exception("Unable to read DSS1 data")
            ts_original_graph_file = os.path.join(
                data_dir, "bipartite_graph_output_DSS_overall.txt"
            )
            ts_bicliques_file = os.path.join(
                data_dir, "bipartite_graph_output.txt.biclusters"
            )
            print(ts_original_graph_file)
            timepoint_id = get_or_create_timepoint(session, "DSStimeseries")
            process_timepoint_table_data(
                session, timepoint_id, df_DSS1, gene_id_mapping
            )
            session.commit()
            process_bicliques_for_timepoint(
                session=session,
                timepoint_id=timepoint_id,
                timepoint_name="DSStimeseries",
                original_graph_file=ts_original_graph_file,
                bicliques_file=ts_bicliques_file,
                df=df_DSS1,
                gene_id_mapping=gene_id_mapping,
                file_format="gene_name",
            )
            session.commit()
            # Process pairwise sheets
            """
            pairwise_dfs = {}
            for sheet in pairwise_sheets:
                print(f"\nProcessing sheet: {sheet}")
                df_sheet = read_excel_file(dss_pairwise_file, sheet_name=sheet)
                if df_sheet is not None:
                    pairwise_dfs[sheet] = df_sheet
                    #all_genes.update(get_genes_from_df(df))

                original_graph_file = os.path.join(
                    data_dir, "bipartite_graph_output_", f"{sheet}.txt"
                )
                bicliques_file = os.path.join(data_dir, "bipartite_graph_output.txt.", f"{sheet}_bicluster")
                timepoint_id = get_or_create_timepoint(session, sheet)
                process_timepoint_table_data(
                    session=session,
                    timepoint_id=timepoint_id,
                    df=df_sheet,
                    gene_id_mapping=gene_id_mapping
                )
                original_graph_file = os.path.join(data_dir, f"bipartite_graph_output_{sheet}.txt")
                bicliques_file = os.path.join(data_dir, f"bipartite_graph_output_{sheet}.txt.biclusters")
                
                process_bicliques_for_timepoint(
                    session=session,
                    timepoint_id=get_or_create_timepoint(session, sheet),
                    original_graph_file=original_graph_file,
                    bicliques_file=bicliques_file,
                    df=df_sheet,
                    gene_id_mapping=gene_id_mapping,
                )
            session.commit()
            """
            print("\nDatabase initialization completed successfully")

    except Exception as e:
        print(f"An error occurred during database initialization: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
