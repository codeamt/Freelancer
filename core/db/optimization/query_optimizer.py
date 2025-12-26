"""
Query Optimizer

Provides utilities for optimizing database queries.
"""

from typing import Dict, List, Any, Optional, Tuple
import re
from dataclasses import dataclass

from core.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class QuerySuggestion:
    """Query optimization suggestion"""
    type: str
    description: str
    impact: str  # High, Medium, Low
    example: Optional[str] = None


class QueryOptimizer:
    """Optimizes database queries"""
    
    def __init__(self, postgres_adapter):
        self.postgres = postgres_adapter
    
    async def optimize_query(self, query: str) -> Tuple[str, List[QuerySuggestion]]:
        """
        Optimize a SQL query
        
        Args:
            query: SQL query to optimize
            
        Returns:
            Tuple of (optimized_query, suggestions)
        """
        suggestions = []
        optimized = query
        
        # Analyze and optimize
        optimized = self._remove_unnecessary_columns(optimized)
        optimized = self._optimize_joins(optimized)
        optimized = self._add_limit_clause(optimized)
        optimized = self._optimize_where_clause(optimized)
        
        # Generate suggestions
        suggestions.extend(self._analyze_query_patterns(query))
        
        # Get execution plan for more suggestions
        plan_analysis = await self._analyze_execution_plan(optimized)
        suggestions.extend(plan_analysis)
        
        return optimized, suggestions
    
    def _remove_unnecessary_columns(self, query: str) -> str:
        """Remove SELECT * and suggest specific columns"""
        if "SELECT *" in query.upper():
            # Extract table name from FROM clause
            from_match = re.search(r'FROM\s+(\w+)', query, re.IGNORECASE)
            if from_match:
                table = from_match.group(1)
                logger.warning(f"Consider specifying columns instead of SELECT * for table {table}")
        
        return query
    
    def _optimize_joins(self, query: str) -> str:
        """Optimize JOIN operations"""
        # Check for CROSS JOIN that could be INNER JOIN
        if "CROSS JOIN" in query.upper():
            logger.warning("Consider using INNER JOIN instead of CROSS JOIN for better performance")
        
        # Check for missing JOIN conditions
        join_patterns = re.findall(r'JOIN\s+(\w+)\s+(?:ON|USING)', query, re.IGNORECASE)
        for table in join_patterns:
            # This is simplified - real implementation would be more complex
            pass
        
        return query
    
    def _add_limit_clause(self, query: str) -> str:
        """Add LIMIT clause if missing for non-aggregate queries"""
        upper_query = query.upper()
        
        # Don't add LIMIT if already present
        if "LIMIT" in upper_query:
            return query
        
        # Don't add LIMIT for aggregate queries
        if any(keyword in upper_query for keyword in ["COUNT(", "SUM(", "AVG(", "MAX(", "MIN("]):
            return query
        
        # Don't add LIMIT for subqueries or CTEs
        if "WITH " in upper_query or ")" in query:
            return query
        
        # Suggest adding LIMIT
        logger.info("Consider adding LIMIT clause to prevent returning too many rows")
        
        return query
    
    def _optimize_where_clause(self, query: str) -> str:
        """Optimize WHERE clause"""
        # Check for functions on indexed columns
        patterns = [
            (r'WHERE\s+LOWER\((\w+)\)', "Avoid using LOWER() on indexed columns"),
            (r'WHERE\s+(\w+)\s+LIKE\s+\'%', "Avoid leading wildcards in LIKE"),
            (r'WHERE\s+(\w+)\s+\+\s+', "Avoid concatenation in WHERE clause"),
        ]
        
        for pattern, message in patterns:
            if re.search(pattern, query, re.IGNORECASE):
                logger.warning(message)
        
        return query
    
    def _analyze_query_patterns(self, query: str) -> List[QuerySuggestion]:
        """Analyze query for common patterns and suggest optimizations"""
        suggestions = []
        upper_query = query.upper()
        
        # Check for N+1 query pattern
        if "SELECT" in upper_query and upper_query.count("SELECT") > 1:
            suggestions.append(QuerySuggestion(
                type="pattern",
                description="Possible N+1 query detected. Consider using JOIN or bulk operations.",
                impact="High"
            ))
        
        # Check for missing indexes
        if "WHERE" in upper_query and "ORDER BY" in upper_query:
            suggestions.append(QuerySuggestion(
                type="index",
                description="Consider adding a composite index on WHERE and ORDER BY columns",
                impact="Medium"
            ))
        
        # Check for large result sets
        if "SELECT" in upper_query and "LIMIT" not in upper_query:
            suggestions.append(QuerySuggestion(
                type="performance",
                description="Query may return large result set. Consider adding LIMIT.",
                impact="Medium"
            ))
        
        # Check for subqueries that could be JOINs
        if "SELECT" in upper_query and "(SELECT" in upper_query:
            suggestions.append(QuerySuggestion(
                type="rewrite",
                description="Consider rewriting subquery as JOIN for better performance",
                impact="Medium",
                example="SELECT ... FROM table1 JOIN table2 ON ... WHERE ..."
            ))
        
        return suggestions
    
    async def _analyze_execution_plan(self, query: str) -> List[QuerySuggestion]:
        """Analyze execution plan for optimization opportunities"""
        suggestions = []
        
        try:
            explain_query = f"EXPLAIN (FORMAT JSON) {query}"
            result = await self.postgres.fetch_one(explain_query)
            plan = result['QUERY PLAN'][0]['Plan']
            
            # Check for sequential scans
            if self._has_sequential_scan(plan):
                suggestions.append(QuerySuggestion(
                    type="index",
                    description="Sequential scan detected. Consider adding an index.",
                    impact="High"
                ))
            
            # Check for sorts
            if self._has_sort(plan):
                suggestions.append(QuerySuggestion(
                    type="index",
                    description="Sort operation detected. Consider adding an index with ORDER BY columns.",
                    impact="Medium"
                ))
            
            # Check for hash joins
            if self._has_hash_join(plan):
                suggestions.append(QuerySuggestion(
                    type="join",
                    description="Hash join detected. Ensure join columns are indexed.",
                    impact="Medium"
                ))
            
            # Check for high cost
            if plan.get('Total Cost', 0) > 1000:
                suggestions.append(QuerySuggestion(
                    type="performance",
                    description=f"High query cost: {plan['Total Cost']:.2f}. Consider optimization.",
                    impact="High"
                ))
        
        except Exception as e:
            logger.error(f"Failed to analyze execution plan: {e}")
        
        return suggestions
    
    def _has_sequential_scan(self, plan: Dict) -> bool:
        """Check if plan contains sequential scan"""
        if plan.get('Node Type') == 'Seq Scan':
            return True
        
        # Check nested plans
        for key, value in plan.items():
            if isinstance(value, dict):
                if self._has_sequential_scan(value):
                    return True
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and self._has_sequential_scan(item):
                        return True
        
        return False
    
    def _has_sort(self, plan: Dict) -> bool:
        """Check if plan contains sort operation"""
        if plan.get('Node Type') == 'Sort':
            return True
        
        # Check nested plans
        for key, value in plan.items():
            if isinstance(value, dict):
                if self._has_sort(value):
                    return True
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and self._has_sort(item):
                        return True
        
        return False
    
    def _has_hash_join(self, plan: Dict) -> bool:
        """Check if plan contains hash join"""
        if plan.get('Node Type') == 'Hash Join':
            return True
        
        # Check nested plans
        for key, value in plan.items():
            if isinstance(value, dict):
                if self._has_hash_join(value):
                    return True
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and self._has_hash_join(item):
                        return True
        
        return False
    
    async def suggest_indexes_for_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Suggest indexes for a specific query
        
        Args:
            query: SQL query
            
        Returns:
            List of index suggestions
        """
        suggestions = []
        
        # Extract WHERE conditions
        where_match = re.search(r'WHERE\s+(.+?)(?:\s+ORDER\s+BY|\s+GROUP\s+BY|\s+LIMIT|$)', query, re.IGNORECASE | re.DOTALL)
        if where_match:
            where_clause = where_match.group(1)
            columns = self._extract_columns_from_where(where_clause)
            
            if columns:
                suggestions.append({
                    'table': self._extract_table_from_query(query),
                    'columns': columns,
                    'type': 'btree',
                    'reason': 'WHERE clause optimization'
                })
        
        # Extract ORDER BY columns
        order_match = re.search(r'ORDER\s+BY\s+(.+?)(?:\s+LIMIT|$)', query, re.IGNORECASE)
        if order_match:
            order_clause = order_match.group(1)
            columns = [c.strip().split()[0] for c in order_clause.split(',')]
            
            if columns:
                suggestions.append({
                    'table': self._extract_table_from_query(query),
                    'columns': columns,
                    'type': 'btree',
                    'reason': 'ORDER BY optimization'
                })
        
        return suggestions
    
    def _extract_columns_from_where(self, where_clause: str) -> List[str]:
        """Extract column names from WHERE clause"""
        columns = []
        
        # Simple pattern to find column comparisons
        patterns = [
            r'(\w+)\s*=',
            r'(\w+)\s+>',
            r'(\w+)\s+<',
            r'(\w+)\s+LIKE',
            r'(\w+)\s+IN',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, where_clause, re.IGNORECASE)
            columns.extend(matches)
        
        # Remove duplicates and common keywords
        columns = list(set(columns))
        columns = [c for c in columns if c.upper() not in ['AND', 'OR', 'NOT', 'NULL']]
        
        return columns
    
    def _extract_table_from_query(self, query: str) -> str:
        """Extract main table name from query"""
        from_match = re.search(r'FROM\s+(\w+)', query, re.IGNORECASE)
        if from_match:
            return from_match.group(1)
        return "unknown"
    
    async def analyze_index_usage(self, table: str) -> Dict[str, Any]:
        """
        Analyze index usage for a table
        
        Args:
            table: Table name
            
        Returns:
            Index usage analysis
        """
        query = """
            SELECT 
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch,
                pg_size_pretty(pg_relation_size(indexrelid)) as size
            FROM pg_stat_user_indexes 
            WHERE schemaname = 'public' AND tablename = $1
            ORDER BY idx_scan DESC
        """
        
        results = await self.postgres.fetch_all(query, table)
        
        unused_indexes = []
        underutilized = []
        well_used = []
        
        for row in results:
            info = {
                'name': row['indexname'],
                'scans': row['idx_scan'],
                'size': row['size']
            }
            
            if row['idx_scan'] == 0:
                unused_indexes.append(info)
            elif row['idx_scan'] < 10:
                underutilized.append(info)
            else:
                well_used.append(info)
        
        return {
            'table': table,
            'unused_indexes': unused_indexes,
            'underutilized_indexes': underutilized,
            'well_used_indexes': well_used,
            'total_indexes': len(results)
        }
    
    async def vacuum_analyze_table(self, table: str) -> bool:
        """
        Run VACUUM ANALYZE on a table
        
        Args:
            table: Table name
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Running VACUUM ANALYZE on table {table}")
            await self.postgres.execute(f"VACUUM ANALYZE {table}")
            logger.info(f"✓ VACUUM ANALYZE completed for {table}")
            return True
        except Exception as e:
            logger.error(f"Failed to VACUUM ANALYZE {table}: {e}")
            return False
    
    async def update_table_statistics(self, table: str = None) -> bool:
        """
        Update table statistics
        
        Args:
            table: Table name (or None for all tables)
            
        Returns:
            True if successful
        """
        try:
            if table:
                query = f"ANALYZE {table}"
                logger.info(f"Updating statistics for table {table}")
            else:
                query = "ANALYZE"
                logger.info("Updating statistics for all tables")
            
            await self.postgres.execute(query)
            logger.info("✓ Statistics updated successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to update statistics: {e}")
            return False
