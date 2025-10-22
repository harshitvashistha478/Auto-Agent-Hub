from typing import List, Optional
from pydantic import BaseModel


class Node(BaseModel):
    name: str
    description: str
    inputs: List[str]
    outputs: List[str]


class Edge(BaseModel):
    source: str
    target: str
    condition: Optional[str] = None


class GraphOverview(BaseModel):
    nodes: List[Node]
    edges: List[Edge]


class SupervisorStructuredModel(BaseModel):
    summary: str
    graph_overview: GraphOverview
    flow_description: str
