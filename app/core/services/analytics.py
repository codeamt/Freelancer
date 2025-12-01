# -----------------------------------------------------------------------------
# DuckDB Analytics + KPI Aggregation
# -----------------------------------------------------------------------------
import os
import duckdb
from core.utils.logger import get_logger

logger = get_logger(__name__)

DUCKDB_PATH = os.getenv("DUCKDB_PATH", "analytics.db")

class AnalyticsService:
    @staticmethod
    def init_db():
        logger.info("Initializing DuckDB analytics store")
        conn = duckdb.connect(DUCKDB_PATH)
        conn.execute("CREATE TABLE IF NOT EXISTS metrics (timestamp TIMESTAMP, metric TEXT, value DOUBLE)")
        conn.close()

    @staticmethod
    def log_metric(metric: str, value: float):
        logger.info(f"Logging metric: {metric}={value}")
        conn = duckdb.connect(DUCKDB_PATH)
        conn.execute("INSERT INTO metrics VALUES (CURRENT_TIMESTAMP, ?, ?)", (metric, value))
        conn.close()

    @staticmethod
    def summarize_metrics():
        conn = duckdb.connect(DUCKDB_PATH)
        data = conn.execute("SELECT metric, AVG(value) AS avg_value FROM metrics GROUP BY metric").fetchall()
        conn.close()
        logger.debug(f"Metrics summary: {data}")
        return {metric: avg for metric, avg in data}