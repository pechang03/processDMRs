"""SQLAlchemy models for DMR analysis system."""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, ARRAY, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Timepoint(Base):
    __tablename__ = 'timepoints'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    dmrs = relationship("DMR", back_populates="timepoint")
    bicliques = relationship("Biclique", back_populates="timepoint")
    components = relationship("Component", back_populates="timepoint")

class Gene(Base):
    __tablename__ = 'genes'
    id = Column(Integer, primary_key=True)
    symbol = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    master_gene_id = Column(Integer, ForeignKey('master_gene_ids.id'))
    node_type = Column(String(50))  # regular_gene, split_gene
    degree = Column(Integer, default=0)
    from sqlalchemy import Boolean
    is_hub = Column(Boolean, default=False)
    master_gene = relationship("MasterGeneID", back_populates="genes")

class MasterGeneID(Base):
    __tablename__ = 'master_gene_ids'
    id = Column(Integer, primary_key=True)
    gene_symbol = Column(String(255), unique=True, nullable=False)
    genes = relationship("Gene", back_populates="master_gene")

class DMR(Base):
    __tablename__ = 'dmrs'
    id = Column(Integer, primary_key=True)
    timepoint_id = Column(Integer, ForeignKey('timepoints.id'))
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
    timepoint = relationship("Timepoint", back_populates="dmrs")
    __table_args__ = (UniqueConstraint('timepoint_id', 'dmr_number', name='uq_dmrs_timepoint_dmr'),)

class Biclique(Base):
    __tablename__ = 'bicliques'
    id = Column(Integer, primary_key=True)
    timepoint_id = Column(Integer, ForeignKey('timepoints.id'))
    component_id = Column(Integer, ForeignKey('components.id'))
    dmr_ids = Column(ARRAY(Integer))
    gene_ids = Column(ARRAY(Integer))
    timepoint = relationship("Timepoint", back_populates="bicliques")
    component = relationship("Component", back_populates="bicliques")

class Component(Base):
    __tablename__ = 'components'
    id = Column(Integer, primary_key=True)
    timepoint_id = Column(Integer, ForeignKey('timepoints.id'))
    category = Column(String(50))
    size = Column(Integer)
    dmr_count = Column(Integer)
    gene_count = Column(Integer)
    edge_count = Column(Integer)
    density = Column(Float)
    timepoint = relationship("Timepoint", back_populates="components")
    bicliques = relationship("Biclique", back_populates="component")
    component_bicliques = relationship("ComponentBiclique", back_populates="component")

class ComponentBiclique(Base):
    __tablename__ = 'component_bicliques'
    component_id = Column(Integer, ForeignKey('components.id'), primary_key=True)
    biclique_id = Column(Integer, ForeignKey('bicliques.id'), primary_key=True)
    component = relationship("Component", back_populates="component_bicliques")
    biclique = relationship("Biclique")

class Statistic(Base):
    __tablename__ = 'statistics'
    id = Column(Integer, primary_key=True)
    category = Column(String(50))
    key = Column(String(255))
    value = Column(Text)

class Metadata(Base):
    __tablename__ = 'metadata'
    id = Column(Integer, primary_key=True)
    entity_type = Column(String(50))
    entity_id = Column(Integer)
    key = Column(String(255))
    value = Column(Text)

class Relationship(Base):
    __tablename__ = 'relationships'
    id = Column(Integer, primary_key=True)
    source_entity_type = Column(String(50))
    source_entity_id = Column(Integer)
    target_entity_type = Column(String(50))
    target_entity_id = Column(Integer)
    relationship_type = Column(String(50))
