"""
Query Analyzer

Analyzes database queries to identify performance issues and optimization opportunities.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from core.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class QueryMetric:
    """Query performance metric"""
    query: str
    execution_time: float
    rows_examined: int
    rows_returned: int
    index_used: Optional[str]
    timestamp: datetime
    
    @property
    def efficiency(self) -> float:
        """Calculate query efficiency (rows returned / rows examined)"""
        if self.rows_examined == 0:
            return 1.0
        return self.rows_returned / self.rows_examined


@dataclass
class IndexRecommendation:
    """Index recommendation for optimization"""
    table: str
    columns: List[str]
    index_type: str
    estimated_impact: str
    query_count: int
    reason: str


class QueryAnalyzer:
    """Analyzes database queries for performance issues"""
    
    def __init__(self, postgres_adapter):
        self.postgres = postgres_adapter
        self.slow_query_threshold = 1.0  # seconds
        self.inefficiency_threshold = 0.1  # 10% efficiency threshold
    
    async def analyze_slow_queries(self, hours: int = 24) -> List[QueryMetric]:
        """
        Get slow queries from PostgreSQL statistics
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of slow query metrics
        """
        query = """
            SELECT 
                query,
                mean_exec_time as execution_time,
                calls,
                total_exec_time,
                rows,
                100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
            FROM pg_stat_statements 
            WHERE mean_exec_time > $1
            AND calls > 10
            ORDER BY mean_exec_time DESC
            LIMIT 50
        """
        
        results = await self.postgres.fetch_all(query, self.slow_query_threshold)
        
        metrics = []
        for row in results:
            metric = QueryMetric(
                query=row['query'],
                execution_time=row['execution_time'],
                rows_examined=row.get('rows', 0),
                rows_returned=row.get('rows', 0),
                index_used=None,  # Would need EXPLAIN ANALYZE for this
                timestamp=datetime.utcnow()
            )
            metrics.append(metric)
        
        return metrics
    
    async def get_missing_indexes(self) -> List[IndexRecommendation]:
        """
        Identify potential missing indexes based on query patterns
        
        Returns:
            List of index recommendations
        """
        recommendations = []
        
        # Get queries that would benefit from indexes
        query = """
            SELECT 
                schemaname,
                tablename,
                attname,
                n_distinct,
                correlation
            FROM pg_stats 
            WHERE schemaname = 'public'
            AND n_distinct > 100
            ORDER BY n_distinct DESC
        """
        
        results = await self.postgres.fetch_all(query)
        
        # Analyze common patterns
        table_columns = {}
        for row in results:
            table = row['tablename']
            if table not in table_columns:
                table_columns[table] = []
            table_columns[table].append(row['attname'])
        
        # Generate recommendations based on common patterns
        for table, columns in table_columns.items():
            if table == 'users':
                # Users table recommendations
                if 'email' in columns and 'is_active' in columns:
                    recommendations.append(IndexRecommendation(
                        table='users',
                        columns=['email', 'is_active'],
                        index_type='btree',
                        estimated_impact='High',
                        query_count=0,
                        reason='Frequent lookups by email and status'
                    ))
                
                if 'created_at' in columns:
                    recommendations.append(IndexRecommendation(
                        table='users',
                        columns=['created_at'],
                        index_type='btree',
                        estimated_impact='Medium',
                        query_count=0,
                        reason='Time-based queries for user analytics'
                    ))
            
            elif table == 'devices':
                # Devices table recommendations
                if 'user_id' in columns and 'last_seen_at' in columns:
                    recommendations.append(IndexRecommendation(
                        table='devices',
                        columns=['user_id', 'last_seen_at'],
                        index_type='btree',
                        estimated_impact='High',
                        query_count=0,
                        reason='Device listing with recent activity filtering'
                    ))
            
            elif table == 'refresh_tokens':
                # Refresh tokens recommendations
                if 'user_id' in columns and 'expires_at' in columns:
                    recommendations.append(IndexRecommendation(
                        table='refresh_tokens',
                        columns=['user_id', 'expires_at'],
                        index_type='btree',
                        estimated_impact='High',
                        query_count=0,
                        reason='Token cleanup and user token queries'
                    ))
        
        return recommendations
    
    async def analyze_table_bloat(self) -> List[Dict[str, Any]]:
        """
        Analyze table and index bloat
        
        Returns:
            List of tables with bloat information
        """
        query = """
            SELECT 
                schemaname,
                tablename,
                ROUND(CASE WHEN otta=0 THEN 0.0 ELSE sml.relpages/otta::numeric END,1) AS tbloat,
                CASE WHEN relpages < otta THEN 0 ELSE relpages::bigint - otta END AS wastedpages,
                CASE WHEN relpages < otta THEN 0 ELSE bs*(sml.relpages-otta)::bigint END AS wastedbytes,
                CASE WHEN relpages < otta THEN 0 ELSE (bs*(relpages-otta))::bigint END AS wastedsize,
                iname, 
                ROUND(CASE WHEN iotta=0 OR ipages=0 THEN 0.0 ELSE ipages/iotta::numeric END,1) AS ibloat,
                CASE WHEN ipages < iotta THEN 0 ELSE ipages::bigint - iotta END AS wastedipages,
                CASE WHEN ipages < iotta THEN 0 ELSE bs*(ipages-iotta) END AS wastedibytes
            FROM (
                SELECT 
                    schemaname, tablename, cc.reltuples, cc.relpages, bs,
                    CEIL((cc.reltuples*((datahdr+ma-
                        (CASE WHEN datahdr%ma=0 THEN ma ELSE datahdr%ma END))+nullhdr2+(4*ceil(reltuples/( (bs-page_hdr)/tpl_size )) )))::numeric/(bs-page_hdr)::numeric,1) AS otta,
                    COALESCE(c2.relname,'?') AS iname, COALESCE(c2.reltuples,0) AS ituples, COALESCE(c2.relpages,0) AS ipages, COALESCE(CEIL((c2.reltuples*(datahdr-12))/(bs-page_hdr)::numeric),1) AS iotta
                FROM (
                    SELECT 
                        ma,bs,schemaname,tablename,
                        (datawidth+(hdr+ma-(CASE WHEN hdr%ma=0 THEN ma ELSE hdr%ma END)))::numeric AS datahdr,
                        (maxfracsum*(nullhdr+ma-(CASE WHEN nullhdr%ma=0 THEN ma ELSE nullhdr%ma END))) AS nullhdr2
                    FROM (
                        SELECT 
                            schemaname, tablename, hdr, ma, bs,
                            SUM((1-null_frac)*avg_width) AS datawidth,
                            MAX(null_frac) AS maxfracsum,
                            hdr+(
                                SELECT 1+COUNT(*)*(8-CASE WHEN avg_width<=248 THEN 1 ELSE 8 END)
                                FROM pg_stats s2 
                                WHERE s2.schemaname=s.schemaname AND s2.tablename=s.tablename AND null_frac<>0
                            ) AS nullhdr
                        FROM pg_stats s, (
                            SELECT 
                                (SELECT current_setting('block_size')::numeric) AS bs,
                                CASE WHEN substring(v,12,3) IN ('8.0','8.1','8.2') THEN 27 ELSE 23 END AS hdr,
                                CASE WHEN v ~ 'mingw32' THEN 8 ELSE 4 END AS ma
                            FROM (SELECT version() AS v) AS foo
                        ) AS constants
                        WHERE schemaname='public'
                        GROUP BY 1,2,3,4,5
                    ) AS foo
                ) AS rs
                JOIN pg_class cc ON cc.relname = rs.tablename
                JOIN pg_namespace nn ON cc.relnamespace = nn.oid AND nn.nspname = rs.schemaname AND nn.nspname <> 'information_schema'
                LEFT JOIN pg_index i ON indrelid = cc.oid
                LEFT JOIN pg_class c2 ON c2.oid = i.indexrelid
            ) AS sml
            WHERE tbloat > 1.5 OR ibloat > 1.5
            ORDER BY wastedibytes DESC
        """
        
        results = await self.postgres.fetch_all(query)
        
        bloat_info = []
        for row in results:
            bloat_info.append({
                'table': row['tablename'],
                'index': row['iname'],
                'table_bloat_percent': row['tbloat'],
                'index_bloat_percent': row['ibloat'],
                'wasted_space_mb': row.get('wastedsize', 0) / (1024 * 1024),
                'needs_vacuum': row['tbloat'] > 1.5,
                'needs_reindex': row['ibloat'] > 1.5
            })
        
        return bloat_info
    
    async def get_unused_indexes(self) -> List[Dict[str, Any]]:
        """
        Find indexes that are not being used
        
        Returns:
            List of unused indexes
        """
        query = """
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes 
            WHERE idx_scan = 0
            AND schemaname = 'public'
            ORDER BY tablename, indexname
        """
        
        results = await self.postgres.fetch_all(query)
        
        unused = []
        for row in results:
            unused.append({
                'schema': row['schemaname'],
                'table': row['tablename'],
                'index': row['indexname'],
                'scan_count': row['idx_scan'],
                'recommendation': 'Consider dropping this unused index'
            })
        
        return unused
    
    async def analyze_query_plan(self, query: str) -> Dict[str, Any]:
        """
        Analyze execution plan for a specific query
        
        Args:
            query: SQL query to analyze
            
        Returns:
            Query plan analysis
        """
        explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
        
        result = await self.postgres.fetch_one(explain_query)
        plan = result['QUERY PLAN'][0]
        
        analysis = {
            'total_cost': plan['Plan']['Total Cost'],
            'actual_time': plan['Execution Time'],
            'planning_time': plan['Planning Time'],
            'rows_returned': plan['Plan']['Actual Rows'],
            'has_seq_scan': 'Seq Scan' in str(plan),
            'has_index_scan': 'Index Scan' in str(plan),
            'has_sort': 'Sort' in str(plan),
            'has_hash_join': 'Hash Join' in str(plan),
            'buffer_hits': plan.get('Buffers', {}).get('Shared Hit Blocks', 0),
            'buffer_reads': plan.get('Buffers', {}).get('Shared Read Blocks', 0),
            'recommendations': []
        }
        
        # Generate recommendations
        if analysis['has_seq_scan'] and analysis['rows_returned'] > 1000:
            analysis['recommendations'].append(
                "Consider adding an index to avoid full table scan"
            )
        
        if analysis['has_sort']:
            analysis['recommendations'].append(
                "Consider adding an index with ORDER BY columns"
            )
        
        if analysis['buffer_reads'] > analysis['buffer_hits']:
            analysis['recommendations'].append(
                "High disk I/O detected - consider increasing shared_buffers or adding indexes"
            )
        
        return analysis
    
    async def get_query_statistics(self) -> Dict[str, Any]:
        """
        Get overall database query statistics
        
        Returns:
            Query performance statistics
        """
        query = """
            SELECT 
                datname,
                numbackends,
                xact_commit,
                xact_rollback,
                blks_read,
                blks_hit,
                tup_returned,
                tup_fetched,
                tup_inserted,
                tup_updated,
                tup_deleted
            FROM pg_stat_database 
            WHERE datname = current_database()
        """
        
        result = await self.postgres.fetch_one(query)
        
        stats = {
            'database': result['datname'],
            'active_connections': result['numbackends'],
            'transactions_committed': result['xact_commit'],
            'transactions_rolled_back': result['xact_rollback'],
            'blocks_read': result['blks_read'],
            'blocks_hit': result['blks_hit'],
            'cache_hit_ratio': (
                result['blks_hit'] / (result['blks_hit'] + result['blks_read'])
                if (result['blks_hit'] + result['blks_read']) > 0 else 0
            ),
            'tuples_returned': result['tup_returned'],
            'tuples_fetched': result['tup_fetched'],
            'tuples_inserted': result['tup_inserted'],
            'tuples_updated': result['tup_updated'],
            'tuples_deleted': result['tup_deleted']
        }
        
        return stats
