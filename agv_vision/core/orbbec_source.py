from __future__ import annotations  # 启用未来版本类型注解语法，支持 str | None 这类写法

from typing import Any  # 导入 Any 类型，用于表示不确定的对象类型
import time  # USB相机超时自动重连前短暂等待
import cv2  # 导入 OpenCV，用于图像解码和颜色空间转换
import numpy as np  # 导入 numpy，用于处理底层图像字节数据

from agv_vision.core.frame_source import BaseFrameSource  # 导入图像源抽象基类
from agv_vision.core.models import FrameBundle  # 导入统一的图像帧数据结构
from agv_vision.core.exceptions import SourceError  # 导入图像源异常类


# 尝试导入奥比中光 Python SDK。
# 现场使用的 pip 包名是 pyorbbecsdk2；部分版本安装后的 import 名仍可能是 pyorbbecsdk。
ORBBEC_SDK_IMPORT_ERROR: Exception | None = None
try:
    from pyorbbecsdk2 import (  # type: ignore
        Context,       # 设备上下文，用于枚举设备
        Pipeline,      # 数据流管线，用于启动相机取流
        Config,        # 管线配置对象
        OBSensorType,  # 传感器类型枚举（彩色/深度等）
        OBFormat,      # 图像格式枚举
    )
except Exception as first_error:  # pragma: no cover
    try:
        from pyorbbecsdk import (  # type: ignore
            Context,
            Pipeline,
            Config,
            OBSensorType,
            OBFormat,
        )
    except Exception as second_error:  # pragma: no cover
        # 如果导入失败，则把这些对象都设为 None
        # 这样程序在离线模式下仍然可以导入此文件，但在线模式会在运行时报错提示
        ORBBEC_SDK_IMPORT_ERROR = RuntimeError(
            f'pyorbbecsdk2: {first_error}; pyorbbecsdk: {second_error}'
        )
        Context = Pipeline = Config = OBSensorType = OBFormat = None


# =====================================================
# 奥比中光彩色相机输入源
# 在线模式下，通过 pyorbbecsdk2/pyorbbecsdk 从真实相机取图
# =====================================================
class OrbbecColorSource(BaseFrameSource):

    # -------------------------------------------------
    # 初始化
    # -------------------------------------------------
    def __init__(
        self,
        width: int,                         # 希望的取图宽度
        height: int,                        # 希望的取图高度
        fps: int,                           # 希望的帧率
        timeout_ms: int = 2000,             # 等待帧超时时间（毫秒）
        enable_depth: bool = False,         # 是否启用深度流（当前代码里暂未实际启用）
        prefer_format: str = 'MJPG',        # 优先图像格式
        ip_address: str | None = None,      # 网络相机 IP 地址
        control_port: int = 8090,           # 网络相机控制端口
        serial_number: str | None = None,   # 指定设备序列号，多相机时用
    ):
        self.width = width  # 保存目标宽度
        self.height = height  # 保存目标高度
        self.fps = fps  # 保存目标帧率
        self.timeout_ms = timeout_ms  # 保存超时时间
        self.enable_depth = enable_depth  # 保存是否启用深度流的标志
        self.prefer_format = prefer_format  # 保存优先格式
        self.ip_address = ip_address  # 保存网络相机 IP
        self.control_port = control_port  # 保存网络相机控制端口
        self.serial_number = serial_number  # 保存目标相机序列号
        self.ctx = None  # 后续保存 SDK 上下文对象
        self.device = None  # 后续保存选中的设备对象
        self.pipeline = None  # 后续保存取流管线对象

    # -------------------------------------------------
    # 检查 SDK 是否已安装
    # -------------------------------------------------
    def _require_sdk(self) -> None:
        # 如果 Context 为空，说明奥比中光 Python SDK 没有正确安装
        if Context is None:
            detail = f': {ORBBEC_SDK_IMPORT_ERROR}' if ORBBEC_SDK_IMPORT_ERROR else ''
            raise SourceError(f'未安装或无法导入 pyorbbecsdk2，在线模式不可用{detail}')

    # -------------------------------------------------
    # 打开相机
    # -------------------------------------------------
    def open(self) -> None:
        self._require_sdk()  # 先检查 SDK 是否可用

        self.ctx = Context()  # 创建设备上下文

        # 现场多相机场景下，serial_number 比 IP 更稳定。
        # 因此当 serial_number 存在时，优先按序列号选本地设备。
        if self.serial_number:
            devices = self.ctx.query_devices()  # 查询当前连接的设备列表

            # 如果没有检测到任何设备，直接报错
            if devices.get_count() == 0:
                raise SourceError('未检测到奥比中光设备')

            selected = None  # 先定义一个空的目标设备变量

            # 遍历所有设备
            for i in range(devices.get_count()):
                dev = devices.get_device_by_index(i)  # 获取第 i 个设备
                info = dev.get_device_info()  # 获取设备信息

                # 如果序列号匹配，就选中它
                if info.get_serial_number() == self.serial_number:
                    selected = dev
                    break

            self.device = selected  # 保存选中的设备

            # 如果遍历完还没找到，则报错
            if self.device is None:
                raise SourceError(f'未找到指定序列号设备: {self.serial_number}')
        elif self.ip_address:
            try:
                self.device = self.ctx.create_net_device(self.ip_address, self.control_port)
            except Exception as e:
                raise SourceError(f'按 IP 连接奥比中光设备失败: {self.ip_address}:{self.control_port}, {e}')
            if self.device is None:
                raise SourceError(f'按 IP 连接奥比中光设备失败: {self.ip_address}:{self.control_port}')
        else:
            devices = self.ctx.query_devices()  # 查询当前连接的设备列表

            # 如果没有检测到任何设备，直接报错
            if devices.get_count() == 0:
                raise SourceError('未检测到奥比中光设备')

            # 如果没有指定序列号，就默认取第一个设备
            self.device = devices.get_device_by_index(0)

        # 基于选中的设备创建 Pipeline
        self.pipeline = Pipeline(self.device)

        config = Config()  # 创建配置对象

        # 获取彩色传感器的可用流配置列表
        profile_list = self.pipeline.get_stream_profile_list(OBSensorType.COLOR_SENSOR)

        # 根据字符串格式名，从 OBFormat 中取出对应格式枚举
        fmt = getattr(OBFormat, self.prefer_format, None)

        profile = None  # 先定义 profile 为空

        # 尝试用用户指定的宽高、帧率、格式获取视频流配置
        try:
            if fmt is not None:
                profile = profile_list.get_video_stream_profile(
                    self.width,
                    self.height,
                    fmt,
                    self.fps
                )
        except Exception:
            # 如果获取失败，先置空，后面走默认配置兜底
            profile = None

        # 如果指定配置获取不到，则尝试获取默认配置
        if profile is None:
            try:
                profile = profile_list.get_default_video_stream_profile()
            except Exception as e:
                # 连默认流都拿不到，说明相机流配置有问题
                raise SourceError(f'获取彩色流失败: {e}')

        config.enable_stream(profile)  # 在配置中启用该视频流

        self.pipeline.start(config)  # 启动相机数据流

    # -------------------------------------------------
    # SDK 彩色帧转 OpenCV BGR 图像
    # -------------------------------------------------
    def _frame_to_bgr(self, color_frame: Any) -> np.ndarray:
        # 从 SDK 帧中取出原始字节数据，并转成 numpy 一维数组
        data = np.frombuffer(color_frame.get_data(), dtype=np.uint8)

        width = color_frame.get_width()  # 获取帧宽度
        height = color_frame.get_height()  # 获取帧高度

        fmt_name = str(color_frame.get_format())  # 获取当前帧格式名，转成字符串方便判断

        # 如果是 MJPG / JPEG 压缩格式
        if 'MJPG' in fmt_name or 'JPEG' in fmt_name:
            img = cv2.imdecode(data, cv2.IMREAD_COLOR)  # 直接解码成 BGR 彩图

            # 如果解码失败
            if img is None:
                raise SourceError('MJPG 解码失败')

            return img  # 返回解码后的图像

        # 如果是 RGB 三通道格式，并且不是 RGBA
        if 'RGB' in fmt_name and 'RGBA' not in fmt_name:
            # 先 reshape 成 H x W x 3，再从 RGB 转为 OpenCV 使用的 BGR
            return cv2.cvtColor(
                data.reshape((height, width, 3)),
                cv2.COLOR_RGB2BGR
            )

        # 如果本身已经是 BGR 格式
        if 'BGR' in fmt_name:
            # 直接 reshape 成 H x W x 3，并 copy 一份返回
            return data.reshape((height, width, 3)).copy()

        # 如果是 YUYV / YUY2 格式
        if 'YUYV' in fmt_name or 'YUY2' in fmt_name:
            # 按 H x W x 2 reshape，然后做 YUV -> BGR 转换
            return cv2.cvtColor(
                data.reshape((height, width, 2)),
                cv2.COLOR_YUV2BGR_YUY2
            )

        # 如果是 UYVY 格式
        if 'UYVY' in fmt_name:
            # 按 H x W x 2 reshape，然后做 UYVY -> BGR 转换
            return cv2.cvtColor(
                data.reshape((height, width, 2)),
                cv2.COLOR_YUV2BGR_UYVY
            )

        # 其他格式当前不支持
        raise SourceError(f'暂不支持的彩色格式: {fmt_name}')

    # -------------------------------------------------
    # 获取一帧图像
    # -------------------------------------------------
    def grab(self) -> FrameBundle:
        # 如果 pipeline 还没创建，说明 open() 还没调用
        if self.pipeline is None:
            raise SourceError('在线图像源尚未打开')

        # USB Orbbec 长时间没有取帧时，第一次 wait_for_frames 可能超时。
        # 第一次失败后重启一次管线，再重新等待；第二次仍失败才向上报错。
        frames = self.pipeline.wait_for_frames(self.timeout_ms)
        if frames is None:
            self.close()
            time.sleep(0.2)
            self.open()
            frames = self.pipeline.wait_for_frames(self.timeout_ms)
        if frames is None:
            raise SourceError('等待帧超时（USB 管线自动重连后仍无图像）')

        # 获取彩色帧
        color_frame = frames.get_color_frame()

        # 如果彩色帧为空
        if color_frame is None:
            raise SourceError('未获取到彩色帧')

        # 把 SDK 帧转换成 OpenCV BGR 图像
        image = self._frame_to_bgr(color_frame)

        # 返回统一格式的 FrameBundle
        return FrameBundle(
            color=image,  # 彩色图像
            timestamp_ms=getattr(color_frame, 'get_timestamp', lambda: None)(),  # 时间戳，若无此方法则返回 None
            meta={
                'source': 'orbbec',  # 数据来源
                'width': color_frame.get_width(),  # 图像宽度
                'height': color_frame.get_height(),  # 图像高度
                'format': str(color_frame.get_format()),  # 原始帧格式
            },
        )

    # -------------------------------------------------
    # 关闭相机
    # -------------------------------------------------
    def close(self) -> None:
        # 如果 pipeline 已经存在
        if self.pipeline is not None:
            try:
                self.pipeline.stop()  # 停止数据流
            except Exception:
                # 即使 stop 失败也不再向外抛异常，避免关闭流程中断
                pass

        self.pipeline = None  # 清空 pipeline 引用
