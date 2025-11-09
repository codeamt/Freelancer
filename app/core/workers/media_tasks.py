# Asynchronous Media Processing Worker with Metrics and Scheduled Cleanup

import os
import io
import logging
import threading
from celery import Celery
from celery.schedules import crontab
from prometheus_client import Counter, Histogram, start_http_server
from app.core.services.storage import StorageService

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Prometheus Metrics Setup
# ---------------------------------------------------------------------------

tasks_started = Counter("fastapp_tasks_started_total", "Total tasks started", ["task"])
tasks_succeeded = Counter("fastapp_tasks_succeeded_total", "Total tasks succeeded", ["task"])
tasks_failed = Counter("fastapp_tasks_failed_total", "Total tasks failed", ["task"])
tasks_duration = Histogram("fastapp_task_duration_seconds", "Task execution duration in seconds", ["task"])

def start_metrics_server(port=9102):
    def run():
        logger.info(f"📊 Starting Prometheus metrics server on port {port}")
        start_http_server(port)
    thread = threading.Thread(target=run, daemon=True)
    thread.start()

start_metrics_server()

# ---------------------------------------------------------------------------
# Celery Setup
# ---------------------------------------------------------------------------

celery = Celery(
    "media_tasks",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
)
celery.conf.update(task_track_started=True, task_time_limit=600)

storage = StorageService()

# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

@celery.task(bind=True, max_retries=3)
def process_media_upload(self, module: str, user_id: int, filename: str, temp_path: str, content_type: str):
    task_name = "process_media_upload"
    tasks_started.labels(task=task_name).inc()
    with tasks_duration.labels(task=task_name).time():
        try:
            logger.info(f"Starting post-upload processing for {module}/{user_id}/{filename}")
            with open(temp_path, "rb") as f:
                raw_data = f.read()

            storage.upload_secure_object(module, user_id, filename, raw_data, content_type)

            os.remove(temp_path)
            tasks_succeeded.labels(task=task_name).inc()
            logger.info(f"Completed processing for {module}/{user_id}/{filename}")
            return {"status": "success", "file": filename}

        except Exception as e:
            tasks_failed.labels(task=task_name).inc()
            logger.error(f"Processing failed for {filename}: {e}")
            raise self.retry(exc=e, countdown=15)


@celery.task
def cleanup_old_media(module: str, user_id: int, hours: int = 24):
    task_name = "cleanup_old_media"
    tasks_started.labels(task=task_name).inc()
    with tasks_duration.labels(task=task_name).time():
        try:
            logger.info(f"Running cleanup for {module}/{user_id}")
            storage.cleanup_temp_files(module, user_id, older_than_hours=hours)
            tasks_succeeded.labels(task=task_name).inc()
            return {"status": "ok"}
        except Exception as e:
            tasks_failed.labels(task=task_name).inc()
            logger.error(f"Cleanup failed: {e}")
            return {"status": "error", "error": str(e)}

# ---------------------------------------------------------------------------
# Scheduled Celery Beat Task (24h Cleanup)
# ---------------------------------------------------------------------------

celery.conf.beat_schedule = {
    'cleanup-media-every-24h': {
        'task': 'app.workers.media_tasks.run_daily_cleanup',
        'schedule': crontab(minute=0, hour=0),
    }
}

@celery.task
def run_daily_cleanup():
    task_name = "run_daily_cleanup"
    tasks_started.labels(task=task_name).inc()
    with tasks_duration.labels(task=task_name).time():
        try:
            logger.info("Starting scheduled cleanup across modules.")
            modules = ["commerce", "lms", "social"]
            for module in modules:
                for user_id in range(1, 1001):
                    storage.cleanup_temp_files(module, user_id, older_than_hours=24)
            tasks_succeeded.labels(task=task_name).inc()
            logger.info("✅ Scheduled cleanup complete.")
            return {"status": "ok"}
        except Exception as e:
            tasks_failed.labels(task=task_name).inc()
            logger.error(f"Scheduled cleanup failed: {e}")
            return {"status": "error", "error": str(e)}