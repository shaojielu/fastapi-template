from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "app", broker=settings.CELERY_BROKER, backend=settings.CELERY_BACKEND
)

celery_app.conf.timezone = "Asia/Shanghai"

# 启动命令 celery -A app worker -l info -P eventlet
