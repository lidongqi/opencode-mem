"""Test intelligent memory service."""

import asyncio
import sys
from pathlib import Path

src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from services.memory_cache import MemoryCacheSystem
from services.memory_metrics import MemoryMetricsCollector
from services.intelligent_memory_service import IntelligentMemoryService, MemoryQueryIntent


async def test_cache_system():
    """Test cache system functionality."""
    print("\n=== Testing Cache System ===")
    
    cache = MemoryCacheSystem(
        session_ttl=3600,
        query_cache_ttl=300,
        lru_max_size=10
    )
    
    memories = [
        {"id": "1", "content": "用户名叫张三", "score": 0.95},
        {"id": "2", "content": "用户喜欢Python", "score": 0.88},
    ]
    
    cache.set_session_memories("session_123", memories)
    cached = cache.get_session_memories("session_123")
    assert cached is not None, "Session cache should return memories"
    assert len(cached) == 2, f"Should have 2 memories, got {len(cached)}"
    print("✓ Session cache working")
    
    query_hash = MemoryCacheSystem.hash_query("用户名字", "user_001")
    cache.set_query_cache(query_hash, memories)
    cached_query = cache.get_query_cache(query_hash)
    assert cached_query is not None, "Query cache should return memories"
    print("✓ Query cache working")
    
    cache.set_hot_memory("1", memories[0])
    hot = cache.get_hot_memory("1")
    assert hot is not None, "LRU cache should return memory"
    print("✓ LRU cache working")
    
    stats = cache.get_stats()
    print(f"✓ Cache stats: {stats}")
    
    cache.invalidate_user_cache("user_001")
    print("✓ Cache invalidation working")


async def test_metrics_collector():
    """Test metrics collection."""
    print("\n=== Testing Metrics Collector ===")
    
    metrics = MemoryMetricsCollector()
    
    metrics.record_query(
        session_id="session_001",
        user_id="user_001",
        query_type="personal",
        latency_ms=150.5,
        cache_hit=True,
        cache_type="session",
        memories_count=3,
        tokens_used=120
    )
    print("✓ Recorded query metric")
    
    metrics.record_skip("session_001", "user_001", reason="not_needed")
    print("✓ Recorded skip metric")
    
    report = metrics.get_performance_report()
    print(f"✓ Performance report: {report}")


async def test_intent_analysis():
    """Test memory query intent analysis."""
    print("\n=== Testing Intent Analysis ===")
    
    from services.intelligent_memory_service import IntelligentMemoryService
    
    class MockMemoryService:
        async def search_memories(self, **kwargs):
            return {"success": True, "memories": []}
    
    service = IntelligentMemoryService(
        memory_service=MockMemoryService(),
        cache_system=MemoryCacheSystem(),
        metrics_collector=MemoryMetricsCollector()
    )
    
    test_cases = [
        ("我是谁", True, "personal"),
        ("我喜欢什么", True, "preferences"),
        ("今天天气怎么样", False, "none"),
        ("你还记得我的名字吗", True, "history"),
        ("帮我写一个函数", False, "none"),
    ]
    
    for user_input, expected_needed, expected_type in test_cases:
        intent = await service._analyze_memory_need(user_input, [])
        
        status = "✓" if intent.needed == expected_needed else "✗"
        print(
            f"{status} Input: '{user_input}' -> "
            f"needed={intent.needed} (expected={expected_needed}), "
            f"type={intent.query_type} (expected={expected_type})"
        )


async def test_scoring_algorithm():
    """Test memory scoring and filtering."""
    print("\n=== Testing Scoring Algorithm ===")
    
    from datetime import datetime, timedelta
    
    class MockMemoryService:
        async def search_memories(self, **kwargs):
            return {"success": True, "memories": []}
    
    service = IntelligentMemoryService(
        memory_service=MockMemoryService(),
        cache_system=MemoryCacheSystem(),
        metrics_collector=MemoryMetricsCollector()
    )
    
    memories = [
        {
            "id": "1",
            "content": "用户名叫张三",
            "score": 0.95,
            "created_at": datetime.now().isoformat(),
            "metadata": {"importance": 0.9}
        },
        {
            "id": "2",
            "content": "用户喜欢Python编程",
            "score": 0.85,
            "created_at": (datetime.now() - timedelta(days=10)).isoformat(),
            "metadata": {"importance": 0.7}
        },
        {
            "id": "3",
            "content": "用户上次提到想吃披萨",
            "score": 0.75,
            "created_at": (datetime.now() - timedelta(days=30)).isoformat(),
            "metadata": {"importance": 0.5}
        },
    ]
    
    filtered = service._score_and_filter_memories(memories, [], token_budget=200)
    
    print(f"✓ Filtered {len(memories)} memories to {len(filtered)}")
    for i, mem in enumerate(filtered, 1):
        print(f"  {i}. {mem['content']} (score: {mem['total_score']:.3f})")


async def test_end_to_end():
    """Test end-to-end intelligent memory query."""
    print("\n=== Testing End-to-End Query ===")
    
    class MockMemoryService:
        async def search_memories(self, query, user_id, limit):
            if "名字" in query or "身份" in query:
                return {
                    "success": True,
                    "memories": [
                        {
                            "id": "mem_001",
                            "content": "用户名叫张三",
                            "score": 0.95,
                            "created_at": "2025-01-01T10:00:00",
                            "metadata": {}
                        }
                    ]
                }
            return {"success": True, "memories": []}
    
    cache = MemoryCacheSystem()
    metrics = MemoryMetricsCollector()
    service = IntelligentMemoryService(
        memory_service=MockMemoryService(),
        cache_system=cache,
        metrics_collector=metrics
    )
    
    context = await service.get_context_aware_memories(
        user_input="我是谁",
        user_id="user_001",
        conversation_history=[],
        session_id="session_001"
    )
    
    print(f"✓ Query result: {context[:100] if context else 'No context'}...")
    
    report = metrics.get_performance_report()
    print(f"✓ Metrics: queries={report['summary']['total_queries']}")


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Intelligent Memory Service Test Suite")
    print("="*60)
    
    try:
        await test_cache_system()
        await test_metrics_collector()
        await test_intent_analysis()
        await test_scoring_algorithm()
        await test_end_to_end()
        
        print("\n" + "="*60)
        print("✓ All tests passed!")
        print("="*60 + "\n")
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}\n")
        raise
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}\n")
        raise


if __name__ == "__main__":
    asyncio.run(main())
