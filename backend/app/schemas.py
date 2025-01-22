from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class DominatingSetSchema(BaseModel):
    """Schema for dominating set data"""
    timepoint_id: int
    dmr_id: int
    area_stat: Optional[float] = None
    utility_score: Optional[float] = None
    dominated_gene_count: Optional[int] = None
    calculation_timestamp: Optional[datetime] = None

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


class ComponentDetailsSchema(BaseModel):
    """Pydantic model matching component_details_view"""

    timepoint_id: int
    timepoint: str
    component_id: int
    graph_type: str
    categories: str
    total_dmr_count: int
    total_gene_count: int
    all_dmr_ids: List[str]
    all_gene_ids: List[str]

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
    node_type: Optional[str] = None
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


class DmrAnnotationViewSchema(BaseModel):
    dmr_id: int
    chromosome: str
    start_position: int
    end_position: int
    methylation_difference: Optional[float] = None  # Make nullable
    p_value: Optional[float] = None
    q_value: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    timepoint_id: int
    node_type: str
    degree: int
    is_isolate: bool
    biclique_ids: Optional[str] = None
    component_id: int
    timepoint_name: str

    class Config:
        orm_mode = True
