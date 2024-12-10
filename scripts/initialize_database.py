"""Script to initialize the database for DMR analysis system."""

import os
import sys
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from biclique_analysis.component_analyzer import ComponentAnalyzer
from biclique_analysis.triconnected import analyze_triconnected_components, find_separation_pairs
from biclique_analysis.classifier import classify_component
import networkx as nx
from sqlalchemy.orm import Session
from database import schema, connection, operations
from utils import id_mapping, constants
from biclique_analysis import processor, reader
from data_loader import read_excel_file
from data_loader import read_gene_mapping

# Load environment variables
load_dotenv()


def populate_timepoints(session: Session):
    """Populate timepoints table."""
    timepoints = [
        "DSStimeseries",  # Changed from DSStimeseries to DSS1 to match Excel sheet name
        "P21-P28_TSS",
        "P21-P40_TSS",
        "P21-P60_TSS",
        "P21-P180_TSS",
        "TP28-TP180_TSS",
        "TP40-TP180_TSS",
        "TP60-TP180_TSS",
    ]
    for tp in timepoints:
        operations.insert_timepoint(session, tp)


def populate_genes(
    session: Session, gene_id_mapping: dict, df_DSStimeseries: pd.DataFrame = None
):
    """Populate genes and master_gene_ids tables."""
    print("\nPopulating gene tables...")

    # First populate master_gene_ids
    for gene_symbol, gene_id in gene_id_mapping.items():
        from database.schema import MasterGeneID

        master_gene = MasterGeneID(id=gene_id, gene_symbol=gene_symbol)
        session.add(master_gene)

    try:
        session.commit()
        print(f"Added {len(gene_id_mapping)} master gene IDs")
    except Exception as e:
        session.rollback()
        print(f"Error adding master gene IDs: {str(e)}")
        raise

    # Now populate genes table with available info
    genes_added = 0
    if df_DSStimeseries is not None:
        for gene_symbol, gene_id in gene_id_mapping.items():
            # Look for gene description in DSStimeseries data
            gene_rows = df_DSStimeseries[
                df_DSStimeseries["Gene_Symbol_Nearby"].str.lower()
                == gene_symbol.lower()
            ]

            description = None
            if not gene_rows.empty and "Gene_Description" in gene_rows.columns:
                description = gene_rows.iloc[0]["Gene_Description"]

            # Create gene entry with available info
            gene = Gene(
                symbol=gene_symbol,
                description=description,
                master_gene_id=gene_id,
                node_type="regular_gene",  # Default type, can be updated later
                degree=0,  # Will be updated when processing each timepoint
                is_hub=False,  # Will be updated when dominating sets are calculated
            )
            session.add(gene)
            genes_added += 1

            # Commit in batches
            if genes_added % 100 == 0:
                try:
                    session.commit()
                except Exception as e:
                    session.rollback()
                    print(f"Error adding genes batch: {str(e)}")
                    raise

    # Final commit for remaining genes
    try:
        session.commit()
        print(f"Added {genes_added} genes")
    except Exception as e:
        session.rollback()
        print(f"Error adding final genes: {str(e)}")
        raise


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


from database.schema import (
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
        engine = connection.get_db_engine()
        schema.create_tables(engine)

        with Session(engine) as session:
            clean_database(session)

            # First read master gene mapping
            gene_id_mapping = read_gene_mapping()
            if not gene_id_mapping:
                print("Error: Could not read master gene mapping")
                return

            # Read DSStimeseries data
            df_DSStimeseries = read_excel_file(constants.DSS1_FILE)

            # Populate genes with initial data
            populate_genes(session, gene_id_mapping, df_DSStimeseries)

            # Populate timepoints
            populate_timepoints(session)

            # Process DSStimeseries
            timepoint = session.query(Timepoint).filter_by(name="DSStimeseries").first()
            if timepoint:
                populate_dmrs(session, df_DSStimeseries, timepoint.id)

                # Process bicliques for DSStimeseries
                biclique_file = constants.BIPARTITE_GRAPH_TEMPLATE.format(
                    "DSStimeseries"
                )
                if os.path.exists(biclique_file):
                    bicliques_result = reader.read_bicliques_file(
                        biclique_file,
                        None,  # Original graph not needed for reading
                        gene_id_mapping=gene_id_mapping,
                        file_format="gene_name",
                    )
                    populate_bicliques(session, bicliques_result, timepoint.id)
                    populate_components(session, bicliques_result, timepoint.id)
                    populate_statistics(session, bicliques_result.get("statistics", {}))
                    populate_metadata(session, bicliques_result.get("metadata", {}))

            # Process pairwise timepoints from DSS_PAIRWISE_FILE
            print("\nProcessing pairwise timepoints...")
            xl = pd.ExcelFile(constants.DSS_PAIRWISE_FILE)

            for sheet_name in xl.sheet_names:
                print(f"\nProcessing timepoint: {sheet_name}")
                try:
                    df = pd.read_excel(
                        constants.DSS_PAIRWISE_FILE, sheet_name=sheet_name
                    )
                    if not df.empty:
                        timepoint = (
                            session.query(Timepoint).filter_by(name=sheet_name).first()
                        )
                        if timepoint:
                            populate_dmrs(session, df, timepoint.id)

                            # Process bicliques for this timepoint
                            biclique_file = constants.BIPARTITE_GRAPH_TEMPLATE.format(
                                sheet_name
                            )
                            if os.path.exists(biclique_file):
                                bicliques_result = reader.read_bicliques_file(
                                    biclique_file,
                                    None,
                                    gene_id_mapping=gene_id_mapping,
                                    file_format="gene_name",
                                )
                                populate_bicliques(
                                    session, bicliques_result, timepoint.id
                                )
                                populate_components(
                                    session, bicliques_result, timepoint.id
                                )
                                populate_statistics(
                                    session, bicliques_result.get("statistics", {})
                                )
                                populate_metadata(
                                    session, bicliques_result.get("metadata", {})
                                )

                            # Update gene metadata
                            from data_loader import update_gene_metadata

                            update_gene_metadata(df, gene_id_mapping, sheet_name)
                    else:
                        print(f"Empty sheet: {sheet_name}")
                except Exception as e:
                    print(f"Error processing sheet {sheet_name}: {str(e)}")
                    session.rollback()
                    continue

            print("Database initialization completed successfully.")

    except Exception as e:
        print(f"An error occurred during database initialization: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
