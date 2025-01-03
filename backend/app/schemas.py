from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ComponentSummarySchema(BaseModel):
    """Pydantic model matching component_summary_view"""
    component_id: int = Field(..., alias='id')
    name: str
    timepoint_id: int
    bicliques_count: int = Field(description="Number of bicliques")
    genes_count: int = Field(description="Number of genes")
    dmrs_count: int = Field(description="Number of DMRs")
    
    class Config:
        from_attributes = True
        populate_by_name = True

class ComponentDetailsSchema(BaseModel):
    """Pydantic model matching component_details_view"""
    component_id: int = Field(..., alias='id')
    timepoint_id: int
    biclique_id: int
    gene_symbol: str
    dmr_name: str
    methylation_change: float
    p_value: float
    
    class Config:
        from_attributes = True
        populate_by_name = True

class TimePointSchema(BaseModel):
    """Pydantic model for TimePoint data transfer"""
    timepoint_id: int = Field(..., alias='id')
    name: str
    components: List[ComponentSummarySchema] = []
    
    class Config:
        from_attributes = True
        populate_by_name = True
