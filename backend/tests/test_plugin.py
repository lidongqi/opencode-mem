"""Tests for opencode-mem0 plugin."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from opencode_mem0 import Mem0MemoryPlugin, Mem0Config


class TestMem0Config:
    """Test Mem0Config class."""

    def test_default_config(self):
        """Test default configuration."""
        config = Mem0Config()
        assert config.vector_store == "chroma"
        assert config.llm == "ollama"
        assert config.llm_model == "glm-4.7-flash:latest"
        assert config.user_id == "default"
        assert config.search_limit == 5

    def test_custom_config(self):
        """Test custom configuration."""
        config = Mem0Config(
            api_key="test-key",
            vector_store="qdrant",
            user_id="test_user",
            search_limit=10
        )
        assert config.api_key == "test-key"
        assert config.vector_store == "qdrant"
        assert config.user_id == "test_user"
        assert config.search_limit == 10


class TestMem0MemoryPlugin:
    """Test Mem0MemoryPlugin class."""

    def test_plugin_properties(self):
        """Test plugin properties."""
        plugin = Mem0MemoryPlugin()
        assert plugin.name == "mem0_memory"
        assert "memory" in plugin.description.lower()

    def test_get_tools(self):
        """Test getting tools list."""
        plugin = Mem0MemoryPlugin()
        tools = plugin.get_tools()
        
        tool_names = [t.name for t in tools]
        assert "memory_add" in tool_names
        assert "memory_search" in tool_names
        assert "memory_get_all" in tool_names
        assert "memory_delete" in tool_names
        assert "memory_update" in tool_names
        assert "memory_history" in tool_names

    @patch("mem0.Memory")
    @patch("mem0.MemoryClient")
    def test_initialize_self_hosted(self, mock_client, mock_memory):
        """Test initialization in self-hosted mode."""
        config = Mem0Config()  # No API key = self-hosted
        plugin = Mem0MemoryPlugin(config)
        plugin.initialize()
        
        assert plugin._memory is not None
        assert plugin._client is None

    @patch("mem0.Memory")
    @patch("mem0.MemoryClient")
    def test_initialize_hosted(self, mock_client, mock_memory):
        """Test initialization in hosted mode."""
        config = Mem0Config(api_key="test-key")
        plugin = Mem0MemoryPlugin(config)
        plugin.initialize()
        
        assert plugin._client is not None
        assert plugin._memory is None

    def test_build_mem0_config(self):
        """Test building mem0 configuration."""
        config = Mem0Config(
            vector_store="qdrant",
            llm_model="gpt-4",
            embedding_model="text-embedding-3-large"
        )
        plugin = Mem0MemoryPlugin(config)
        
        mem0_config = plugin._build_mem0_config()
        
        assert mem0_config["vector_store"]["provider"] == "qdrant"
        assert mem0_config["llm"]["config"]["model"] == "gpt-4"
        assert mem0_config["embedder"]["config"]["model"] == "text-embedding-3-large"

    @patch("mem0.Memory")
    def test_handle_add_self_hosted(self, mock_memory_class):
        """Test adding memory in self-hosted mode."""
        mock_memory = MagicMock()
        mock_memory.add.return_value = {"id": "mem-123"}
        mock_memory_class.from_config.return_value = mock_memory
        
        config = Mem0Config()
        plugin = Mem0MemoryPlugin(config)
        plugin.initialize()
        
        result = plugin._handle_add("Test content")
        
        assert result["success"] is True
        assert result["memory_id"] == "mem-123"

    @patch("mem0.Memory")
    def test_handle_search_self_hosted(self, mock_memory_class):
        """Test searching memories in self-hosted mode."""
        mock_memory = MagicMock()
        mock_memory.search.return_value = [
            {"id": "mem-1", "memory": "Content 1", "score": 0.9},
            {"id": "mem-2", "memory": "Content 2", "score": 0.8}
        ]
        mock_memory_class.from_config.return_value = mock_memory
        
        config = Mem0Config()
        plugin = Mem0MemoryPlugin(config)
        plugin.initialize()
        
        result = plugin._handle_search("test query")
        
        assert result["success"] is True
        assert result["count"] == 2
        assert len(result["memories"]) == 2

    @patch("mem0.Memory")
    def test_handle_get_all_self_hosted(self, mock_memory_class):
        """Test getting all memories in self-hosted mode."""
        mock_memory = MagicMock()
        mock_memory.get_all.return_value = [
            {"id": "mem-1", "memory": "Content 1", "created_at": "2024-01-01"},
            {"id": "mem-2", "memory": "Content 2", "created_at": "2024-01-02"}
        ]
        mock_memory_class.from_config.return_value = mock_memory
        
        config = Mem0Config()
        plugin = Mem0MemoryPlugin(config)
        plugin.initialize()
        
        result = plugin._handle_get_all()
        
        assert result["success"] is True
        assert result["count"] == 2

    @patch("mem0.Memory")
    def test_handle_delete_self_hosted(self, mock_memory_class):
        """Test deleting memory in self-hosted mode."""
        mock_memory = MagicMock()
        mock_memory_class.from_config.return_value = mock_memory
        
        config = Mem0Config()
        plugin = Mem0MemoryPlugin(config)
        plugin.initialize()
        
        result = plugin._handle_delete("mem-123")
        
        assert result["success"] is True
        mock_memory.delete.assert_called_once_with("mem-123")

    @patch("mem0.Memory")
    def test_handle_update_self_hosted(self, mock_memory_class):
        """Test updating memory in self-hosted mode."""
        mock_memory = MagicMock()
        mock_memory_class.from_config.return_value = mock_memory
        
        config = Mem0Config()
        plugin = Mem0MemoryPlugin(config)
        plugin.initialize()
        
        result = plugin._handle_update("mem-123", "New content")
        
        assert result["success"] is True
        mock_memory.update.assert_called_once_with("mem-123", data="New content")

    @patch("mem0.Memory")
    def test_get_context(self, mock_memory_class):
        """Test getting context for conversation."""
        mock_memory = MagicMock()
        mock_memory.search.return_value = [
            {"id": "mem-1", "memory": "Python is great", "score": 0.95},
            {"id": "mem-2", "memory": "I love coding", "score": 0.85}
        ]
        mock_memory_class.from_config.return_value = mock_memory
        
        config = Mem0Config()
        plugin = Mem0MemoryPlugin(config)
        plugin.initialize()
        
        context = plugin.get_context("programming")
        
        assert "Relevant Memories" in context
        assert "Python is great" in context
        assert "I love coding" in context

    @patch("mem0.Memory")
    def test_get_context_no_results(self, mock_memory_class):
        """Test getting context with no results."""
        mock_memory = MagicMock()
        mock_memory.search.return_value = []
        mock_memory_class.from_config.return_value = mock_memory
        
        config = Mem0Config()
        plugin = Mem0MemoryPlugin(config)
        plugin.initialize()
        
        context = plugin.get_context("unknown topic")
        
        assert context == ""

    @patch("mem0.Memory")
    def test_error_handling(self, mock_memory_class):
        """Test error handling."""
        mock_memory = MagicMock()
        mock_memory.add.side_effect = Exception("Test error")
        mock_memory_class.from_config.return_value = mock_memory
        
        config = Mem0Config()
        plugin = Mem0MemoryPlugin(config)
        plugin.initialize()
        
        result = plugin._handle_add("Test content")
        
        assert result["success"] is False
        assert "Test error" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
