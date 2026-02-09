from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field  #type: ignore

class CellNode(BaseModel):
    """Represents a single data point in the table graph."""
    coordinate: str  # e.g., "B4"
    value: Union[str, int, float, bool, None]
    data_type: str   # e.g., "currency", "percentage", "text"
    context: Dict[str, Any] = Field(
        description="Linked headers or hierarchical context, e.g., {'Year': '2023', 'Metric': 'Revenue'}"
    )

class ColumnMetadata(BaseModel):
    """Statistical profile and semantic meaning of a column."""
    name: str
    inferred_type: str
    description: Optional[str] = None
    stats: Dict[str, Any] = Field(default_factory=dict) # Min, max, unique count

class TableGraph(BaseModel):
    """The Semantic Graph representation of the Excel sheet."""
    sheet_name: str
    dimensions: str # e.g., "10x50"
    columns: List[ColumnMetadata]
    nodes: List[CellNode] = Field(
        description="Flattened list of semantic nodes containing data and relationships"
    )
    summary: str = Field(description="High-level summary of what this table contains")

class ExtractionResponse(BaseModel):
    filename: str
    tables: List[TableGraph]