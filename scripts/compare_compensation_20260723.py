"""用 pkg5 当前完整 3D 链重跑 2026-07-23 的二次补偿图片并对比旧结果。"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np

from agv_vision.config.settings import ArucoSettings
from agv_vision.vision.aruco_detector import ArucoReferenceDetector
from agv_vision.vision.compensator import CompensationCalculator
from agv_vision.vision.pose3d import solve_aruco_pose_lm, yaw_deg


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def wrap_deg(value: float) -> float:
    return (float(value) + 180.0) % 360.0 - 180.0


def scalar_stats(values: list[float]) -> dict:
    data = np.asarray(values, dtype=np.float64)
    if data.size == 0:
        return {"count": 0}
    return {
        "count": int(data.size),
        "mean": float(np.mean(data)),
        "median": float(np.median(data)),
        "mae": float(np.mean(np.abs(data))),
        "rmse": float(np.sqrt(np.mean(data * data))),
        "p95_abs": float(np.percentile(np.abs(data), 95)),
        "max_abs": float(np.max(np.abs(data))),
    }


def correlation(left: list[float], right: list[float]) -> float | None:
    if len(left) < 2 or np.std(left) == 0 or np.std(right) == 0:
        return None
    return float(np.corrcoef(left, right)[0, 1])


def fit_planar_map(inputs: list[list[float]], outputs: list[list[float]]) -> dict:
    source = np.asarray(inputs, dtype=np.float64)
    target = np.asarray(outputs, dtype=np.float64)
    coefficients, _, _, _ = np.linalg.lstsq(source, target, rcond=None)
    mapping = coefficients.T
    u, singular_values, vt = np.linalg.svd(mapping)
    rotation = u @ vt
    predicted = source @ coefficients
    residual = np.linalg.norm(predicted - target, axis=1)
    return {
        "matrix_2x2": mapping.tolist(),
        "equivalent_rotation_deg": float(
            math.degrees(math.atan2(rotation[1, 0], rotation[0, 0]))
        ),
        "singular_values": singular_values.tolist(),
        "residual_vector_mm": scalar_stats(residual.tolist()),
    }


def detect(detector: ArucoReferenceDetector, image_path: Path):
    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"无法读取图片: {image_path}")
    result = detector.detect(image)
    if result is None:
        raise ValueError("未检测到 ArUco")
    return result


def matrix4(payload: list[list[float]]) -> np.ndarray:
    matrix = np.asarray(payload, dtype=np.float64)
    if matrix.shape != (4, 4):
        raise ValueError(f"4x4 矩阵格式错误: {matrix.shape}")
    return matrix


def robot_rotation_rz_ry_rx(rx: float, ry: float, rz: float) -> np.ndarray:
    sx, cx = math.sin(rx), math.cos(rx)
    sy, cy = math.sin(ry), math.cos(ry)
    sz, cz = math.sin(rz), math.cos(rz)
    rotation_x = np.asarray(
        [[1.0, 0.0, 0.0], [0.0, cx, -sx], [0.0, sx, cx]], dtype=np.float64
    )
    rotation_y = np.asarray(
        [[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]], dtype=np.float64
    )
    rotation_z = np.asarray(
        [[cz, -sz, 0.0], [sz, cz, 0.0], [0.0, 0.0, 1.0]], dtype=np.float64
    )
    return rotation_z @ rotation_y @ rotation_x


def pose3d_payload(calibration: dict) -> tuple[dict, np.ndarray, np.ndarray, np.ndarray]:
    pose = calibration["data"]["angleCalibration"]["pose3d"]
    camera_matrix = np.asarray(pose["cameraMatrix"], dtype=np.float64)
    dist_coeffs = np.asarray(pose["distCoeffs"], dtype=np.float64)
    gripper_from_camera = matrix4(pose["gTc"])
    return pose, camera_matrix, dist_coeffs, gripper_from_camera


def pose_matrix(reference, camera_matrix, dist_coeffs) -> np.ndarray:
    return solve_aruco_pose_lm(reference, camera_matrix, dist_coeffs)


def closest_reference(old_reference: dict, reference_records: list[dict]) -> dict:
    target = np.asarray(
        [
            old_reference["board_center_x"],
            old_reference["board_center_y"],
            old_reference["board_angle_deg"],
        ],
        dtype=np.float64,
    )

    def score(record: dict) -> float:
        center = record["center"]
        candidate = np.asarray(
            [
                center["board_center_x"],
                center["board_center_y"],
                center["board_angle_deg"],
            ],
            dtype=np.float64,
        )
        delta = candidate - target
        delta[2] = wrap_deg(delta[2])
        return float(np.linalg.norm(delta))

    return min(reference_records, key=score)


def timestamp_key(name: str) -> str:
    match = re.search(r"(\d{8}_\d{6}_\d{6})", name)
    return match.group(1) if match else name


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--calibration", type=Path, required=True)
    parser.add_argument("--handeye-request", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    calibration = load_json(args.calibration)
    pose, camera_matrix, dist_coeffs, gripper_from_camera = pose3d_payload(calibration)
    base_from_gripper_rotation = None
    nominal_robot_pose = None
    if args.handeye_request:
        request = load_json(args.handeye_request)
        nominal_robot_pose = request["imagePointList"][0]
        base_from_gripper_rotation = robot_rotation_rz_ry_rx(
            float(nominal_robot_pose["rx"]),
            float(nominal_robot_pose["ry"]),
            float(nominal_robot_pose["rz"]),
        )

    settings = ArucoSettings(
        dictionary_name="DICT_5X5_50",
        preferred_origin_id=0,
        marker_length_m=0.150,
    )
    detector = ArucoReferenceDetector(settings)
    calculator = CompensationCalculator(pixels_per_m_fallback=1.0)

    reference_records = []
    for folder in sorted(args.data_dir.glob("*_station_ref_*")):
        center_path = folder / "center.json"
        raw_path = folder / "raw.jpg"
        if center_path.exists() and raw_path.exists():
            reference_records.append(
                {"folder": folder, "center": load_json(center_path), "raw": raw_path}
            )

    old_results = {}
    for path in sorted(args.data_dir.glob("compensation_*.json")):
        payload = load_json(path)
        debug_dir = Path(payload.get("debug_dir", "")).name
        if debug_dir:
            old_results[debug_dir] = {"path": path, "payload": payload}

    rows = []
    failures = []
    reference_pose_cache: dict[str, np.ndarray] = {}

    for current_folder in sorted(args.data_dir.glob("*_compensation_current")):
        old_record = old_results.get(current_folder.name)
        if old_record is None:
            failures.append({"folder": current_folder.name, "reason": "找不到旧结果 JSON"})
            continue
        raw_path = current_folder / "raw.jpg"
        try:
            current_detection = detect(detector, raw_path)
            old_payload = old_record["payload"]
            matched_reference = closest_reference(
                old_payload["reference"], reference_records
            )
            reference_key = matched_reference["folder"].name
            if reference_key not in reference_pose_cache:
                reference_detection = detect(detector, matched_reference["raw"])
                reference_pose_cache[reference_key] = pose_matrix(
                    reference_detection, camera_matrix, dist_coeffs
                )

            camera_from_current = pose_matrix(
                current_detection, camera_matrix, dist_coeffs
            )
            gripper_from_current = gripper_from_camera @ camera_from_current
            gripper_from_reference = (
                gripper_from_camera @ reference_pose_cache[reference_key]
            )

            online = calculator.compute(
                old_payload["reference"],
                current_detection,
                handeye_matrix_2x3=None,
                calibration_pixels_per_m=None,
                angle_calibration={"pose3d": pose},
            )
            online_dict = asdict(online)

            relative_dx_m = float(
                gripper_from_reference[0, 3] - gripper_from_current[0, 3]
            )
            relative_dy_m = float(
                gripper_from_reference[1, 3] - gripper_from_current[1, 3]
            )
            relative_dtheta_deg = wrap_deg(
                yaw_deg(gripper_from_reference) - yaw_deg(gripper_from_current)
            )
            camera_relative_dx_m = float(
                reference_pose_cache[reference_key][0, 3] - camera_from_current[0, 3]
            )
            camera_relative_dy_m = float(
                reference_pose_cache[reference_key][1, 3] - camera_from_current[1, 3]
            )
            camera_relative_dz_m = float(
                reference_pose_cache[reference_key][2, 3] - camera_from_current[2, 3]
            )
            z_coupling_dx_m = float(
                gripper_from_camera[0, 2] * camera_relative_dz_m
            )
            z_coupling_dy_m = float(
                gripper_from_camera[1, 2] * camera_relative_dz_m
            )
            planar_only_dx_m = float(
                gripper_from_camera[0, 0] * camera_relative_dx_m
                + gripper_from_camera[0, 1] * camera_relative_dy_m
            )
            planar_only_dy_m = float(
                gripper_from_camera[1, 0] * camera_relative_dx_m
                + gripper_from_camera[1, 1] * camera_relative_dy_m
            )
            old_reference = old_payload["reference"]
            matched_center = matched_reference["center"]
            reference_center_error_px = math.hypot(
                float(old_reference["board_center_x"])
                - float(matched_center["board_center_x"]),
                float(old_reference["board_center_y"])
                - float(matched_center["board_center_y"]),
            )
            reference_angle_error_deg = abs(
                wrap_deg(
                    float(old_reference["board_angle_deg"])
                    - float(matched_center["board_angle_deg"])
                )
            )
            old_comp = old_payload["compensation"]
            base_correction_m = None
            if base_from_gripper_rotation is not None:
                gripper_target_delta_m = (
                    gripper_from_reference[:3, 3] - gripper_from_current[:3, 3]
                )
                base_correction_m = (
                    -base_from_gripper_rotation @ gripper_target_delta_m
                )
            old_dx_m = float(old_comp["dx_m_robot"])
            old_dy_m = float(old_comp["dy_m_robot"])
            old_dtheta_deg = float(old_comp["dtheta_robot_deg"])
            rows.append(
                {
                    "case": current_folder.name,
                    "timestamp": timestamp_key(current_folder.name),
                    "reference_case": reference_key,
                    "old_result_json": old_record["path"].name,
                    "old_dx_mm": old_dx_m * 1000.0,
                    "old_dy_mm": old_dy_m * 1000.0,
                    "old_dtheta_deg": old_dtheta_deg,
                    "new_online_absolute_dx_mm": float(online_dict["dx_m_robot"]) * 1000.0,
                    "new_online_absolute_dy_mm": float(online_dict["dy_m_robot"]) * 1000.0,
                    "new_online_absolute_dtheta_deg": float(
                        online_dict["dtheta_robot_deg"]
                    ),
                    "new_relative_dx_mm": relative_dx_m * 1000.0,
                    "new_relative_dy_mm": relative_dy_m * 1000.0,
                    "new_relative_dtheta_deg": relative_dtheta_deg,
                    "old_camera_dx_mm": float(old_comp["dx_m_camera_dynamic"]) * 1000.0,
                    "old_camera_dy_mm": float(old_comp["dy_m_camera_dynamic"]) * 1000.0,
                    "new_camera_relative_dx_mm": camera_relative_dx_m * 1000.0,
                    "new_camera_relative_dy_mm": camera_relative_dy_m * 1000.0,
                    "new_camera_relative_dz_mm": camera_relative_dz_m * 1000.0,
                    "z_coupling_dx_mm": z_coupling_dx_m * 1000.0,
                    "z_coupling_dy_mm": z_coupling_dy_m * 1000.0,
                    "z_coupling_vector_mm": math.hypot(
                        z_coupling_dx_m, z_coupling_dy_m
                    )
                    * 1000.0,
                    "planar_only_dx_mm": planar_only_dx_m * 1000.0,
                    "planar_only_dy_mm": planar_only_dy_m * 1000.0,
                    "reference_center_match_error_px": reference_center_error_px,
                    "reference_angle_match_error_deg": reference_angle_error_deg,
                    "base_corrected_dx_mm": (
                        float(base_correction_m[0]) * 1000.0
                        if base_correction_m is not None
                        else math.nan
                    ),
                    "base_corrected_dy_mm": (
                        float(base_correction_m[1]) * 1000.0
                        if base_correction_m is not None
                        else math.nan
                    ),
                    "base_corrected_minus_old_dx_mm": (
                        float(base_correction_m[0]) * 1000.0 - old_dx_m * 1000.0
                        if base_correction_m is not None
                        else math.nan
                    ),
                    "base_corrected_minus_old_dy_mm": (
                        float(base_correction_m[1]) * 1000.0 - old_dy_m * 1000.0
                        if base_correction_m is not None
                        else math.nan
                    ),
                    "camera_relative_minus_old_dx_mm": camera_relative_dx_m * 1000.0
                    - float(old_comp["dx_m_camera_dynamic"]) * 1000.0,
                    "camera_relative_minus_old_dy_mm": camera_relative_dy_m * 1000.0
                    - float(old_comp["dy_m_camera_dynamic"]) * 1000.0,
                    "relative_minus_old_dx_mm": relative_dx_m * 1000.0
                    - old_dx_m * 1000.0,
                    "relative_minus_old_dy_mm": relative_dy_m * 1000.0
                    - old_dy_m * 1000.0,
                    "relative_minus_old_dtheta_deg": wrap_deg(
                        relative_dtheta_deg - old_dtheta_deg
                    ),
                    "current_marker_count": len(current_detection.markers),
                }
            )
        except Exception as exc:
            failures.append({"folder": current_folder.name, "reason": str(exc)})

    csv_path = args.output_dir / "comparison_cases.csv"
    if rows:
        with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    dx_errors = [row["relative_minus_old_dx_mm"] for row in rows]
    dy_errors = [row["relative_minus_old_dy_mm"] for row in rows]
    da_errors = [row["relative_minus_old_dtheta_deg"] for row in rows]
    vector_errors = [
        math.hypot(row["relative_minus_old_dx_mm"], row["relative_minus_old_dy_mm"])
        for row in rows
    ]
    old_dx = [row["old_dx_mm"] for row in rows]
    old_dy = [row["old_dy_mm"] for row in rows]
    old_da = [row["old_dtheta_deg"] for row in rows]
    new_dx = [row["new_relative_dx_mm"] for row in rows]
    new_dy = [row["new_relative_dy_mm"] for row in rows]
    new_da = [row["new_relative_dtheta_deg"] for row in rows]
    camera_dx_errors = [row["camera_relative_minus_old_dx_mm"] for row in rows]
    camera_dy_errors = [row["camera_relative_minus_old_dy_mm"] for row in rows]
    height_deltas = [row["new_camera_relative_dz_mm"] for row in rows]
    z_coupling_vectors = [row["z_coupling_vector_mm"] for row in rows]
    translation_errors = [
        math.hypot(row["relative_minus_old_dx_mm"], row["relative_minus_old_dy_mm"])
        for row in rows
    ]
    close_1mm_02deg = sum(
        math.hypot(row["relative_minus_old_dx_mm"], row["relative_minus_old_dy_mm"]) <= 1.0
        and abs(row["relative_minus_old_dtheta_deg"]) <= 0.2
        for row in rows
    )
    close_2mm_05deg = sum(
        math.hypot(row["relative_minus_old_dx_mm"], row["relative_minus_old_dy_mm"]) <= 2.0
        and abs(row["relative_minus_old_dtheta_deg"]) <= 0.5
        for row in rows
    )
    summary = {
        "input": {
            "data_dir": str(args.data_dir),
            "calibration": str(args.calibration),
            "current_image_count": len(list(args.data_dir.glob("*_compensation_current"))),
            "old_result_count": len(old_results),
            "reference_image_count": len(reference_records),
        },
        "method": {
            "new_online": "Aruco cornerSubPix -> solvePnP ITERATIVE -> solvePnPRefineLM -> gTc*cTt",
            "dictionary": settings.dictionary_name,
            "marker_length_m": settings.marker_length_m,
            "primary_comparison": "新3D参考绝对位姿 - 新3D当前绝对位姿，与旧2D相对补偿比较",
            "note": "当前 pkg5 在线接口直接返回的是 gTc*cTt 的绝对值，不是相对参考差值。",
        },
        "processed": len(rows),
        "failed": len(failures),
        "difference_new_relative_minus_old": {
            "dx_mm": scalar_stats(dx_errors),
            "dy_mm": scalar_stats(dy_errors),
            "translation_vector_mm": scalar_stats(vector_errors),
            "dtheta_deg": scalar_stats(da_errors),
        },
        "camera_frame_difference_new_pnp_minus_old_2d": {
            "dx_mm": scalar_stats(camera_dx_errors),
            "dy_mm": scalar_stats(camera_dy_errors),
        },
        "height_diagnostics": {
            "reference_minus_current_z_mm": scalar_stats(height_deltas),
            "z_to_robot_xy_coupling_vector_mm": scalar_stats(z_coupling_vectors),
            "correlation_abs_z_vs_new_old_translation_error": correlation(
                [abs(value) for value in height_deltas], translation_errors
            ),
            "gTc_z_axis_xy_coefficients": [
                float(gripper_from_camera[0, 2]),
                float(gripper_from_camera[1, 2]),
            ],
        },
        "base_frame_compensation_diagnostics": (
            {
                "nominal_robot_pose": nominal_robot_pose,
                "base_from_gripper_rotation": base_from_gripper_rotation.tolist(),
                "difference_base_corrected_minus_old": {
                    "dx_mm": scalar_stats(
                        [row["base_corrected_minus_old_dx_mm"] for row in rows]
                    ),
                    "dy_mm": scalar_stats(
                        [row["base_corrected_minus_old_dy_mm"] for row in rows]
                    ),
                    "translation_vector_mm": scalar_stats(
                        [
                            math.hypot(
                                row["base_corrected_minus_old_dx_mm"],
                                row["base_corrected_minus_old_dy_mm"],
                            )
                            for row in rows
                        ]
                    ),
                },
            }
            if base_from_gripper_rotation is not None
            else None
        ),
        "reference_pairing_quality": {
            "center_error_px": scalar_stats(
                [row["reference_center_match_error_px"] for row in rows]
            ),
            "angle_error_deg": scalar_stats(
                [row["reference_angle_match_error_deg"] for row in rows]
            ),
        },
        "agreement_counts": {
            "translation_le_1mm_and_angle_le_0_2deg": close_1mm_02deg,
            "translation_le_2mm_and_angle_le_0_5deg": close_2mm_05deg,
            "total": len(rows),
        },
        "correlation_old_vs_new_relative": {
            "dx": correlation(old_dx, new_dx),
            "dy": correlation(old_dy, new_dy),
            "dtheta": correlation(old_da, new_da),
        },
        "fitted_camera_to_robot_planar_maps": {
            "old_2d": fit_planar_map(
                [[row["old_camera_dx_mm"], row["old_camera_dy_mm"]] for row in rows],
                [[row["old_dx_mm"], row["old_dy_mm"]] for row in rows],
            ),
            "new_3d": fit_planar_map(
                [
                    [row["new_camera_relative_dx_mm"], row["new_camera_relative_dy_mm"]]
                    for row in rows
                ],
                [[row["new_relative_dx_mm"], row["new_relative_dy_mm"]] for row in rows],
            ),
        },
        "old_output_range": {
            "dx_mm": scalar_stats(old_dx),
            "dy_mm": scalar_stats(old_dy),
            "dtheta_deg": scalar_stats(old_da),
        },
        "new_relative_output_range": {
            "dx_mm": scalar_stats(new_dx),
            "dy_mm": scalar_stats(new_dy),
            "dtheta_deg": scalar_stats(new_da),
        },
        "failures": failures,
    }
    (args.output_dir / "comparison_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
