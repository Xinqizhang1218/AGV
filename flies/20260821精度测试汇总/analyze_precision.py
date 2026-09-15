from __future__ import annotations

import csv
import json
import math
import re
import sys
from pathlib import Path

import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from agv_vision.config.settings import AppSettings
from agv_vision.vision.charuco_detector import CharucoBoardDetector


SOURCE_MARKDOWN = PROJECT_ROOT / "flies" / "20260821精度测试.md"
DEBUG_ROOT = PROJECT_ROOT / "data" / "debug" / "20260821"
REFERENCE_IMAGE = (
    DEBUG_ROOT
    / "20260821_100240_878987_station_ref_station_001"
    / "raw.jpg"
)
OUTPUT_CSV = Path(__file__).with_name("逐次测量汇总.csv")
SETTINGS_FILE = PROJECT_ROOT / "agv_vision" / "config" / "settings_online.yaml"

SAMPLE_DIRS = [
    "20260821_100336_258756_compensation_current",
    "20260821_100402_719917_compensation_current",
    "20260821_100411_625711_compensation_current",
    "20260821_100419_770080_compensation_current",
    "20260821_100505_983585_compensation_current",
    "20260821_100511_840648_compensation_current",
    "20260821_100515_501750_compensation_current",
    "20260821_100520_425750_compensation_current",
    "20260821_100524_932615_compensation_current",
    "20260821_100540_581823_compensation_current",
    "20260821_100544_810111_compensation_current",
    "20260821_100548_129514_compensation_current",
    "20260821_100551_103270_compensation_current",
    "20260821_100553_897144_compensation_current",
    "20260821_100556_126456_compensation_current",
    "20260821_100559_399239_compensation_current",
    "20260821_100605_100678_compensation_current",
]

CAMERA_MATRIX = np.asarray(
    [[613.160035, 0.0, 640.889254], [0.0, 612.441245, 405.239469], [0.0, 0.0, 1.0]],
    dtype=np.float64,
)
DIST_COEFFS = np.asarray(
    [-0.029229, 0.076615, 0.000084, -0.000156, -0.151429],
    dtype=np.float64,
)


def load_image(image_path: Path) -> np.ndarray:
    image_bytes = np.fromfile(image_path, dtype=np.uint8)
    image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"无法读取图片: {image_path}")
    return image


def parse_target_poses(markdown_text: str) -> list[dict[str, float]]:
    pattern = re.compile(r'"targetFlangePose"\s*:\s*(\{.*?\})', re.DOTALL)
    poses: list[dict[str, float]] = []
    for match in pattern.finditer(markdown_text):
        payload = json.loads(match.group(1))
        poses.append({axis: float(payload[axis]) for axis in ("x", "y", "z", "rx", "ry", "rz")})
    if len(poses) != len(SAMPLE_DIRS):
        raise RuntimeError(f"返回值数量 {len(poses)} 与图片数量 {len(SAMPLE_DIRS)} 不一致")
    return poses


def observation_by_id(observation) -> dict[int, np.ndarray]:
    return {
        int(corner_id): np.asarray(point, dtype=np.float64)
        for corner_id, point in zip(observation.corner_ids or [], observation.image_points)
    }


def pnp_reprojection_rmse(observation) -> float:
    object_points = np.asarray(observation.board_points_m, dtype=np.float64)
    object_points = np.column_stack([object_points, np.zeros(len(object_points), dtype=np.float64)])
    image_points = np.asarray(observation.image_points, dtype=np.float64)
    ok, rotation_vector, translation_vector = cv2.solvePnP(
        object_points,
        image_points,
        CAMERA_MATRIX,
        DIST_COEFFS,
        flags=cv2.SOLVEPNP_ITERATIVE,
    )
    if not ok:
        raise RuntimeError("solvePnP 失败")
    rotation_vector, translation_vector = cv2.solvePnPRefineLM(
        object_points,
        image_points,
        CAMERA_MATRIX,
        DIST_COEFFS,
        rotation_vector,
        translation_vector,
    )
    projected, _ = cv2.projectPoints(
        object_points,
        rotation_vector,
        translation_vector,
        CAMERA_MATRIX,
        DIST_COEFFS,
    )
    residual = projected.reshape(-1, 2) - image_points
    return float(np.sqrt(np.mean(np.sum(residual * residual, axis=1))))


def image_quality(image: np.ndarray) -> tuple[float, float]:
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(gray_image.mean()), float(cv2.Laplacian(gray_image, cv2.CV_64F).var())


def build_rows() -> tuple[list[dict[str, float | int | str]], dict[str, float]]:
    settings = AppSettings.from_yaml(SETTINGS_FILE)
    detector = CharucoBoardDetector(settings.charuco)
    target_poses = parse_target_poses(SOURCE_MARKDOWN.read_text(encoding="utf-8"))

    reference_image = load_image(REFERENCE_IMAGE)
    reference_observation = detector.detect(reference_image)
    reference_points = observation_by_id(reference_observation)
    reference_brightness, reference_sharpness = image_quality(reference_image)

    rows: list[dict[str, float | int | str]] = []
    for index, (sample_dir, pose) in enumerate(zip(SAMPLE_DIRS, target_poses), start=1):
        image_path = DEBUG_ROOT / sample_dir / "raw.jpg"
        image = load_image(image_path)
        observation = detector.detect(image)
        current_points = observation_by_id(observation)
        common_ids = sorted(set(reference_points) & set(current_points))
        if len(common_ids) < settings.charuco.min_corners:
            raise RuntimeError(f"第 {index} 次共同角点不足: {len(common_ids)}")

        reference_array = np.asarray([reference_points[corner_id] for corner_id in common_ids])
        current_array = np.asarray([current_points[corner_id] for corner_id in common_ids])
        displacement = current_array - reference_array
        center_shift = displacement.mean(axis=0)
        displacement_norm = np.linalg.norm(displacement, axis=1)
        nonrigid_displacement = displacement - center_shift
        nonrigid_norm = np.linalg.norm(nonrigid_displacement, axis=1)
        brightness, sharpness = image_quality(image)

        translation_norm_mm = 1000.0 * math.sqrt(pose["x"] ** 2 + pose["y"] ** 2 + pose["z"] ** 2)
        rotation_norm_deg = math.degrees(math.sqrt(pose["rx"] ** 2 + pose["ry"] ** 2 + pose["rz"] ** 2))
        time_text = f"{sample_dir[9:11]}:{sample_dir[11:13]}:{sample_dir[13:15]}"

        rows.append(
            {
                "序号": index,
                "时间": time_text,
                "共同角点数": len(common_ids),
                "中心dx_px": float(center_shift[0]),
                "中心dy_px": float(center_shift[1]),
                "角点RMS_px": float(np.sqrt(np.mean(displacement_norm * displacement_norm))),
                "去平移形变RMS_px": float(np.sqrt(np.mean(nonrigid_norm * nonrigid_norm))),
                "最大角点差_px": float(displacement_norm.max()),
                "PnP重投影RMSE_px": pnp_reprojection_rmse(observation),
                "平均灰度": brightness,
                "相对基准灰度": brightness - reference_brightness,
                "拉普拉斯清晰度": sharpness,
                "相对基准清晰度": sharpness - reference_sharpness,
                "返回X_mm": pose["x"] * 1000.0,
                "返回Y_mm": pose["y"] * 1000.0,
                "返回Z_mm": pose["z"] * 1000.0,
                "返回平移模长_mm": translation_norm_mm,
                "返回Rx_deg": math.degrees(pose["rx"]),
                "返回Ry_deg": math.degrees(pose["ry"]),
                "返回Rz_deg": math.degrees(pose["rz"]),
                "返回旋转模长_deg": rotation_norm_deg,
                "图片": str(image_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            }
        )

    metrics = {
        "reference_brightness": reference_brightness,
        "reference_sharpness": reference_sharpness,
        "corner_rms_translation_correlation": float(
            np.corrcoef(
                [float(row["角点RMS_px"]) for row in rows],
                [float(row["返回平移模长_mm"]) for row in rows],
            )[0, 1]
        ),
        "nonrigid_rotation_correlation": float(
            np.corrcoef(
                [float(row["去平移形变RMS_px"]) for row in rows],
                [float(row["返回旋转模长_deg"]) for row in rows],
            )[0, 1]
        ),
    }
    return rows, metrics


def write_csv(rows: list[dict[str, float | int | str]]) -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows, metrics = build_rows()
    write_csv(rows)
    print(json.dumps({"rows": rows, "metrics": metrics}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
