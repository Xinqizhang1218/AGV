from __future__ import annotations  # 启用未来版本类型注解语法

from datetime import datetime  # 导入 datetime 模块，用于获取当前时间


def today_str() -> str:
    return datetime.now().strftime('%Y%m%d')

def now_str() -> str:  # 返回当前时间的字符串表示
    return datetime.now().strftime('%Y%m%d_%H%M%S_%f')  
    # 格式化为 YYYYMMDD_HHMMSS_microseconds，用于文件命名或时间戳
