"""
日志管理模块
提供统一的日志记录功能
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
import asyncio
import time
from functools import wraps

from app.core.config import settings

# 创建logs目录
Path("logs").mkdir(exist_ok=True)


class ColoredFormatter(logging.Formatter):
    """
    带颜色的日志格式化器。
    通过重写 format 方法为不同级别的日志应用不同的颜色，
    而不是在每次调用时都创建一个新的 Formatter 实例。
    """
    
    grey = "\x1b[38;20m"
    blue = "\x1b[34;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    COLORS = {
        logging.DEBUG: grey,
        logging.INFO: blue,
        logging.WARNING: yellow,
        logging.ERROR: red,
        logging.CRITICAL: bold_red
    }
    
    def __init__(self, fmt: str, datefmt: Optional[str] = None):
        super().__init__(fmt, datefmt)

    def format(self, record: logging.LogRecord) -> str:
        log_color = self.COLORS.get(record.levelno)
        
        # 根据日志级别动态构建格式字符串
        if record.levelno >= logging.ERROR:
            format_string = (
                f"{log_color}%(asctime)s{self.reset} - "
                f"%(name)s - "
                f"{log_color}%(levelname)s{self.reset} - "
                f"%(message)s"
                f"\n{log_color}%(pathname)s:%(lineno)d{self.reset}"
            )
        else:
            format_string = (
                f"{log_color}%(asctime)s{self.reset} - "
                f"%(name)s - "
                f"{log_color}%(levelname)s{self.reset} - "
                f"%(message)s"
            )

        # 临时设置格式字符串，然后调用父类的 format 方法
        original_fmt = self._fmt
        self._fmt = format_string
        result = super().format(record)
        self._fmt = original_fmt # 恢复原始格式
        
        return result


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: Optional[str] = None
) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        log_file: 日志文件路径
        level: 日志级别
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level or settings.LOG_LEVEL))
    
    # 移除已存在的处理器，避免重复添加
    # 仅移除由本函数添加的处理器，避免影响其他模块的日志配置
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.StreamHandler) and handler.stream is sys.stdout:
            logger.removeHandler(handler)
        elif isinstance(handler, RotatingFileHandler) and handler.baseFilename == Path(log_file_path).resolve().as_posix():
            logger.removeHandler(handler)
    
    # 控制台处理器
    # 注意: ANSI颜色代码在某些环境（如旧版Windows CMD）下可能无法正常显示
    # 可以考虑使用 colorama 库来改善跨平台兼容性
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = ColoredFormatter(
        '%(message)s', # 基础格式，具体格式在 format 方法中动态构建
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    log_file_path = log_file or settings.LOG_FILE
    if log_file_path:
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # 防止日志消息传播到根记录器
    logger.propagate = False
    
    return logger


# 创建一个基础的根日志记录器
logger = setup_logger(settings.PROJECT_NAME)


def get_logger(name: str) -> logging.Logger:
    """
    获取一个以项目名称为前缀的日志记录器。
    这个函数确保了所有子模块的 logger 都继承自统一的配置。
    """
    return logging.getLogger(f"{settings.PROJECT_NAME}.{name}")


def log_execution_time(func):
    """
    记录函数执行时间的装饰器。
    优化后，直接使用 logging.getLogger 获取已配置的实例，而非重新配置。
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        # 高效地获取已配置的 logger 实例
        func_logger = get_logger(func.__module__)
        start_time = time.time()
        func_logger.info(f"Starting async function '{func.__name__}'...")
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            func_logger.info(f"Completed '{func.__name__}' in {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            func_logger.error(f"Error in '{func.__name__}' after {execution_time:.2f}s: {e}", exc_info=True)
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        # 高效地获取已配置的 logger 实例
        func_logger = get_logger(func.__module__)
        start_time = time.time()
        func_logger.info(f"Starting sync function '{func.__name__}'...")
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            func_logger.info(f"Completed '{func.__name__}' in {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            func_logger.error(f"Error in '{func.__name__}' after {execution_time:.2f}s: {e}", exc_info=True)
            raise
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper