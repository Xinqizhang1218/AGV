"""批量检查二次标定 ArUco 板的重复定位误差。

默认读取 ``agv_vision/config/settings_online.yaml``，使用项目现有的
``ArucoReferenceDetector``，因此检测逻辑与线上二次标定保持一致。

示例：
    python check_secondary_board_repeatability.py "重复定位图片/20260717"

说明：
    这些图片应当是在相机、标定板和 AGV 均未移动的情况下拍摄。脚本检查的是
    视觉识别的重复性；若要检查绝对定位精度，还需要机器人或量具提供的真实位置。
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np

from agv_vision.config.settings import AppSettings
from agv_vision.vision.aruco_detector import ArucoReferenceDetector


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


@dataclass
class ImageResult:
    filename: str
    detected: bool
    marker_count: int | None = None
    marker_ids: str = ""
    center_x_px: float | None = None
    center_y_px: float | None = None
    angle_deg: float | None = None
    pixels_per_m: float | None = None
    position_error_px: float | None = None
    position_error_m: float | None = None
    angle_error_deg: float | None = None
    scale_error_percent: float | None = None
    passed: bool = False
    error: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="检查同一位置连续拍摄的二次标定板图像是否存在重复定位误差"
    )
    parser.add_argument(
        "image_dir",
        nargs="?",
        default=r"重复定位图片\20260717",
        help="图片文件夹（默认：重复定位图片/20260717）",
    )
    parser.add_argument(
        "--config",
        default="agv_vision/config/settings_online.yaml",
        help="项目 YAML 配置文件",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="结果目录（默认：图片目录/check_repeatability_result）",
    )
    parser.add_argument(
        "--max-position-m",
        type=float,
        default=0.001,
        help="单张图片相对中位位置允许的最大误差，默认 0.001 m",
    )
    parser.add_argument(
        "--max-angle-deg",
        type=float,
        default=0.30,
        help="单张图片相对中位角度允许的最大误差，默认 0.30 度",
    )
    parser.add_argument(
        "--max-scale-percent",
        type=float,
        default=1.0,
        help="单张图片 px/m 相对中位值允许的最大变化，默认 1.0%%",
    )
    parser.add_argument(
        "--marker-length-m",
        type=float,
        default=None,
        help="覆盖配置中的 ArUco 实际边长（m）；配置不正确时必须指定",
    )
    return parser.parse_args()


def read_image(path: Path) -> np.ndarray | None:
    """支持 Windows 中文路径的 OpenCV 读图。"""
    try:
        data = np.fromfile(str(path), dtype=np.uint8)
        return cv2.imdecode(data, cv2.IMREAD_COLOR)
    except (OSError, cv2.error):
        return None


def write_image(path: Path, image: np.ndarray) -> None:
    """支持 Windows 中文路径的 OpenCV 写图。"""
    suffix = path.suffix or ".jpg"
    ok, encoded = cv2.imencode(suffix, image)
    if not ok:
        raise RuntimeError(f"无法编码标注图：{path.name}")
    encoded.tofile(str(path))


def angle_delta_deg(value: float, reference: float) -> float:
    """返回 [-180, 180) 内的最短有符号角度差。"""
    return (value - reference + 180.0) % 360.0 - 180.0


def circular_median_deg(values: list[float]) -> float:
    """选择总角度距离最小的样本，避免 -180/180 边界破坏普通中位数。"""
    return min(
        values,
        key=lambda candidate: sum(abs(angle_delta_deg(v, candidate)) for v in values),
    )


def finite_float(value: float | None) -> float | None:
    if value is None:
        return None
    value = float(value)
    return value if math.isfinite(value) else None


def main() -> int:
    args = parse_args()
    image_dir = Path(args.image_dir).expanduser().resolve()
    config_path = Path(args.config).expanduser().resolve()
    output_dir = (
        Path(args.output_dir).expanduser().resolve()
        if args.output_dir
        else image_dir / "check_repeatability_result"
    )

    if not image_dir.is_dir():
        print(f"错误：图片目录不存在：{image_dir}", file=sys.stderr)
        return 2
    if not config_path.is_file():
        print(f"错误：配置文件不存在：{config_path}", file=sys.stderr)
        return 2

    images = sorted(
        p for p in image_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
    )
    if not images:
        print(f"错误：目录中没有支持的图片：{image_dir}", file=sys.stderr)
        return 2

    settings = AppSettings.from_yaml(config_path)
    if args.marker_length_m is not None:
        if args.marker_length_m <= 0:
            print("错误：--marker-length-m 必须大于 0", file=sys.stderr)
            return 2
        settings.aruco.marker_length_m = args.marker_length_m

    if settings.aruco.marker_length_m <= 0:
        print("错误：aruco.marker_length_m 必须大于 0", file=sys.stderr)
        return 2

    detector = ArucoReferenceDetector(settings.aruco)
    output_dir.mkdir(parents=True, exist_ok=True)
    annotated_dir = output_dir / "annotated"
    annotated_dir.mkdir(parents=True, exist_ok=True)

    results: list[ImageResult] = []
    detected_refs: dict[str, object] = {}

    for image_path in images:
        image = read_image(image_path)
        if image is None:
            results.append(ImageResult(image_path.name, False, error="图片读取失败"))
            continue
        try:
            ref = detector.detect(image, station_id="repeatability_check")
            marker_ids = ",".join(str(m.marker_id) for m in ref.markers)
            results.append(
                ImageResult(
                    filename=image_path.name,
                    detected=True,
                    marker_count=ref.marker_count,
                    marker_ids=marker_ids,
                    center_x_px=finite_float(ref.board_center_x),
                    center_y_px=finite_float(ref.board_center_y),
                    angle_deg=finite_float(ref.board_angle_deg),
                    pixels_per_m=finite_float(ref.pixels_per_m),
                )
            )
            detected_refs[image_path.name] = ref
            write_image(annotated_dir / image_path.name, detector.draw(image, ref))
        except Exception as exc:  # 单张失败不应中断整批检查
            results.append(
                ImageResult(image_path.name, False, error=f"{type(exc).__name__}: {exc}")
            )

    valid = [r for r in results if r.detected]
    if valid:
        ref_x = float(np.median([r.center_x_px for r in valid]))
        ref_y = float(np.median([r.center_y_px for r in valid]))
        ref_angle = circular_median_deg([r.angle_deg for r in valid])
        valid_scales = [r.pixels_per_m for r in valid if r.pixels_per_m and r.pixels_per_m > 0]
        ref_scale = float(np.median(valid_scales)) if valid_scales else None

        for row in valid:
            dx = row.center_x_px - ref_x
            dy = row.center_y_px - ref_y
            row.position_error_px = float(math.hypot(dx, dy))
            row.position_error_m = (
                row.position_error_px / ref_scale if ref_scale and ref_scale > 0 else None
            )
            row.angle_error_deg = abs(angle_delta_deg(row.angle_deg, ref_angle))
            row.scale_error_percent = (
                abs(row.pixels_per_m - ref_scale) / ref_scale * 100.0
                if ref_scale and row.pixels_per_m and row.pixels_per_m > 0
                else None
            )
            row.passed = (
                row.position_error_m is not None
                and row.position_error_m <= args.max_position_m
                and row.angle_error_deg <= args.max_angle_deg
                and row.scale_error_percent is not None
                and row.scale_error_percent <= args.max_scale_percent
            )
    else:
        ref_x = ref_y = ref_angle = ref_scale = None

    failed_detection_count = sum(not r.detected for r in results)
    failed_tolerance_count = sum(r.detected and not r.passed for r in results)
    overall_passed = failed_detection_count == 0 and failed_tolerance_count == 0

    position_errors = [r.position_error_m for r in valid if r.position_error_m is not None]
    angle_errors = [r.angle_error_deg for r in valid if r.angle_error_deg is not None]
    scale_errors = [r.scale_error_percent for r in valid if r.scale_error_percent is not None]
    summary = {
        "verdict": "PASS" if overall_passed else "FAIL",
        "meaning": "重复性合格" if overall_passed else "存在识别失败或超出阈值的重复定位误差",
        "image_dir": str(image_dir),
        "config": str(config_path),
        "image_count": len(results),
        "detected_count": len(valid),
        "detection_failed_count": failed_detection_count,
        "tolerance_failed_count": failed_tolerance_count,
        "marker_length_m": settings.aruco.marker_length_m,
        "reference": {
            "method": "各指标的稳健中位参考值",
            "center_x_px": ref_x,
            "center_y_px": ref_y,
            "angle_deg": ref_angle,
            "pixels_per_m": ref_scale,
        },
        "thresholds": {
            "max_position_m": args.max_position_m,
            "max_angle_deg": args.max_angle_deg,
            "max_scale_percent": args.max_scale_percent,
        },
        "statistics": {
            "mean_position_error_m": float(np.mean(position_errors)) if position_errors else None,
            "max_position_error_m": max(position_errors, default=None),
            "mean_angle_error_deg": float(np.mean(angle_errors)) if angle_errors else None,
            "max_angle_error_deg": max(angle_errors, default=None),
            "mean_scale_error_percent": float(np.mean(scale_errors)) if scale_errors else None,
            "max_scale_error_percent": max(scale_errors, default=None),
        },
        "note": "本结果评价同一固定位置的视觉重复性，不代表绝对定位精度。",
    }

    json_path = output_dir / "repeatability_report.json"
    csv_path = output_dir / "repeatability_details.csv"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(
            {"summary": summary, "images": [asdict(r) for r in results]},
            f,
            ensure_ascii=False,
            indent=2,
        )
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(results[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(r) for r in results)

    print("=" * 78)
    print(f"二次标定板重复定位检查：{summary['verdict']}（{summary['meaning']}）")
    print(f"图片：{len(results)} 张，识别成功：{len(valid)} 张，识别失败：{failed_detection_count} 张")
    print(
        f"阈值：位置 <= {args.max_position_m:.6f} m，"
        f"角度 <= {args.max_angle_deg:.3f} deg，"
        f"比例变化 <= {args.max_scale_percent:.3f}%"
    )
    print(f"ArUco 实际边长配置：{settings.aruco.marker_length_m:.6f} m")
    if ref_scale:
        print(f"中位图像比例：{ref_scale:.6f} px/m")
    print("-" * 78)
    print(f"{'结果':<6} {'位置误差(m)':>14} {'角度误差(deg)':>15} {'比例误差(%)':>13}  文件")
    for row in results:
        status = "PASS" if row.passed else "FAIL"
        pos = f"{row.position_error_m:.4f}" if row.position_error_m is not None else "-"
        ang = f"{row.angle_error_deg:.4f}" if row.angle_error_deg is not None else "-"
        scale = f"{row.scale_error_percent:.4f}" if row.scale_error_percent is not None else "-"
        detail = row.filename if not row.error else f"{row.filename}  ({row.error})"
        print(f"{status:<6} {pos:>14} {ang:>15} {scale:>13}  {detail}")
    print("-" * 78)
    print(f"JSON 报告：{json_path}")
    print(f"CSV 明细： {csv_path}")
    print(f"标注图片： {annotated_dir}")
    print("=" * 78)
    return 0 if overall_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
