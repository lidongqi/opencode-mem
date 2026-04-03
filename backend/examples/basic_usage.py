"""Basic usage example for opencode-mem0 plugin."""

import os
from opencode_mem0 import Mem0MemoryPlugin, Mem0Config


def main():
    """Run basic usage example."""
    # Configuration
    config = Mem0Config(
        vector_store="chroma",
        chroma_path="./example_mem0_db",
        llm="openai",
        llm_model="gpt-4o-mini",
        embedding_model="text-embedding-3-small",
        user_id="demo_user"
    )

    # Initialize plugin
    plugin = Mem0MemoryPlugin(config)
    plugin.initialize()

    print("=" * 50)
    print("OpenCode mem0 Memory Plugin Demo")
    print("=" * 50)

    # 1. Add memories
    print("\n1. Adding memories...")
    memories = [
        "我喜欢用 Python 进行数据分析",
        "我熟悉 pandas 和 numpy 库",
        "我正在学习机器学习",
        "我的邮箱是 user@example.com",
        "我喜欢在周末打篮球"
    ]

    for mem in memories:
        result = plugin._handle_add(mem)
        print(f"  Added: {mem[:30]}... -> {result['success']}")

    # 2. Search memories
    print("\n2. Searching memories...")
    queries = [
        "编程相关",
        "联系方式",
        "兴趣爱好"
    ]

    for query in queries:
        print(f"\n  Query: '{query}'")
        results = plugin._handle_search(query, limit=3)
        if results["success"]:
            for mem in results["memories"]:
                print(f"    - {mem['content']} (score: {mem['score']:.2f})")

    # 3. Get all memories
    print("\n3. Getting all memories...")
    all_memories = plugin._handle_get_all()
    if all_memories["success"]:
        print(f"  Total memories: {all_memories['count']}")
        for mem in all_memories["memories"]:
            print(f"    - [{mem['id'][:8]}] {mem['content'][:40]}...")

    # 4. Get context for conversation
    print("\n4. Getting context for conversation...")
    context = plugin.get_context("我想学习数据分析")
    print(context)

    print("\n" + "=" * 50)
    print("Demo completed!")
    print("=" * 50)


if __name__ == "__main__":
    main()
