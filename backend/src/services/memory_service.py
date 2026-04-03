from typing import Optional, Dict, Any, List
import sys
from pathlib import Path

# Add src directory to Python path if not already added
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from opencode_mem0 import Mem0MemoryPlugin, Mem0Config


class MemoryService:
    def __init__(self, config: Optional[Mem0Config] = None):
        self.config = config or Mem0Config()
        self.plugin = Mem0MemoryPlugin(self.config)
        self._initialized = False

    async def initialize(self):
        if not self._initialized:
            self.plugin.initialize()
            self._initialized = True

    async def add_memory(
        self, content: str, user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        await self.initialize()
        return self.plugin._handle_add(content, user_id, metadata)

    async def search_memories(
        self, query: str, user_id: Optional[str] = None, limit: Optional[int] = None
    ) -> Dict[str, Any]:
        await self.initialize()
        return self.plugin._handle_search(query, user_id, limit)

    async def get_all_memories(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        await self.initialize()
        return self.plugin._handle_get_all(user_id)

    async def update_memory(self, memory_id: str, content: str) -> Dict[str, Any]:
        await self.initialize()
        return self.plugin._handle_update(memory_id, content)

    async def delete_memory(self, memory_id: str) -> Dict[str, Any]:
        await self.initialize()
        return self.plugin._handle_delete(memory_id)

    async def get_memory_history(self, memory_id: str) -> Dict[str, Any]:
        await self.initialize()
        return self.plugin._handle_history(memory_id)

    async def get_context(self, query: str, user_id: Optional[str] = None) -> str:
        await self.initialize()
        return self.plugin.get_context(query, user_id)
