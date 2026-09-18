from __future__ import annotations  # 启用未来版本类型注解语法，支持 str | None 等写法

from pathlib import Path  # 导入 Path，用于路径拼接和文件操作
from typing import Literal
from pydantic import BaseModel, Field, model_validator  # 导入配置模型与校验器
import yaml  # 导入 yaml，用于读取配置文件


# =====================================================
# 相机参数配置
# =====================================================
class VendorSdkSettings(BaseModel):
    installer_path: str | None = None
    python_path: str | None = None
    serial_number: str | None = None
    ip_address: str | None = None
    width: int | None = None
    height: int | None = None
    fps: int | None = None


class CameraIntrinsicsSettings(BaseModel):
    enabled: bool = False
    image_size: list[int] = []
    camera_matrix: list[list[float]] = []
    dist_coeffs: list[float] = []
    calibration_rms_px: float | None = None
    source: str | None = None


class CameraSettings(BaseModel):

    vendor: Literal["orbbec", "daheng", "hikvision"] = "orbbec"

    width: int = 1280                 # 图像宽度
    height: int = 800                # 图像高度
    fps: int = 15                    # 帧率（每秒多少帧）

    enable_depth: bool = False       # 是否开启深度图

    timeout_ms: int = 2000           # 取图超时时间（毫秒）

    prefer_format: str = 'MJPG'      # 优先图像格式（MJPG / RGB 等）

    ip_address: str | None = None    # 网络相机 IP 地址
    control_port: int = 8090         # 网络相机控制端口，Orbbec 默认 8090

    serial_number: str | None = None # 指定相机序列号（多相机时使用）

    auto_exposure: bool = True       # 是否自动曝光
    exposure: int | None = None      # 手动曝光值（关闭自动曝光时使用）

    gain: int | None = None          # 增益值

    auto_white_balance: bool = True  # 自动白平衡
    white_balance: int | None = None # 手动白平衡值

    orbbec: VendorSdkSettings = VendorSdkSettings()
    daheng: VendorSdkSettings = VendorSdkSettings()
    hikvision: VendorSdkSettings = VendorSdkSettings()
    intrinsics: CameraIntrinsicsSettings = CameraIntrinsicsSettings()


# =====================================================
# 离线测试配置
# =====================================================
class OfflineSettings(BaseModel):

    scenario: str = 'station_reference'  # 当前离线场景名称

    base_dir: str = 'examples/offline_images'  # 离线图片根目录

    loop: bool = True  # 图片是否循环读取

    # 支持读取的图片后缀
    supported_suffixes: list[str] = [
        '.jpg',
        '.jpeg',
        '.png',
        '.bmp'
    ]

    # 当前场景图像目录（动态生成）
    @property
    def image_dir(self) -> str:
        return str(Path(self.base_dir) / self.scenario)


# =====================================================
# Charuco 标定板参数配置
# =====================================================
class CharucoSettings(BaseModel):

    dictionary_name: str = 'DICT_5X5_100'  # Aruco字典类型

    squares_x: int = Field(default=7, ge=2)  # X方向格子数
    squares_y: int = Field(default=5, ge=2)  # Y方向格子数

    square_length_m: float = Field(default=0.030, gt=0, allow_inf_nan=False)

    marker_length_m: float = Field(default=0.021, gt=0, allow_inf_nan=False)

    min_corners: int = Field(default=8, ge=4)  # 最少检测角点数

    adaptive_thresh_constant: float = 7.0  # 自适应阈值参数

    min_marker_perimeter_rate: float = 0.03  # 最小码周长比例
    max_marker_perimeter_rate: float = 4.0   # 最大码周长比例

    use_subpix: bool = True  # 是否开启亚像素角点优化

    @model_validator(mode='after')
    def validate_board_geometry(self) -> 'CharucoSettings':
        if self.marker_length_m >= self.square_length_m:
            raise ValueError('marker_length_m 必须小于 square_length_m（单位：米）')
        if self.min_corners > (self.squares_x - 1) * (self.squares_y - 1):
            raise ValueError('min_corners 不能超过棋盘内部角点总数')
        return self


# =====================================================
# Aruco 定位码参数配置
# =====================================================
class ArucoSettings(BaseModel):

    dictionary_name: str = 'DICT_4X4_50'  # Aruco码字典

    marker_length_m: float = Field(default=0.150, gt=0)  # 码实际边长(m)

    marker_ids: list[int] = [0, 1, 2, 3]  # 允许识别的ID列表

    preferred_origin_id: int = 0  # 优先作为原点的码ID

    pixels_per_m_fallback: float = 3000.0  # 像素/米换算默认值

    min_markers: int = 1  # 至少识别几个码才有效

    adaptive_thresh_constant: float = 7.0  # 自适应阈值参数

    min_marker_perimeter_rate: float = 0.03
    max_marker_perimeter_rate: float = 4.0


class CrossCalibrationSettings(BaseModel):

    target_type: Literal['aruco', 'charuco'] = 'charuco'
    # aruco 保持现有单码流程；charuco 使用整块 ChArUco 棋盘角点。

    charuco_marker_id: int = 2
    # ChArUco 模式对外使用的逻辑 markerId，不是棋盘内部角点 ID。


class CompensationSafetySettings(BaseModel):

    max_translation_m: float = Field(default=0.050, gt=0)

    max_rotation_rad: float = Field(default=0.174533, gt=0)


# =====================================================
# 后端接口配置
# =====================================================
class BackendSettings(BaseModel):

    enabled: bool = False  # 是否启用真实后端接口

    base_url: str = 'http://127.0.0.1:9000'  # 后端地址

    timeout_sec: float = 5.0  # 请求超时时间（秒）


# =====================================================
# 调试配置
# =====================================================
class DebugSettings(BaseModel):

    save_debug_images: bool = True  # 是否保存调试图

    debug_dir: str = 'data/debug'   # 调试图目录

    log_dir: str = 'logs'           # 日志目录

    save_result_json: bool = True   # 是否保存结果JSON


# =====================================================
# FastAPI 服务配置
# =====================================================
class ServiceSettings(BaseModel):

    host: str = '0.0.0.0'  # 监听地址（全网卡）

    port: int = 8010       # 服务端口


# =====================================================
# 总配置类
# =====================================================
class AppSettings(BaseModel):

    # 当前模式：offline / online
    mode: str = Field(
        default='offline',
        description='offline or online'
    )

    # 相机配置
    camera: CameraSettings = CameraSettings()

    # 离线配置
    offline: OfflineSettings = OfflineSettings()

    # 旧版兼容入口；新流程分别使用下面两套配置。
    charuco: CharucoSettings = CharucoSettings()
    handeye_charuco: CharucoSettings = Field(default_factory=CharucoSettings)
    station_charuco: CharucoSettings = Field(default_factory=CharucoSettings)

    @model_validator(mode='before')
    @classmethod
    def resolve_charuco_profiles(cls, data):
        """仅当新配置块缺失时回退到旧 charuco；显式配置必须完整独立。"""
        if isinstance(data, dict):
            data = dict(data)
            legacy = data.get('charuco')
            if legacy is not None:
                for name in ('handeye_charuco', 'station_charuco'):
                    if name not in data:
                        data[name] = (
                            legacy.model_dump() if isinstance(legacy, CharucoSettings)
                            else dict(legacy) if isinstance(legacy, dict) else legacy
                        )
        return data

    # Aruco 定位配置
    aruco: ArucoSettings = ArucoSettings()

    # 跨机台基准目标类型
    cross_calibration: CrossCalibrationSettings = CrossCalibrationSettings()

    compensation: CompensationSafetySettings = CompensationSafetySettings()

    # 后端配置
    backend: BackendSettings = BackendSettings()

    # 调试配置
    debug: DebugSettings = DebugSettings()

    # 服务配置
    service: ServiceSettings = ServiceSettings()

    # -------------------- 从 YAML 加载配置 --------------------
    @classmethod
    def from_yaml(cls, path: str | Path) -> 'AppSettings':

        # 打开 yaml 文件
        with open(path, 'r', encoding='utf-8') as f:

            # 读取 yaml 内容，空文件则返回 {}
            data = yaml.safe_load(f) or {}

        # 将字典自动映射成配置对象
        return cls(**data)
