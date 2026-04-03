import sys
from pathlib import Path

# Add src directory to Python path
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from contextlib import asynccontextmanager
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from models.schemas import (
    MemoryAddRequest,
    MemorySearchRequest,
    MemoryUpdateRequest,
    MemoryResponse,
    MemorySearchResponse,
    MemoryListResponse,
    MemoryHistoryResponse,
    HealthResponse,
)
from services.memory_service import MemoryService
from services.memory_queue import MemoryQueue
from api.auth import get_api_key
from opencode_mem0 import Mem0Config


def get_memory_service() -> MemoryService:
    chroma_path = os.getenv("CHROMA_PATH", "./mem0_db")
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
        user_id=os.getenv("DEFAULT_USER_ID", "default_user"),
    )
    return MemoryService(config)


memory_queue: Optional[MemoryQueue] = None


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
