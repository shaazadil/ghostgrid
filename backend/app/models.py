from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class PostInput(BaseModel):
    post_id: str
    user_id: str
    text: str
    timestamp: str
    ground_truth: Optional[str] = "unknown"


class AnalyzeRequest(BaseModel):
    posts: List[PostInput]
    scan_name: Optional[str] = "Automated Feed Scan"
    similarity_threshold: float = Field(default=0.70, ge=0.50, le=0.98)
    burst_window_minutes: int = Field(default=20, ge=1, le=1440)
    k_core_min: int = Field(default=2, ge=1, le=20)


class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # "account" or "narrative"
    threat_level: str  # "COORDINATED_BOT", "SUSPICIOUS", "ORGANIC", "NARRATIVE_HUB"
    threat_score: Optional[float] = 0.0
    coreness: Optional[int] = 0
    val: Optional[int] = 2
    canonical_claim: Optional[str] = None
    post_count: Optional[int] = None
    user_count: Optional[int] = None
    narratives: Optional[List[str]] = None


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str  # "posted_narrative" or "co_coordinated"
    weight: Optional[float] = 1.0
    timestamp: Optional[str] = None
    delta_minutes: Optional[float] = None
    similarity: Optional[float] = None
    narratives: Optional[List[str]] = None


class NarrativeMeta(BaseModel):
    narrative_id: str
    canonical_claim: str
    canonical_post_id: str
    post_count: int
    unique_user_count: int
    users: List[str]
    mean_similarity: float


class FlaggedAccount(BaseModel):
    user_id: str
    threat_score: float
    threat_level: str
    coreness: int
    burst_count: int
    narratives_count: int
    narratives: List[str]
    ground_truth: Optional[str] = "unknown"


class SummaryMetrics(BaseModel):
    total_accounts: int
    flagged_bots: int
    suspicious_accounts: int
    organic_accounts: int
    narratives_count: int
    max_coreness: int


class AnalyzeResponse(BaseModel):
    scan_id: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    narratives: Dict[str, NarrativeMeta]
    flagged_accounts: List[FlaggedAccount]
    summary: SummaryMetrics
