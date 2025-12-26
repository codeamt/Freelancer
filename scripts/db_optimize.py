#!/usr/bin/env python3
"""
Database Optimization CLI Tool

Provides commands for optimizing database performance.
"""

import asyncio
import argparse
import sys
from datetime import datetime
from tabulate import tabulate

from core.db.config import configure_database
from core.db.adapters.postgres_adapter import PostgresAdapter
from core.db.optimization import QueryAnalyzer, IndexManager, PerformanceMonitor, QueryOptimizer
from core.utils.logger import get_logger

logger = get_logger(__name__)


class DBOptimizer:
    """Database optimization CLI"""
    
    def __init__(self):
        self.config = configure_database()
        self.postgres = PostgresAdapter(self.config)
        self.analyzer = QueryAnalyzer(self.postgres)
        self.index_manager = IndexManager(self.postgres)
        self.monitor = PerformanceMonitor(self.postgres)
        self.optimizer = QueryOptimizer(self.postgres)
    
    async def analyze(self):
        """Analyze database performance"""
        print("\n🔍 Database Performance Analysis")
        print("=" * 60)
        
        # Get query statistics
        stats = await self.analyzer.get_query_statistics()
        print(f"\n📊 Database Statistics:")
        print(f"  • Active connections: {stats['active_connections']}")
        print(f"  • Cache hit ratio: {stats['cache_hit_ratio']:.1f}%")
        print(f"  • Transactions committed: {stats['transactions_committed']}")
        print(f"  • Tuples returned: {stats['tuples_returned']:,}")
        
        # Get slow queries
        slow_queries = await self.analyzer.analyze_slow_queries()
        if slow_queries:
            print(f"\n🐌 Slow Queries (>{self.analyzer.slow_query_threshold}s):")
            for query in slow_queries[:5]:
                print(f"  • {query.execution_time:.2f}s: {query.query[:100]}...")
        
        # Get missing indexes
        missing_indexes = await self.analyzer.get_missing_indexes()
        if missing_indexes:
            print(f"\n📝 Recommended Indexes:")
            for idx in missing_indexes:
                print(f"  • {idx.table}({', '.join(idx.columns)}) - {idx.reason}")
        
        # Get unused indexes
        unused = await self.analyzer.get_unused_indexes()
        if unused:
            print(f"\n🗑️  Unused Indexes:")
            for idx in unused[:5]:
                print(f"  • {idx['table']}.{idx['index']}")
    
    async def indexes(self, action: str = "list"):
        """Manage indexes"""
        if action == "list":
            print("\n📋 Database Indexes")
            print("=" * 60)
            
            usage = await self.index_manager.get_index_usage()
            
            data = []
            for idx in usage:
                data.append([
                    idx['table'],
                    idx['index'],
                    idx['scan_count'],
                    idx['size']
                ])
            
            print(tabulate(data, headers=["Table", "Index", "Scans", "Size"], tablefmt="grid"))
        
        elif action == "optimize":
            print("\n🚀 Creating Optimal Indexes...")
            created = await self.index_manager.create_optimal_indexes()
            
            if created:
                print(f"✓ Created {len(created)} indexes:")
                for idx in created:
                    print(f"  • {idx}")
            else:
                print("✓ All optimal indexes already exist")
        
        elif action == "cleanup":
            print("\n🧹 Cleaning up unused indexes...")
            unused = await self.analyzer.get_unused_indexes()
            
            if unused:
                print(f"Found {len(unused)} unused indexes:")
                for idx in unused:
                    print(f"  • {idx['table']}.{idx['index']}")
                
                response = input("\nDrop these indexes? (y/N): ")
                if response.lower() == 'y':
                    for idx in unused:
                        await self.index_manager.drop_index(idx['index'])
                        print(f"  ✓ Dropped {idx['index']}")
            else:
                print("✓ No unused indexes found")
    
    async def vacuum(self, table: str = None):
        """Run VACUUM ANALYZE"""
        print("\n🧹 Running VACUUM ANALYZE...")
        
        if table:
            success = await self.optimizer.vacuum_analyze_table(table)
            if success:
                print(f"✓ VACUUM ANALYZE completed for {table}")
        else:
            print("Running VACUUM ANALYZE on all tables...")
            tables = ['users', 'devices', 'refresh_tokens', 'user_sessions', 'sites']
            for t in tables:
                await self.optimizer.vacuum_analyze_table(t)
                print(f"  ✓ {t}")
    
    async def monitor(self, duration: int = 60):
        """Monitor performance in real-time"""
        print(f"\n📊 Monitoring database performance for {duration} seconds...")
        print("=" * 60)
        print(f"{'Time':<10} {'Connections':<12} {'Cache Hit%':<10} {'Tuples/s':<10}")
        print("-" * 60)
        
        start_time = datetime.utcnow()
        last_tuples = 0
        
        while (datetime.utcnow() - start_time).seconds < duration:
            metrics = await self.monitor.collect_metrics()
            
            # Calculate tuples per second
            current_tuples = metrics['queries']['tuples_returned']
            tuples_per_sec = current_tuples - last_tuples
            last_tuples = current_tuples
            
            print(f"{datetime.now().strftime('%H:%M:%S'):<10} "
                  f"{metrics['connections']['total']:<12} "
                  f"{metrics['cache']['hit_ratio']:<10.1f} "
                  f"{tuples_per_sec:<10}")
            
            await asyncio.sleep(5)
    
    async def optimize_query(self, query: str):
        """Optimize a specific query"""
        print(f"\n🔧 Optimizing Query:")
        print(f"Original: {query}")
        print("-" * 60)
        
        optimized, suggestions = await self.optimizer.optimize_query(query)
        
        print(f"\nOptimized: {optimized}")
        
        if suggestions:
            print(f"\n💡 Suggestions:")
            for i, sugg in enumerate(suggestions, 1):
                print(f"  {i}. [{sugg.impact}] {sugg.description}")
                if sugg.example:
                    print(f"     Example: {sugg.example}")
        
        # Get index suggestions
        index_suggestions = await self.optimizer.suggest_indexes_for_query(query)
        if index_suggestions:
            print(f"\n📝 Index Suggestions:")
            for idx in index_suggestions:
                print(f"  • CREATE INDEX ON {idx['table']}({', '.join(idx['columns'])})")
                print(f"    Reason: {idx['reason']}")
    
    async def bloat(self):
        """Analyze table and index bloat"""
        print("\n📦 Database Bloat Analysis")
        print("=" * 60)
        
        bloat_info = await self.analyzer.analyze_table_bloat()
        
        if bloat_info:
            data = []
            for info in bloat_info:
                data.append([
                    info['table'],
                    f"{info['table_bloat_percent']:.1f}%",
                    f"{info['wasted_space_mb']:.1f} MB",
                    "VACUUM" if info['needs_vacuum'] else "",
                    "REINDEX" if info['needs_reindex'] else ""
                ])
            
            print(tabulate(data, headers=["Table", "Bloat %", "Wasted", "Action Needed", "Index Action"], tablefmt="grid"))
        else:
            print("✓ No significant bloat detected")
    
    async def report(self, hours: int = 24):
        """Generate performance report"""
        print(f"\n📊 Performance Report (Last {hours} hours)")
        print("=" * 60)
        
        report = await self.monitor.get_performance_report(hours)
        
        # Current metrics
        print("\n📈 Current Metrics:")
        metrics = report['current_metrics']
        print(f"  • Connections: {metrics['connections']['total']} total, {metrics['connections']['active']} active")
        print(f"  • Cache Hit Ratio: {metrics['cache']['hit_ratio']:.1f}%")
        print(f"  • Database Size: {metrics['size']['total_size']}")
        
        # Alerts
        if report['alerts']:
            print(f"\n⚠️  Alerts:")
            for alert in report['alerts']:
                icon = "🔴" if alert['type'] == 'error' else "🟡"
                print(f"  {icon} {alert['message']}")
        
        # Recommendations
        if report['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in report['recommendations']:
                print(f"  • {rec}")
        
        # Trends
        if report['trends']:
            print(f"\n📊 Trends:")
            for metric, trend in report['trends'].items():
                icon = "📈" if trend['direction'] == 'up' else "📉"
                print(f"  {icon} {metric}: {trend['change_percent']:+.1f}%")
    
    async def close(self):
        """Close database connection"""
        await self.postgres.close()


async def main():
    parser = argparse.ArgumentParser(description="Database Optimization Tool")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    subparsers.add_parser('analyze', help='Analyze database performance')
    
    # Index commands
    index_parser = subparsers.add_parser('indexes', help='Manage indexes')
    index_parser.add_argument('action', choices=['list', 'optimize', 'cleanup'], 
                            help='Index action', default='list', nargs='?')
    
    # Vacuum command
    vacuum_parser = subparsers.add_parser('vacuum', help='Run VACUUM ANALYZE')
    vacuum_parser.add_argument('--table', help='Specific table to vacuum')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor performance')
    monitor_parser.add_argument('--duration', type=int, default=60, 
                              help='Monitoring duration in seconds')
    
    # Query optimization
    query_parser = subparsers.add_parser('query', help='Optimize a query')
    query_parser.add_argument('sql', help='SQL query to optimize')
    
    # Bloat analysis
    subparsers.add_parser('bloat', help='Analyze database bloat')
    
    # Performance report
    report_parser = subparsers.add_parser('report', help='Generate performance report')
    report_parser.add_argument('--hours', type=int, default=24, 
                             help='Hours to include in report')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    optimizer = DBOptimizer()
    
    try:
        if args.command == 'analyze':
            await optimizer.analyze()
        
        elif args.command == 'indexes':
            await optimizer.indexes(args.action or 'list')
        
        elif args.command == 'vacuum':
            await optimizer.vacuum(args.table)
        
        elif args.command == 'monitor':
            await optimizer.monitor(args.duration)
        
        elif args.command == 'query':
            await optimizer.optimize_query(args.sql)
        
        elif args.command == 'bloat':
            await optimizer.bloat()
        
        elif args.command == 'report':
            await optimizer.report(args.hours)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Operation cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    finally:
        await optimizer.close()


if __name__ == "__main__":
    asyncio.run(main())
