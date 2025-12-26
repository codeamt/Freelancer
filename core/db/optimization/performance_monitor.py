"""
Performance Monitor

Monitors database performance and provides optimization insights.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import asyncio

from core.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data point"""
    timestamp: datetime
    metric_name: str
    value: float
    unit: str
    tags: Dict[str, str]


@dataclass
class SlowQuery:
    """Slow query information"""
    query: str
    duration: float
    timestamp: datetime
    rows_examined: int
    rows_returned: int
    database: str
    user: str


class PerformanceMonitor:
    """Monitors database performance metrics"""
    
    def __init__(self, postgres_adapter):
        self.postgres = postgres_adapter
        self.metrics_history: List[PerformanceMetric] = []
        self.slow_queries: List[SlowQuery] = []
        self.alert_thresholds = {
            'slow_query_seconds': 1.0,
            'cpu_usage_percent': 80,
            'memory_usage_percent': 85,
            'disk_usage_percent': 90,
            'connection_count': 100
        }
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """
        Collect current performance metrics
        
        Returns:
            Dictionary of performance metrics
        """
        metrics = {}
        
        # Connection metrics
        metrics['connections'] = await self._get_connection_metrics()
        
        # Database size metrics
        metrics['size'] = await self._get_size_metrics()
        
        # Query metrics
        metrics['queries'] = await self._get_query_metrics()
        
        # Cache metrics
        metrics['cache'] = await self._get_cache_metrics()
        
        # Lock metrics
        metrics['locks'] = await self._get_lock_metrics()
        
        # Replication metrics (if applicable)
        metrics['replication'] = await self._get_replication_metrics()
        
        # Store metrics in history
        timestamp = datetime.utcnow()
        for name, value in metrics.items():
            if isinstance(value, (int, float)):
                metric = PerformanceMetric(
                    timestamp=timestamp,
                    metric_name=name,
                    value=value,
                    unit=self._get_metric_unit(name),
                    tags={}
                )
                self.metrics_history.append(metric)
        
        # Keep only last 1000 metrics
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        
        return metrics
    
    async def _get_connection_metrics(self) -> Dict[str, Any]:
        """Get connection-related metrics"""
        query = """
            SELECT 
                count(*) as total,
                count(*) FILTER (WHERE state = 'active') as active,
                count(*) FILTER (WHERE state = 'idle') as idle,
                count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction,
                max(query_start) as longest_query_start
            FROM pg_stat_activity 
            WHERE datname = current_database()
        """
        
        result = await self.postgres.fetch_one(query)
        
        return {
            'total': result['total'],
            'active': result['active'],
            'idle': result['idle'],
            'idle_in_transaction': result['idle_in_transaction'],
            'longest_query_duration': (
                datetime.utcnow() - result['longest_query_start']
            ).total_seconds() if result['longest_query_start'] else 0
        }
    
    async def _get_size_metrics(self) -> Dict[str, Any]:
        """Get database size metrics"""
        query = """
            SELECT 
                pg_size_pretty(pg_database_size(current_database())) as total_size,
                pg_size_pretty(sum(pg_relation_size(schemaname||'.'||tablename))) as table_size
            FROM pg_tables 
            WHERE schemaname = 'public'
        """
        
        result = await self.postgres.fetch_one(query)
        
        # Get individual table sizes
        table_query = """
            SELECT 
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """
        
        tables = await self.postgres.fetch_all(table_query)
        
        return {
            'total_size': result['total_size'],
            'tables_size': result['table_size'],
            'table_details': [
                {
                    'name': t['tablename'],
                    'size': t['size'],
                    'size_bytes': t['size_bytes']
                }
                for t in tables
            ]
        }
    
    async def _get_query_metrics(self) -> Dict[str, Any]:
        """Get query performance metrics"""
        # Check if pg_stat_statements is enabled
        check_query = """
            SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'
        """
        
        ext_exists = await self.postgres.fetch_one(check_query)
        
        if not ext_exists:
            return {'error': 'pg_stat_statements extension not enabled'}
        
        query = """
            SELECT 
                calls,
                total_exec_time,
                mean_exec_time,
                rows,
                100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
            FROM pg_stat_statements 
            ORDER BY total_exec_time DESC
            LIMIT 1
        """
        
        result = await self.postgres.fetch_one(query)
        
        return {
            'total_calls': result['calls'],
            'total_time': result['total_exec_time'],
            'avg_time': result['mean_exec_time'],
            'rows_returned': result['rows'],
            'cache_hit_percent': result['hit_percent']
        }
    
    async def _get_cache_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics"""
        query = """
            SELECT 
                sum(heap_blks_read) as heap_read,
                sum(heap_blks_hit) as heap_hit,
                sum(heap_blks_hit) / nullif(sum(heap_blks_hit) + sum(heap_blks_read), 0) * 100 as ratio
            FROM pg_statio_user_tables
        """
        
        result = await self.postgres.fetch_one(query)
        
        return {
            'heap_blocks_read': result['heap_read'],
            'heap_blocks_hit': result['heap_hit'],
            'hit_ratio': result['ratio']
        }
    
    async def _get_lock_metrics(self) -> Dict[str, Any]:
        """Get lock information"""
        query = """
            SELECT 
                mode,
                count(*) as count,
                array_agg(pid) as pids
            FROM pg_locks 
            WHERE NOT granted
            GROUP BY mode
        """
        
        results = await self.postgres.fetch_all(query)
        
        waiting_locks = []
        for row in results:
            waiting_locks.append({
                'mode': row['mode'],
                'count': row['count'],
                'pids': row['pids']
            })
        
        return {
            'waiting_locks': waiting_locks,
            'total_waiting': sum(l['count'] for l in waiting_locks)
        }
    
    async def _get_replication_metrics(self) -> Dict[str, Any]:
        """Get replication metrics (if configured)"""
        query = """
            SELECT 
                pg_is_in_recovery() as in_recovery,
                pg_last_wal_receive_lsn() as last_received_lsn,
                pg_last_wal_replay_lsn() as last_replayed_lsn,
                pg_last_xact_replay_timestamp() as last_replay_time
        """
        
        try:
            result = await self.postgres.fetch_one(query)
            
            lag = None
            if result['last_received_lsn'] and result['last_replayed_lsn']:
                lag = result['last_received_lsn'] - result['last_replayed_lsn']
            
            return {
                'is_standby': result['in_recovery'],
                'replication_lag_bytes': lag,
                'last_replay_time': result['last_replay_time']
            }
        except:
            return {'error': 'Replication not configured or insufficient permissions'}
    
    def _get_metric_unit(self, metric_name: str) -> str:
        """Get unit for a metric"""
        units = {
            'connections': 'count',
            'size': 'bytes',
            'queries': 'count',
            'cache': 'percent',
            'locks': 'count'
        }
        return units.get(metric_name, 'unknown')
    
    async def monitor_slow_queries(self, duration_minutes: int = 60) -> List[SlowQuery]:
        """
        Monitor for slow queries
        
        Args:
            duration_minutes: How far back to look
            
        Returns:
            List of slow queries
        """
        # This would require logging configuration
        # For now, return empty list
        return []
    
    async def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """
        Generate performance report
        
        Args:
            hours: Number of hours to include in report
            
        Returns:
            Performance report
        """
        # Collect current metrics
        current_metrics = await self.collect_metrics()
        
        # Get historical metrics
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        historical = [
            m for m in self.metrics_history 
            if m.timestamp > cutoff
        ]
        
        # Calculate trends
        trends = {}
        for metric_name in set(m.metric_name for m in historical):
            values = [m.value for m in historical if m.metric_name == metric_name]
            if len(values) > 1:
                trend = (values[-1] - values[0]) / values[0] * 100
                trends[metric_name] = {
                    'change_percent': trend,
                    'direction': 'up' if trend > 0 else 'down'
                }
        
        # Generate alerts
        alerts = self._generate_alerts(current_metrics)
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'current_metrics': current_metrics,
            'trends': trends,
            'alerts': alerts,
            'slow_queries': len(self.slow_queries),
            'recommendations': self._generate_recommendations(current_metrics)
        }
    
    def _generate_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate alerts based on metrics"""
        alerts = []
        
        # Connection alerts
        if 'connections' in metrics:
            conn = metrics['connections']
            if conn['total'] > self.alert_thresholds['connection_count']:
                alerts.append({
                    'type': 'warning',
                    'metric': 'connections',
                    'message': f"High connection count: {conn['total']}"
                })
            
            if conn['idle_in_transaction'] > 10:
                alerts.append({
                    'type': 'warning',
                    'metric': 'idle_transactions',
                    'message': f"Many idle transactions: {conn['idle_in_transaction']}"
                })
        
        # Cache alerts
        if 'cache' in metrics:
            cache = metrics['cache']
            if cache['hit_ratio'] < 90:
                alerts.append({
                    'type': 'warning',
                    'metric': 'cache_hit_ratio',
                    'message': f"Low cache hit ratio: {cache['hit_ratio']:.1f}%"
                })
        
        # Lock alerts
        if 'locks' in metrics:
            locks = metrics['locks']
            if locks['total_waiting'] > 5:
                alerts.append({
                    'type': 'error',
                    'metric': 'waiting_locks',
                    'message': f"High number of waiting locks: {locks['total_waiting']}"
                })
        
        return alerts
    
    def _generate_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        # Cache recommendations
        if 'cache' in metrics:
            cache = metrics['cache']
            if cache['hit_ratio'] < 90:
                recommendations.append(
                    "Consider increasing shared_buffers or adding frequently queried indexes"
                )
        
        # Connection recommendations
        if 'connections' in metrics:
            conn = metrics['connections']
            if conn['total'] > self.alert_thresholds['connection_count'] * 0.8:
                recommendations.append(
                    "Consider implementing connection pooling or increasing max_connections"
                )
        
        # Size recommendations
        if 'size' in metrics:
            size = metrics['size']
            large_tables = [
                t for t in size.get('table_details', [])
                if t['size_bytes'] > 100 * 1024 * 1024  # > 100MB
            ]
            if large_tables:
                recommendations.append(
                    f"Consider partitioning large tables: {', '.join(t['name'] for t in large_tables[:3])}"
                )
        
        return recommendations
    
    async def start_monitoring(self, interval_seconds: int = 60):
        """
        Start continuous monitoring
        
        Args:
            interval_seconds: How often to collect metrics
        """
        logger.info(f"Starting performance monitoring with {interval_seconds}s interval")
        
        while True:
            try:
                await self.collect_metrics()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                await asyncio.sleep(5)
