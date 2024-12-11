"""Database schema definitions for DMR analysis system."""

import json
from sqlalchemy.types import TypeDecorator, TEXT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    Float,
    Boolean,
    UniqueConstraint,
)

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
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)


class Gene(Base):
    __tablename__ = "genes"
    id = Column(Integer, primary_key=True)
    symbol = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    master_gene_id = Column(Integer, ForeignKey("master_gene_ids.id"))
    node_type = Column(String(30), nullable=True)
    gene_type = Column(String(30), nullable=True)
    interaction_source = Column(String(30), nullable=True)
    promoter_info = Column(String(30), nullable=True)
    degree = Column(Integer, nullable=True)
    # AI We need to code the relationship for genes-timepoint-biclique


class MasterGeneID(Base):
    __tablename__ = "master_gene_ids"
    id = Column(Integer, primary_key=True)
    gene_symbol = Column(String(255), unique=True, nullable=False)


class DMR(Base):
    __tablename__ = "dmrs"
    id = Column(Integer, primary_key=True)
    timepoint_id = Column(Integer, ForeignKey("timepoints.id"))
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

    __table_args__ = (
        UniqueConstraint("timepoint_id", "dmr_number", name="uq_dmrs_timepoint_dmr"),
    )


class Biclique(Base):
    __tablename__ = "bicliques"
    id = Column(Integer, primary_key=True)
    timepoint_id = Column(Integer, ForeignKey("timepoints.id"))
    component_id = Column(Integer, ForeignKey("components.id"))
    dmr_ids = Column(ArrayType)
    gene_ids = Column(ArrayType)


class Component(Base):
    __tablename__ = "components"
    id = Column(Integer, primary_key=True)
    timepoint_id = Column(Integer, ForeignKey("timepoints.id"))
    category = Column(String(50))
    size = Column(Integer)
    dmr_count = Column(Integer)
    gene_count = Column(Integer)
    edge_count = Column(Integer)
    density = Column(Float)


class ComponentBiclique(Base):
    __tablename__ = "component_bicliques"
    component_id = Column(Integer, ForeignKey("components.id"), primary_key=True)
    biclique_id = Column(Integer, ForeignKey("bicliques.id"), primary_key=True)


class Statistic(Base):
    __tablename__ = "statistics"
    id = Column(Integer, primary_key=True)
    category = Column(String(50))
    key = Column(String(255))
    value = Column(Text)


class Metadata(Base):
    __tablename__ = "metadata"
    id = Column(Integer, primary_key=True)
    entity_type = Column(String(50))
    entity_id = Column(Integer)
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


def create_tables(engine):
    """Create all tables in the database."""
    Base.metadata.create_all(engine)
