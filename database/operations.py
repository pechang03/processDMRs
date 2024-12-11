"""Core database operations for DMR analysis system."""

from typing import Set, Dict, List, Tuple
import pandas as pd

# from utils import node_info, edge_info

from .models import TriconnectedComponent
from sqlalchemy.orm import Session
from sqlalchemy import func
from .models import (
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
)


def insert_timepoint(session: Session, name: str, description: str = None):
    """Insert a new timepoint into the database."""
    timepoint = Timepoint(name=name, description=description)
    session.add(timepoint)
    session.commit()
    return timepoint.id


def insert_dmr(session: Session, timepoint_id: int, dmr_number: int, **kwargs):
    """Insert a new DMR into the database."""
    dmr = DMR(timepoint_id=timepoint_id, dmr_number=dmr_number, **kwargs)
    session.add(dmr)
    session.commit()
    return dmr.id


def insert_biclique(
    session: Session,
    timepoint_id: int,
    component_id: int,
    dmr_ids: list,
    gene_ids: list,
):
    """Insert a new biclique into the database."""
    from biclique_analysis.classifier import classify_biclique
    
    # Classify the biclique
    category = classify_biclique(set(dmr_ids), set(gene_ids))
    
    biclique = Biclique(
        timepoint_id=timepoint_id,
        component_id=component_id,
        dmr_ids=dmr_ids,
        gene_ids=gene_ids,
        category=category.name.lower()  # Add category
    )
    session.add(biclique)
    session.commit()
    return biclique.id


def insert_component(session: Session, timepoint_id: int, **kwargs):
    """Insert a new component into the database."""
    component = Component(timepoint_id=timepoint_id, **kwargs)
    session.add(component)
    session.commit()
    return component.id


def insert_triconnected_component(
    session: Session,
    timepoint_id: int,
    size: int,
    dmr_count: int,
    gene_count: int,
    edge_count: int,
    density: float,
    category: str,
    separation_pairs: List[Tuple[int, int]],
    nodes: List[int],
    avg_dmrs: float = None,
    avg_genes: float = None,
    is_simple: bool = None,
) -> int:
    """Insert a new triconnected component into the database."""
    component = TriconnectedComponent(
        timepoint_id=timepoint_id,
        size=size,
        dmr_count=dmr_count,
        gene_count=gene_count,
        edge_count=edge_count,
        density=density,
        category=category,
        separation_pairs=separation_pairs,
        nodes=nodes,
        avg_dmrs=avg_dmrs,
        avg_genes=avg_genes,
        is_simple=is_simple,
    )
    session.add(component)
    session.commit()
    return component.id

def update_biclique_category(
    session: Session, 
    biclique_id: int,
    dmr_ids: List[int],
    gene_ids: List[int]
) -> None:
    """
    Update the category field for a biclique based on its composition.
    
    Args:
        session: Database session
        biclique_id: ID of the biclique to update
        dmr_ids: List of DMR IDs in the biclique
        gene_ids: List of gene IDs in the biclique
    """
    from biclique_analysis.classifier import classify_biclique, BicliqueSizeCategory
    
    # Get the biclique
    biclique = session.query(Biclique).get(biclique_id)
    if not biclique:
        return
        
    # Classify the biclique
    category = classify_biclique(set(dmr_ids), set(gene_ids))
    
    # Update the category
    biclique.category = category.name.lower()
    session.commit()


def insert_component_biclique(session: Session, component_id: int, biclique_id: int):
    """Insert a relationship between a component and a biclique."""
    comp_biclique = ComponentBiclique(
        component_id=component_id, biclique_id=biclique_id
    )
    session.add(comp_biclique)
    session.commit()


def insert_statistics(session: Session, category: str, key: str, value: str):
    """Insert new statistics into the database."""
    stat = Statistic(category=category, key=key, value=value)
    session.add(stat)
    session.commit()


def insert_metadata(
    session: Session, entity_type: str, entity_id: int, key: str, value: str
):
    """Insert new metadata into the database."""
    meta = Metadata(entity_type=entity_type, entity_id=entity_id, key=key, value=value)
    session.add(meta)
    session.commit()


def insert_relationship(
    session: Session,
    source_type: str,
    source_id: int,
    target_type: str,
    target_id: int,
    relationship_type: str,
):
    """Insert a new relationship into the database."""
    rel = Relationship(
        source_entity_type=source_type,
        source_entity_id=source_id,
        target_entity_type=target_type,
        target_entity_id=target_id,
        relationship_type=relationship_type,
    )
    session.add(rel)
    session.commit()


def insert_gene(
    session: Session,
    symbol: str,
    description: str = None,
    master_gene_id: int = None,
    node_type: str = "regular_gene",
    gene_type: str = None,
    interaction_source: str = None,
    promoter_info: str = None,
    degree: int = 0,
):
    """Insert a new gene into the database."""
    # Skip invalid gene symbols
    if not symbol:  # Handle None or empty string
        return None

    # Clean and lowercase the symbol
    symbol = str(symbol).strip().lower()

    # Extended validation for unnamed columns and invalid symbols
    invalid_patterns = ["unnamed:", "nan", ".", "n/a", ""]
    if any(symbol.startswith(pat) for pat in invalid_patterns) or not symbol:
        return None  # Skip invalid symbols instead of raising error

    # Check for duplicate gene symbols (case-insensitive)
    existing_gene = (
        session.query(Gene).filter(func.lower(Gene.symbol) == symbol).first()
    )
    if existing_gene:
        return existing_gene.id

    try:
        # Create or get MasterGeneID if master_gene_id is provided
        if master_gene_id is not None:
            # Try to get existing master gene ID (case-insensitive)
            master_gene = (
                session.query(MasterGeneID)
                .filter(func.lower(MasterGeneID.gene_symbol) == symbol.lower())
                .first()
            )

            if master_gene:
                master_gene_id = master_gene.id
            else:
                # Create new master gene ID
                master_gene = MasterGeneID(id=master_gene_id, gene_symbol=symbol)
                session.add(master_gene)
                try:
                    session.flush()
                except Exception as e:
                    session.rollback()
                    print(f"Error creating master gene ID for {symbol}: {str(e)}")
                    return None

        # Create the gene
        gene = Gene(
            symbol=symbol,
            description=description,
            master_gene_id=master_gene_id,
            node_type=node_type,
            gene_type=gene_type,
            interaction_source=interaction_source,
            promoter_info=promoter_info,
            degree=degree,
        )
        session.add(gene)
        try:
            session.commit()
            return gene.id
        except Exception as e:
            session.rollback()
            raise ValueError(f"Error creating gene: {str(e)}")

    except Exception as e:
        session.rollback()
        raise ValueError(f"Error inserting gene {symbol}: {str(e)}")


def update_gene_metadata(
    session: Session,
    gene_symbol: str,
    timepoint: str,
    degree: int = None,
    node_type: str = None,
    is_hub: bool = None,
):
    """Update gene metadata for a specific timepoint."""
    gene = (
        session.query(Gene)
        .filter(func.lower(Gene.symbol) == gene_symbol.lower())
        .first()
    )
    if gene:
        if degree is not None:
            gene.degree = max(
                gene.degree, degree
            )  # Keep highest degree across timepoints
        if node_type:
            if node_type == "split_gene":  # Once split, always split
                gene.node_type = "split_gene"
        if is_hub is not None:
            gene.is_hub = gene.is_hub or is_hub  # True if hub in any timepoint
        session.commit()


def get_or_create_gene(
    session: Session, symbol: str, description: str = None, master_gene_id: int = None
) -> int:
    """Get an existing gene or create a new one if it doesn't exist."""
    gene = session.query(Gene).filter_by(symbol=symbol).first()
    if gene:
        return gene.id
    else:
        return insert_gene(session, symbol, description, master_gene_id)


# Query functions
def query_timepoints(session: Session):
    """Query all timepoints."""
    return session.query(Timepoint).all()


def query_genes(session: Session):
    """Query all genes."""
    return session.query(Gene).all()


def query_dmrs(session: Session):
    """Query all DMRs."""
    return session.query(DMR).all()


def query_bicliques(session: Session):
    """Query all bicliques."""
    return session.query(Biclique).all()


def query_components(session: Session):
    """Query all components."""
    return session.query(Component).all()


def query_statistics(session: Session):
    """Query all statistics."""
    return session.query(Statistic).all()


def query_metadata(session: Session):
    """Query all metadata."""
    return session.query(Metadata).all()


def query_relationships(session: Session):
    """Query all relationships."""
    return session.query(Relationship).all()


def update_gene_hub_status(
    session: Session,
    timepoint: str,
    dominating_set: Set[int],
    gene_id_mapping: Dict[str, int],
):
    """Update hub status for genes in dominating set."""
    reverse_mapping = {v: k for k, v in gene_id_mapping.items()}

    for gene_id in dominating_set:
        if gene_id in reverse_mapping:
            gene_symbol = reverse_mapping[gene_id]
            update_gene_metadata(session, gene_symbol, timepoint, is_hub=True)


def populate_genes(
    session: Session, gene_id_mapping: dict, df_DSStimeseries: pd.DataFrame = None
):
    """Populate genes and master_gene_ids tables."""
    print("\nPopulating gene tables...")

    # First populate master_gene_ids
    genes_added = 0
    for gene_symbol, gene_id in gene_id_mapping.items():
        # Check if gene ID already exists
        existing = session.query(MasterGeneID).filter_by(id=gene_id).first()
        if not existing:
            try:
                master_gene = MasterGeneID(id=gene_id, gene_symbol=gene_symbol)
                session.add(master_gene)
                genes_added += 1
                # Commit in smaller batches to avoid memory issues
                if genes_added % 1000 == 0:
                    session.commit()
            except Exception as e:
                session.rollback()
                print(f"Error adding master gene ID for {gene_symbol}: {str(e)}")
                continue

    try:
        # Final commit for remaining genes
        session.commit()
        print(f"Added {genes_added} master gene IDs")
    except Exception as e:
        session.rollback()
        print(f"Error adding master gene IDs: {str(e)}")
        raise

    # Now populate genes table with available info
    if df_DSStimeseries is not None:
        # Process each gene source separately
        process_gene_sources(df_DSStimeseries, gene_id_mapping, session)


def process_gene_sources(
    df: pd.DataFrame, gene_id_mapping: Dict[str, int], session: Session
):
    """
    Process genes from different sources and populate the gene table with metadata.

    Args:
        df: DataFrame containing gene information
        gene_id_mapping: Mapping of gene symbols to IDs
        session: Database session
    """
    print("\nProcessing genes from different sources...")

    # Track processed genes to avoid duplicates
    processed_genes = set()

    # Process each row in the dataframe
    for _, row in df.iterrows():
        # Process nearby genes
        if "Gene_Symbol_Nearby" in df.columns and pd.notna(row["Gene_Symbol_Nearby"]):
            gene_symbol = str(row["Gene_Symbol_Nearby"]).strip().lower()
            if gene_symbol and gene_symbol not in processed_genes:
                gene_id = gene_id_mapping.get(gene_symbol)
                if gene_id:
                    gene_data = {
                        "symbol": gene_symbol,
                        "description": row.get("Gene_Description", "N/A"),
                        "master_gene_id": gene_id,
                        "node_type": "regular_gene",
                        "gene_type": "Nearby",
                        "interaction_source": "Gene_Symbol_Nearby",
                        "degree": 0,
                    }
                    insert_gene(session, **gene_data)
                    processed_genes.add(gene_symbol)

        # Process enhancer interactions
        if "ENCODE_Enhancer_Interaction(BingRen_Lab)" in df.columns:
            enhancer_info = row["ENCODE_Enhancer_Interaction(BingRen_Lab)"]
            if pd.notna(enhancer_info):
                # Split enhancer info on '/' to get gene name and promoter info
                from utils import process_enhancer_info

                genes = process_enhancer_info(enhancer_info)
                for gene in genes:
                    gene_symbol = str(gene).strip().lower()
                    if gene_symbol and gene_symbol not in processed_genes:
                        gene_id = gene_id_mapping.get(gene_symbol)
                        if gene_id:
                            # Check if there's promoter info (after '/')
                            promoter_info = None
                            if "/" in str(enhancer_info):
                                _, promoter_part = str(enhancer_info).split("/", 1)
                                promoter_info = promoter_part.strip()

                            gene_data = {
                                "symbol": gene_symbol,
                                "description": row.get("Gene_Description", "N/A"),
                                "master_gene_id": gene_id,
                                "node_type": "regular_gene",
                                "gene_type": "Enhancer",
                                "promoter_info": promoter_info,
                                "interaction_source": "ENCODE_Enhancer",
                                "degree": 0,
                            }
                            insert_gene(session, **gene_data)
                            processed_genes.add(gene_symbol)

        # Process promoter interactions
        if "ENCODE_Promoter_Interaction(BingRen_Lab)" in df.columns:
            promoter_info = row["ENCODE_Promoter_Interaction(BingRen_Lab)"]
            if pd.notna(promoter_info):
                from utils import process_enhancer_info

                genes = process_enhancer_info(
                    promoter_info
                )  # Reuse enhancer processing
                for gene in genes:
                    gene_symbol = str(gene).strip().lower()
                    if gene_symbol and gene_symbol not in processed_genes:
                        gene_id = gene_id_mapping.get(gene_symbol)
                        if gene_id:
                            gene_data = {
                                "symbol": gene_symbol,
                                "description": row.get("Gene_Description", "N/A"),
                                "master_gene_id": gene_id,
                                "node_type": "regular_gene",
                                "gene_type": "Promoter",
                                "interaction_source": "ENCODE_Promoter",
                                "degree": 0,
                            }
                            insert_gene(session, **gene_data)
                            processed_genes.add(gene_symbol)

    print(f"Processed {len(processed_genes)} unique genes")


def populate_dmrs(
    session: Session, df: pd.DataFrame, timepoint_id: int, gene_id_mapping: dict
):
    """Populate DMRs table with dominating set information."""
    # Create bipartite graph
    from data_loader import create_bipartite_graph

    bipartite_graph = create_bipartite_graph(df, gene_id_mapping, "DSStimeseries")

    # Calculate dominating set
    from rb_domination import calculate_dominating_sets

    dominating_set = calculate_dominating_sets(bipartite_graph, df, "DSStimeseries")

    for _, row in df.iterrows():
        dmr_id = row["DMR_No."] - 1  # Convert to 0-based index
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
            "is_hub": dmr_id in dominating_set,
        }
        insert_dmr(session, timepoint_id, **dmr_data)
