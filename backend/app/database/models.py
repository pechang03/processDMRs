"""Database schema definitions for DMR analysis system."""

import json
from typing import List, Optional

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    ARRAY,
    Float,
    Boolean,
    UniqueConstraint,
    Index,
    DateTime,
)
from sqlalchemy.types import TypeDecorator, TEXT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class ArrayType(TypeDecorator):
    """Convert between Python list and string stored in database."""

    impl = TEXT

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value)


class Timepoint(Base):
    __tablename__ = "timepoints"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)  # Display name without _TSS
    sheet_name = Column(String(255), unique=True, nullable=False)  # Original sheet name
    description = Column(Text)
    dmr_id_offset = Column(Integer, default=0)
    components = relationship(
        "Component", cascade="all, delete-orphan", back_populates="timepoint"
    )
    bicliques = relationship(
        "Biclique", cascade="all, delete-orphan", back_populates="timepoint"
    )
    dominating_set_dmrs = relationship("DominatingSet", back_populates="timepoint")


class Gene(Base):
    __tablename__ = "genes"
    id = Column(Integer, primary_key=True)
    symbol = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    master_gene_id = Column(Integer, ForeignKey("master_gene_ids.id"))
    interaction_source = Column(String(30), nullable=True)
    promoter_info = Column(String(30), nullable=True)
    master_gene = relationship("MasterGeneID", back_populates="genes")
    # AI We need to code the relationship for genes-timepoint-biclique


class GeneTimepointAnnotation(Base):
    __tablename__ = "gene_timepoint_annotations"
    timepoint_id = Column(Integer, ForeignKey("timepoints.id"), primary_key=True)
    gene_id = Column(Integer, ForeignKey("genes.id"), primary_key=True)
    component_id = Column(Integer, ForeignKey("components.id"), primary_key=False)
    triconnected_id = Column(
        Integer, ForeignKey("triconnected_components.id"), nullable=True
    )  # 1:1
    degree = Column(Integer, nullable=True)
    node_type = Column(String(30), nullable=True)
    gene_type = Column(String(30), nullable=True)
    is_isolate = Column(Boolean, default=False)
    biclique_ids = Column(ArrayType, nullable=True)


# AI MasterGeneID is a table separte to Genes. It should be used to find the ID for genes
# But is a separte entity to the genes table as it is independent to the genes


class MasterGeneID(Base):
    __tablename__ = "master_gene_ids"
    id = Column(Integer, primary_key=True)
    gene_symbol = Column(String(255), nullable=False)
    genes = relationship("Gene", back_populates="master_gene")

    __table_args__ = (
        Index(
            "ix_master_gene_ids_gene_symbol_lower", func.lower(gene_symbol), unique=True
        ),
    )


class DMR(Base):
    __tablename__ = "dmrs"
    timepoint_id = Column(Integer, ForeignKey("timepoints.id"))
    id = Column(Integer, primary_key=True)
    dmr_number = Column(Integer, nullable=False)
    area_stat = Column(Float)
    description = Column(Text)
    dmr_name = Column(String(255))
    gene_description = Column(Text)
    chromosome = Column(String(50))
    start_position = Column(Integer)
    end_position = Column(Integer)
    strand = Column(String(1))
    p_value = Column(Float)
    q_value = Column(Float)
    mean_methylation = Column(Float)
    is_hub = Column(Boolean, default=False)  # Single definition
    dominating_set_entries = relationship("DominatingSet", back_populates="dmr")

    __table_args__ = (
        UniqueConstraint("timepoint_id", "dmr_number", name="uq_dmrs_timepoint_dmr"),
    )


class DMRTimepointAnnotation(Base):
    __tablename__ = "dmr_timepoint_annotations"
    timepoint_id = Column(Integer, ForeignKey("timepoints.id"), primary_key=True)
    dmr_id = Column(Integer, ForeignKey("dmrs.id"), primary_key=True)
    component_id = Column(Integer, ForeignKey("components.id"), primary_key=False)
    triconnected_id = Column(
        Integer, ForeignKey("triconnected_components.id"), nullable=True
    )  # 1:1
    degree = Column(Integer, nullable=True)
    node_type = Column(String(30), nullable=True)
    gene_type = Column(String(30), nullable=True)
    is_isolate = Column(Boolean, default=False)
    biclique_ids = Column(ArrayType, nullable=True)


class Metadata(Base):
    __tablename__ = "metadata"
    id = Column(Integer, primary_key=True)
    entity_type = Column(String(50))
    entity_id = Column(Integer, ForeignKey("bicliques.id"))  # Add the ForeignKey
    key = Column(String(255))
    value = Column(Text)


class Biclique(Base):
    __tablename__ = "bicliques"
    id = Column(Integer, primary_key=True)
    timepoint_id = Column(Integer, ForeignKey("timepoints.id"))
    component_id = Column(Integer, ForeignKey("components.id"))
    category = Column(String(50))
    encoding = Column(String(255))
    dmr_ids = Column(ArrayType)
    gene_ids = Column(ArrayType)
    timepoint = relationship("Timepoint", back_populates="bicliques")
    component = relationship("Component", back_populates="bicliques")
    component_bicliques = relationship("ComponentBiclique", back_populates="biclique")
    biclique_metadata = relationship(
        "Metadata",
        backref="biclique",
        foreign_keys=[Metadata.entity_id],
        primaryjoin="and_(Metadata.entity_type=='biclique', "
        "Metadata.entity_id==Biclique.id)",
    )


class Component(Base):
    __tablename__ = "components"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timepoint_id = Column(Integer, ForeignKey("timepoints.id"))
    graph_type = Column(String(50), nullable=False)  # 'original' or 'split'
    category = Column(String(50))
    size = Column(Integer)
    dmr_count = Column(Integer)
    gene_count = Column(Integer)
    edge_count = Column(Integer)
    density = Column(Float)
    endcoding = Column(String(255))
    bicliques = relationship("Biclique", back_populates="component")
    component_bicliques = relationship("ComponentBiclique", back_populates="component")
    timepoint = relationship("Timepoint", back_populates="components")


# AI there are two different graphs the original graph and the biconnected graph
# Biclique apply o the biclique graph
class ComponentBiclique(Base):
    __tablename__ = "component_bicliques"
    timepoint_id = Column(Integer, ForeignKey("timepoints.id"), primary_key=True)
    component_id = Column(Integer, ForeignKey("components.id"), primary_key=True)
    biclique_id = Column(Integer, ForeignKey("bicliques.id"), primary_key=True)
    # Add these relationships:
    component = relationship("Component", back_populates="component_bicliques")
    biclique = relationship("Biclique", back_populates="component_bicliques")


# AI there are two different graphs the original graph and the biconnected graph
# Triconnected componets apply to the orriginal graph
class TriconnectedComponent(Base):
    __tablename__ = "triconnected_components"
    id = Column(Integer, primary_key=True)
    timepoint_id = Column(Integer, ForeignKey("timepoints.id"))
    component_id = Column(Integer, ForeignKey("components.id"))
    dmr_ids = Column(ArrayType)
    gene_ids = Column(ArrayType)
    category = Column(String(50))
    endcoding = Column(String(255))

    # Basic metrics
    size = Column(Integer)
    dmr_count = Column(Integer)
    gene_count = Column(Integer)
    edge_count = Column(Integer)
    density = Column(Float)

    # Classification
    is_simple = Column(Boolean, default=False)

    # Component structure
    nodes = Column(ArrayType)  # Store actual nodes in component
    separation_pairs = Column(ArrayType)  # Store pairs that separate component

    # Additional statistics
    avg_dmrs = Column(Float)  # Average DMRs for interesting components
    avg_genes = Column(Float)  # Average genes for interesting components


class Statistic(Base):
    __tablename__ = "statistics"
    id = Column(Integer, primary_key=True)
    category = Column(String(50))
    key = Column(String(255))
    value = Column(Text)


class Relationship(Base):
    __tablename__ = "relationships"
    id = Column(Integer, primary_key=True)
    source_entity_type = Column(String(50))
    source_entity_id = Column(Integer)
    target_entity_type = Column(String(50))
    target_entity_id = Column(Integer)
    relationship_type = Column(String(50))


from sqlalchemy import DateTime


class EdgeDetails(Base):
    __tablename__ = "edge_details"
    
    dmr_id = Column(Integer, ForeignKey("dmrs.id"), primary_key=True)
    gene_id = Column(Integer, ForeignKey("genes.id"), primary_key=True)
    timepoint_id = Column(Integer, ForeignKey("timepoints.id"), primary_key=True)
    edge_type = Column(String(50))  # e.g., 'nearby', 'enhancer', 'promoter'
    edit_type = Column(String(50))  # For tracking modifications
    distance_from_tss = Column(Integer)
    description = Column(Text)

    # Relationships
    dmr = relationship("DMR", backref="edge_details")
    gene = relationship("Gene", backref="edge_details")
    timepoint = relationship("Timepoint", backref="edge_details")


class DominatingSet(Base):
    __tablename__ = "dominating_sets"
    timepoint_id = Column(Integer, ForeignKey("timepoints.id"), primary_key=True)
    dmr_id = Column(Integer, ForeignKey("dmrs.id"), primary_key=True)
    area_stat = Column(Float)  # Store the area statistic used in calculation
    utility_score = Column(Float)  # Store the utility score from the greedy algorithm
    dominated_gene_count = Column(Integer)  # Number of genes this DMR dominates
    calculation_timestamp = Column(
        DateTime, default=func.now()
    )  # When this was calculated

    # Relationships
    timepoint = relationship("Timepoint", back_populates="dominating_set_dmrs")
    dmr = relationship("DMR", back_populates="dominating_set_entries")


def create_tables(engine):
    """Create all tables in the database."""
    Base.metadata.create_all(engine)
