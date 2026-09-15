from __future__ import annotations  # 启用未来版本类型注解语法，支持类型提示

import logging  # Python 内置日志模块
from logging.handlers import RotatingFileHandler  # 支持日志文件滚动写入
from pathlib import Path  # 用于路径和目录处理
from agv_vision.utils.time_utils import today_str


def setup_logging(log_dir: str) -> logging.Logger:  # 定义日志初始化函数，返回 Logger 对象
    daily_log_dir = Path(log_dir) / today_str()
    daily_log_dir.mkdir(parents=True, exist_ok=True)  # 创建日志目录（不存在则创建，已存在不报错）
    logger = logging.getLogger('agv_vision')  # 获取名为 agv_vision 的 Logger
    logger.setLevel(logging.INFO)  # 设置日志等级为 INFO
    logger.propagate = False  # 防止日志重复向上层 Logger 传播
    if logger.handlers:  # 如果已有 Handler，直接返回 Logger
        return logger

    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')  # 日志输出格式

    sh = logging.StreamHandler()  # 创建控制台日志 Handler
    sh.setFormatter(formatter)  # 设置格式
    logger.addHandler(sh)  # 添加到 Logger

    # 创建文件日志 Handler，支持滚动（每个文件最大 5MB，保留 5 个备份）
    fh = RotatingFileHandler(
        daily_log_dir / 'agv_vision.log',  # 日志文件路径
        maxBytes=5 * 1024 * 1024,          # 文件大小上限 5MB
        backupCount=5,                     # 备份文件数量
        encoding='utf-8'                   # 文件编码
    )
    fh.setFormatter(formatter)  # 设置文件日志格式
    logger.addHandler(fh)  # 添加到 Logger
    return logger  # 返回 Logger 对象
