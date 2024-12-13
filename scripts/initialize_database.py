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
    create_bipartite_graph,
    create_gene_mapping,
)

from database import models, connection, operations, clean_database
from database.models import Base
from database.operations import get_or_create_timepoint
from database.populate_tables import (
    populate_timepoints,
    populate_core_genes,
)

from database.process_timepoints import (
    process_bicliques_for_timepoint,
    get_genes_from_df,
    process_timepoint_data,
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
        engine = connection.get_db_engine()
        Base.metadata.create_all(engine)
        models.create_tables(engine)

        with Session(engine) as session:
            # Clean and recreate database
            clean_database(session)

            print("\nCollecting all unique genes across timepoints...")

            # Read sheets from pairwise file
            pairwise_sheets = get_excel_sheets(dss_pairwise_file)
            all_genes = set()
            # Create and write gene mapping
            # AI NO NO NO do not write the gene mappings
            # write_gene_mappings(
            #    gene_id_mapping,
            #    os.path.join(data_dir, "master_gene_ids.csv"),
            #    "All_Timepoints",
            # )

            # Populate timepoints
            print("\nPopulating timepoints...")
            populate_timepoints(session)
            session.commit()
            
            gene_id_mapping = create_gene_mapping(all_genes)
                
            # Populate genes with initial data
            print("\nPopulating genes table...")
            populate_core_genes(session, gene_id_mapping)
            session.commit()

            ts_original_graph_file = os.path.join(data_dir, "bipartite_graph_output_DSS_overall.txt")
            ts_bicliques_file = os.path.join(data_dir, "bipartite_graph_output.txt.biclusters")
            print("\nProcessing DSS1 data...")                                                                    
            df_DSS1 = read_excel_file(dss1_file, sheet_name="DSS_Time_Series")
            if df_DSS1 is not None:                                                                               
                 print(f"Successfully read DSS1 data with {len(df_DSS1)} rows")                                    
                 all_genes.update(get_genes_from_df(df_DSS1))                                                      
                 max_dmr_id = len(df_DSS1) - 1
            else:
                print(f"Unable to read DSS1 from path {dss1_file}")
                raise Exception("Unable to read DSS1 data") 

            process_bicliques_for_timepoint(
                session=session,
                timepoint_id=get_or_create_timepoint(session, "DSStimeseries"),
                original_graph_file=ts_original_graph_file,
                bicliques_file=ts_bicliques_file,
                df=df_DSS1,
                gene_id_mapping=gene_id_mapping,
            )
            session.commit()
            # Process pairwise sheets
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
                process_timepoint_data(
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

            print("\nDatabase initialization completed successfully")

    except Exception as e:
        print(f"An error occurred during database initialization: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
