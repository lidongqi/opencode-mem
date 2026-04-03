"""Basic test without OpenAI API Key."""

import os
from opencode_mem0 import Mem0MemoryPlugin, Mem0Config


def main():
    """Run basic test."""
    print("=" * 50)
    print("OpenCode mem0 Memory Plugin - Basic Test")
    print("=" * 50)

    # Test 1: Configuration
    print("\n1. Testing configuration...")
    config = Mem0Config(
        vector_store="chroma",
        chroma_path="./test_mem0_db",
        user_id="test_user"
    )
    print(f"  Vector store: {config.vector_store}")
    print(f"  Chroma path: {config.chroma_path}")
    print(f"  User ID: {config.user_id}")

    # Test 2: Plugin initialization
    print("\n2. Testing plugin initialization...")
    try:
        plugin = Mem0MemoryPlugin(config)
        # We won't initialize without valid API key
        # plugin.initialize()
        print("  Plugin created successfully")
    except Exception as e:
        print(f"  Error: {e}")

    # Test 3: Tool listing
    print("\n3. Testing tool listing...")
    try:
        tools = plugin.get_tools()
        print(f"  Number of tools: {len(tools)}")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
    except Exception as e:
        print(f"  Error: {e}")

    # Test 4: Configuration building
    print("\n4. Testing configuration building...")
    try:
        mem0_config = plugin._build_mem0_config()
        print(f"  Vector store provider: {mem0_config['vector_store']['provider']}")
        print(f"  LLM provider: {mem0_config['llm']['provider']}")
        print(f"  Embedder provider: {mem0_config['embedder']['provider']}")
    except Exception as e:
        print(f"  Error: {e}")

    print("\n" + "=" * 50)
    print("Basic test completed!")
    print("=" * 50)


if __name__ == "__main__":
    main()
