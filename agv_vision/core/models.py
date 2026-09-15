from __future__ import annotations  # 启用未来版本类型注解语法

from dataclasses import dataclass, field, asdict  # 导入数据类工具
from typing import Any  # 任意类型提示
import numpy as np  # 导入 numpy，用于图像矩阵


# =====================================================
# 图像帧数据结构
# =====================================================
@dataclass
class FrameBundle:
    """
    一帧图像数据包
    """

    color: np.ndarray  # 彩色图像（必须）

    depth: np.ndarray | None = None  # 深度图（可选）

    timestamp_ms: int | None = None  # 时间戳（毫秒）

    meta: dict[str, Any] = field(default_factory=dict)  # 附加信息


# =====================================================
# Charuco 棋盘检测结果
# =====================================================
@dataclass
class CharucoObservation:
    """
    Charuco 标定板识别结果
    """

    image_points: list[list[float]]  
    # 图像角点坐标（像素）

    board_points_m: list[list[float]]
    # 标定板真实物理坐标（m）

    corner_count: int
    # 检测到角点数量

    marker_image_points: list[list[list[float]]] | None = None
    # ChArUco 板内 ArUco marker 的四角像点，仅供 3D solvePnP

    marker_object_points_m: list[list[list[float]]] | None = None
    # 与 marker_image_points 对应的板坐标系三维物点

    marker_ids: list[int] | None = None
    # 参与手眼 solvePnP 的 ChArUco 板内 marker ID

    corner_ids: list[int] | None = None
    # 与 image_points 一一对应的 ChArUco 棋盘交点 ID


# =====================================================
# 手眼标定单组采样数据
# =====================================================
@dataclass
class HandEyeSample:
    """
    一组手眼标定样本
    """

    sample_id: str  # 样本编号

    robot_x_m: float  # 机器人X坐标(m)

    robot_y_m: float  # 机器人Y坐标(m)

    observation: CharucoObservation
    # 对应图像识别结果

    image_path: str | None = None
    # 原图保存路径（可选）

    meta: dict[str, Any] = field(default_factory=dict)
    # 扩展信息


# =====================================================
# 手眼标定结果
# =====================================================
@dataclass
class HandEyeCalibrationResult:
    """
    相机坐标 -> 机器人坐标 变换结果
    """

    matrix_2x3: list[list[float]]
    # 2x3 仿射矩阵

    rmse_m: float
    # 拟合误差（米）

    sample_count: int
    # 样本数量

    calibration_type: str = 'charuco_calibrateCamera_pnp_handeye_tsai_park_3d'

    angle_calibration: dict[str, Any] | None = None
    # 复用现有接口字段，内部保存 cameraMatrix/distCoeffs/gTc


# =====================================================
# 单个 Aruco 二维码位姿
# =====================================================
@dataclass
class ArucoMarkerPose2D:
    """
    单个Aruco码检测结果
    """

    marker_id: int  # 二维码ID

    center_x: float  # 中心X像素

    center_y: float  # 中心Y像素

    angle_deg: float  # 角度（度）

    corners: list[list[float]]
    # 四角点坐标

    marker_pixel_length_px: float | None = None
    # 图像里该 ArUco 四边平均像素边长

    pixels_per_m: float | None = None
    # 该 ArUco 根据真实边长估算出的像素/米比例


# =====================================================
# 工位基准点数据
# =====================================================
@dataclass
class StationReference:
    """
    工位视觉基准点
    """

    station_id: str  # 工位编号

    board_center_x: float  # 当前工位中心X

    board_center_y: float  # 当前工位中心Y

    board_angle_deg: float  # 当前工位角度

    marker_count: int  # 识别码数量

    markers: list[ArucoMarkerPose2D]
    # 所有码信息

    marker_length_m: float
    # 码实际边长(m)

    preferred_origin_id: int
    # 原点码ID

    marker_pixel_length_px: float | None = None
    # 当前基准板/码在图像中的平均像素边长

    pixels_per_m: float | None = None
    # 当前基准板/码估算出的像素/米比例

    reference_type: str = 'aruco'
    # aruco 或 charuco；默认值保证旧 reference 仍可读取。

    charuco_corners: list[dict[str, float | int]] = field(default_factory=list)
    # ChArUco 交点，接口形状为 {id, x, y}。

    charuco_object_points_m: list[list[float]] = field(default_factory=list)
    # 与 charuco_corners 一一对应的标定板物理坐标。


# =====================================================
# 补偿结果
# =====================================================
@dataclass
class CompensationResult:
    """
    AGV / 机械臂补偿结果
    """

    dtheta_deg: float  # 角度偏差（度）

    dx_m_camera: float  # 相机坐标系X偏移(m)

    dy_m_camera: float  # 相机坐标系Y偏移(m)

    dtheta_robot_deg: float

    dx_m_robot: float
    # 转到机器人坐标系X偏移

    dy_m_robot: float
    # 转到机器人坐标系Y偏移

    robot_command: dict[str, Any] = field(default_factory=dict)
    # 六自由度机械臂补偿命令。使用 4x4 矩阵表达，避免直接累加欧拉角。



# =====================================================
# dataclass 转 dict 工具函数
# =====================================================
def dataclass_to_dict(obj: Any) -> Any:
    """
    如果对象是 dataclass，则转为字典
    否则原样返回
    """

    # 判断是否是 dataclass 对象
    if hasattr(obj, '__dataclass_fields__'):

        # 转字典
        return asdict(obj)

    # 非 dataclass 直接返回
    return obj
