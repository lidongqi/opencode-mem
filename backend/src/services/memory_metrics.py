"""Performance metrics collection for memory system."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class QueryMetric:
    """Single query metric record."""
    timestamp: datetime
    session_id: str
    user_id: str
    query_type: str
    latency_ms: float
    cache_hit: bool
    cache_type: str
    memories_count: int
    tokens_used: int
    query_skipped: bool = False
    relevance_score: float = 0.0


class MemoryMetricsCollector:
    """Collect and analyze memory system performance metrics."""

    def __init__(self, max_metrics: int = 10000):
        """
        Initialize metrics collector.

        Args:
            max_metrics: Maximum number of metrics to keep in memory
        """
        self.metrics: List[QueryMetric] = []
        self.max_metrics = max_metrics
        self.session_stats: Dict[str, Dict[str, Any]] = {}
        self.global_stats = {
            'total_queries': 0,
            'total_skipped': 0,
            'total_cache_hits': 0,
            'total_latency_ms': 0.0,
            'total_tokens': 0,
            'query_types': {},
            'cache_types': {},
        }

    def record_query(
        self,
        session_id: str,
        user_id: str,
        query_type: str,
        latency_ms: float,
        cache_hit: bool,
        cache_type: str,
        memories_count: int,
        tokens_used: int,
        relevance_score: float = 0.0
    ) -> None:
        """Record a query metric."""
        metric = QueryMetric(
            timestamp=datetime.now(),
            session_id=session_id,
            user_id=user_id,
            query_type=query_type,
            latency_ms=latency_ms,
            cache_hit=cache_hit,
            cache_type=cache_type,
            memories_count=memories_count,
            tokens_used=tokens_used,
            relevance_score=relevance_score,
        )

        self.metrics.append(metric)
        if len(self.metrics) > self.max_metrics:
            self.metrics.pop(0)

        self._update_global_stats(metric)
        self._update_session_stats(session_id, metric)

        logger.debug(
            f"[Metrics] Recorded query - session={session_id}, "
            f"type={query_type}, latency={latency_ms:.2f}ms, "
            f"cache_hit={cache_hit}, memories={memories_count}"
        )

    def record_skip(self, session_id: str, user_id: str, reason: str = "not_needed") -> None:
        """Record a skipped query."""
        metric = QueryMetric(
            timestamp=datetime.now(),
            session_id=session_id,
            user_id=user_id,
            query_type="skipped",
            latency_ms=0.0,
            cache_hit=False,
            cache_type="none",
            memories_count=0,
            tokens_used=0,
            query_skipped=True,
        )

        self.metrics.append(metric)
        if len(self.metrics) > self.max_metrics:
            self.metrics.pop(0)

        self.global_stats['total_skipped'] += 1

        if session_id not in self.session_stats:
            self.session_stats[session_id] = self._init_session_stats(user_id)
        self.session_stats[session_id]['skipped_queries'] += 1

        logger.debug(f"[Metrics] Recorded skip - session={session_id}, reason={reason}")

    def _update_global_stats(self, metric: QueryMetric) -> None:
        """Update global statistics."""
        self.global_stats['total_queries'] += 1
        if metric.cache_hit:
            self.global_stats['total_cache_hits'] += 1
        self.global_stats['total_latency_ms'] += metric.latency_ms
        self.global_stats['total_tokens'] += metric.tokens_used

        if metric.query_type not in self.global_stats['query_types']:
            self.global_stats['query_types'][metric.query_type] = 0
        self.global_stats['query_types'][metric.query_type] += 1

        if metric.cache_type not in self.global_stats['cache_types']:
            self.global_stats['cache_types'][metric.cache_type] = 0
        self.global_stats['cache_types'][metric.cache_type] += 1

    def _update_session_stats(self, session_id: str, metric: QueryMetric) -> None:
        """Update session statistics."""
        if session_id not in self.session_stats:
            self.session_stats[session_id] = self._init_session_stats(metric.user_id)

        stats = self.session_stats[session_id]
        stats['total_queries'] += 1
        if metric.cache_hit:
            stats['cache_hits'] += 1
        stats['total_latency_ms'] += metric.latency_ms
        stats['total_tokens'] += metric.tokens_used

    def _init_session_stats(self, user_id: str) -> Dict[str, Any]:
        """Initialize session statistics."""
        return {
            'user_id': user_id,
            'total_queries': 0,
            'cache_hits': 0,
            'skipped_queries': 0,
            'total_latency_ms': 0.0,
            'total_tokens': 0,
        }

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report."""
        if not self.metrics:
            return {
                'status': 'no_data',
                'message': 'No metrics collected yet'
            }

        total_queries = self.global_stats['total_queries']
        total_skipped = self.global_stats['total_skipped']
        total_requests = total_queries + total_skipped

        avg_latency = (
            self.global_stats['total_latency_ms'] / total_queries
            if total_queries > 0 else 0
        )

        avg_tokens = (
            self.global_stats['total_tokens'] / total_queries
            if total_queries > 0 else 0
        )

        cache_hit_rate = (
            self.global_stats['total_cache_hits'] / total_queries
            if total_queries > 0 else 0
        )

        query_reduction_rate = (
            total_skipped / total_requests
            if total_requests > 0 else 0
        )

        estimated_token_savings = self._calculate_token_savings()

        return {
            'summary': {
                'total_requests': total_requests,
                'total_queries': total_queries,
                'total_skipped': total_skipped,
                'query_reduction_rate': f"{query_reduction_rate * 100:.1f}%",
            },
            'performance': {
                'avg_latency_ms': round(avg_latency, 2),
                'avg_tokens_per_query': round(avg_tokens, 1),
                'cache_hit_rate': f"{cache_hit_rate * 100:.1f}%",
            },
            'efficiency': {
                'estimated_token_savings': estimated_token_savings,
                'savings_percentage': f"{(estimated_token_savings / (estimated_token_savings + self.global_stats['total_tokens']) * 100):.1f}%" if (estimated_token_savings + self.global_stats['total_tokens']) > 0 else "0%",
            },
            'breakdown': {
                'query_types': self.global_stats['query_types'],
                'cache_types': self.global_stats['cache_types'],
            },
            'active_sessions': len(self.session_stats),
        }

    def _calculate_token_savings(self) -> int:
        """Calculate estimated token savings compared to old approach."""
        old_approach_tokens_per_query = 250
        queries = [m for m in self.metrics if not m.query_skipped]

        if not queries:
            return 0

        old_total = len(queries) * old_approach_tokens_per_query
        new_total = sum(m.tokens_used for m in queries)

        return max(0, old_total - new_total)

    def get_session_report(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get report for a specific session."""
        if session_id not in self.session_stats:
            return None

        stats = self.session_stats[session_id]
        session_metrics = [m for m in self.metrics if m.session_id == session_id]

        if not session_metrics:
            return None

        avg_latency = (
            stats['total_latency_ms'] / stats['total_queries']
            if stats['total_queries'] > 0 else 0
        )

        cache_hit_rate = (
            stats['cache_hits'] / stats['total_queries']
            if stats['total_queries'] > 0 else 0
        )

        return {
            'session_id': session_id,
            'user_id': stats['user_id'],
            'total_queries': stats['total_queries'],
            'cache_hits': stats['cache_hits'],
            'skipped_queries': stats['skipped_queries'],
            'avg_latency_ms': round(avg_latency, 2),
            'cache_hit_rate': f"{cache_hit_rate * 100:.1f}%",
            'total_tokens': stats['total_tokens'],
        }

    def clear_metrics(self) -> None:
        """Clear all collected metrics."""
        self.metrics.clear()
        self.session_stats.clear()
        self.global_stats = {
            'total_queries': 0,
            'total_skipped': 0,
            'total_cache_hits': 0,
            'total_latency_ms': 0.0,
            'total_tokens': 0,
            'query_types': {},
            'cache_types': {},
        }
        logger.info("[Metrics] Cleared all metrics")

    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics in specified format."""
        if format == 'json':
            report = self.get_performance_report()
            return json.dumps(report, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported format: {format}")
