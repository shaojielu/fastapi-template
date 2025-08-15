# -*- coding:utf-8 -*-
from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "app",
    broker=settings.celery_broker,
    backend=settings.celery_backend
)

celery_app.conf.timezone = 'Asia/Shanghai'
# 是否使用UTC
celery_app.conf.enable_utc = False
celery_app.conf.broker_connection_retry_on_startup = True # 是否重试连接


# 启动命令 celery -A app worker -l info -P eventlet
