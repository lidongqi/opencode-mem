from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class MemoryAddRequest(BaseModel):
    content: str = Field(..., description="The content to remember")
    user_id: Optional[str] = Field(None, description="User ID")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Optional metadata"
    )


class MemorySearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    user_id: Optional[str] = Field(None, description="User ID")
    limit: Optional[int] = Field(5, description="Maximum number of results")


class MemoryUpdateRequest(BaseModel):
    memory_id: str = Field(..., description="Memory ID to update")
    content: str = Field(..., description="New content")


class MemoryResponse(BaseModel):
    success: bool
    memory_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None


class MemoryItem(BaseModel):
    id: str
    content: str
    score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class MemorySearchResponse(BaseModel):
    success: bool
    memories: List[MemoryItem] = []
    count: int = 0
    error: Optional[str] = None


class MemoryListResponse(BaseModel):
    success: bool
    memories: List[MemoryItem] = []
    count: int = 0
    error: Optional[str] = None


class MemoryHistoryResponse(BaseModel):
    success: bool
    history: List[Dict[str, Any]] = []
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    backend: str


class IntelligentMemoryRequest(BaseModel):
    user_input: str = Field(..., description="Current user input")
    user_id: Optional[str] = Field(None, description="User ID")
    session_id: str = Field(..., description="Session ID for caching")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list, description="Recent conversation messages"
    )
    token_budget: Optional[int] = Field(500, description="Maximum tokens for memories")


class IntelligentMemoryResponse(BaseModel):
    success: bool
    context: Optional[str] = None
    memories_count: int = 0
    query_type: Optional[str] = None
    cache_hit: bool = False
    latency_ms: Optional[float] = None
    error: Optional[str] = None


class MetricsResponse(BaseModel):
    success: bool
    report: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class CacheStatsResponse(BaseModel):
    success: bool
    stats: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
