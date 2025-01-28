from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float, JSON, Index
from sqlalchemy.orm import relationship, declarative_base

from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

Base = declarative_base()


class EdgeDetails(Base):
    __tablename__ = "edge_details"

    # Composite primary key columns
    dmr_id = Column(Integer, ForeignKey("dmrs.id"), primary_key=True)
    gene_id = Column(Integer, ForeignKey("genes.id"), primary_key=True)
    timepoint_id = Column(Integer, ForeignKey("timepoints.id"), primary_key=True)

    # Additional columns
    edge_type = Column(String(50))
    edit_type = Column(String(50))
    distance_from_tss = Column(Integer)
    description = Column(Text)

    # Relationships
    dmr = relationship("Dmr", back_populates="edge_details")
    gene = relationship("Gene", back_populates="edge_details")
    timepoint = relationship("Timepoint", back_populates="edge_details")

    def __repr__(self):
        return f"<EdgeDetails(dmr_id={self.dmr_id}, gene_id={self.gene_id}, timepoint_id={self.timepoint_id})>"


class EdgeStatsSchema(BaseModel):
    """Schema for edge classification statistics"""

    permanent_edges: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    reliability: dict = Field(
        default_factory=lambda: {
            "accuracy": 0.0,
            "noise_percentage": 0.0,
            "false_positive_rate": 0.0,
            "false_negative_rate": 0.0,
        }
    )

    class Config:
        from_attributes = True


class ComponentSummarySchema(BaseModel):
    """Pydantic model matching component_summary_view"""

    component_id: Optional[int] = None
    timepoint_id: int
    timepoint: str = ""  # Default empty string if missing
    graph_type: str = "split"  # Default value
    category: str = ""
    size: int = 0
    dmr_count: int = 0
    gene_count: int = 0
    edge_count: int = 0
    density: float = 0.0
    biclique_count: int = 0
    biclique_categories: str = ""

    class Config:
        from_attributes = True


class TimePointSchema(BaseModel):
    """Pydantic model for TimePoint data transfer"""

    timepoint_id: int = Field(..., alias="id")
    name: str
    components: List[ComponentSummarySchema] = []

    class Config:
        from_attributes = True
        populate_by_name = True


class GeneTimepointAnnotationSchema(BaseModel):
    """Pydantic model for gene_timepoint_annotations table"""

    timepoint_id: int
    gene_id: int
    symbol: Optional[str] = None
    component_id: Optional[int] = None
    triconnected_id: Optional[int] = None
    degree: Optional[int] = None
    node_type: Optional[str] = None  # Now derived from is_hub field
    gene_type: Optional[str] = None
    is_isolate: Optional[bool] = None
    biclique_ids: Optional[str] = None
    interaction_source: Optional[str] = None
    promoter_info: Optional[str] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class DmrTimepointAnnotationSchema(BaseModel):
    """Pydantic model for dmr_timepoint_annotations table"""

    timepoint_id: int
    dmr_id: int
    component_id: Optional[int] = None
    triconnected_id: Optional[int] = None
    degree: Optional[int] = None
    node_type: Optional[str] = None
    is_isolate: Optional[bool] = None
    biclique_ids: Optional[str] = None

    class Config:
        from_attributes = True


class BicliqueMemberSchema(BaseModel):
    """Schema for biclique member data"""

    biclique_id: int
    category: str
    dmr_ids: str  # Comma-separated string of IDs
    gene_ids: str  # Comma-separated string of IDs

    class Config:
        from_attributes = True


class DominatingSetSchema(BaseModel):
    """Schema for dominating set data"""

    dmr_id: int
    dominated_gene_count: Optional[int] = None
    utility_score: Optional[float] = None

    class Config:
        from_attributes = True


class TriconnectedComponentViewSchema(BaseModel):
    """Pydantic model matching triconnected_component_view"""

    component_id: int
    timepoint_id: int
    triconnected_id: int
    size: int
    edge_count: int
    density: float
    component_position: str

    class Config:
        from_attributes = True


class TimepointStatsViewSchema(BaseModel):
    """Pydantic model matching timepoint_stats_view"""

    timepoint_id: int
    timepoint_name: str
    component_count: int
    total_nodes: int
    total_edges: int
    total_bicliques: int
    avg_density: float
    isolated_nodes: int

    class Config:
        from_attributes = True


class ComponentNodesViewSchema(BaseModel):
    """Pydantic model matching component_nodes_view"""

    component_id: int
    timepoint_id: int
    dmr_ids: List[int]
    gene_ids: List[int]
    dmr_count: int
    gene_count: int
    edge_count: int

    class Config:
        from_attributes = True


class BicliqueDetailsViewSchema(BaseModel):
    """Pydantic model matching biclique_details_view"""

    biclique_id: int
    component_id: int
    timepoint_id: int
    dmr_count: int
    gene_count: int
    total_edges: int
    categories: str
    dmr_ids: List[int]
    gene_ids: List[int]

    class Config:
        from_attributes = True


class ComponentDetailsSchema(BaseModel):
    """Schema for component details including dominating sets"""

    timepoint_id: int
    timepoint: str
    component_id: int
    graph_type: str
    categories: str
    total_dmr_count: int
    total_gene_count: int
    biclique_count: int
    all_dmr_ids: List[int]
    all_gene_ids: List[int]
    bicliques: List[BicliqueMemberSchema]
    dominating_sets: Dict[str, DominatingSetSchema]
    edge_stats: Optional[EdgeStatsSchema] = None

    class Config:
        from_attributes = True


class GraphComponentSchema(BaseModel):
    """Schema for graph component data"""

    component_id: int
    timepoint_id: int
    dmr_ids: str  # Comma-separated string of IDs
    gene_ids: str  # Comma-separated string of IDs
    graph_type: str
    categories: str  # Changed back to categories to match the view
    bicliques: List[BicliqueMemberSchema]


class NodeSymbolRequest(BaseModel):
    """Schema for node symbol request"""

    gene_ids: List[int]
    timepoint_id: int


class NodeStatusRequest(BaseModel):
    """Schema for node status request"""

    dmr_ids: List[int]
    timepoint_id: int


class MasterGeneIDSchema(BaseModel):
    """Schema for master gene ID mapping."""

    id: int
    gene_symbol: str

    class Config:
        """Configure schema to work with SQLAlchemy models."""

        from_attributes = True


class DmrComponentSchema(BaseModel):
    """Schema for DMR component data"""

    id: int = Field(alias="dmr_id")  # Changed to match the view's dmr_id field
    area: Optional[float] = Field(
        alias="area_stat"
    )  # Changed to match area_stat from view
    description: Optional[str]
    node_type: Optional[str]
    degree: Optional[int]
    is_isolate: Optional[bool]
    biclique_ids: Optional[str]

    class Config:
        from_attributes = True
        populate_by_name = True


class GeneAnnotationViewSchema(BaseModel):
    """Pydantic model matching gene_annotations_view"""

    gene_id: int
    symbol: str
    description: Optional[str] = None
    master_gene_id: Optional[int] = None
    interaction_source: Optional[str] = None
    promoter_info: Optional[str] = None
    timepoint: Optional[str] = None
    timepoint_id: Optional[int] = None
    component_id: Optional[int] = None
    triconnected_id: Optional[int] = None
    degree: Optional[int] = None
    node_type: Optional[str] = None
    gene_type: Optional[str] = None
    is_isolate: Optional[bool] = None
    biclique_ids: Optional[str] = None

    class Config:
        from_attributes = True


class GeneDetails(Base):
    __tablename__ = "gene_details"

    gene_id = Column(Integer, ForeignKey("genes.id"), primary_key=True)
    NCBI_id = Column(String(50))
    annotations = Column(JSON)

    # Relationships
    gene = relationship("Gene")

    __table_args__ = (
        Index('idx_gene_details_ncbi_id', 'NCBI_id'),
    )


class TopGoProcessesDmr(Base):
    __tablename__ = "top_go_processes_dmr"

    dmr_id = Column(Integer, ForeignKey("go_enrichment_dmr.dmr_id"), primary_key=True)
    termId = Column(String(50), primary_key=True)
    pValue = Column(Float)
    enrichmentScore = Column(Float)

    # Relationships
    go_enrichment = relationship("GoEnrichmentDmr")


class TopGoProcessesBiclique(Base):
    __tablename__ = "top_go_processes_biclique"

    biclique_id = Column(Integer, ForeignKey("go_enrichment_biclique.biclique_id"), primary_key=True)
    termId = Column(String(50), primary_key=True)
    pValue = Column(Float)
    enrichmentScore = Column(Float)

    # Relationships
    go_enrichment = relationship("GoEnrichmentBiclique")


class GoEnrichmentDmr(Base):
    __tablename__ = "go_enrichment_dmr"

    dmr_id = Column(Integer, ForeignKey("dmrs.id"), primary_key=True)
    go_terms = Column(JSON)
    p_value = Column(Float)
    enrichment_score = Column(Float)
    source = Column(Text)
    biologicalProcessCount = Column(Integer)
    significantBiologicalProcesses = Column(JSON)
    topBiologicalProcess = Column(Text)
    biologicalProcessAnnotationDetails = Column(JSON)

    # Relationships
    dmr = relationship("Dmr")
    top_go_processes = relationship("TopGoProcessesDmr", back_populates="go_enrichment")


class GoEnrichmentBiclique(Base):
    __tablename__ = "go_enrichment_biclique"

    biclique_id = Column(Integer, ForeignKey("bicliques.id"), primary_key=True)
    go_terms = Column(JSON)
    p_value = Column(Float)
    enrichment_score = Column(Float)
    source = Column(Text)
    biologicalProcessCount = Column(Integer)
    significantBiologicalProcesses = Column(JSON)
    topBiologicalProcess = Column(Text)
    biologicalProcessAnnotationDetails = Column(JSON)

    # Relationships
    biclique = relationship("Biclique")
    top_go_processes = relationship("TopGoProcessesBiclique", back_populates="go_enrichment")


class DmrAnnotationViewSchema(BaseModel):
    dmr_id: int
    chromosome: str
    start_position: int
    end_position: int
    methylation_diff: float = Field(
        ..., alias="methylation_difference"
    )  # Remove Optional
    p_value: Optional[float] = None
    q_value: Optional[float] = None
    node_type: str
    degree: int
    is_isolate: bool
    biclique_ids: Optional[str] = None
    component_id: int
    timepoint_name: str

    class Config:
        from_attributes = True
        allow_population_by_field_name = True
