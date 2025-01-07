from pydantic import BaseModel, Field
from typing import List, Optional

class ComponentSummarySchema(BaseModel):
    """Pydantic model matching component_summary_view"""
    component_id: int
    timepoint_id: int
    timepoint: str
    graph_type: str
    category: Optional[str]
    size: int
    dmr_count: int
    gene_count: int
    edge_count: int
    density: float
    biclique_count: int
    biclique_categories: Optional[str]

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
    timepoint_id: int = Field(..., alias='id')
    name: str
    components: List[ComponentSummarySchema] = []
    
    class Config:
        from_attributes = True
        populate_by_name = True


class GeneTimepointAnnotationSchema(BaseModel):
    """Pydantic model for gene_timepoint_annotations table"""
    timepoint_id: int
    gene_id: int
    component_id: Optional[int] = None
    triconnected_id: Optional[int] = None
    degree: Optional[int] = None
    node_type: Optional[str] = None
    gene_type: Optional[str] = None
    is_isolate: Optional[bool] = None
    biclique_ids: Optional[str] = None

    class Config:
        from_attributes = True


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

class DmrComponentSchema(BaseModel):
    """Schema for DMR component data"""
    id: int = Field(alias='dmr_id')  # Changed to match the view's dmr_id field
    area: Optional[float] = Field(alias='area_stat')  # Changed to match area_stat from view
    description: Optional[str]
    node_type: Optional[str]
    degree: Optional[int]
    is_isolate: Optional[bool]
    biclique_ids: Optional[str]

    class Config:
        from_attributes = True
        populate_by_name = True
