from enum import Enum
from .database.models import (
    Base,
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
    GeneTimepointAnnotation,
    DMRTimepointAnnotation,
    TriconnectedComponent,
    DominatingSet,
    GOEnrichmentDMR,
    GOEnrichmentBiclique,
    TopGOProcessesDMR,
    TopGOProcessesBiclique,
    EdgeDetails,
    GeneDetails,
    GeneReference,
    EnsemblGenes,
)
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

__all__ = [
    "Base",
    "Timepoint",
    "Gene",
    "DMR",
    "Biclique",
    "Component",
    "ComponentBiclique",
    "Statistic",
    "Metadata",
    "Relationship",
    "MasterGeneID",
    "GeneTimepointAnnotation",
    "DMRTimepointAnnotation",
    "TriconnectedComponent",
    "DominatingSet",
    "GOEnrichmentDMR",
    "GOEnrichmentBiclique",
    "TopGOProcessesDMR",
    "TopGOProcessesBiclique",
    "EdgeDetails",
    "GeneDetails",
    "EnsemblGenes",
    "GeneReference",
    # Add Pydantic schemas as well
    "TopGOProcessBase",
    "DmrAnnotationViewSchema",
    "ProcessStatus",
    "ProcessStatusEnum",
]


# Start with Pydantic schemas for data validation and transfer
class TopGOProcessBase(BaseModel):
    go_id: str
    timepoint_id: int
    description: str | None = None
    category: str | None = None
    p_value: float
    genes: str | None = None


class TopGOProcessBicliqueCreate(TopGOProcessBase):
    biclique_id: int


class TopGOProcessDMRCreate(TopGOProcessBase):
    dmr_id: int


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

    @property
    def component(self) -> List[int]:
        dmr_list = [int(x.strip()) for x in self.dmr_ids.split(",") if x.strip()]
        gene_list = [int(x.strip()) for x in self.gene_ids.split(",") if x.strip()]
        return list(set(dmr_list) | set(gene_list))


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


class ProcessStatusEnum(str, Enum):
    """Enum for process status values"""

    INITIATED = "INITIATED"
    FETCHING_GENES = "FETCHING_GENES"
    FETCHING_NCBI_IDS = "FETCHING_NCBI_IDS"
    CALCULATING_ENRICHMENT = "CALCULATING_ENRICHMENT"
    SAVING_RESULTS = "SAVING_RESULTS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ProcessStatus(BaseModel):
    """Schema for tracking enrichment process status"""

    id: int
    process_type: str
    entity_id: int
    timepoint_id: int
    status: ProcessStatusEnum
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
