"""OpenCode mem0 memory plugin implementation."""

import os
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass

from .config import Mem0Config


@dataclass
class Tool:
    """Tool definition for OpenCode."""

    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable


class Mem0MemoryPlugin:
    """OpenCode memory plugin using mem0."""

    def __init__(self, config: Optional[Mem0Config] = None):
        """Initialize the mem0 memory plugin.

        Args:
            config: Plugin configuration
        """
        self.config = config or Mem0Config()
        self._memory = None
        self._client = None

    @property
    def name(self) -> str:
        """Plugin name."""
        return "mem0_memory"

    @property
    def description(self) -> str:
        """Plugin description."""
        return "Persistent memory storage using mem0 with semantic search"

    def initialize(self) -> None:
        """Initialize mem0 client."""
        try:
            from mem0 import Memory, MemoryClient
        except ImportError:
            raise ImportError("mem0ai is required. Install with: pip install mem0ai")

        if self.config.api_key:
            # Use hosted mem0
            self._client = MemoryClient(api_key=self.config.api_key)
        else:
            # Use self-hosted mem0
            config_dict = self._build_mem0_config()
            self._memory = Memory.from_config(config_dict)

    def _build_mem0_config(self) -> Dict[str, Any]:
        """Build mem0 configuration dictionary."""
        config = {
            "vector_store": {
                "provider": self.config.vector_store,
                "config": {
                    "path": self.config.chroma_path,
                },
            },
            "llm": {
                "provider": self.config.llm_provider,
                "config": {
                    "model": self.config.llm_model,
                },
            },
            "embedder": {
                "provider": self.config.embedding_provider,
                "config": {
                    "model": self.config.embedding_model,
                },
            },
        }

        # Configure LLM
        if self.config.llm_provider == "ollama":
            llm_base_url = self.config.llm_base_url or self.config.ollama_base_url
            config["llm"]["config"]["ollama_base_url"] = llm_base_url
        elif self.config.llm_base_url:
            config["llm"]["config"]["openai_base_url"] = self.config.llm_base_url
            if self.config.llm_api_key:
                config["llm"]["config"]["openai_api_key"] = self.config.llm_api_key

        # Configure Embedder
        if self.config.embedding_provider == "ollama":
            embedding_base_url = self.config.embedding_base_url or self.config.ollama_base_url
            config["embedder"]["config"]["ollama_base_url"] = embedding_base_url
        elif self.config.embedding_base_url:
            config["embedder"]["config"]["openai_base_url"] = self.config.embedding_base_url
            if self.config.embedding_api_key:
                config["embedder"]["config"]["openai_api_key"] = self.config.embedding_api_key

        return config

    def get_tools(self) -> List[Tool]:
        """Get list of tools provided by this plugin."""
        return [
            Tool(
                name="memory_add",
                description="Add a memory to the mem0 storage",
                parameters={
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "The content to remember"},
                        "user_id": {
                            "type": "string",
                            "description": "User ID for the memory",
                            "default": self.config.user_id,
                        },
                        "metadata": {
                            "type": "object",
                            "description": "Optional metadata for the memory",
                            "default": {},
                        },
                    },
                    "required": ["content"],
                },
                handler=self._handle_add,
            ),
            Tool(
                name="memory_search",
                description="Search for relevant memories",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "user_id": {
                            "type": "string",
                            "description": "User ID to search memories for",
                            "default": self.config.user_id,
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": self.config.search_limit,
                        },
                    },
                    "required": ["query"],
                },
                handler=self._handle_search,
            ),
            Tool(
                name="memory_get_all",
                description="Get all memories for a user",
                parameters={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID to get memories for",
                            "default": self.config.user_id,
                        }
                    },
                    "required": [],
                },
                handler=self._handle_get_all,
            ),
            Tool(
                name="memory_delete",
                description="Delete a specific memory by ID",
                parameters={
                    "type": "object",
                    "properties": {
                        "memory_id": {"type": "string", "description": "ID of the memory to delete"}
                    },
                    "required": ["memory_id"],
                },
                handler=self._handle_delete,
            ),
            Tool(
                name="memory_update",
                description="Update a specific memory by ID",
                parameters={
                    "type": "object",
                    "properties": {
                        "memory_id": {
                            "type": "string",
                            "description": "ID of the memory to update",
                        },
                        "content": {"type": "string", "description": "New content for the memory"},
                    },
                    "required": ["memory_id", "content"],
                },
                handler=self._handle_update,
            ),
            Tool(
                name="memory_history",
                description="Get the history of changes for a memory",
                parameters={
                    "type": "object",
                    "properties": {
                        "memory_id": {
                            "type": "string",
                            "description": "ID of the memory to get history for",
                        }
                    },
                    "required": ["memory_id"],
                },
                handler=self._handle_history,
            ),
        ]

    def _handle_add(
        self, content: str, user_id: Optional[str] = None, metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Handle memory_add tool call."""
        user_id = user_id or self.config.user_id
        metadata = metadata or {}

        messages = [{"role": "user", "content": content}]

        try:
            if self._client:
                # Hosted mem0
                result = self._client.add(messages, user_id=user_id, metadata=metadata)
            else:
                # Self-hosted mem0
                result = self._memory.add(messages, user_id=user_id, metadata=metadata)

            return {
                "success": True,
                "memory_id": result.get("id") if isinstance(result, dict) else result,
                "message": "Memory added successfully",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _handle_search(
        self, query: str, user_id: Optional[str] = None, limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Handle memory_search tool call."""
        user_id = user_id or self.config.user_id
        limit = limit or self.config.search_limit

        try:
            if self._client:
                # Hosted mem0
                results = self._client.search(query, user_id=user_id, limit=limit)
            else:
                # Self-hosted mem0
                results = self._memory.search(query, user_id=user_id, limit=limit)

            memories = []
            if isinstance(results, dict) and "results" in results:
                results = results["results"]
            
            if isinstance(results, list):
                for r in results:
                    memories.append(
                        {
                            "id": r.get("id"),
                            "content": r.get("memory") or r.get("content"),
                            "score": r.get("score", 0),
                            "metadata": r.get("metadata", {}),
                        }
                    )

            return {"success": True, "memories": memories, "count": len(memories)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _handle_get_all(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle memory_get_all tool call."""
        user_id = user_id or self.config.user_id

        try:
            if self._client:
                # Hosted mem0
                results = self._client.get_all(user_id=user_id)
            else:
                # Self-hosted mem0
                results = self._memory.get_all(user_id=user_id)

            memories = []
            if isinstance(results, dict) and "results" in results:
                results = results["results"]
            
            if isinstance(results, list):
                for r in results:
                    memories.append(
                        {
                            "id": r.get("id"),
                            "content": r.get("memory") or r.get("content"),
                            "metadata": r.get("metadata", {}),
                            "created_at": r.get("created_at"),
                            "updated_at": r.get("updated_at"),
                        }
                    )

            return {"success": True, "memories": memories, "count": len(memories)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _handle_delete(self, memory_id: str) -> Dict[str, Any]:
        """Handle memory_delete tool call."""
        try:
            if self._client:
                # Hosted mem0
                self._client.delete(memory_id)
            else:
                # Self-hosted mem0
                self._memory.delete(memory_id)

            return {"success": True, "message": f"Memory {memory_id} deleted successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _handle_update(self, memory_id: str, content: str) -> Dict[str, Any]:
        """Handle memory_update tool call."""
        try:
            if self._client:
                # Hosted mem0
                result = self._client.update(memory_id, data=content)
            else:
                # Self-hosted mem0
                result = self._memory.update(memory_id, data=content)

            return {
                "success": True,
                "memory_id": memory_id,
                "message": "Memory updated successfully",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _handle_history(self, memory_id: str) -> Dict[str, Any]:
        """Handle memory_history tool call."""
        try:
            if self._client:
                # Hosted mem0 - may not support history
                return {"success": False, "error": "History not supported in hosted mode"}
            else:
                # Self-hosted mem0
                history = self._memory.history(memory_id)
                return {"success": True, "history": history if isinstance(history, list) else []}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_context(self, query: str, user_id: Optional[str] = None) -> str:
        """Get relevant memories as context for the conversation.

        This method is called by OpenCode to inject relevant memories
        into the conversation context.

        Args:
            query: The current conversation context/query
            user_id: User ID to get memories for

        Returns:
            Formatted string of relevant memories
        """
        result = self._handle_search(query, user_id=user_id)

        if not result.get("success") or not result.get("memories"):
            return ""

        memories = result["memories"]
        context_parts = ["## Relevant Memories"]

        for i, mem in enumerate(memories, 1):
            content = mem.get("content", "")
            score = mem.get("score", 0)
            context_parts.append(f"{i}. {content} (relevance: {score:.2f})")

        return "\n".join(context_parts)
