"""Script to initialize the database for DMR analysis system."""

import os
import sys
from typing import Dict, List, Set, Tuple
import pandas as pd
import networkx as nx
from dotenv import load_dotenv
from pandas.core.api import DataFrame
from sqlalchemy import create_engine
from biclique_analysis.component_analyzer import ComponentAnalyzer
from biclique_analysis.triconnected import (
    analyze_triconnected_components,
    find_separation_pairs,
)
from biclique_analysis.classifier import classify_component
from sqlalchemy.orm import Session
from database import schema, connection, operations, clean_database
from database.models import Base

from utils import id_mapping, constants
from utils import node_info, edge_info
from biclique_analysis import reader
from biclique_analysis.processor import create_node_metadata
from data_loader import create_bipartite_graph
# from biclique_analysis.component_analyzer import Analyzer, ComponentAnalyzer

from data_loader import (
    get_excel_sheets,
    read_excel_file,
    create_original_graph,
    create_gene_mapping,
    # validate_original_graph,
)
from biclique_analysis import process_timepoint_data

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
from database.operations import populate_genes, populate_dmrs
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

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


def populate_bicliques(
    # AI fix this function
    session: Session,
    split_bigraph: nx.graph,
    bicliques_result: dict,
    timepoint_id: int,
):
    """Populate bicliques table."""
    for biclique in bicliques_result["bicliques"]:
        dmr_ids, gene_ids = biclique
        operations.insert_biclique(
            session, timepoint_id, None, list(dmr_ids), list(gene_ids)
        )

    # Store bicliques
    for idx, (dmr_nodes, gene_nodes) in enumerate(bicliques_result["bicliques"]):
        # AI we need to classify this biclque and then also record is classification
        split_graph.add_edges_from((d, g) for d in dmr_nodes for g in gene_nodes)
        biclique_id = operations.insert_biclique(
            session,
            timepoint_id=timepoint_id,
            component_id=None,  # Will update after creating component
            dmr_ids=list(dmr_nodes),
            gene_ids=list(gene_nodes),
        )

        # AI todo we need to update genes and dmrs in the database with the bclilque id
        # AI As a gene can be part of more one biclique and the this varies betwen timepoints
        # AI THis detail needs a many-to-many table index by timepoint_id, gene_id with a list of blciqueids


def add_split_graph_nodes(original_graph: nx.Graph, split_graph: nx.Graph):
    """Split graph into DMRs and genes."""
    # For a given timepoint the dmr_nodes and gene_nodes are the same.
    dmr_nodes = [node for node in original_graph.nodes if node in original_graph[0]]
    gene_nodes = [node for node in original_graph.nodes if node in original_graph[1]]
    split_graph.add_nodes_from(dmr_nodes, bipartite=0)
    split_graph.add_nodes_from(gene_nodes, bipartite=1)
    ## We don't add the edge yet as the are not the same between original and split graphs


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
        original_graph = nx.Graph()
        split_graph = nx.Graph()
        original_graph = create_bipartite_graph(df, gene_id_mapping)

        # Read and process bicliques
        bicliques_result = reader.read_bicliques_file(
            bicliques_file,
            original_graph,
            gene_id_mapping=gene_id_mapping,
            file_format="gene_name",
        )

        if not bicliques_result or not bicliques_result.get("bicliques"):
            print("No bicliques found")
            return
        add_split_graph_nodes(original_graph, split_graph)
        populate_bicliques(session, split_graph, biclique_result, timepoint_id)

        # Create biclique graph
        # Process components using ComponentAnalyzer
        # AI We need to itterate through the original graph compoents first and record the componet data
        # AI original_graph -> components (original type) -> triconnected_components
        # AI split_graph -> components (split type) -> bicliques
        # AI Split vertices are vertices in the split graph that belong to more than one biclique in that component
        # AI complex split_graph components contain more than one biclique and thus split vertices (genes) are present
        # AI Functions like populate_bicliques and populate_components should be called but need to be modified to also update the tables correctly
        analyzer = ComponentAnalyzer(
            original_graph, bicliques_result, split_graph
        )  # AI this class/function may need reviewing
        component_results = analyzer.analyze_components()
        for comp_type, comp_data in component_results["components"].items():
            for category, count in comp_data.items():
                component_id = operations.insert_component(
                    session,
                    timepoint_id=timepoint_id,
                    category=f"{comp_type}_{category}",
                    size=count,
                    dmr_count=len(
                        {
                            n
                            for n in original_graph.nodes()
                            if original_graph.nodes[n]["bipartite"] == 0
                        }
                    ),
                    gene_count=len(
                        {
                            n
                            for n in original_graph.nodes()
                            if original_graph.nodes[n]["bipartite"] == 1
                        }
                    ),
                    edge_count=original_graph.number_of_edges(),
                    density=2.0
                    * original_graph.number_of_edges()
                    / (
                        original_graph.number_of_nodes()
                        * (original_graph.number_of_nodes() - 1)
                    ),
                )
                # The component can differ between timepoints
                # AI todo a timepoint, gene, component_id table is appropriate.

        # Process triconnected components
        # AI extract this block to a function
        tricomps, stats = analyze_triconnected_components(original_graph)
        for comp_nodes in tricomps:
            subgraph = original_graph.subgraph(comp_nodes)
            dmr_nodes = {
                n for n in comp_nodes if original_graph.nodes[n]["bipartite"] == 0
            }
            gene_nodes = {
                n for n in comp_nodes if original_graph.nodes[n]["bipartite"] == 1
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
            # The component can differ between timepoints
            # AI todo a timepoint, gene, component_id table is appropriate.

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


def main():
    """Main entry point for initializing the database."""
    try:
        engine = connection.get_db_engine()
        Base.metadata.create_all(engine)
        schema.create_tables(engine)
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
            populate_genes(session, gene_id_mapping, df_DSStimeseries)
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
