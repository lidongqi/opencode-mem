"""Intelligent memory query service with context-aware retrieval."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import logging
import time

from services.memory_cache import MemoryCacheSystem
from services.memory_metrics import MemoryMetricsCollector
from services.memory_service import MemoryService

logger = logging.getLogger(__name__)


@dataclass
class MemoryQueryIntent:
    """Intent analysis result for memory query."""
    needed: bool
    query_type: str
    keywords: List[str]
    priority: str
    search_query: str
    confidence: float = 0.0


class IntelligentMemoryService:
    """Intelligent memory query service with context-aware retrieval."""

    MEMORY_TRIGGERS = {
        'personal': ['我', '我的', '自己', '名字', '是谁', '个人信息', '身份'],
        'preferences': ['喜欢', '偏好', '想要', '习惯', '爱好', '偏好'],
        'history': ['之前', '上次', '记得', '忘记', '说过', '以前', '曾经'],
        'questions': ['我是谁', '你知道', '还记得', '什么是我', '告诉我关于我'],
    }

    def __init__(
        self,
        memory_service: MemoryService,
        cache_system: Optional[MemoryCacheSystem] = None,
        metrics_collector: Optional[MemoryMetricsCollector] = None,
        llm_client: Optional[Any] = None
    ):
        """
        Initialize intelligent memory service.

        Args:
            memory_service: Base memory service
            cache_system: Cache system instance
            metrics_collector: Metrics collector instance
            llm_client: LLM client for intent analysis
        """
        self.memory_service = memory_service
        self.cache = cache_system or MemoryCacheSystem()
        self.metrics = metrics_collector or MemoryMetricsCollector()
        self.llm_client = llm_client

        logger.info("[IntelligentMemory] Service initialized")

    async def get_context_aware_memories(
        self,
        user_input: str,
        user_id: str,
        conversation_history: List[Dict],
        session_id: str,
        token_budget: int = 500
    ) -> str:
        """
        Get context-aware memories for current conversation.

        Args:
            user_input: Current user input
            user_id: User ID
            conversation_history: Recent conversation messages
            session_id: Session ID
            token_budget: Maximum tokens to use for memories

        Returns:
            Formatted memory context string
        """
        start_time = time.time()

        cached = self.cache.get_session_memories(session_id)
        if cached is not None:
            latency = (time.time() - start_time) * 1000
            self.metrics.record_query(
                session_id=session_id,
                user_id=user_id,
                query_type="session_cache",
                latency_ms=latency,
                cache_hit=True,
                cache_type="session",
                memories_count=len(cached),
                tokens_used=self._estimate_tokens(cached)
            )
            logger.info(f"[IntelligentMemory] Session cache hit - session={session_id}")
            return self._format_memories(cached)

        intent = await self._analyze_memory_need(user_input, conversation_history)

        if not intent.needed:
            self.metrics.record_skip(session_id, user_id, reason="not_needed")
            logger.info(f"[IntelligentMemory] Query not needed - type={intent.query_type}")
            return ""

        query_hash = MemoryCacheSystem.hash_query(intent.search_query, user_id)
        cached_result = self.cache.get_query_cache(query_hash)
        if cached_result is not None:
            latency = (time.time() - start_time) * 1000
            self.metrics.record_query(
                session_id=session_id,
                user_id=user_id,
                query_type=intent.query_type,
                latency_ms=latency,
                cache_hit=True,
                cache_type="query",
                memories_count=len(cached_result),
                tokens_used=self._estimate_tokens(cached_result)
            )
            logger.info(f"[IntelligentMemory] Query cache hit - hash={query_hash[:8]}")
            return self._format_memories(cached_result)

        memories = await self._execute_intelligent_search(
            intent, user_id, conversation_history
        )

        if not memories:
            latency = (time.time() - start_time) * 1000
            self.metrics.record_query(
                session_id=session_id,
                user_id=user_id,
                query_type=intent.query_type,
                latency_ms=latency,
                cache_hit=False,
                cache_type="none",
                memories_count=0,
                tokens_used=0
            )
            logger.info(f"[IntelligentMemory] No memories found")
            return ""

        filtered_memories = self._score_and_filter_memories(
            memories, conversation_history, token_budget
        )

        self.cache.set_session_memories(session_id, filtered_memories)
        self.cache.set_query_cache(query_hash, filtered_memories)

        for mem in filtered_memories:
            self.cache.set_hot_memory(mem['id'], mem)

        latency = (time.time() - start_time) * 1000
        self.metrics.record_query(
            session_id=session_id,
            user_id=user_id,
            query_type=intent.query_type,
            latency_ms=latency,
            cache_hit=False,
            cache_type="none",
            memories_count=len(filtered_memories),
            tokens_used=self._estimate_tokens(filtered_memories)
        )

        logger.info(
            f"[IntelligentMemory] Query completed - "
            f"type={intent.query_type}, memories={len(filtered_memories)}, "
            f"latency={latency:.2f}ms"
        )

        return self._format_memories(filtered_memories)

    async def _analyze_memory_need(
        self,
        user_input: str,
        conversation_history: List[Dict]
    ) -> MemoryQueryIntent:
        """Analyze if memory query is needed."""
        logger.info(f"[IntelligentMemory] Analyzing user input: '{user_input}'")
        
        quick_check = self._quick_keyword_check(user_input)
        logger.info(f"[IntelligentMemory] Quick check result: potential_need={quick_check['potential_need']}, keywords={quick_check['keywords']}, types={quick_check['types']}")

        if not quick_check['potential_need']:
            logger.info(f"[IntelligentMemory] No memory need detected")
            return MemoryQueryIntent(
                needed=False,
                query_type='none',
                keywords=[],
                priority='low',
                search_query='',
                confidence=1.0
            )

        if self.llm_client:
            return await self._llm_intent_analysis(user_input, conversation_history, quick_check)
        else:
            intent = self._rule_based_intent(user_input, quick_check)
            logger.info(f"[IntelligentMemory] Rule-based intent: needed={intent.needed}, type={intent.query_type}, search_query='{intent.search_query}'")
            return intent

    def _quick_keyword_check(self, user_input: str) -> Dict[str, Any]:
        """Quick keyword-based check for memory need."""
        found_keywords = []
        matched_types = []

        for category, keywords in self.MEMORY_TRIGGERS.items():
            for kw in keywords:
                if kw in user_input:
                    found_keywords.append(kw)
                    if category not in matched_types:
                        matched_types.append(category)

        return {
            'potential_need': len(found_keywords) > 0,
            'keywords': found_keywords,
            'types': matched_types,
        }

    async def _llm_intent_analysis(
        self,
        user_input: str,
        conversation_history: List[Dict],
        quick_check: Dict[str, Any]
    ) -> MemoryQueryIntent:
        """Use LLM for deep intent analysis."""
        if not self.llm_client:
            logger.warning("[IntelligentMemory] LLM client not available, using rule-based")
            return self._rule_based_intent(user_input, quick_check)

        recent_context = self._format_recent_conversation(conversation_history[-3:])

        prompt = f"""分析用户输入是否需要查询历史记忆。

用户输入："{user_input}"

最近对话：
{recent_context}

请判断：
1. 是否需要查询记忆？（true/false）
2. 需要查询什么类型的记忆？（personal/preferences/history/facts/none）
3. 提取关键实体和查询词
4. 查询优先级

返回 JSON 格式：
{{
  "needed": true/false,
  "query_type": "类型",
  "keywords": ["关键词1", "关键词2"],
  "priority": "high/medium/low",
  "search_query": "构建的查询语句",
  "confidence": 0.0-1.0
}}"""

        try:
            response = await self.llm_client.complete(prompt, max_tokens=200)
            result = json.loads(response)
            return MemoryQueryIntent(**result)
        except json.JSONDecodeError as e:
            logger.warning(f"[IntelligentMemory] LLM response JSON parse failed: {e}")
            return self._rule_based_intent(user_input, quick_check)
        except Exception as e:
            logger.warning(f"[IntelligentMemory] LLM analysis failed: {e}, using rule-based")
            return self._rule_based_intent(user_input, quick_check)

    def _rule_based_intent(
        self,
        user_input: str,
        quick_check: Dict[str, Any]
    ) -> MemoryQueryIntent:
        """Rule-based intent analysis."""
        if not quick_check['potential_need']:
            return MemoryQueryIntent(
                needed=False,
                query_type='none',
                keywords=[],
                priority='low',
                search_query='',
                confidence=1.0
            )

        query_type = quick_check['types'][0] if quick_check['types'] else 'facts'
        keywords = quick_check['keywords']

        if 'personal' in quick_check['types']:
            search_query = f"用户身份 名字 个人信息 {' '.join(keywords[:3])}"
            priority = 'high'
        elif 'preferences' in quick_check['types']:
            search_query = f"用户偏好 喜好 {' '.join(keywords[:3])}"
            priority = 'medium'
        elif 'history' in quick_check['types']:
            search_query = f"历史记录 {' '.join(keywords[:3])}"
            priority = 'medium'
        else:
            search_query = ' '.join(keywords[:5])
            priority = 'low'

        return MemoryQueryIntent(
            needed=True,
            query_type=query_type,
            keywords=keywords,
            priority=priority,
            search_query=search_query,
            confidence=0.7
        )

    async def _execute_intelligent_search(
        self,
        intent: MemoryQueryIntent,
        user_id: str,
        conversation_history: List[Dict]
    ) -> List[Dict]:
        """Execute intelligent search strategies."""
        memories = []
        logger.info(f"[IntelligentMemory] Executing search - query: '{intent.search_query}', user_id: {user_id}")

        try:
            semantic_results = await self.memory_service.search_memories(
                query=intent.search_query,
                user_id=user_id,
                limit=10
            )
            if semantic_results.get('success'):
                found_memories = semantic_results.get('memories', [])
                memories.extend(found_memories)
                logger.info(f"[IntelligentMemory] Semantic search found {len(found_memories)} memories")
            else:
                logger.warning(f"[IntelligentMemory] Semantic search failed: {semantic_results.get('error')}")
        except Exception as e:
            logger.error(f"[IntelligentMemory] Semantic search failed: {e}")

        if intent.query_type == 'personal':
            logger.info(f"[IntelligentMemory] Running additional identity search for personal query")
            try:
                identity_results = await self.memory_service.search_memories(
                    query=f"用户身份 名字 个人信息 {user_id}",
                    user_id=user_id,
                    limit=5
                )
                if identity_results.get('success'):
                    found_memories = identity_results.get('memories', [])
                    memories.extend(found_memories)
                    logger.info(f"[IntelligentMemory] Identity search found {len(found_memories)} memories")
            except Exception as e:
                logger.error(f"[IntelligentMemory] Identity search failed: {e}")

        seen = set()
        unique_memories = []
        for m in memories:
            if m['id'] not in seen:
                seen.add(m['id'])
                unique_memories.append(m)

        logger.info(f"[IntelligentMemory] Total unique memories found: {len(unique_memories)}")
        return unique_memories

    def _score_and_filter_memories(
        self,
        memories: List[Dict],
        conversation_history: List[Dict],
        token_budget: int
    ) -> List[Dict]:
        """Score and filter memories."""
        scored = []
        for m in memories:
            relevance = m.get('score', 0)
            recency = self._calculate_recency_score(m.get('created_at'))
            importance = m.get('metadata', {}).get('importance', 0.5)

            total_score = relevance * 0.5 + recency * 0.3 + importance * 0.2
            scored.append({**m, 'total_score': total_score})

        scored.sort(key=lambda x: x['total_score'], reverse=True)

        selected = []
        total_tokens = 0

        for m in scored:
            tokens = self._estimate_tokens([m])
            if total_tokens + tokens <= token_budget:
                selected.append(m)
                total_tokens += tokens

        return selected

    def _calculate_recency_score(self, timestamp: Optional[str]) -> float:
        """Calculate recency score."""
        if not timestamp:
            return 0.5

        try:
            created = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            now = datetime.now(created.tzinfo) if created.tzinfo else datetime.now()
            age = now - created
            days = age.total_seconds() / (24 * 3600)
            return max(0, 1 - days / 90)
        except Exception as e:
            logger.debug(f"[IntelligentMemory] Failed to parse timestamp: {e}")
            return 0.5

    def _format_memories(self, memories: List[Dict]) -> str:
        """Format memories for injection."""
        if not memories:
            return ""

        lines = ["## 相关历史记忆"]
        for i, m in enumerate(memories, 1):
            score = m.get('total_score', m.get('score', 0))
            lines.append(f"{i}. {m['content']} (相关度: {score:.2f})")

        return "\n".join(lines)

    def _format_recent_conversation(self, messages: List[Dict]) -> str:
        """Format recent conversation for context."""
        if not messages:
            return "无"

        lines = []
        for msg in messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')[:100]
            lines.append(f"{role}: {content}")

        return "\n".join(lines)

    def _estimate_tokens(self, memories: List[Dict]) -> int:
        """Estimate token count for memories."""
        total_chars = sum(len(m.get('content', '')) for m in memories)
        return total_chars // 4

    async def invalidate_user_cache(self, user_id: str) -> None:
        """Invalidate cache when user adds new memory."""
        self.cache.invalidate_user_cache(user_id)
        logger.info(f"[IntelligentMemory] Invalidated cache for user: {user_id}")

    def get_metrics_report(self) -> Dict[str, Any]:
        """Get performance metrics report."""
        return self.metrics.get_performance_report()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache.get_stats()
