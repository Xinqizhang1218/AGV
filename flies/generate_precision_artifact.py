from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path


FLIES_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = next(path for path in FLIES_DIR.glob("20260821*") if path.is_dir())
CSV_PATH = next(OUTPUT_DIR.glob("*.csv"))
ARTIFACT_PATH = OUTPUT_DIR / "artifact.json"
SUMMARY_PATH = OUTPUT_DIR / "summary.json"


def read_rows() -> list[dict[str, float | int | str]]:
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as csv_file:
        csv_rows = list(csv.reader(csv_file))[1:]

    rows: list[dict[str, float | int | str]] = []
    for row in csv_rows:
        rows.append(
            {
                "test": int(row[0]),
                "time": row[1],
                "common_corners": int(row[2]),
                "center_dx_px": float(row[3]),
                "center_dy_px": float(row[4]),
                "center_shift_px": math.hypot(float(row[3]), float(row[4])),
                "corner_rms_px": float(row[5]),
                "nonrigid_rms_px": float(row[6]),
                "max_corner_px": float(row[7]),
                "pnp_reproj_rmse_px": float(row[8]),
                "brightness": float(row[9]),
                "brightness_delta": float(row[10]),
                "sharpness": float(row[11]),
                "sharpness_delta": float(row[12]),
                "x_mm": float(row[13]),
                "y_mm": float(row[14]),
                "z_mm": float(row[15]),
                "translation_norm_mm": float(row[16]),
                "rx_deg": float(row[17]),
                "ry_deg": float(row[18]),
                "rz_deg": float(row[19]),
                "rotation_norm_deg": float(row[20]),
                "image": row[21],
            }
        )
    return rows


def mean(rows: list[dict], field: str) -> float:
    return sum(float(row[field]) for row in rows) / len(rows)


def sample_sd(rows: list[dict], field: str) -> float:
    average = mean(rows, field)
    return math.sqrt(
        sum((float(row[field]) - average) ** 2 for row in rows) / (len(rows) - 1)
    )


def correlation(rows: list[dict], field_a: str, field_b: str) -> float:
    average_a = mean(rows, field_a)
    average_b = mean(rows, field_b)
    numerator = sum(
        (float(row[field_a]) - average_a) * (float(row[field_b]) - average_b)
        for row in rows
    )
    denominator = math.sqrt(
        sum((float(row[field_a]) - average_a) ** 2 for row in rows)
        * sum((float(row[field_b]) - average_b) ** 2 for row in rows)
    )
    return numerator / denominator


def build_summary(rows: list[dict]) -> dict[str, float | int]:
    summary: dict[str, float | int] = {
        "sample_count": len(rows),
        "all_common_corners": min(int(row["common_corners"]) for row in rows),
        "max_center_shift_px": max(float(row["center_shift_px"]) for row in rows),
        "corner_rms_min_px": min(float(row["corner_rms_px"]) for row in rows),
        "corner_rms_mean_px": mean(rows, "corner_rms_px"),
        "corner_rms_max_px": max(float(row["corner_rms_px"]) for row in rows),
        "max_single_corner_px": max(float(row["max_corner_px"]) for row in rows),
        "brightness_delta_max_abs": max(abs(float(row["brightness_delta"])) for row in rows),
        "sharpness_range": max(float(row["sharpness"]) for row in rows)
        - min(float(row["sharpness"]) for row in rows),
        "pnp_reproj_mean_px": mean(rows, "pnp_reproj_rmse_px"),
        "translation_mean_mm": mean(rows, "translation_norm_mm"),
        "translation_min_mm": min(float(row["translation_norm_mm"]) for row in rows),
        "translation_max_mm": max(float(row["translation_norm_mm"]) for row in rows),
        "rotation_mean_deg": mean(rows, "rotation_norm_deg"),
        "rotation_min_deg": min(float(row["rotation_norm_deg"]) for row in rows),
        "rotation_max_deg": max(float(row["rotation_norm_deg"]) for row in rows),
        "corner_translation_corr": correlation(rows, "corner_rms_px", "translation_norm_mm"),
        "nonrigid_rotation_corr": correlation(rows, "nonrigid_rms_px", "rotation_norm_deg"),
    }
    for axis in ("x", "y", "z", "rx", "ry", "rz"):
        unit = "mm" if axis in {"x", "y", "z"} else "deg"
        field = f"{axis}_{unit}"
        summary[f"{axis}_mean_{unit}"] = mean(rows, field)
        summary[f"{axis}_sd_{unit}"] = sample_sd(rows, field)
        summary[f"{axis}_p2p_{unit}"] = max(float(row[field]) for row in rows) - min(
            float(row[field]) for row in rows
        )
    return summary


def build_axis_rows(summary: dict[str, float | int]) -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    for axis in ("x", "y", "z", "rx", "ry", "rz"):
        unit = "mm" if axis in {"x", "y", "z"} else "deg"
        rows.append(
            {
                "axis": f"{axis.upper()} ({unit})",
                "mean": float(summary[f"{axis}_mean_{unit}"]),
                "sd": float(summary[f"{axis}_sd_{unit}"]),
                "p2p": float(summary[f"{axis}_p2p_{unit}"]),
            }
        )
    return rows


def build_artifact(rows: list[dict], summary: dict[str, float | int]) -> dict:
    generated_at = datetime.now(timezone.utc).isoformat()
    measurement_rows = [{**row, "test_label": f"#{row['test']}"} for row in rows]
    overview = [
        {
            "common_corners": summary["all_common_corners"],
            "max_center_shift_px": summary["max_center_shift_px"],
            "corner_rms_max_px": summary["corner_rms_max_px"],
            "max_single_corner_px": summary["max_single_corner_px"],
            "translation_mean_mm": summary["translation_mean_mm"],
            "translation_max_mm": summary["translation_max_mm"],
            "rotation_mean_deg": summary["rotation_mean_deg"],
            "rotation_max_deg": summary["rotation_max_deg"],
        }
    ]

    return {
        "surface": "report",
        "manifest": {
            "version": 1,
            "surface": "report",
            "title": "2026-08-21 ChArUco 静止重复测量精度分析",
            "generatedAt": generated_at,
            "cards": [
                {
                    "id": "image_stability",
                    "description": "17 张当前图相对 10:02:40 基准图的角点变化。",
                    "dataset": "overview",
                    "sourceId": "debug_images",
                    "metrics": [
                        {"label": "共同角点", "field": "common_corners", "format": "number"},
                        {"label": "最大中心位移 (px)", "field": "max_center_shift_px", "format": "number"},
                        {"label": "最大角点 RMS (px)", "field": "corner_rms_max_px", "format": "number"},
                        {"label": "最大单角点差 (px)", "field": "max_single_corner_px", "format": "number"},
                    ],
                },
                {
                    "id": "returned_range",
                    "description": "接口 targetFlangePose 的六轴增量模长。",
                    "dataset": "overview",
                    "sourceId": "precision_log",
                    "metrics": [
                        {"label": "平移均值 (mm)", "field": "translation_mean_mm", "format": "number"},
                        {"label": "平移最大 (mm)", "field": "translation_max_mm", "format": "number"},
                        {"label": "旋转均值 (deg)", "field": "rotation_mean_deg", "format": "number"},
                        {"label": "旋转最大 (deg)", "field": "rotation_max_deg", "format": "number"},
                    ],
                },
            ],
            "charts": [
                {
                    "id": "pixel_vs_translation",
                    "title": "角点差异与返回平移模长几乎无相关",
                    "subtitle": "每个点代表一次静止重复测量。",
                    "type": "scatter",
                    "dataset": "measurements",
                    "sourceId": "debug_images",
                    "encodings": {
                        "x": {"field": "corner_rms_px", "type": "quantitative", "label": "角点 RMS (px)"},
                        "y": {"field": "translation_norm_mm", "type": "quantitative", "label": "返回平移模长 (mm)"},
                        "color": {"field": "test_label", "type": "nominal", "label": "测量序号"},
                    },
                }
            ],
            "tables": [
                {
                    "id": "measurement_detail",
                    "title": "17 次图片差异与接口返回明细",
                    "subtitle": "图片指标由 raw.jpg 重新检测；六轴值来自 targetFlangePose。",
                    "dataset": "measurements",
                    "sourceId": "precision_log",
                    "density": "dense",
                    "layout": "full",
                    "defaultSort": {"field": "test", "direction": "asc"},
                    "columns": [
                        {"field": "test", "label": "序号", "type": "number"},
                        {"field": "time", "label": "时间", "type": "text"},
                        {"field": "common_corners", "label": "角点数", "type": "number"},
                        {"field": "center_dx_px", "label": "中心 dx(px)", "format": "number"},
                        {"field": "center_dy_px", "label": "中心 dy(px)", "format": "number"},
                        {"field": "corner_rms_px", "label": "角点 RMS(px)", "format": "number"},
                        {"field": "max_corner_px", "label": "最大角点差(px)", "format": "number"},
                        {"field": "pnp_reproj_rmse_px", "label": "PnP 重投影(px)", "format": "number"},
                        {"field": "x_mm", "label": "X(mm)", "format": "number"},
                        {"field": "y_mm", "label": "Y(mm)", "format": "number"},
                        {"field": "z_mm", "label": "Z(mm)", "format": "number"},
                        {"field": "translation_norm_mm", "label": "平移模长(mm)", "format": "number"},
                        {"field": "rx_deg", "label": "Rx(deg)", "format": "number"},
                        {"field": "ry_deg", "label": "Ry(deg)", "format": "number"},
                        {"field": "rz_deg", "label": "Rz(deg)", "format": "number"},
                        {"field": "rotation_norm_deg", "label": "旋转模长(deg)", "format": "number"},
                    ],
                },
                {
                    "id": "axis_summary",
                    "title": "六轴重复测量统计",
                    "subtitle": "SD 为样本标准差；P2P 为最大值减最小值。",
                    "dataset": "axis_summary",
                    "sourceId": "precision_log",
                    "density": "dense",
                    "columns": [
                        {"field": "axis", "label": "轴", "type": "text"},
                        {"field": "mean", "label": "均值", "format": "number"},
                        {"field": "sd", "label": "标准差", "format": "number"},
                        {"field": "p2p", "label": "峰峰值", "format": "number"},
                    ],
                },
            ],
            "sources": [
                {"id": "precision_log", "label": "20260821 精度测试日志", "path": "flies/20260821精度测试.md"},
                {"id": "debug_images", "label": "20260821 调试原图", "path": "data/debug/20260821"},
            ],
            "blocks": [
                {"id": "title", "type": "markdown", "body": "# 2026-08-21 ChArUco 静止重复测量精度分析"},
                {"id": "answer", "type": "markdown", "body": "## 结论\n\n**图片没有差很多。** 17 次均稳定识别同一组 16/16 角点；相对基准图的整板角点 RMS 只有 **0.122–0.196 px**，最坏单角点差 **0.394 px**，最大中心位移 **0.172 px**。这些差异肉眼基本不可见。接口仍返回 **0.099–0.746 mm** 和 **0.011–0.130°**，说明较大的六轴波动主要来自平面 PnP 对亚像素角点噪声的姿态敏感性及后续手眼坐标变换，而不是标定板真的在图片里移动了相应幅度。"},
                {"id": "image_metrics", "type": "metric-strip", "cardIds": ["image_stability"]},
                {"id": "return_metrics", "type": "metric-strip", "cardIds": ["returned_range"]},
                {"id": "relationship", "type": "markdown", "body": "## 图片变化能否解释返回误差？\n\n不能直接解释。角点 RMS 与平移模长的 Pearson 相关系数仅 **0.016**；去除整板平移后的角点形变 RMS 与旋转模长相关系数为 **-0.043**，都接近 0。第 12 次的图片角点 RMS 为 0.171 px，但返回平移只有 0.099 mm；第 16 次角点 RMS 也为 0.169 px，返回却达到 0.746 mm。"},
                {"id": "scatter", "type": "chart", "chartId": "pixel_vs_translation", "layout": "full"},
                {"id": "detail_intro", "type": "markdown", "body": "## 逐次明细\n\n中心 dx/dy 和角点差均以 10:02:40 的 reference raw.jpg 为基准，按 ChArUco 角点 ID 一一配对。"},
                {"id": "detail", "type": "table", "tableId": "measurement_detail", "layout": "full"},
                {"id": "repeatability", "type": "markdown", "body": "## 六轴重复性\n\n机械臂静止时，应同时看均值偏置和离散度。Y 均值为 -0.367 mm，说明存在系统性偏置；X/Y 的样本标准差约 0.17 mm，峰峰值分别 0.655/0.623 mm。Rz 最稳定，峰峰值仅 0.0148°；Rx/Ry 更敏感，峰峰值约 0.116/0.130°。"},
                {"id": "axes", "type": "table", "tableId": "axis_summary"},
                {"id": "method", "type": "markdown", "body": "## 口径与限制\n\n- 基准：10:02:40 的跨机台 reference raw.jpg。\n- 当前图：10:03:36–10:06:05 的 17 张 compensation_current/raw.jpg。\n- 图片复算：使用 settings_online.yaml 与线上相同的 ChArUco 检测器，按 16 个共同角点 ID 计算。\n- 六轴返回：直接取日志中的 data.targetFlangePose，并换算为 mm/deg。\n- raw.jpg 是调试保存的 JPEG，重新检测会受压缩影响；图片指标用于判断视觉差异量级，不替代接口运行时的内存角点。\n- 这里只能评价静止重复性，不能评价机械臂实际定位精度；定位精度还需要外部测量基准。"},
            ],
        },
        "snapshot": {
            "version": 1,
            "generatedAt": generated_at,
            "status": "ready",
            "datasets": {
                "overview": overview,
                "measurements": measurement_rows,
                "axis_summary": build_axis_rows(summary),
            },
        },
    }


def main() -> None:
    rows = read_rows()
    summary = build_summary(rows)
    artifact = build_artifact(rows, summary)
    ARTIFACT_PATH.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    SUMMARY_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(ARTIFACT_PATH)


if __name__ == "__main__":
    main()
