import sys
from pathlib import Path

# Add src directory to Python path
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from contextlib import asynccontextmanager
import os
import logging
import json
import time
from pathlib import Path
from starlette.middleware.base import BaseHTTPMiddleware

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)
    logger.info(f"[CONFIG] Loaded .env from {env_path}")
else:
    logger.warning(f"[CONFIG] .env file not found at {env_path}")

from models.schemas import (
    MemoryAddRequest,
    MemorySearchRequest,
    MemoryUpdateRequest,
    MemoryResponse,
    MemorySearchResponse,
    MemoryListResponse,
    MemoryHistoryResponse,
    HealthResponse,
    IntelligentMemoryRequest,
    IntelligentMemoryResponse,
    MetricsResponse,
    CacheStatsResponse,
)
from services.memory_service import MemoryService
from services.memory_queue import MemoryQueue
from services.intelligent_memory_service import IntelligentMemoryService
from services.memory_cache import MemoryCacheSystem
from services.memory_metrics import MemoryMetricsCollector
from api.auth import get_api_key
from opencode_mem0 import Mem0Config


def get_memory_service() -> MemoryService:
    chroma_path = os.getenv("CHROMA_PATH", "./mem0_db")
    if not Path(chroma_path).is_absolute():
        backend_dir = Path(__file__).parent.parent.parent
        chroma_path = str(backend_dir / chroma_path)
        logger.info(f"[CONFIG] Converted relative path to absolute: {chroma_path}")
    
    logger.info(f"[CONFIG] CHROMA_PATH: {chroma_path}")
    
    config = Mem0Config(
        vector_store=os.getenv("VECTOR_STORE", "chroma"),
        chroma_path=chroma_path,
        llm_provider=os.getenv("LLM_PROVIDER", "ollama"),
        llm_model=os.getenv("LLM_MODEL", "glm-4.7-flash:latest"),
        llm_base_url=os.getenv("LLM_BASE_URL"),
        llm_api_key=os.getenv("LLM_API_KEY"),
        embedding_provider=os.getenv("EMBEDDING_PROVIDER", "ollama"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "nomic-embed-text-v2-moe:latest"),
        embedding_base_url=os.getenv("EMBEDDING_BASE_URL"),
        embedding_api_key=os.getenv("EMBEDDING_API_KEY"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        user_id=os.getenv("DEFAULT_USER_ID", "default"),
    )
    return MemoryService(config)


cache_system = MemoryCacheSystem(
    session_ttl=int(os.getenv("CACHE_SESSION_TTL", "3600")),
    query_cache_ttl=int(os.getenv("CACHE_QUERY_TTL", "300")),
    lru_max_size=int(os.getenv("CACHE_LRU_SIZE", "100"))
)
metrics_collector = MemoryMetricsCollector()


def get_intelligent_memory_service() -> IntelligentMemoryService:
    memory_service = get_memory_service()
    return IntelligentMemoryService(
        memory_service=memory_service,
        cache_system=cache_system,
        metrics_collector=metrics_collector,
        llm_client=None
    )


memory_queue: Optional[MemoryQueue] = None


class RequestResponseLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                request_body = await request.body()
                request_body_str = request_body.decode('utf-8')
                try:
                    request_body_json = json.loads(request_body_str)
                    logger.info(f"[REQUEST] {request.method} {request.url.path} - Body: {json.dumps(request_body_json, ensure_ascii=False, indent=2)}")
                except json.JSONDecodeError:
                    logger.info(f"[REQUEST] {request.method} {request.url.path} - Body: {request_body_str}")
            except Exception as e:
                logger.warning(f"[REQUEST] {request.method} {request.url.path} - Failed to read body: {e}")
        else:
            logger.info(f"[REQUEST] {request.method} {request.url.path}")
        
        async def receive():
            return {"type": "http.request", "body": request_body}
        
        if request_body:
            request._receive = receive
        
        response = await call_next(request)
        
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk
        
        try:
            response_body_str = response_body.decode('utf-8')
            try:
                response_body_json = json.loads(response_body_str)
                logger.info(f"[RESPONSE] {request.method} {request.url.path} - Status: {response.status_code} - Body: {json.dumps(response_body_json, ensure_ascii=False, indent=2)}")
            except json.JSONDecodeError:
                logger.info(f"[RESPONSE] {request.method} {request.url.path} - Status: {response.status_code} - Body: {response_body_str}")
        except Exception as e:
            logger.warning(f"[RESPONSE] {request.method} {request.url.path} - Status: {response.status_code} - Failed to decode body: {e}")
        
        return Response(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    global memory_queue
    max_workers = int(os.getenv("QUEUE_WORKERS", "3"))
    memory_queue = MemoryQueue(get_memory_service, max_workers=max_workers)
    await memory_queue.start()
    logger.info(f"[App] Memory queue started with {max_workers} workers")
    yield
    await memory_queue.stop()
    logger.info("[App] Memory queue stopped")


app = FastAPI(
    title="OpenCode mem0 Memory Backend",
    description="REST API backend for OpenCode mem0 memory plugin",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(RequestResponseLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", version="0.1.0", backend="python-fastapi")


@app.get("/")
async def root(api_key: str = Depends(get_api_key)):
    return {
        "name": "OpenCode mem0 Memory Backend",
        "version": "0.1.0",
        "status": "running",
        "auth_enabled": bool(os.getenv("MEM0_API_KEY")),
    }


@app.post("/api/memory/add", response_model=MemoryResponse)
async def add_memory(
    request: MemoryAddRequest,
    api_key: str = Depends(get_api_key),
):
    logger.info(f"[API] add_memory called - user_id: {request.user_id}, content_preview: {request.content[:50]}...")
    
    if memory_queue is None:
        raise HTTPException(status_code=503, detail="Memory queue not initialized")
    
    task_id = memory_queue.add_task(
        content=request.content,
        user_id=request.user_id,
        metadata=request.metadata,
    )
    logger.info(f"[API] add_memory queued - task_id: {task_id}")
    
    return MemoryResponse(
        success=True,
        memory_id=task_id,
        message="Memory add task queued for processing",
    )


@app.post("/api/memory/search", response_model=MemorySearchResponse)
async def search_memories(
    request: MemorySearchRequest,
    service: MemoryService = Depends(get_memory_service),
    api_key: str = Depends(get_api_key),
):
    logger.info(f"[API] search_memories called - user_id: {request.user_id}, query: {request.query}, limit: {request.limit}")
    result = await service.search_memories(
        query=request.query, user_id=request.user_id, limit=request.limit
    )
    memories_count = len(result.get('memories', [])) if result.get('success') else 0
    logger.info(f"[API] search_memories result - success: {result.get('success')}, found: {memories_count} memories")
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return MemorySearchResponse(**result)


@app.get("/api/memory/all", response_model=MemoryListResponse)
async def get_all_memories(
    user_id: Optional[str] = None,
    service: MemoryService = Depends(get_memory_service),
    api_key: str = Depends(get_api_key),
):
    logger.info(f"[API] get_all_memories called - user_id: {user_id}")
    result = await service.get_all_memories(user_id)
    memories_count = len(result.get('memories', [])) if result.get('success') else 0
    logger.info(f"[API] get_all_memories result - success: {result.get('success')}, total: {memories_count} memories")
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return MemoryListResponse(**result)


@app.put("/api/memory/update", response_model=MemoryResponse)
async def update_memory(
    request: MemoryUpdateRequest,
    service: MemoryService = Depends(get_memory_service),
    api_key: str = Depends(get_api_key),
):
    logger.info(f"[API] update_memory called - memory_id: {request.memory_id}")
    result = await service.update_memory(memory_id=request.memory_id, content=request.content)
    logger.info(f"[API] update_memory result - success: {result.get('success')}, memory_id: {result.get('memory_id')}")
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return MemoryResponse(**result)


@app.delete("/api/memory/{memory_id}", response_model=MemoryResponse)
async def delete_memory(
    memory_id: str,
    service: MemoryService = Depends(get_memory_service),
    api_key: str = Depends(get_api_key),
):
    logger.info(f"[API] delete_memory called - memory_id: {memory_id}")
    result = await service.delete_memory(memory_id)
    logger.info(f"[API] delete_memory result - success: {result.get('success')}, memory_id: {result.get('memory_id')}")
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return MemoryResponse(**result)


@app.get("/api/memory/{memory_id}/history", response_model=MemoryHistoryResponse)
async def get_memory_history(
    memory_id: str,
    service: MemoryService = Depends(get_memory_service),
    api_key: str = Depends(get_api_key),
):
    logger.info(f"[API] get_memory_history called - memory_id: {memory_id}")
    result = await service.get_memory_history(memory_id)
    history_count = len(result.get('history', [])) if result.get('success') else 0
    logger.info(f"[API] get_memory_history result - success: {result.get('success')}, history_count: {history_count}")
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return MemoryHistoryResponse(**result)


@app.get("/api/memory/context")
async def get_context(
    query: str,
    user_id: Optional[str] = None,
    service: MemoryService = Depends(get_memory_service),
    api_key: str = Depends(get_api_key),
):
    logger.info(f"[API] get_context called - user_id: {user_id}, query: {query}")
    context = await service.get_context(query, user_id)
    context_preview = context[:100] + "..." if len(context) > 100 else context
    logger.info(f"[API] get_context result - context_preview: {context_preview}")
    return {"context": context}


@app.get("/api/queue/status")
async def get_queue_status(
    api_key: str = Depends(get_api_key),
):
    if memory_queue is None:
        raise HTTPException(status_code=503, detail="Memory queue not initialized")
    
    stats = memory_queue.get_stats()
    return {
        "success": True,
        "queue": stats,
    }


@app.get("/api/queue/task/{task_id}")
async def get_task_status(
    task_id: str,
    api_key: str = Depends(get_api_key),
):
    if memory_queue is None:
        raise HTTPException(status_code=503, detail="Memory queue not initialized")
    
    task = memory_queue.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return {
        "success": True,
        "task": {
            "id": task.id,
            "status": task.status.value,
            "content_preview": task.content[:50] + "..." if len(task.content) > 50 else task.content,
            "user_id": task.user_id,
            "result": task.result,
            "error": task.error,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        },
    }


@app.post("/api/memory/intelligent", response_model=IntelligentMemoryResponse)
async def get_intelligent_memories(
    request: IntelligentMemoryRequest,
    service: IntelligentMemoryService = Depends(get_intelligent_memory_service),
    api_key: str = Depends(get_api_key),
):
    logger.info(
        f"[API] get_intelligent_memories called - "
        f"user_id: {request.user_id}, session: {request.session_id}, "
        f"input: {request.user_input[:50]}..."
    )
    
    start_time = time.time()
    
    try:
        context = await service.get_context_aware_memories(
            user_input=request.user_input,
            user_id=request.user_id,
            conversation_history=request.conversation_history or [],
            session_id=request.session_id,
            token_budget=request.token_budget or 500
        )
        
        latency = (time.time() - start_time) * 1000
        memories_count = 0
        if context:
            lines = [line for line in context.split('\n') if line.strip() and not line.startswith('##')]
            memories_count = len(lines)
        
        logger.info(
            f"[API] get_intelligent_memories result - "
            f"memories: {memories_count}, latency: {latency:.2f}ms"
        )
        
        return IntelligentMemoryResponse(
            success=True,
            context=context,
            memories_count=memories_count,
            latency_ms=round(latency, 2)
        )
    except Exception as e:
        logger.error(f"[API] get_intelligent_memories error: {e}")
        return IntelligentMemoryResponse(
            success=False,
            error=str(e)
        )


@app.get("/api/metrics", response_model=MetricsResponse)
async def get_metrics(
    api_key: str = Depends(get_api_key),
):
    logger.info("[API] get_metrics called")
    try:
        report = metrics_collector.get_performance_report()
        return MetricsResponse(success=True, report=report)
    except Exception as e:
        logger.error(f"[API] get_metrics error: {e}")
        return MetricsResponse(success=False, error=str(e))


@app.get("/api/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    api_key: str = Depends(get_api_key),
):
    logger.info("[API] get_cache_stats called")
    try:
        stats = cache_system.get_stats()
        return CacheStatsResponse(success=True, stats=stats)
    except Exception as e:
        logger.error(f"[API] get_cache_stats error: {e}")
        return CacheStatsResponse(success=False, error=str(e))


@app.post("/api/cache/clear")
async def clear_cache(
    user_id: Optional[str] = None,
    api_key: str = Depends(get_api_key),
):
    logger.info(f"[API] clear_cache called - user_id: {user_id}")
    try:
        if user_id:
            cache_system.invalidate_user_cache(user_id)
            message = f"Cache cleared for user: {user_id}"
        else:
            cache_system.clear_all()
            message = "All cache cleared"
        
        logger.info(f"[API] clear_cache result - {message}")
        return {"success": True, "message": message}
    except Exception as e:
        logger.error(f"[API] clear_cache error: {e}")
        return {"success": False, "error": str(e)}
