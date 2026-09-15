from __future__ import annotations  # 启用未来版本类型注解语法

import cv2  # OpenCV，用于 ArUco 检测与绘制
import numpy as np  # numpy，用于数组计算

from agv_vision.config.settings import ArucoSettings  # Aruco 配置类
from agv_vision.core.exceptions import DetectorError  # 检测异常
from agv_vision.core.models import ArucoMarkerPose2D, StationReference  # 数据模型
from agv_vision.vision.common import get_aruco_dictionary  # 获取 Aruco 字典工具


class ArucoReferenceDetector:
    def __init__(self, settings: ArucoSettings):
        self.settings = settings  # 保存配置
        self.aruco = cv2.aruco  # OpenCV ArUco 模块
        dictionary = get_aruco_dictionary(settings.dictionary_name)  # 获取字典
        self.detector_params = self.aruco.DetectorParameters()  # 初始化检测参数
        self.detector_params.cornerRefinementMethod = self.aruco.CORNER_REFINE_SUBPIX  # 启用亚像素角点优化20260721
        self.detector_params.adaptiveThreshConstant = settings.adaptive_thresh_constant  # 设置自适应阈值
        self.detector_params.minMarkerPerimeterRate = settings.min_marker_perimeter_rate  # 最小码周长比例
        self.detector_params.maxMarkerPerimeterRate = settings.max_marker_perimeter_rate  # 最大码周长比例
        self.detector = self.aruco.ArucoDetector(dictionary, self.detector_params)  # 初始化检测器

    def _marker_pixel_length(self, pts: np.ndarray) -> float:
        edges = [
            float(np.linalg.norm(pts[1] - pts[0])),
            float(np.linalg.norm(pts[2] - pts[1])),
            float(np.linalg.norm(pts[3] - pts[2])),
            float(np.linalg.norm(pts[0] - pts[3])),
        ]
        return float(np.mean(edges))

    def detect(self, image: np.ndarray, station_id: str = 'unknown') -> StationReference:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = self.detector.detectMarkers(gray)  # 检测 ArUco 标记
        if ids is None or len(ids) < self.settings.min_markers:  # 检测不到足够的码
            raise DetectorError('未检测到足够的 ArUco 标记')
        ids = ids.reshape(-1).astype(int)  # 转成一维整型数组
        allowed_ids = set(self.settings.marker_ids)
        detected = [
            (corner, marker_id)
            for corner, marker_id in zip(corners, ids)
            if not allowed_ids or int(marker_id) in allowed_ids
        ]
        if len(detected) < self.settings.min_markers:
            raise DetectorError('未检测到足够的目标 ArUco 标记')
        subpix_criteria = (
            cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_MAX_ITER,
            50,
            1e-4,
        )
        markers: list[ArucoMarkerPose2D] = []  # 保存标记对象
        centers = []  # 保存每个标记中心
        all_pts = []  # 保存所有角点
        for c, marker_id in detected:  # 遍历每个标记
            refined = cv2.cornerSubPix(
                gray,
                np.ascontiguousarray(c, dtype=np.float32).reshape(-1, 1, 2),
                (5, 5),
                (-1, -1),
                subpix_criteria,
            )
            pts = refined.reshape(4, 2).astype(np.float32)  # 四角点坐标
            center = pts.mean(axis=0)  # 中心点
            vec = pts[1] - pts[0]  # 计算第一条边向量
            angle = float(np.degrees(np.arctan2(vec[1], vec[0])))  # 计算角度
            marker_pixel_length = self._marker_pixel_length(pts)
            pixels_per_m = marker_pixel_length / self.settings.marker_length_m if self.settings.marker_length_m > 0 else None
            marker = ArucoMarkerPose2D(  # 构建标记对象
                marker_id=int(marker_id),
                center_x=float(center[0]),
                center_y=float(center[1]),
                angle_deg=angle,
                corners=pts.tolist(),
                marker_pixel_length_px=marker_pixel_length,
                pixels_per_m=pixels_per_m,
            )
            markers.append(marker)  # 添加到列表
            centers.append(center)  # 保存中心
            all_pts.extend(pts.tolist())  # 保存角点
        centers = np.array(centers, dtype=np.float32)  # 转成 numpy 数组
        center = centers.mean(axis=0)  # 所有中心点平均
        mean, eigenvectors = cv2.PCACompute(centers, mean=None)  # PCA 计算主方向
        principal = eigenvectors[0]  # 第一主向量
        angle_deg = float(np.degrees(np.arctan2(principal[1], principal[0]))) if len(centers) >= 2 else markers[0].angle_deg  # 计算整体角度
        marker_lengths = [m.marker_pixel_length_px for m in markers if m.marker_pixel_length_px is not None]
        pixels_per_m_values = [m.pixels_per_m for m in markers if m.pixels_per_m is not None]
        marker_pixel_length = float(np.mean(marker_lengths)) if marker_lengths else None
        pixels_per_m = float(np.mean(pixels_per_m_values)) if pixels_per_m_values else None
        return StationReference(  # 构建返回工位对象
            station_id=station_id,
            board_center_x=float(center[0]),
            board_center_y=float(center[1]),
            board_angle_deg=angle_deg,
            marker_count=len(markers),
            markers=markers,
            marker_length_m=self.settings.marker_length_m,
            preferred_origin_id=self.settings.preferred_origin_id,
            marker_pixel_length_px=marker_pixel_length,
            pixels_per_m=pixels_per_m,
        )

    def draw(self, image: np.ndarray, ref: StationReference) -> np.ndarray:
        vis = image.copy()  # 复制图像
        for marker in ref.markers:  # 遍历标记
            pts = np.array(marker.corners, dtype=np.int32)  # 转 int32
            cv2.polylines(vis, [pts], True, (0, 255, 0), 2)  # 绘制多边形
            c = (int(round(marker.center_x)), int(round(marker.center_y)))  # 中心坐标
            cv2.circle(vis, c, 5, (0, 0, 255), -1)  # 绘制中心点
            cv2.putText(vis, f'id={marker.marker_id}', c, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)  # 绘制 ID
        center = (int(round(ref.board_center_x)), int(round(ref.board_center_y)))  # 工位中心
        cv2.circle(vis, center, 8, (255, 0, 255), -1)  # 绘制中心点
        cv2.putText(vis, f'center=({ref.board_center_x:.1f},{ref.board_center_y:.1f}) angle={ref.board_angle_deg:.1f} scale={ref.pixels_per_m or 0:.3f}px/m',
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)  # 显示中心坐标和角度
        return vis  # 返回绘制图像
