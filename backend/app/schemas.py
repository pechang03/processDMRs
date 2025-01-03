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
from pydantic import BaseModel, Field
from typing import List, Optional

class ComponentSummarySchema(BaseModel):
    component_id: int
    timepoint_id: int
    bicliques_count: int = Field(..., alias="biclique_count")
    genes_count: int = Field(..., alias="gene_count")
    dmrs_count: int = Field(..., alias="dmr_count")
    name: Optional[str] = None  # Added optional name field

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "component_id": 1,
                "timepoint_id": 1,
                "bicliques_count": 5,
                "genes_count": 10,
                "dmrs_count": 8,
                "name": "Component 1"
            }
        }

class ComponentDetailsSchema(BaseModel):
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
        schema_extra = {
            "example": {
                "timepoint_id": 1,
                "timepoint": "Timepoint 1",
                "component_id": 1,
                "graph_type": "SPLIT",
                "categories": "Category A",
                "total_dmr_count": 10,
                "total_gene_count": 15,
                "all_dmr_ids": ["DMR1", "DMR2"],
                "all_gene_ids": ["GENE1", "GENE2"]
            }
        }
