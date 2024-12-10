"""Script to initialize the database for DMR analysis system."""

import os
import sys
from typing import Dict, List, Set, Tuple
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from biclique_analysis.component_analyzer import ComponentAnalyzer
from biclique_analysis.triconnected import (
    analyze_triconnected_components,
    find_separation_pairs,
)
from biclique_analysis.classifier import classify_component
import networkx as nx
from sqlalchemy.orm import Session
from database import schema, connection, operations
from utils import id_mapping, constants
from biclique_analysis import processor, reader
from data_loader import create_bipartite_graph

from data_loader import (
    get_excel_sheets,
    read_excel_file,
    create_bipartite_graph,
    create_gene_mapping,
    # validate_bipartite_graph,
)

from utils.graph_io import write_gene_mappings
from utils import process_enhancer_info
from utils.constants import DSS1_FILE, DSS_PAIRWISE_FILE, BIPARTITE_GRAPH_TEMPLATE

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

# Load environment variables
load_dotenv()

from database.operations import populate_genes, populate_dmrs


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


def populate_bicliques(session: Session, bicliques_result: dict, timepoint_id: int):
    """Populate bicliques table."""
    for biclique in bicliques_result["bicliques"]:
        dmr_ids, gene_ids = biclique
        operations.insert_biclique(
            session, timepoint_id, None, list(dmr_ids), list(gene_ids)
        )


def process_bicliques_for_timepoint(
    session: Session,
    timepoint_id: int,
    bicliques_file: str,
    df: pd.DataFrame,
    gene_id_mapping: dict,
):
    """Process bicliques for a timepoint and store results in database."""
    print(f"\nProcessing bicliques for timepoint {timepoint_id} from {bicliques_file}")

    try:
        # Create bipartite graph from DataFrame

        bipartite_graph = create_bipartite_graph(df, gene_id_mapping)

        # Read and process bicliques
        bicliques_result = reader.read_bicliques_file(
            bicliques_file,
            bipartite_graph,
            gene_id_mapping=gene_id_mapping,
            file_format="gene_name",
        )

        if not bicliques_result or not bicliques_result.get("bicliques"):
            print("No bicliques found")
            return

        # Create biclique graph
        biclique_graph = nx.Graph()
        for dmr_nodes, gene_nodes in bicliques_result["bicliques"]:
            biclique_graph.add_nodes_from(dmr_nodes, bipartite=0)
            biclique_graph.add_nodes_from(gene_nodes, bipartite=1)
            biclique_graph.add_edges_from((d, g) for d in dmr_nodes for g in gene_nodes)

        # Process components using ComponentAnalyzer
        analyzer = ComponentAnalyzer(bipartite_graph, bicliques_result, biclique_graph)
        component_results = analyzer.analyze_components()

        # Store bicliques
        for idx, (dmr_nodes, gene_nodes) in enumerate(bicliques_result["bicliques"]):
            biclique_id = operations.insert_biclique(
                session,
                timepoint_id=timepoint_id,
                component_id=None,  # Will update after creating component
                dmr_ids=list(dmr_nodes),
                gene_ids=list(gene_nodes),
            )

        # Store components
        for comp_type, comp_data in component_results["components"].items():
            for category, count in comp_data.items():
                comp_id = operations.insert_component(
                    session,
                    timepoint_id=timepoint_id,
                    category=f"{comp_type}_{category}",
                    size=count,
                    dmr_count=len(
                        {
                            n
                            for n in bipartite_graph.nodes()
                            if bipartite_graph.nodes[n]["bipartite"] == 0
                        }
                    ),
                    gene_count=len(
                        {
                            n
                            for n in bipartite_graph.nodes()
                            if bipartite_graph.nodes[n]["bipartite"] == 1
                        }
                    ),
                    edge_count=bipartite_graph.number_of_edges(),
                    density=2.0
                    * bipartite_graph.number_of_edges()
                    / (
                        bipartite_graph.number_of_nodes()
                        * (bipartite_graph.number_of_nodes() - 1)
                    ),
                )

        # Process triconnected components
        tricomps, stats = analyze_triconnected_components(bipartite_graph)
        for comp_nodes in tricomps:
            subgraph = bipartite_graph.subgraph(comp_nodes)
            dmr_nodes = {
                n for n in comp_nodes if bipartite_graph.nodes[n]["bipartite"] == 0
            }
            gene_nodes = {
                n for n in comp_nodes if bipartite_graph.nodes[n]["bipartite"] == 1
            }

            # Find separation pairs for this component
            separation_pairs = find_separation_pairs(subgraph)

            operations.insert_triconnected_component(
                session,
                timepoint_id=timepoint_id,
                size=len(comp_nodes),
                dmr_count=len(dmr_nodes),
                gene_count=len(gene_nodes),
                edge_count=subgraph.number_of_edges(),
                density=2.0
                * subgraph.number_of_edges()
                / (len(comp_nodes) * (len(comp_nodes) - 1))
                if len(comp_nodes) > 1
                else 0,
                category=classify_component(
                    dmr_nodes, gene_nodes, [(dmr_nodes, gene_nodes)]
                ).name.lower(),
                separation_pairs=list(separation_pairs),
                nodes=list(comp_nodes),
            )

        # Store statistics
        for category, stats in bicliques_result.get("statistics", {}).items():
            if isinstance(stats, dict):
                for key, value in stats.items():
                    operations.insert_statistics(
                        session, category=category, key=key, value=str(value)
                    )

        print(f"Processed {len(bicliques_result['bicliques'])} bicliques")
        print(f"Found {len(tricomps)} triconnected components")

    except Exception as e:
        print(f"Error processing bicliques: {str(e)}")
        raise


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
            populate_timepoints(session)

            # Populate genes with initial data
            populate_genes(session, gene_id_mapping, df_DSStimeseries)

            # Process DSStimeseries timepoint
            timepoint = session.query(Timepoint).filter_by(name="DSStimeseries").first()
            if timepoint and df_DSStimeseries is not None:
                print("\nProcessing DSStimeseries timepoint...")
                populate_dmrs(session, df_DSStimeseries, timepoint.id, gene_id_mapping)

                # Create bipartite graph
                bipartite_graph = create_bipartite_graph(
                    df_DSStimeseries, gene_id_mapping, "DSStimeseries"
                )

                # Process bicliques
                biclique_file = constants.BIPARTITE_GRAPH_TEMPLATE.format(
                    "DSStimeseries"
                )
                if os.path.exists(biclique_file):
                    process_bicliques_for_timepoint(
                        session,
                        timepoint.id,
                        biclique_file,
                        df_DSStimeseries,
                        gene_id_mapping,
                    )

            # Process pairwise timepoints
            for sheet_name, df in pairwise_dfs.items():
                print(f"\nProcessing timepoint: {sheet_name}")
                try:
                    timepoint = (
                        session.query(Timepoint).filter_by(name=sheet_name).first()
                    )
                    if timepoint:
                        # Populate DMRs
                        populate_dmrs(session, df, timepoint.id, gene_id_mapping)

                        # Create bipartite graph
                        bipartite_graph = create_bipartite_graph(
                            df, gene_id_mapping, sheet_name
                        )

                        # Process bicliques
                        biclique_file = constants.BIPARTITE_GRAPH_TEMPLATE.format(
                            sheet_name
                        )
                        if os.path.exists(biclique_file):
                            process_bicliques_for_timepoint(
                                session,
                                timepoint.id,
                                biclique_file,
                                df,
                                gene_id_mapping,
                            )

                        # Update gene metadata
                        from database.operations import update_gene_metadata

                        update_gene_metadata(df, gene_id_mapping, sheet_name)

                except Exception as e:
                    print(f"Error processing timepoint {sheet_name}: {str(e)}")
                    continue

            print("\nDatabase initialization completed successfully")

    except Exception as e:
        print(f"An error occurred during database initialization: {str(e)}")
        sys.exit(1)


def get_genes_from_df(df: pd.DataFrame) -> Set[str]:
    """Extract all genes from a dataframe."""
    genes = set()

    # Get gene column
    gene_column = next(
        (
            col
            for col in ["Gene_Symbol_Nearby", "Gene_Symbol", "Gene"]
            if col in df.columns
        ),
        None,
    )
    if gene_column:
        genes.update(df[gene_column].dropna().str.strip().str.lower())

    # Get genes from enhancer/promoter info
    if "Processed_Enhancer_Info" not in df.columns:
        interaction_col = next(
            (
                col
                for col in [
                    "ENCODE_Enhancer_Interaction(BingRen_Lab)",
                    "ENCODE_Promoter_Interaction(BingRen_Lab)",
                ]
                if col in df.columns
            ),
            None,
        )

        if interaction_col:
            df["Processed_Enhancer_Info"] = df[interaction_col].apply(
                process_enhancer_info
            )

    if "Processed_Enhancer_Info" in df.columns:
        for gene_list in df["Processed_Enhancer_Info"]:
            if gene_list:
                genes.update(g.strip().lower() for g in gene_list)

    return genes


if __name__ == "__main__":
    main()
