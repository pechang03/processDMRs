"""Script to initialize the database for DMR analysis system."""

import os
import sys
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from database import schema, connection, operations
from utils import id_mapping, constants
from biclique_analysis import processor, reader

# Load environment variables
load_dotenv()


def populate_timepoints(session: Session):
    """Populate timepoints table."""
    timepoints = [
        "DSS1",  # Changed from DSStimeseries to DSS1 to match Excel sheet name
        "P21-P28_TSS",
        "P21-P40_TSS", 
        "P21-P60_TSS",
        "P21-P180_TSS",
        "TP28-TP180_TSS",
        "TP40-TP180_TSS",
        "TP60-TP180_TSS"
    ]
    for tp in timepoints:
        operations.insert_timepoint(session, tp)


def populate_genes(session: Session, gene_id_mapping: dict):
    """Populate genes table."""
    for gene_name, gene_id in gene_id_mapping.items():
        operations.insert_gene(session, gene_name, master_gene_id=gene_id)


def populate_dmrs(session: Session, df: pd.DataFrame, timepoint_id: int):
    """Populate DMRs table."""
    for _, row in df.iterrows():
        dmr_data = {
            "dmr_number": row["DMR_No."],
            "area_stat": row.get("Area_Stat"),
            "description": row.get("Gene_Description"),
            "dmr_name": row.get("DMR_Name"),
            "gene_description": row.get("Gene_Description"),
            "chromosome": row.get("Chromosome"),
            "start_position": row.get("Start"),
            "end_position": row.get("End"),
            "strand": row.get("Strand"),
            "p_value": row.get("P-value"),
            "q_value": row.get("Q-value"),
            "mean_methylation": row.get("Mean_Methylation"),
        }
        operations.insert_dmr(session, timepoint_id, **dmr_data)


def populate_bicliques(session: Session, bicliques_result: dict, timepoint_id: int):
    """Populate bicliques table."""
    for biclique in bicliques_result["bicliques"]:
        dmr_ids, gene_ids = biclique
        operations.insert_biclique(
            session, timepoint_id, None, list(dmr_ids), list(gene_ids)
        )


def populate_components(session: Session, bicliques_result: dict, timepoint_id: int):
    """Populate components table."""
    for component in bicliques_result.get("components", []):
        if isinstance(component, dict):
            comp_data = {
                "category": component.get("category"),
                "size": component.get("size"),
                "dmr_count": component.get("dmrs"),
                "gene_count": component.get("genes"),
                "edge_count": component.get("total_edges"),
                "density": component.get("density"),
            }
            comp_id = operations.insert_component(session, timepoint_id, **comp_data)
            for biclique in component.get("raw_bicliques", []):
                biclique_id = operations.insert_biclique(
                    session, timepoint_id, comp_id, list(biclique[0]), list(biclique[1])
                )
                operations.insert_component_biclique(session, comp_id, biclique_id)


def populate_statistics(session: Session, statistics: dict):
    """Populate statistics table."""
    for category, stats in statistics.items():
        for key, value in stats.items():
            operations.insert_statistics(session, category, key, str(value))


def populate_metadata(session: Session, metadata: dict):
    """Populate metadata table."""
    for entity_type, entity_data in metadata.items():
        for entity_id, entity_metadata in entity_data.items():
            for key, value in entity_metadata.items():
                operations.insert_metadata(
                    session, entity_type, entity_id, key, str(value)
                )


def populate_relationships(session: Session, relationships: list):
    """Populate relationships table."""
    for rel in relationships:
        operations.insert_relationship(session, **rel)


from database.schema import ComponentBiclique, Relationship, Metadata, Statistic, Biclique, Component, DMR, Gene, Timepoint

def clean_database(session: Session):
    """Clean out existing data from all tables."""
    print("Cleaning existing data from database...")
    try:
        # Delete in reverse order of dependencies
        session.query(ComponentBiclique).delete()
        session.query(Relationship).delete()
        session.query(Metadata).delete()
        session.query(Statistic).delete()
        session.query(Biclique).delete()
        session.query(Component).delete()
        session.query(DMR).delete()
        session.query(Gene).delete()
        session.query(Timepoint).delete()
        session.commit()
        print("Database cleaned successfully")
    except Exception as e:
        session.rollback()
        print(f"Error cleaning database: {str(e)}")
        raise

def main():
    """Main function to initialize the database."""
    try:
        # Create database engine
        engine = connection.get_db_engine()

        # Create tables
        schema.create_tables(engine)

        # Start a session
        with Session(engine) as session:
            # Clean existing data
            clean_database(session)

            # Populate timepoints
            populate_timepoints(session)

            # Process DSS1 file using data_loader function
            df_DSStimeseries = read_excel_file(constants.DSS1_FILE)
            gene_id_mapping = id_mapping.create_gene_mapping(df_DSStimeseries)
            populate_genes(session, gene_id_mapping)

            # Process each timepoint
            timepoints = operations.query_timepoints(session)
            for timepoint in timepoints:
                print(f"Processing timepoint: {timepoint.name}")
                if timepoint.name == "DSS1":
                    df = df_DSStimeseries
                else:
                    df = read_excel_file(constants.DSS_PAIRWISE_FILE, sheet_name=timepoint.name)

                if df is not None:  # Only process if we got valid data
                    # Populate DMRs
                    populate_dmrs(session, df, timepoint.id)

                # Process bicliques
                biclique_file = constants.BIPARTITE_GRAPH_TEMPLATE.format(
                    timepoint.name
                )
                if os.path.exists(biclique_file):
                    bicliques_result = reader.read_bicliques_file(
                        biclique_file,
                        None,  # No original graph needed for reading
                        gene_id_mapping=gene_id_mapping,
                        file_format="gene_name",
                    )
                    populate_bicliques(session, bicliques_result, timepoint.id)
                    populate_components(session, bicliques_result, timepoint.id)
                    populate_statistics(session, bicliques_result.get("statistics", {}))
                    populate_metadata(session, bicliques_result.get("metadata", {}))
                    populate_relationships(
                        session, bicliques_result.get("relationships", [])
                    )
                else:
                    print(f"No bicliques file found for {timepoint.name}")

            print("Database initialization completed successfully.")
    except Exception as e:
        print(f"An error occurred during database initialization: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
