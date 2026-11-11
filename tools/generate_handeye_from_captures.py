"""从拍照目录的图片和位姿 JSON 生成手眼标定结果。

读取每个点的 jpg + json（aubo_hik_capture 输出），检测 ChArUco，
估计相机内参，求解 eye-in-hand 的 gTc，并写出三份结果：

- handeye_result.json：完整离线报告（观测、交叉验证、质量）
- handeye_api.json：给跨机台/在线补偿用的精简 pose3d
- handeye_comparison.json：与同规格其它批次的变换差异

目录名中的 ``6cm`` 表示图案宽度 60 mm（5x5 时每格 12 mm，码边长 8 mm），
不要使用 settings 里手眼板 30 mm 格的配置。

示例：

    python tools/generate_handeye_from_captures.py
    python tools/generate_handeye_from_captures.py --image-dir capture_images6cm09203
    python tools/generate_handeye_from_captures.py --image-dir capture_images6cm09203 --method PARK
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agv_vision.config.settings import CharucoSettings
from agv_vision.core.exceptions import DetectorError
from agv_vision.core.image_io import read_image
from agv_vision.core.models import HandEyeSample
from agv_vision.vision.charuco_detector import CharucoBoardDetector
from agv_vision.vision.pose3d import (
    calibrate_camera_from_charuco,
    calibrate_handeye_tsai_park,
    make_transform,
    robot_pose_to_transform,
    solve_charuco_poses,
)

DEFAULT_IMAGE_DIR = REPO_ROOT / 'capture_images6cm09203'
IMAGE_SUFFIXES = {'.jpg', '.jpeg', '.png', '.bmp'}
POINT_NAME_PATTERN = re.compile(r'^(P\d+)', re.IGNORECASE)
FOLDER_PATTERN_WIDTH_PATTERN = re.compile(r'(\d+)\s*cm', re.IGNORECASE)
POSE_FIELD_NAMES = ('x', 'y', 'z', 'rx', 'ry', 'rz')
HANDEYE_METHOD_ENUMS = (
    ('TSAI', cv2.CALIB_HAND_EYE_TSAI),
    ('PARK', cv2.CALIB_HAND_EYE_PARK),
    ('HORAUD', cv2.CALIB_HAND_EYE_HORAUD),
    ('ANDREFF', cv2.CALIB_HAND_EYE_ANDREFF),
    ('DANIILIDIS', cv2.CALIB_HAND_EYE_DANIILIDIS),
)
ASSUMPTIONS = [
    'eye in hand; board fixed during each batch',
    'robot pose uses metres and Rz*Ry*Rx radians',
    'output frame is the robot reported frame; TCP versus flange not independently confirmed',
    'pattern width is full ChArUco pattern width, not single square or outer plate width',
]
API_USAGE_NOTES = [
    'Candidate, not independently validated positioning accuracy.',
    'gTc is relative to the robot frame reported during calibration. Online currentFlangePose must refer to that SAME frame; otherwise convert TCP/flange first.',
    'Requires original camera, lens, mounting, focus and matching image geometry.',
]
COMPARISON_WARNING = (
    'Within-batch held-out consistency is not independent physical accuracy; '
    'transforms require same mounting and robot reported frame.'
)
SATURATION_GRAY_VALUE = 255
GRAY_PERCENTILES = (5.0, 25.0, 75.0, 95.0)
CROSS_VALIDATION_FOLDS = 5
MIN_SAMPLE_COUNT = 5


@dataclass
class BoardSpec:
    squares_x: int
    squares_y: int
    square_length_m: float
    marker_length_m: float
    dictionary_name: str

    @property
    def pattern_width_m(self) -> float:
        return self.squares_x * self.square_length_m

    def to_json(self) -> dict[str, Any]:
        return {
            'pattern_width_m': self.pattern_width_m,
            'squares_x': self.squares_x,
            'squares_y': self.squares_y,
            'square_length_m': self.square_length_m,
            'marker_length_m_assumed': self.marker_length_m,
            'dictionary': self.dictionary_name,
        }


@dataclass
class CaptureRecord:
    point_name: str
    point_number: int
    image_path: Path
    json_path: Path
    meta: dict[str, Any]
    timestamp: datetime
    robot_pose: list[float]


@dataclass
class PreparedSample:
    record: CaptureRecord
    sample: HandEyeSample
    image_size: tuple[int, int]
    image_sha256: str
    objects_m: list[list[float]]
    corners_px: list[list[float]]
    corner_ids: list[int]
    board_gray_percentiles: list[float]
    board_saturated_pct: float
    edge_margin_px: float
    is_selected: bool = True
    exclude_reason: str | None = None


def json_ready(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return json_ready(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, float):
        return float(value)
    return value


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(json_ready(payload), ensure_ascii=False, indent=2),
        encoding='utf-8',
    )


def parse_point_name(text: str) -> tuple[str, int] | None:
    match = POINT_NAME_PATTERN.match(text.strip())
    if match is None:
        return None
    point_name = match.group(1).upper()
    return point_name, int(point_name[1:])


def parse_timestamp(meta: dict[str, Any], image_path: Path) -> datetime:
    for key in ('time_before', 'time_after'):
        raw = meta.get(key)
        if not raw:
            continue
        try:
            return datetime.fromisoformat(str(raw))
        except ValueError:
            continue
    match = re.search(r'(\d{8})_(\d{6})(?:_(\d+))?', image_path.stem)
    if match is not None:
        date_text, time_text, fraction = match.groups()
        microsecond = int((fraction or '0')[:6].ljust(6, '0'))
        return datetime.strptime(date_text + time_text, '%Y%m%d%H%M%S').replace(
            microsecond=microsecond
        )
    return datetime.fromtimestamp(image_path.stat().st_mtime)


def pose_from_meta(meta: dict[str, Any], pose_source: str) -> list[float]:
    candidates = [pose_source, 'actual_pose_before', 'actual_pose_after', 'target_pose']
    seen: set[str] = set()
    for key in candidates:
        if key in seen:
            continue
        seen.add(key)
        pose = meta.get(key)
        if not isinstance(pose, list) or len(pose) != 6:
            continue
        values = [float(item) for item in pose]
        if all(math.isfinite(item) for item in values):
            return values
    raise ValueError(f'{meta.get("image") or meta.get("point_name")} 缺少有效六轴位姿')


def infer_board_spec(image_dir: Path, args: argparse.Namespace) -> BoardSpec:
    squares_x = int(args.squares_x)
    squares_y = int(args.squares_y)
    square_length_m = args.square_length_m
    marker_length_m = args.marker_length_m
    pattern_width_m = args.pattern_width_m
    if pattern_width_m is None:
        match = FOLDER_PATTERN_WIDTH_PATTERN.search(image_dir.name)
        if match is not None:
            pattern_width_m = float(match.group(1)) / 100.0
    if square_length_m is None:
        if pattern_width_m is None:
            raise ValueError(
                '无法从目录名推断标定板尺寸，请传入 --square-length-m 或 --pattern-width-m'
            )
        square_length_m = float(pattern_width_m) / squares_x
    if marker_length_m is None:
        marker_length_m = square_length_m * (2.0 / 3.0)
    return BoardSpec(
        squares_x=squares_x,
        squares_y=squares_y,
        square_length_m=float(square_length_m),
        marker_length_m=float(marker_length_m),
        dictionary_name=str(args.dictionary),
    )


def load_capture_records(image_dir: Path, pose_source: str) -> list[CaptureRecord]:
    records: list[CaptureRecord] = []
    for image_path in sorted(image_dir.iterdir()):
        if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        json_path = image_path.with_suffix('.json')
        if not json_path.exists():
            continue
        meta = json.loads(json_path.read_text(encoding='utf-8'))
        if not isinstance(meta, dict):
            raise ValueError(f'位姿 JSON 顶层必须是对象: {json_path}')
        point_text = str(meta.get('point_name') or image_path.stem)
        parsed = parse_point_name(point_text)
        if parsed is None:
            raise ValueError(f'无法解析点位名称: {image_path.name}')
        point_name, point_number = parsed
        records.append(
            CaptureRecord(
                point_name=point_name,
                point_number=point_number,
                image_path=image_path,
                json_path=json_path,
                meta=meta,
                timestamp=parse_timestamp(meta, image_path),
                robot_pose=pose_from_meta(meta, pose_source),
            )
        )
    if not records:
        raise ValueError(f'{image_dir} 中没有成对的图片和 JSON')
    return records


def select_main_sequence(
    records: list[CaptureRecord],
) -> tuple[list[CaptureRecord], list[dict[str, str]]]:
    by_point: dict[int, list[CaptureRecord]] = {}
    for record in records:
        by_point.setdefault(record.point_number, []).append(record)
    for group in by_point.values():
        group.sort(key=lambda item: (item.timestamp, item.image_path.name))

    point_numbers = sorted(by_point)
    selected: list[CaptureRecord] = []
    excluded: list[dict[str, str]] = []
    for index, point_number in enumerate(point_numbers):
        group = by_point[point_number]
        if index + 1 < len(point_numbers):
            next_first = by_point[point_numbers[index + 1]][0].timestamp
            in_sequence = [item for item in group if item.timestamp < next_first]
            chosen = (in_sequence or group)[-1]
        else:
            chosen = group[-1]
        selected.append(chosen)
        for item in group:
            if item is chosen:
                continue
            excluded.append({
                'image': item.image_path.name,
                'reason': 'duplicate pose outside main sequence',
            })
    selected.sort(key=lambda item: (item.point_number, item.timestamp, item.image_path.name))
    return selected, excluded


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def board_region_stats(
    gray_image: np.ndarray,
    corners_px: np.ndarray,
) -> tuple[list[float], float, float]:
    height, width = gray_image.shape[:2]
    corners = np.asarray(corners_px, dtype=np.float32).reshape(-1, 2)
    edge_margin_px = float(
        np.min(
            np.concatenate([
                corners[:, 0],
                corners[:, 1],
                (width - 1.0) - corners[:, 0],
                (height - 1.0) - corners[:, 1],
            ])
        )
    )
    if len(corners) < 3:
        pixels = gray_image.reshape(-1)
    else:
        hull = cv2.convexHull(corners.astype(np.float32))
        mask = np.zeros((height, width), dtype=np.uint8)
        cv2.fillConvexPoly(mask, np.round(hull).astype(np.int32), 255)
        pixels = gray_image[mask > 0]
        if pixels.size == 0:
            pixels = gray_image.reshape(-1)
    percentiles = [float(value) for value in np.percentile(pixels, GRAY_PERCENTILES)]
    saturated_pct = float(100.0 * np.mean(pixels >= SATURATION_GRAY_VALUE))
    return percentiles, saturated_pct, edge_margin_px


def build_handeye_sample(record: CaptureRecord, observation, image_size: tuple[int, int]) -> HandEyeSample:
    x_m, y_m, z_m, rx, ry, rz = record.robot_pose
    return HandEyeSample(
        sample_id=record.point_name,
        robot_x_m=x_m,
        robot_y_m=y_m,
        observation=observation,
        image_path=str(record.image_path),
        meta={
            'z': z_m,
            'rx': rx,
            'ry': ry,
            'rz': rz,
            'image_width_px': int(image_size[0]),
            'image_height_px': int(image_size[1]),
            'raw_image_path': str(record.image_path),
            'point_name': record.point_name,
        },
    )


def detect_captures(
    records: list[CaptureRecord],
    detector: CharucoBoardDetector,
    selected_names: set[str],
) -> tuple[list[PreparedSample], list[dict[str, str]]]:
    prepared: list[PreparedSample] = []
    excluded: list[dict[str, str]] = []
    for record in records:
        image = read_image(record.image_path)
        if image is None:
            excluded.append({
                'image': record.image_path.name,
                'reason': 'image read failed',
            })
            continue
        try:
            observation = detector.detect(image)
        except (DetectorError, cv2.error, ValueError) as exc:
            excluded.append({
                'image': record.image_path.name,
                'reason': f'detection failed: {exc}',
            })
            continue
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        corners_px = np.asarray(observation.image_points, dtype=np.float32).reshape(-1, 2)
        board_xy = np.asarray(observation.board_points_m, dtype=np.float32).reshape(-1, 2)
        objects_m = np.column_stack([board_xy, np.zeros(len(board_xy), dtype=np.float32)])
        percentiles, saturated_pct, edge_margin_px = board_region_stats(gray_image, corners_px)
        image_size = (int(image.shape[1]), int(image.shape[0]))
        prepared.append(
            PreparedSample(
                record=record,
                sample=build_handeye_sample(record, observation, image_size),
                image_size=image_size,
                image_sha256=file_sha256(record.image_path),
                objects_m=objects_m.tolist(),
                corners_px=corners_px.tolist(),
                corner_ids=[int(item) for item in (observation.corner_ids or [])],
                board_gray_percentiles=percentiles,
                board_saturated_pct=saturated_pct,
                edge_margin_px=edge_margin_px,
                is_selected=record.image_path.name in selected_names,
            )
        )
        del image, gray_image
    return prepared, excluded


def rotation_distance_rad(first: np.ndarray, second: np.ndarray) -> float:
    relative = first @ second.T
    cosine = float(np.clip((np.trace(relative) - 1.0) / 2.0, -1.0, 1.0))
    return math.acos(cosine)


def mean_rotation(rotations: list[np.ndarray]) -> np.ndarray:
    stacked = np.sum(np.asarray(rotations, dtype=np.float64), axis=0)
    u_matrix, _, vt_matrix = np.linalg.svd(stacked)
    rotation = u_matrix @ vt_matrix
    if np.linalg.det(rotation) < 0.0:
        u_matrix[:, -1] *= -1.0
        rotation = u_matrix @ vt_matrix
    return rotation


def pose_consistency_metrics(
    base_from_target: list[np.ndarray],
    gripper_from_camera: np.ndarray,
) -> dict[str, Any]:
    translations = np.array([pose[:3, 3] for pose in base_from_target], dtype=np.float64)
    rotations = [pose[:3, :3] for pose in base_from_target]
    translation_center = translations.mean(axis=0)
    rotation_center = mean_rotation(rotations)
    residuals = translations - translation_center
    distances_m = np.linalg.norm(residuals, axis=1)
    angles_deg = np.array(
        [math.degrees(rotation_distance_rad(rotation, rotation_center)) for rotation in rotations],
        dtype=np.float64,
    )
    xyz_rms_mm = np.sqrt(np.mean(residuals ** 2, axis=0)) * 1000.0
    distances_mm = distances_m * 1000.0
    return {
        'T_robot_reported_frame_from_camera': gripper_from_camera.tolist(),
        'position_rms_mm': float(np.sqrt(np.mean(distances_mm ** 2))),
        'position_p95_mm': float(np.percentile(distances_mm, 95)),
        'position_max_mm': float(np.max(distances_mm)),
        'xyz_rms_mm': xyz_rms_mm.tolist(),
        'rotation_rms_deg': float(np.sqrt(np.mean(angles_deg ** 2))),
        'rotation_max_deg': float(np.max(angles_deg)),
        'distances_mm': distances_mm.tolist(),
        'angles_deg': angles_deg.tolist(),
        'reference': make_transform(rotation_center, translation_center).tolist(),
    }


def board_poses_in_robot_frame(
    samples: list[HandEyeSample],
    camera_from_target: list[np.ndarray],
    gripper_from_camera: np.ndarray,
) -> list[np.ndarray]:
    return [
        robot_pose_to_transform(sample) @ gripper_from_camera @ camera_pose
        for sample, camera_pose in zip(samples, camera_from_target)
    ]


def solve_handeye_method(
    samples: list[HandEyeSample],
    camera_from_target: list[np.ndarray],
    method: int,
) -> np.ndarray:
    base_from_gripper = [robot_pose_to_transform(sample) for sample in samples]
    rotation, translation = cv2.calibrateHandEye(
        [pose[:3, :3] for pose in base_from_gripper],
        [pose[:3, 3].reshape(3, 1) for pose in base_from_gripper],
        [pose[:3, :3] for pose in camera_from_target],
        [pose[:3, 3].reshape(3, 1) for pose in camera_from_target],
        method=method,
    )
    transform = make_transform(rotation, translation)
    if not np.all(np.isfinite(transform)):
        raise ValueError('non-finite hand-eye result')
    return transform


def candidate_metrics(
    samples: list[HandEyeSample],
    camera_from_target: list[np.ndarray],
) -> dict[str, dict[str, Any]]:
    payload: dict[str, dict[str, Any]] = {}
    for name, method in HANDEYE_METHOD_ENUMS:
        transform = solve_handeye_method(samples, camera_from_target, method)
        board_poses = board_poses_in_robot_frame(samples, camera_from_target, transform)
        payload[name] = pose_consistency_metrics(board_poses, transform)
    return payload


def view_reprojection_rms_px(
    sample: HandEyeSample,
    camera_matrix: np.ndarray,
    dist_coeffs: np.ndarray,
) -> float:
    object_points = np.asarray(sample.observation.board_points_m, dtype=np.float32).reshape(-1, 2)
    object_points = np.column_stack([object_points, np.zeros(len(object_points), dtype=np.float32)])
    image_points = np.asarray(sample.observation.image_points, dtype=np.float32).reshape(-1, 2)
    ok, rvec, tvec = cv2.solvePnP(
        np.ascontiguousarray(object_points),
        np.ascontiguousarray(image_points),
        camera_matrix,
        dist_coeffs,
        flags=cv2.SOLVEPNP_ITERATIVE,
    )
    if not ok:
        raise RuntimeError(f'{sample.sample_id} 重投影 PnP 失败')
    projected, _ = cv2.projectPoints(object_points, rvec, tvec, camera_matrix, dist_coeffs)
    residuals = projected.reshape(-1, 2) - image_points
    return float(np.sqrt(np.mean(np.sum(residuals ** 2, axis=1))))


def quality_metrics(samples: list[PreparedSample], image_size: tuple[int, int]) -> dict[str, Any]:
    all_corners = np.vstack(
        [np.asarray(item.corners_px, dtype=np.float32).reshape(-1, 2) for item in samples]
    )
    width, height = image_size
    hull = cv2.convexHull(all_corners.astype(np.float32))
    coverage = float(cv2.contourArea(hull) / float(width * height))
    saturated = np.array([item.board_saturated_pct for item in samples], dtype=np.float64)
    return {
        'corner_counts': [int(item.sample.observation.corner_count) for item in samples],
        'corner_hull_coverage_fraction': coverage,
        'corner_bounds_px': [
            [float(np.min(all_corners[:, 0])), float(np.min(all_corners[:, 1]))],
            [float(np.max(all_corners[:, 0])), float(np.max(all_corners[:, 1]))],
        ],
        'board_saturated_pct_median': float(np.median(saturated)),
        'board_saturated_pct_max': float(np.max(saturated)),
    }


def observation_payload(item: PreparedSample) -> dict[str, Any]:
    return {
        'name': item.record.image_path.stem,
        'point': item.record.point_name,
        'meta': item.record.meta,
        'count': int(item.sample.observation.corner_count),
        'size': [int(item.image_size[0]), int(item.image_size[1])],
        'image_sha256': item.image_sha256,
        'objects': item.objects_m,
        'corners': item.corners_px,
        'ids': item.corner_ids,
        'board_gray_percentiles': item.board_gray_percentiles,
        'board_saturated_pct': item.board_saturated_pct,
        'edge_margin_px': item.edge_margin_px,
    }


def fit_calibration(samples: list[HandEyeSample], method_name: str) -> dict[str, Any]:
    camera_matrix, dist_coeffs, camera_rms_px, image_size = calibrate_camera_from_charuco(samples)
    camera_from_target = solve_charuco_poses(samples, camera_matrix, dist_coeffs)
    method_name = str(method_name).upper()
    if method_name == 'AUTO':
        gripper_from_camera, selected_name, _diagnostics = calibrate_handeye_tsai_park(
            samples,
            camera_from_target,
        )
        method_name = str(selected_name).upper()
    else:
        method_map = {name: enum for name, enum in HANDEYE_METHOD_ENUMS}
        if method_name not in method_map:
            raise ValueError(f'不支持的手眼方法: {method_name}')
        gripper_from_camera = solve_handeye_method(
            samples,
            camera_from_target,
            method_map[method_name],
        )
    return {
        'camera_matrix': np.asarray(camera_matrix, dtype=np.float64),
        'dist_coeffs': np.asarray(dist_coeffs, dtype=np.float64).reshape(-1),
        'camera_rms_px': float(camera_rms_px),
        'image_size': (int(image_size[0]), int(image_size[1])),
        'camera_from_target': camera_from_target,
        'gripper_from_camera': np.asarray(gripper_from_camera, dtype=np.float64),
        'method': method_name,
    }


def translation_difference_mm(first: np.ndarray, second: np.ndarray) -> float:
    return float(np.linalg.norm(first[:3, 3] - second[:3, 3]) * 1000.0)


def rotation_difference_deg(first: np.ndarray, second: np.ndarray) -> float:
    return math.degrees(rotation_distance_rad(first[:3, :3], second[:3, :3]))


def cross_validate(
    prepared: list[PreparedSample],
    full_gripper_from_camera: np.ndarray,
    method_name: str,
) -> dict[str, Any]:
    folds: list[dict[str, Any]] = []
    held_out_distances: list[float] = []
    held_out_angles: list[float] = []
    subset_translation_diffs: list[float] = []
    for remainder in range(CROSS_VALIDATION_FOLDS):
        train_items = [
            item for item in prepared
            if item.record.point_number % CROSS_VALIDATION_FOLDS != remainder
        ]
        test_items = [
            item for item in prepared
            if item.record.point_number % CROSS_VALIDATION_FOLDS == remainder
        ]
        if len(train_items) < MIN_SAMPLE_COUNT or not test_items:
            continue
        train_samples = [item.sample for item in train_items]
        test_samples = [item.sample for item in test_items]
        fitted = fit_calibration(train_samples, method_name)
        test_camera_from_target = solve_charuco_poses(
            test_samples,
            fitted['camera_matrix'],
            fitted['dist_coeffs'],
        )
        test_board_poses = board_poses_in_robot_frame(
            test_samples,
            test_camera_from_target,
            fitted['gripper_from_camera'],
        )
        metrics = pose_consistency_metrics(test_board_poses, fitted['gripper_from_camera'])
        reprojection = [
            view_reprojection_rms_px(
                item.sample,
                fitted['camera_matrix'],
                fitted['dist_coeffs'],
            )
            for item in test_items
        ]
        translation_diff_mm = translation_difference_mm(
            fitted['gripper_from_camera'],
            full_gripper_from_camera,
        )
        subset_translation_diffs.append(translation_diff_mm)
        held_out_distances.extend(metrics['distances_mm'])
        held_out_angles.extend(metrics['angles_deg'])
        folds.append({
            'test_points': [item.record.point_name for item in test_items],
            'train_count': len(train_items),
            'T_robot_reported_frame_from_camera': fitted['gripper_from_camera'].tolist(),
            'camera_matrix': fitted['camera_matrix'].tolist(),
            'dist_coeffs': fitted['dist_coeffs'].tolist(),
            'translation_difference_from_full_mm': translation_diff_mm,
            'rotation_difference_from_full_deg': rotation_difference_deg(
                fitted['gripper_from_camera'],
                full_gripper_from_camera,
            ),
            'test_reprojection_rms_px': float(np.sqrt(np.mean(np.square(reprojection)))),
            'position_rms_mm': metrics['position_rms_mm'],
            'position_p95_mm': metrics['position_p95_mm'],
            'position_max_mm': metrics['position_max_mm'],
            'xyz_rms_mm': metrics['xyz_rms_mm'],
            'rotation_rms_deg': metrics['rotation_rms_deg'],
            'rotation_max_deg': metrics['rotation_max_deg'],
            'distances_mm': metrics['distances_mm'],
            'angles_deg': metrics['angles_deg'],
            'reference': metrics['reference'],
        })
    distances = np.asarray(held_out_distances, dtype=np.float64)
    angles = np.asarray(held_out_angles, dtype=np.float64)
    return {
        'description': (
            'five folds by point number modulo 5; intrinsics and handeye fitted on training only; '
            'not independent physical accuracy'
        ),
        'aggregate': {
            'position_rms_mm': float(np.sqrt(np.mean(distances ** 2))),
            'position_p95_mm': float(np.percentile(distances, 95)),
            'position_max_mm': float(np.max(distances)),
            'rotation_rms_deg': float(np.sqrt(np.mean(angles ** 2))),
            'rotation_max_deg': float(np.max(angles)),
            'max_subset_translation_difference_mm': float(np.max(subset_translation_diffs)),
        },
        'folds': folds,
    }


def comparison_batch_from_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        'source_directory': result['source_directory'],
        'sample_count': result['sample_count'],
        'calibration_rms_px': result['calibration_rms_px'],
        'translation_mm': result['translation_mm'],
        'quality': result['quality'],
        'held_out_metrics': result['cross_validation']['aggregate'],
        'training_position_rms_mm': result['training_metrics']['position_rms_mm'],
    }


def discover_compare_dirs(image_dir: Path) -> list[Path]:
    match = re.match(r'(capture_images\d+cm)', image_dir.name, flags=re.IGNORECASE)
    prefix = match.group(1).lower() if match else None
    found: list[Path] = []
    for child in sorted(image_dir.parent.iterdir()):
        if not child.is_dir() or child.resolve() == image_dir.resolve():
            continue
        if prefix is not None and not child.name.lower().startswith(prefix):
            continue
        if (child / 'handeye_result.json').exists():
            found.append(child)
    return found


def load_existing_result(directory: Path) -> dict[str, Any]:
    path = directory / 'handeye_result.json'
    payload = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(payload, dict) or 'T_robot_reported_frame_from_camera' not in payload:
        raise ValueError(f'不是有效的 handeye_result.json: {path}')
    return payload


def build_comparison(
    current_result: dict[str, Any],
    compare_dirs: list[Path],
) -> dict[str, Any]:
    batches = []
    differences = []
    current_transform = np.asarray(
        current_result['T_robot_reported_frame_from_camera'],
        dtype=np.float64,
    )
    for directory in compare_dirs:
        other = load_existing_result(directory)
        batches.append(comparison_batch_from_result(other))
        other_transform = np.asarray(other['T_robot_reported_frame_from_camera'], dtype=np.float64)
        differences.append({
            'reference': other.get('source_directory', str(directory)),
            'translation_mm': translation_difference_mm(current_transform, other_transform),
            'rotation_deg': rotation_difference_deg(current_transform, other_transform),
        })
    batches.append(comparison_batch_from_result(current_result))
    return {
        'batches': batches,
        'new_batch_transform_differences': differences,
        'warning': COMPARISON_WARNING,
    }


def build_api_payload(result: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        'rmseM': result['training_metrics']['position_rms_mm'] / 1000.0,
        'sampleCount': result['sample_count'],
        'pose3d': {
            'version': 1,
            'cameraMatrix': result['camera_matrix'],
            'distCoeffs': result['dist_coeffs'],
            'gTc': result['T_robot_reported_frame_from_camera'],
            'imageSize': result['image_size'],
            'handEyeMethod': result['method'],
            'cameraCalibrationRmsPx': result['calibration_rms_px'],
        },
        'source': str(result_path),
        'usage_notes': API_USAGE_NOTES,
    }


def build_result_payload(
    image_dir: Path,
    board: BoardSpec,
    all_image_count: int,
    detected_count: int,
    selected: list[PreparedSample],
    excluded: list[dict[str, str]],
    fitted: dict[str, Any],
) -> dict[str, Any]:
    samples = [item.sample for item in selected]
    board_poses = board_poses_in_robot_frame(
        samples,
        fitted['camera_from_target'],
        fitted['gripper_from_camera'],
    )
    training_metrics = pose_consistency_metrics(board_poses, fitted['gripper_from_camera'])
    translation_m = fitted['gripper_from_camera'][:3, 3]
    return {
        'schema_version': 1,
        'status': 'offline_candidate_not_deployed',
        'source_directory': str(image_dir),
        'board': board.to_json(),
        'assumptions': ASSUMPTIONS,
        'image_count': all_image_count,
        'detected_image_count': detected_count,
        'sample_count': len(selected),
        'image_size': [fitted['image_size'][0], fitted['image_size'][1]],
        'selected_images': [item.record.image_path.name for item in selected],
        'excluded_images': excluded,
        'camera_matrix': fitted['camera_matrix'].tolist(),
        'dist_coeffs': fitted['dist_coeffs'].tolist(),
        'distortion_order': ['k1', 'k2', 'p1', 'p2', 'k3'],
        'calibration_rms_px': fitted['camera_rms_px'],
        'method': fitted['method'],
        'transform_definition': 'p_robot_reported_frame = T_robot_reported_frame_from_camera @ p_camera',
        'translation_units': 'm',
        'T_robot_reported_frame_from_camera': fitted['gripper_from_camera'].tolist(),
        'translation_mm': (translation_m * 1000.0).tolist(),
        'training_metrics': training_metrics,
        'cross_validation': cross_validate(
            selected,
            fitted['gripper_from_camera'],
            fitted['method'],
        ),
        'candidates': candidate_metrics(samples, fitted['camera_from_target']),
        'per_view_reprojection_rms_px': [
            view_reprojection_rms_px(
                item.sample,
                fitted['camera_matrix'],
                fitted['dist_coeffs'],
            )
            for item in selected
        ],
        'quality': quality_metrics(selected, fitted['image_size']),
        'observations': [observation_payload(item) for item in selected],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='根据拍照图片和 JSON 生成手眼标定结果')
    parser.add_argument(
        '--image-dir',
        type=Path,
        default=DEFAULT_IMAGE_DIR,
        help='含 Pxx_*.jpg 与同名 json 的拍照目录',
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=None,
        help='结果输出目录，默认写回拍照目录',
    )
    parser.add_argument(
        '--pose-source',
        choices=('actual_pose_before', 'actual_pose_after', 'target_pose'),
        default='actual_pose_before',
        help='用于手眼求解的六轴位姿来源',
    )
    parser.add_argument('--pattern-width-m', type=float, default=None)
    parser.add_argument('--square-length-m', type=float, default=None)
    parser.add_argument('--marker-length-m', type=float, default=None)
    parser.add_argument('--squares-x', type=int, default=5)
    parser.add_argument('--squares-y', type=int, default=5)
    parser.add_argument('--dictionary', default='DICT_4X4_50')
    parser.add_argument('--min-corners', type=int, default=5)
    parser.add_argument(
        '--method',
        choices=('PARK', 'TSAI', 'HORAUD', 'ANDREFF', 'DANIILIDIS', 'AUTO'),
        default='PARK',
        help='手眼求解方法。PARK 与现有批次结果一致；AUTO 按视觉服务的 Tsai/Park 评分选优',
    )
    parser.add_argument(
        '--compare-dir',
        action='append',
        default=[],
        type=Path,
        help='已有 handeye_result.json 的对比目录，可重复传入',
    )
    parser.add_argument(
        '--no-compare',
        action='store_true',
        help='不与其它批次对比，只写当前批次的 comparison',
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    image_dir = args.image_dir.expanduser().resolve()
    if not image_dir.is_dir():
        raise SystemExit(f'拍照目录不存在: {image_dir}')
    output_dir = (args.output_dir or image_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    board = infer_board_spec(image_dir, args)
    detector = CharucoBoardDetector(
        CharucoSettings(
            dictionary_name=board.dictionary_name,
            squares_x=board.squares_x,
            squares_y=board.squares_y,
            square_length_m=board.square_length_m,
            marker_length_m=board.marker_length_m,
            min_corners=int(args.min_corners),
            adaptive_thresh_constant=7.0,
            min_marker_perimeter_rate=0.015,
            max_marker_perimeter_rate=4.0,
            use_subpix=True,
        )
    )
    print(f'拍照目录: {image_dir}')
    print(
        '标定板: '
        f'{board.squares_x}x{board.squares_y}, '
        f'pattern={board.pattern_width_m * 1000:.1f} mm, '
        f'square={board.square_length_m * 1000:.3f} mm, '
        f'marker={board.marker_length_m * 1000:.3f} mm, '
        f'{board.dictionary_name}'
    )

    records = load_capture_records(image_dir, args.pose_source)
    selected_records, duplicate_excluded = select_main_sequence(records)
    selected_names = {item.image_path.name for item in selected_records}
    print(f'成对样本 {len(records)} 张，主序列 {len(selected_records)} 张')
    print('正在检测 ChArUco ...')
    prepared, detect_excluded = detect_captures(records, detector, selected_names)
    prepared_by_name = {item.record.image_path.name: item for item in prepared}
    selected: list[PreparedSample] = []
    missing_selected: list[dict[str, str]] = []
    for record in selected_records:
        item = prepared_by_name.get(record.image_path.name)
        if item is None:
            missing_selected.append({
                'image': record.image_path.name,
                'reason': 'selected pose was not detected',
            })
            continue
        item.is_selected = True
        selected.append(item)
    excluded = duplicate_excluded + detect_excluded + missing_selected
    if len(selected) < MIN_SAMPLE_COUNT:
        raise SystemExit(f'有效样本不足 {MIN_SAMPLE_COUNT} 个，当前 {len(selected)} 个')

    print(f'检测成功 {len(prepared)} 张，用于求解 {len(selected)} 张')
    print('正在估计内参并求解手眼 ...')
    fitted = fit_calibration([item.sample for item in selected], args.method)
    result = build_result_payload(
        image_dir=image_dir,
        board=board,
        all_image_count=len(records),
        detected_count=len(prepared),
        selected=selected,
        excluded=excluded,
        fitted=fitted,
    )

    result_path = output_dir / 'handeye_result.json'
    api_path = output_dir / 'handeye_api.json'
    comparison_path = output_dir / 'handeye_comparison.json'
    write_json(result_path, result)
    write_json(api_path, build_api_payload(result, result_path))
    if args.no_compare:
        compare_dirs: list[Path] = []
    elif args.compare_dir:
        compare_dirs = [path.expanduser().resolve() for path in args.compare_dir]
    else:
        compare_dirs = discover_compare_dirs(image_dir)
    write_json(comparison_path, build_comparison(result, compare_dirs))

    translation_mm = result['translation_mm']
    training = result['training_metrics']
    held_out = result['cross_validation']['aggregate']
    print(f'写出: {result_path}')
    print(f'写出: {api_path}')
    print(f'写出: {comparison_path}')
    print(
        f'方法 {result["method"]}, '
        f'内参 RMS {result["calibration_rms_px"]:.4f} px, '
        f'训练平移 RMS {training["position_rms_mm"]:.3f} mm'
    )
    print(
        'gTc 平移 mm: '
        f'[{translation_mm[0]:.3f}, {translation_mm[1]:.3f}, {translation_mm[2]:.3f}]'
    )
    print(
        f'留出平移 RMS {held_out["position_rms_mm"]:.3f} mm, '
        f'最大子集平移差 {held_out["max_subset_translation_difference_mm"]:.3f} mm'
    )
    if excluded:
        print(f'排除 {len(excluded)} 张: {[item["image"] for item in excluded]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
