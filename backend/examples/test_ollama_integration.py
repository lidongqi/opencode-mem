"""Test mem0 plugin with Ollama."""

import os
from opencode_mem0 import Mem0MemoryPlugin, Mem0Config


def test_with_ollama():
    """Test mem0 plugin integration with Ollama."""
    print("=" * 60)
    print("OpenCode mem0 Plugin - Ollama Integration Test")
    print("=" * 60)

    # 1. Initialize plugin with Ollama
    print("\n1. Initializing mem0 plugin with Ollama...")
    config = Mem0Config(
        vector_store="chroma",
        chroma_path="./test_ollama_mem0",
        llm="ollama",
        llm_model="glm-4.7-flash:latest",
        embedding_model="nomic-embed-text",  # Ollama embedding model
        ollama_base_url="http://localhost:11434",
        user_id="ollama_test_user",
        search_limit=5,
    )

    plugin = Mem0MemoryPlugin(config)
    print(f"  Plugin name: {plugin.name}")
    print(f"  Plugin description: {plugin.description}")

    try:
        plugin.initialize()
        print("  Plugin initialized successfully!")
    except Exception as e:
        print(f"  Initialization failed: {e}")
        print("  Skipping further tests...")
        return

    # 2. Get tools
    print("\n2. Getting available tools...")
    tools = plugin.get_tools()
    print(f"  Number of tools: {len(tools)}")

    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")

    # 3. Test adding memories
    print("\n3. Testing memory add...")
    test_memories = [
        "我喜欢使用 Python 进行数据分析",
        "我熟悉 pandas 和 numpy 库",
        "我的邮箱是 test@example.com",
        "我喜欢在周末跑步",
    ]

    for mem in test_memories:
        result = plugin._handle_add(mem)
        if result["success"]:
            print(f"  ✓ Added: {mem[:40]}...")
        else:
            print(f"  ✗ Failed: {result['error']}")

    # 4. Test searching memories
    print("\n4. Testing memory search...")
    queries = ["编程语言", "联系方式", "兴趣爱好"]

    for query in queries:
        print(f"\n  Query: '{query}'")
        results = plugin._handle_search(query, limit=3)
        if results["success"]:
            print(f"  Found {results['count']} memories:")
            for mem in results["memories"]:
                print(f"    - {mem['content']} (score: {mem.get('score', 0):.2f})")
        else:
            print(f"  ✗ Search failed: {results['error']}")

    # 5. Test getting all memories
    print("\n5. Testing get all memories...")
    all_memories = plugin._handle_get_all()
    if all_memories["success"]:
        print(f"  Total memories: {all_memories['count']}")
        for mem in all_memories["memories"]:
            print(f"    - [{mem['id'][:8]}] {mem['content'][:40]}...")
    else:
        print(f"  ✗ Get all failed: {all_memories['error']}")

    # 6. Test context generation
    print("\n6. Testing context generation...")
    conversation = "我想学习数据分析，有什么推荐？"
    context = plugin.get_context(conversation)
    if context:
        print(f"  Generated context:")
        print(context)
    else:
        print("  No relevant memories found")

    # 7. Test update memory
    if all_memories["success"] and all_memories["count"] > 0:
        print("\n7. Testing memory update...")
        first_mem_id = all_memories["memories"][0]["id"]
        new_content = "我喜欢使用 Python 和 R 进行数据分析"
        result = plugin._handle_update(first_mem_id, new_content)
        if result["success"]:
            print(f"  ✓ Updated memory {first_mem_id[:8]}...")
        else:
            print(f"  ✗ Update failed: {result['error']}")

    # 8. Test history (self-hosted only)
    if all_memories["success"] and all_memories["count"] > 0:
        print("\n8. Testing memory history...")
        first_mem_id = all_memories["memories"][0]["id"]
        result = plugin._handle_history(first_mem_id)
        if result["success"]:
            print(f"  ✓ History retrieved for {first_mem_id[:8]}...")
            if result.get("history"):
                print(f"    History entries: {len(result['history'])}")
        else:
            print(f"  ✗ History failed: {result['error']}")

    print("\n" + "=" * 60)
    print("Ollama Integration Test Completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_with_ollama()
