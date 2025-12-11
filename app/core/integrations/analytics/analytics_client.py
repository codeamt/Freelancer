# -----------------------------------------------------------------------------
# DuckDB Analytics + KPI Aggregation
# -----------------------------------------------------------------------------
import os
import duckdb
from core.utils.logger import get_logger
from abc import ABC, abstractmethod
from typing import Optional
import json
from datetime import datetime
from enum import Enum

class PrivacyRegime(Enum):
    GDPR = "gdpr"       # EU - strict opt-in
    CCPA = "ccpa"       # California - opt-out
    LGPD = "lgpd"       # Brazil - opt-in
    DEFAULT = "default"

class ConsentManager:
    def __init__(self, user_context):
        self.context = user_context
      
    def get_consent_state(self) -> dict:
        consent_json = self.context.get_cookie('cookie_consent')
        if not consent_json:
            return {'necessary': True}
          
        return json.loads(consent_json)
      
    def set_consent(self, categories: dict):
        consent = {
            'necessary': True,
            'analytics': categories.get('analytics', False),
              'marketing': categories.get('marketing', False),
            'functional': categories.get('functional', False),
            'timestamp': datetime.utcnow().isoformat()
        }
          
        cookie_mgr = SecureCookieManager(self.context, settings)
        cookie_mgr.set_session_cookie(
            'cookie_consent',
            json.dumps(consent),
            max_age=31536000  # 1 year
        )
      
    def requires_consent_banner(self) -> bool:
        return 'cookie_consent' not in self.context.cookies
      
    def has_analytics_consent(self) -> bool:
        consent_state = self.get_consent_state()
        return consent_state.get('analytics', False)

logger = get_logger(__name__)

DUCKDB_PATH = os.getenv("DUCKDB_PATH", "analytics.db")


class AnalyticsServiceBase(ABC):
    """Base class for analytics service implementations"""

    @abstractmethod
    def init_db(self):
        """Initialize the analytics database"""
        pass

    @abstractmethod
    def log_metric(self, metric: str, value: float):
        """Log a metric"""
        pass

    @abstractmethod
    def summarize_metrics(self):
        """Summarize metrics"""
        pass


class AnalyticsClient:
    async def track_page_view(self, path: str):
        user_context = current_user_context.get()
        consent_mgr = ConsentManager(user_context)
          
        # Check consent before tracking
        if not consent_mgr.has_analytics_consent():
            logger.info(f"TRACKING SKIPPED: User {user_context.user_id} opted out.")
            return
          
        # Get or create tracking ID
        tracker_id = user_context.get_or_set_cookie(
            'fast_tracker_id',
            self._generate_tracker_id,
            max_age=31536000,
            httponly=True,
            samesite='Lax'
        )
          
        # Send event
        await self._send_event(user_context.user_id, tracker_id, path)


class AnalyticsService(AnalyticsServiceBase):
    """
    Universal analytics service using DuckDB.
    Queries Parquet files on S3 directly.
    """
    def __init__(self, db_path: Optional[str] = None):
        # Can be :memory: or persistent file
        self.db_path = db_path or os.getenv("DUCKDB_PATH", ":memory:")
        self.con = None
    
    def init_db(self):
        logger.info("Initializing DuckDB analytics store")
        if not self.con:
            self.con = duckdb.connect(self.db_path)
        self.con.execute("CREATE TABLE IF NOT EXISTS metrics (timestamp TIMESTAMP, metric TEXT, value DOUBLE)")
        self.con.close()
    
    def connect(self):
        """Create DuckDB connection"""
        if not self.con:
            self.con = duckdb.connect(self.db_path)
            
            # Configure S3 access
            aws_key = os.getenv("AWS_ACCESS_KEY_ID")
            aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
            aws_region = os.getenv("AWS_REGION", "us-east-1")
            
            if aws_key and aws_secret:
                self.con.execute(f"""
                    SET s3_access_key_id='{aws_key}';
                    SET s3_secret_access_key='{aws_secret}';
                    SET s3_region='{aws_region}';
                """)
        
        return self.con

    def log_metric(self, metric: str, value: float):
        logger.info(f"Logging metric: {metric}={value}")
        self.con.execute("INSERT INTO metrics VALUES (CURRENT_TIMESTAMP, ?, ?)", (metric, value))
        #conn.close()

    def summarize_metrics(self):
        data = self.con.execute("SELECT metric, AVG(value) AS avg_value FROM metrics GROUP BY metric").fetchall()
        logger.debug(f"Metrics summary: {data}")
        return {metric: avg for metric, avg in data}
    
    def query(self, sql: str):
        """Execute SQL query and return DataFrame"""
        if not self.con:
            self.connect()
        return self.con.execute(sql).fetchdf()
    
    def query_s3_parquet(self, s3_path: str, filters: Optional[str] = None):
        """
        Query Parquet files on S3.
        
        Example:
            analytics.query_s3_parquet(
                "s3://bucket/analytics/2025-12-*/posts.parquet",
                "WHERE views > 1000"
            )
        """
        sql = f"SELECT * FROM read_parquet('{s3_path}')"
        if filters:
            sql += f" {filters}"
        return self.query(sql)
    
    def close(self):
        if self.con:
            self.con.close()