"""日志模块。

基于 Python 标准库 logging，日志同时输出到控制台和文件，
格式包含时间、级别、模块名和消息，方便现场演示和事后排查。
"""

import logging
import sys
from logging.handlers import RotatingFileHandler

from config.settings import LOG_DIR, LOG_FILE, LOG_LEVEL

_configured = False


def _configure_once() -> None:
    """配置根日志记录器（只执行一次，避免重复添加 handler）。"""
    root = logging.getLogger()
    root.setLevel(LOG_LEVEL)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台输出
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    # 文件输出（滚动文件，避免日志无限增长）
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)


def get_logger(name: str = "inventory") -> logging.Logger:
    """获取一个命名日志记录器。"""
    global _configured
    if not _configured:
        _configure_once()
        _configured = True
    return logging.getLogger(name)
