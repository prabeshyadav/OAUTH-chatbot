import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

@celery_app.task(name="ingest_pdf_task")
def ingest_pdf_task(file_path: str, user_id: str):
    """
    Celery task to offload PDF parsing, text splitting, and vector embedding generation to worker.
    """
    from core.rag_utils import ingest_pdf_to_vector_db
    ingest_pdf_to_vector_db(file_path, user_id)
    return {"status": "success", "user_id": user_id, "file_path": file_path}
