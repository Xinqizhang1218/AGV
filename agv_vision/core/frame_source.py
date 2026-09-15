from __future__ import annotations  # 启用未来版本类型注解语法

from abc import ABC, abstractmethod  # 导入抽象基类模块
from agv_vision.core.models import FrameBundle  # 导入图像数据结构（图像帧容器）


# =====================================================
# 图像源基类（所有相机/离线图片读取器都要继承它）
# =====================================================
class BaseFrameSource(ABC):
    """
    图像输入源抽象基类

    作用：
    统一定义图像采集接口。

    可继承实现：
    1. 在线真实相机（奥比中光、海康等）
    2. 离线图片目录读取
    3. 视频文件读取
    4. 网络流读取

    所有子类必须实现：
    open()   -> 打开设备
    grab()   -> 获取一帧图像
    close()  -> 关闭设备
    """

    # -------------------------------------------------
    # 打开图像源
    # -------------------------------------------------
    @abstractmethod
    def open(self) -> None:
        """
        打开设备或初始化资源

        例如：
        - 打开USB相机
        - 连接网口相机
        - 扫描离线图片目录
        """
        raise NotImplementedError  # 子类必须实现

    # -------------------------------------------------
    # 获取一帧图像
    # -------------------------------------------------
    @abstractmethod
    def grab(self) -> FrameBundle:
        """
        获取一帧图像数据

        返回：
        FrameBundle 对象，通常包含：
        - color 彩图
        - depth 深度图（可选）
        - timestamp 时间戳
        """
        raise NotImplementedError  # 子类必须实现

    # -------------------------------------------------
    # 关闭图像源
    # -------------------------------------------------
    @abstractmethod
    def close(self) -> None:
        """
        关闭设备并释放资源

        例如：
        - 关闭相机句柄
        - 停止线程
        - 释放缓存
        """
        raise NotImplementedError  # 子类必须实现