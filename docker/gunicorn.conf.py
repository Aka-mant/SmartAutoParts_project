"""Конфигурация Gunicorn для контейнера SmartAutoParts."""

import multiprocessing
import os


bind = "0.0.0.0:8000"
workers = int(
    os.getenv(
        "GUNICORN_WORKERS",
        str(max(2, multiprocessing.cpu_count() * 2 + 1)),
    )
)
threads = int(os.getenv("GUNICORN_THREADS", "2"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))
accesslog = "-"
errorlog = "-"
capture_output = True
