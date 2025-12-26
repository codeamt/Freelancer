# Query Optimization and Indexing Strategy

This document describes the query optimization system implemented for improving database performance.

## Overview

The optimization system provides:
- Query analysis and performance monitoring
- Index management and recommendations
- Automatic optimization suggestions
- Performance metrics collection

## Features

### 1. Query Analyzer
- Identifies slow queries
- Analyzes execution plans
- Detects missing indexes
- Monitors table bloat

### 2. Index Manager
- Creates optimal indexes
- Manages index lifecycle
- Tracks index usage
- Identifies unused indexes

### 3. Performance Monitor
- Real-time metrics collection
- Historical performance tracking
- Alert generation
- Automated recommendations

### 4. Query Optimizer
- SQL query optimization
- Index suggestions
- Query rewriting recommendations
- Performance tuning tips

## Created Indexes

### Users Table
- `idx_users_email_active` - Composite index on email and active status
- `idx_users_role_created` - Role and creation date for admin queries
- `idx_users_verified_created` - Verified users with timestamps
- `idx_users_active_verified` - Active/verified status with date

### Devices Table
- `idx_devices_user_last_seen` - User devices ordered by last activity
- `idx_devices_ip_user` - IP address tracking for security
- `idx_devices_user_active_type` - Active devices by type

### Refresh Tokens Table
- `idx_refresh_tokens_user_expires` - User tokens with expiration
- `idx_refresh_tokens_expired_cleanup` - For cleanup operations
- `idx_refresh_tokens_device_active` - Active device tokens

### Sessions Table
- `idx_sessions_user_expires` - User sessions with expiration
- `idx_sessions_expired` - Expired sessions for cleanup
- `idx_sessions_last_accessed` - Recently active sessions

### Sites Table
- `idx_sites_owner_created` - Sites by owner with creation date
- `idx_sites_settings_gin` - GIN index for JSON settings
- `idx_sites_domain_active` - Active domains

## Usage

### CLI Tool

```bash
# Analyze database performance
uv run python scripts/db_optimize.py analyze

# List all indexes
uv run python scripts/db_optimize.py indexes list

# Create optimal indexes
uv run python scripts/db_optimize.py indexes optimize

# Clean up unused indexes
uv run python scripts/db_optimize.py indexes cleanup

# Run VACUUM ANALYZE
uv run python scripts/db_optimize.py vacuum

# Monitor performance in real-time
uv run python scripts/db_optimize.py monitor --duration 60

# Optimize a specific query
uv run python scripts/db_optimize.py query "SELECT * FROM users WHERE email = 'test@example.com'"

# Analyze database bloat
uv run python scripts/db_optimize.py bloat

# Generate performance report
uv run python scripts/db_optimize.py report --hours 24
```

### Programmatic Usage

```python
from core.db.optimization import QueryAnalyzer, IndexManager, PerformanceMonitor

# Initialize components
analyzer = QueryAnalyzer(postgres_adapter)
index_manager = IndexManager(postgres_adapter)
monitor = PerformanceMonitor(postgres_adapter)

# Analyze slow queries
slow_queries = await analyzer.analyze_slow_queries()

# Get index recommendations
recommendations = await analyzer.get_missing_indexes()

# Monitor performance
metrics = await monitor.collect_metrics()

# Create indexes
from core.db.optimization.index_manager import IndexDefinition, IndexType

index_def = IndexDefinition(
    name="idx_custom_index",
    table="users",
    columns=["email", "created_at"],
    index_type=IndexType.BTREE
)

await index_manager.create_index(index_def)
```

## Performance Metrics

### Key Metrics Tracked
- Connection count and status
- Cache hit ratio
- Query execution times
- Index usage statistics
- Table bloat percentage
- Lock contention

### Alert Thresholds
- Slow queries: > 1 second
- Cache hit ratio: < 90%
- Connection count: > 100
- Table bloat: > 50%

## Best Practices

### 1. Query Optimization
- Use specific columns instead of SELECT *
- Add LIMIT clauses to prevent large result sets
- Avoid functions on indexed columns
- Use appropriate JOIN types

### 2. Index Management
- Create indexes for frequent WHERE clauses
- Use composite indexes for multi-column queries
- Consider partial indexes for filtered data
- Regularly review and remove unused indexes

### 3. Performance Monitoring
- Monitor slow query logs
- Track index usage regularly
- Analyze execution plans
- Set up performance alerts

### 4. Maintenance
- Run VACUUM ANALYZE regularly
- Update statistics after large data changes
- Rebuild fragmented indexes
- Monitor disk space usage

## Optimization Examples

### Before Optimization
```sql
-- Slow query without proper indexes
SELECT * FROM users 
WHERE email = 'user@example.com' 
AND is_active = true 
ORDER BY created_at DESC 
LIMIT 10;
```

### After Optimization
```sql
-- Uses idx_users_email_active index
-- Faster with proper indexing
SELECT id, email, created_at FROM users 
WHERE email = 'user@example.com' 
AND is_active = true 
ORDER BY created_at DESC 
LIMIT 10;
```

## Index Types

### B-Tree (Default)
- Best for equality and range queries
- Supports sorting
- Most common index type

### GIN
- For composite values (arrays, JSON)
- Supports containment queries
- Used for sites.settings column

### Partial Indexes
- Index subset of rows
- Smaller and faster
- Example: Active users only

### Composite Indexes
- Multiple columns in one index
- Order matters
- Covers specific query patterns

## Troubleshooting

### Common Issues

1. **Slow Queries**
   - Check if indexes exist
   - Analyze execution plan
   - Consider query rewrite

2. **High Memory Usage**
   - Review index count
   - Check for unused indexes
   - Optimize work_mem

3. **Lock Contention**
   - Identify long-running transactions
   - Use CONCURRENTLY for index creation
   - Consider connection pooling

## Monitoring Dashboard

To set up a monitoring dashboard:

1. Enable pg_stat_statements:
```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
```

2. Configure logging in postgresql.conf:
```
log_min_duration_statement = 1000  # Log queries > 1s
log_checkpoints = on
log_connections = on
log_disconnections = on
```

3. Use the CLI tool for regular reports:
```bash
# Daily performance report
uv run python scripts/db_optimize.py report --hours 24

# Weekly analysis
uv run python scripts/db_optimize.py analyze
uv run python scripts/db_optimize.py bloat
```

## Performance Tuning Parameters

### PostgreSQL Configuration
```ini
# Memory settings
shared_buffers = 256MB
work_mem = 4MB
maintenance_work_mem = 64MB

# Query planning
random_page_cost = 1.1
effective_cache_size = 1GB

# Logging
log_min_duration_statement = 1000
log_checkpoints = on
```

### Application Level
- Use connection pooling
- Implement query caching
- Batch operations when possible
- Use prepared statements

## Future Enhancements

1. **Automatic Index Creation**
   - AI-powered index recommendations
   - Automatic index creation based on query patterns

2. **Advanced Monitoring**
   - Real-time dashboard
   - Performance trend analysis
   - Predictive analytics

3. **Query Caching**
   - Application-level caching
   - Query result caching
   - Invalidation strategies
