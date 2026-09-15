from __future__ import annotations  # 启用未来版本类型注解语法

import cv2  # OpenCV，用于图像处理
import numpy as np  # numpy，用于数组计算

from agv_vision.config.settings import CharucoSettings  # 导入 Charuco 配置
from agv_vision.core.exceptions import DetectorError  # 导入检测异常
from agv_vision.core.models import CharucoObservation  # 导入 Charuco 检测结果对象
from agv_vision.vision.common import get_aruco_dictionary  # 获取 Aruco 字典工具


class CharucoBoardDetector:
    def __init__(self, settings: CharucoSettings):
        self.settings = settings  # 保存配置
        dictionary = get_aruco_dictionary(settings.dictionary_name)  # 获取 Aruco 字典
        self.aruco = cv2.aruco  # OpenCV ArUco 模块
        self.board = self.aruco.CharucoBoard(  # 创建 Charuco 棋盘对象
            (settings.squares_x, settings.squares_y),  # 棋盘格数
            settings.square_length_m,  # 大格边长(m)
            settings.marker_length_m,  # 小码边长(m)
            dictionary,  # Aruco 字典
        )
        self.detector_params = self.aruco.DetectorParameters()  # 初始化检测参数
        self.detector_params.cornerRefinementMethod = self.aruco.CORNER_REFINE_SUBPIX
        self.detector_params.adaptiveThreshConstant = settings.adaptive_thresh_constant  # 自适应阈值
        self.detector_params.minMarkerPerimeterRate = settings.min_marker_perimeter_rate  # 最小码比例
        self.detector_params.maxMarkerPerimeterRate = settings.max_marker_perimeter_rate  # 最大码比例
        self.charuco_params = self.aruco.CharucoParameters()  # Charuco 参数
        self.detector = self.aruco.CharucoDetector(self.board, self.charuco_params, self.detector_params)  # 初始化检测器

    def detect(self, image: np.ndarray) -> CharucoObservation:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # 转灰度图
        charuco_corners, charuco_ids, marker_corners, marker_ids = self.detector.detectBoard(gray)  # 检测角点
        if charuco_ids is None or charuco_corners is None or len(charuco_ids) < self.settings.min_corners:  # 检测角点不足
            raise DetectorError(f'ChArUco 角点不足，至少需要 {self.settings.min_corners} 个')

        if self.settings.use_subpix:
            charuco_corners = cv2.cornerSubPix(
                gray,
                np.ascontiguousarray(charuco_corners, dtype=np.float32).reshape(-1, 1, 2),
                (5, 5),
                (-1, -1),
                (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_MAX_ITER, 50, 1e-4),
            )
        corners = charuco_corners.reshape(-1, 2).astype(np.float32)  # 转为 N x 2 float32
        ids = charuco_ids.reshape(-1).astype(int)  # 转为 int
        board_points = self.board.getChessboardCorners()[ids][:, :2].astype(np.float32)  # 对应物理坐标

        marker_image_points: list[list[list[float]]] = []
        marker_object_points_m: list[list[list[float]]] = []
        detected_marker_ids: list[int] = []
        board_marker_ids = self.board.getIds().reshape(-1).astype(int)
        board_marker_points = self.board.getObjPoints()
        object_points_by_id = {
            int(marker_id): np.asarray(points, dtype=np.float32).reshape(4, 3)
            for marker_id, points in zip(board_marker_ids, board_marker_points)
        }
        if marker_ids is not None and marker_corners is not None:
            marker_criteria = (
                cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_MAX_ITER,
                50,
                1e-4,
            )
            for marker_corner, marker_id in zip(marker_corners, marker_ids.reshape(-1)):
                marker_id_int = int(marker_id)
                if marker_id_int not in object_points_by_id:
                    continue
                refined_marker = cv2.cornerSubPix(
                    gray,
                    np.ascontiguousarray(marker_corner, dtype=np.float32).reshape(-1, 1, 2),
                    (5, 5),
                    (-1, -1),
                    marker_criteria,
                ).reshape(4, 2)
                marker_image_points.append(refined_marker.tolist())
                marker_object_points_m.append(object_points_by_id[marker_id_int].tolist())
                detected_marker_ids.append(marker_id_int)

        return CharucoObservation(  # 返回结果对象
            image_points=corners.tolist(),  # 像素角点
            board_points_m=board_points.tolist(),  # 物理角点
            corner_count=int(len(ids)),  # 检测角点数量
            marker_image_points=marker_image_points,
            marker_object_points_m=marker_object_points_m,
            marker_ids=detected_marker_ids,
            corner_ids=ids.tolist(),
        )

    def board_points_for_corner_ids(self, corner_ids: list[int]) -> list[list[float]]:
        """返回指定 ChArUco 交点 ID 在标定板坐标系中的 XY 坐标。"""
        ids = np.asarray(corner_ids, dtype=np.int32).reshape(-1)
        board_points = self.board.getChessboardCorners()
        if len(ids) == 0 or np.any(ids < 0) or np.any(ids >= len(board_points)):
            raise DetectorError('ChArUco corner id 超出当前标定板范围')
        return board_points[ids][:, :2].astype(np.float32).tolist()

    def draw(self, image: np.ndarray, obs: CharucoObservation) -> np.ndarray:
        vis = image.copy()  # 复制原图
        pts = np.array(obs.image_points, dtype=np.int32)  # 转 int
        for p in pts:  # 绘制角点
            cv2.circle(vis, tuple(p), 4, (0, 255, 0), -1)
        cv2.putText(
            vis,
            f'charuco corners={obs.corner_count} markers={len(obs.marker_ids or [])}',
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2
        )  # 绘制中心坐标和角度
        return vis  # 返回绘制后的图像
