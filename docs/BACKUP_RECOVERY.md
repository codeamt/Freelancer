# Database Backup and Recovery

This document describes the backup and recovery system for PostgreSQL databases.

## Overview

The backup and recovery system provides:
- Automated backup scheduling
- Point-in-time recovery support
- Multiple backup types (full, incremental, differential)
- Cloud storage integration
- Backup verification and integrity checks

## Features

### 1. Backup Manager
- Creates database backups using pg_dump
- Supports compression and encryption
- Uploads to cloud storage (S3)
- Calculates checksums for integrity
- Manages backup retention

### 2. Recovery Manager
- Restores databases from backups
- Point-in-time recovery (PITR)
- Database cloning
- Restore verification
- Target database options

### 3. Backup Scheduler
- Automated backup scheduling
- Configurable retention policies
- Health monitoring
- Notification system
- Cleanup automation

### 4. Read Replica Support
- Automatic read replica routing
- Health checks and failover
- Replication lag monitoring
- Weighted load balancing

## Configuration

### Environment Variables

```bash
# Backup settings
BACKUP_DIR=/backups
BACKUP_RETENTION_DAYS=30
BACKUP_COMPRESSION=true
BACKUP_ENCRYPTION=true

# S3 settings (optional)
AWS_S3_BUCKET=my-backups
AWS_S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# Read replica settings
READ_REPLICA_HOSTS=replica1:5432,replica2:5432
READ_REPLICA_USER=replicator
READ_REPLICA_PASSWORD=password
```

### Backup Configuration

```python
from core.db.backup import BackupConfig, BackupType

config = BackupConfig(
    backup_dir="/backups",
    s3_bucket="my-backups",
    backup_type=BackupType.FULL,
    compression=True,
    encryption=True,
    retention_days=30,
    full_backup_interval="daily",
    incremental_interval="hourly"
)
```

## Usage

### CLI Tool

```bash
# Create a full backup
uv run python scripts/db_backup.py create --type full

# List all backups
uv run python scripts/db_backup.py list

# List only full backups
uv run python scripts/db_backup.py list --type full

# Restore from backup
uv run python scripts/db_backup.py restore <backup-id>

# Restore to different database
uv run python scripts/db_backup.py restore <backup-id> --target new_db

# Verify backup integrity
uv run python scripts/db_backup.py verify <backup-id>

# Delete old backups
uv run python scripts/db_backup.py cleanup

# Show backup statistics
uv run python scripts/db_backup.py stats

# Clone a database
uv run python scripts/db_backup.py clone source_db target_db

# Start automated scheduler
uv run python scripts/db_backup.py schedule
```

### Programmatic Usage

```python
from core.db.backup import BackupManager, RecoveryManager, BackupType

# Initialize managers
backup_manager = BackupManager(postgres_config)
recovery_manager = RecoveryManager(postgres_config, backup_manager)

# Create backup
backup_info = await backup_manager.create_backup(BackupType.FULL)
print(f"Backup created: {backup_info.backup_id}")

# List backups
backups = await backup_manager.list_backups()
for backup in backups:
    print(f"{backup.backup_id}: {backup.size_mb:.1f} MB")

# Restore database
restore_info = await recovery_manager.restore_database(
    backup_info.backup_id,
    target_database="restored_db"
)

# Clone database
clone_info = await recovery_manager.clone_database(
    "source_db",
    "target_db"
)
```

## Backup Types

### Full Backup
- Complete database backup
- Contains all data and schema
- Largest size but fastest restore
- Created daily or weekly

### Incremental Backup
- Backs up changes since last backup
- Smaller size
- Requires full backup + all incrementals to restore
- Created hourly

### Differential Backup
- Backs up changes since last full backup
- Larger than incremental but simpler restore
- Requires full backup + latest differential
- Created daily

## Recovery Scenarios

### 1. Full Database Restore
```bash
# Drop and recreate database
uv run python scripts/db_backup.py restore <backup-id>
```

### 2. Point-in-Time Recovery
```python
# Requires WAL archiving
restore_info = await recovery_manager.point_in_time_recovery(
    target_time=datetime(2023, 12, 26, 12, 0, 0)
)
```

### 3. Database Clone
```bash
# Create a copy for testing
uv run python scripts/db_backup.py clone production_db test_db
```

### 4. Partial Restore
```bash
# Restore to new database without dropping existing
uv run python scripts/db_backup.py restore <backup-id> --target new_db --no-clean
```

## Read Replicas

### Configuration
```python
from core.db.replication import ReadReplicaRouter, ReplicaInfo, ReplicaType

# Create router
router = ReadReplicaRouter(primary_config)

# Add replicas
router.add_replica(ReplicaInfo(
    id="replica1",
    host="replica1.example.com",
    port=5432,
    database="app_db",
    username="replicator",
    password="password",
    replica_type=ReplicaType.READ_ONLY,
    weight=1
))

# Initialize
await router.initialize()
```

### Usage
```python
# Read queries go to replicas
users = await router.fetch_all_read("SELECT * FROM users WHERE active = true")

# Write queries go to primary
await router.execute_write("INSERT INTO users (email) VALUES ('test@example.com')")

# Get primary connection
primary = router.get_primary()

# Get specific replica
replica = router.get_read_replica()
```

## Best Practices

### 1. Backup Strategy
- Daily full backups with 30-day retention
- Hourly incremental backups with 1-day retention
- Weekly backups kept for 1 year
- Monthly backups kept for 7 years

### 2. Storage
- Use cloud storage for offsite backups
- Enable encryption for sensitive data
- Use compression to save space
- Verify backups regularly

### 3. Recovery
- Test restore procedures monthly
- Document recovery steps
- Have multiple recovery options
- Monitor replication lag

### 4. Monitoring
- Monitor backup success/failure
- Track backup sizes and duration
- Alert on backup failures
- Monitor replica health

## Automation

### Cron Jobs
```bash
# Daily backup at 2 AM
0 2 * * * /usr/local/bin/uv run python scripts/db_backup.py create --type full

# Hourly incremental backup
0 * * * * /usr/local/bin/uv run python scripts/db_backup.py create --type incremental

# Weekly cleanup
0 3 * * 0 /usr/local/bin/uv run python scripts/db_backup.py cleanup
```

### Systemd Service
```ini
[Unit]
Description=Database Backup Scheduler
After=postgresql.service

[Service]
Type=simple
User=postgres
WorkingDirectory=/opt/app
ExecStart=/usr/local/bin/uv run python scripts/db_backup.py schedule
Restart=always

[Install]
WantedBy=multi-user.target
```

## Troubleshooting

### Common Issues

1. **Backup Fails with Permission Error**
   ```bash
   # Check permissions
   ls -la /backups
   
   # Fix permissions
   chown -R postgres:postgres /backups
   chmod 700 /backs
   ```

2. **Restore Fails with Database Exists**
   ```bash
   # Drop database first
   dropdb target_db
   
   # Or use --no-clean flag
   uv run python scripts/db_backup.py restore <backup-id> --no-clean
   ```

3. **Replica Lag High**
   ```sql
   -- Check replication status
   SELECT * FROM pg_stat_replication;
   
   -- Check lag
   SELECT pg_last_xact_replay_timestamp();
   ```

4. **S3 Upload Fails**
   ```bash
   # Check AWS credentials
   aws s3 ls
   
   # Verify permissions
   aws s3api get-bucket-policy --bucket my-backups
   ```

### Recovery Procedures

1. **Complete Database Loss**
   - Provision new server
   - Install PostgreSQL
   - Restore latest full backup
   - Apply incremental backups
   - Point-in-time recovery if needed

2. **Table Corruption**
   - Restore to temporary database
   - Export affected table
   - Import into production

3. **Replica Failure**
   - Check replica status
   - Rebuild replica if needed
   - Promote replica if primary fails

## Security Considerations

### Backup Security
- Encrypt backups at rest
- Use secure transfer (HTTPS/SFTP)
- Limit backup file permissions
- Audit backup access

### Network Security
- Use VPN for remote backups
- Configure firewall rules
- Use SSL for replication
- Monitor access logs

### Access Control
- Separate backup user
- Limit database permissions
- Use role-based access
- Regular password rotation

## Performance Optimization

### Backup Performance
- Use parallel dumps
- Compress during backup
- Exclude unnecessary tables
- Use dedicated backup server

### Recovery Performance
- Pre-allocate disk space
- Use parallel restore
- Optimize checkpoint settings
- Monitor I/O usage

### Replication Performance
- Optimize network latency
- Use synchronous replication
- Tune wal_keep_segments
- Monitor lag metrics
