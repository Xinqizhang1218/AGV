"""把补偿对比结果整理为可交付的 Data Analytics 报告输入。"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comparison-dir", type=Path, required=True)
    args = parser.parse_args()

    summary = load_json(args.comparison_dir / "comparison_summary.json")
    with (args.comparison_dir / "comparison_cases.csv").open(
        encoding="utf-8-sig", newline=""
    ) as stream:
        cases = list(csv.DictReader(stream))

    for row in cases:
        for key, value in list(row.items()):
            if key not in {"case", "timestamp", "reference_case", "old_result_json"}:
                try:
                    row[key] = float(value)
                except (TypeError, ValueError):
                    pass

    difference = summary["difference_new_relative_minus_old"]
    camera_difference = summary["camera_frame_difference_new_pnp_minus_old_2d"]
    agreement = summary["agreement_counts"]
    mappings = summary["fitted_camera_to_robot_planar_maps"]
    base_diagnostics = summary["base_frame_compensation_diagnostics"]
    base_difference = base_diagnostics["difference_base_corrected_minus_old"]
    height = summary["height_diagnostics"]
    pairing = summary["reference_pairing_quality"]

    top_cases = sorted(
        cases,
        key=lambda row: (
            row["relative_minus_old_dx_mm"] ** 2
            + row["relative_minus_old_dy_mm"] ** 2
        ),
        reverse=True,
    )[:15]
    top_rows = [
        {
            "case": row["timestamp"],
            "old_dx_mm": round(row["old_dx_mm"], 3),
            "old_dy_mm": round(row["old_dy_mm"], 3),
            "new_dx_mm": round(row["new_relative_dx_mm"], 3),
            "new_dy_mm": round(row["new_relative_dy_mm"], 3),
            "translation_error_mm": round(
                (
                    row["relative_minus_old_dx_mm"] ** 2
                    + row["relative_minus_old_dy_mm"] ** 2
                )
                ** 0.5,
                3,
            ),
            "angle_error_deg": round(
                abs(row["relative_minus_old_dtheta_deg"]), 3
            ),
        }
        for row in top_cases
    ]

    # 最终报告必须使用转换到机器人基座坐标后的补偿量，而不是夹爪坐标中的目标位移。
    top_cases = sorted(
        cases,
        key=lambda row: (
            row["base_corrected_minus_old_dx_mm"] ** 2
            + row["base_corrected_minus_old_dy_mm"] ** 2
        ),
        reverse=True,
    )[:15]
    top_rows = [
        {
            "case": row["timestamp"],
            "old_dx_mm": round(row["old_dx_mm"], 3),
            "old_dy_mm": round(row["old_dy_mm"], 3),
            "new_dx_mm": round(row["base_corrected_dx_mm"], 3),
            "new_dy_mm": round(row["base_corrected_dy_mm"], 3),
            "translation_error_mm": round(
                (
                    row["base_corrected_minus_old_dx_mm"] ** 2
                    + row["base_corrected_minus_old_dy_mm"] ** 2
                )
                ** 0.5,
                3,
            ),
            "angle_error_deg": round(
                abs(row["relative_minus_old_dtheta_deg"]), 3
            ),
        }
        for row in top_cases
    ]

    error_rows = []
    for axis, label in (
        ("dx_mm", "X"),
        ("dy_mm", "Y"),
        ("translation_vector_mm", "XY向量"),
    ):
        error_rows.extend(
            [
                {"axis": label, "stat": "MAE", "value_mm": difference[axis]["mae"]},
                {"axis": label, "stat": "RMSE", "value_mm": difference[axis]["rmse"]},
            ]
        )
    camera_error_rows = []
    for axis, label in (("dx_mm", "相机X"), ("dy_mm", "相机Y")):
        camera_error_rows.extend(
            [
                {
                    "axis": label,
                    "stat": "MAE",
                    "value_mm": camera_difference[axis]["mae"],
                },
                {
                    "axis": label,
                    "stat": "RMSE",
                    "value_mm": camera_difference[axis]["rmse"],
                },
            ]
        )

    # 覆盖旧口径：图表展示正确的基座坐标补偿残差。
    error_rows = []
    for axis, label in (
        ("dx_mm", "X"),
        ("dy_mm", "Y"),
        ("translation_vector_mm", "XY向量"),
    ):
        error_rows.extend(
            [
                {
                    "axis": label,
                    "stat": "MAE",
                    "value_mm": base_difference[axis]["mae"],
                },
                {
                    "axis": label,
                    "stat": "RMSE",
                    "value_mm": base_difference[axis]["rmse"],
                },
            ]
        )
    height_error_rows = [
        {
            "component": "参考-当前 Z",
            "stat": "MAE",
            "value_mm": height["reference_minus_current_z_mm"]["mae"],
        },
        {
            "component": "参考-当前 Z",
            "stat": "RMSE",
            "value_mm": height["reference_minus_current_z_mm"]["rmse"],
        },
        {
            "component": "Z→机器人XY",
            "stat": "MAE",
            "value_mm": height["z_to_robot_xy_coupling_vector_mm"]["mae"],
        },
        {
            "component": "Z→机器人XY",
            "stat": "RMSE",
            "value_mm": height["z_to_robot_xy_coupling_vector_mm"]["rmse"],
        },
    ]

    metrics = [
        {
            "processed": summary["processed"],
            "failed": summary["failed"],
            "xy_mae_mm": difference["translation_vector_mm"]["mae"],
            "angle_rmse_deg": difference["dtheta_deg"]["rmse"],
            "camera_x_rmse_mm": camera_difference["dx_mm"]["rmse"],
            "camera_y_rmse_mm": camera_difference["dy_mm"]["rmse"],
        }
    ]
    metrics[0]["xy_mae_mm"] = base_difference["translation_vector_mm"]["mae"]
    old_angle = mappings["old_2d"]["equivalent_rotation_deg"]
    new_angle = mappings["new_3d"]["equivalent_rotation_deg"]
    markdown = {
        "summary": (
            "## 结论\n\n"
            "**新旧补偿结果不一样，不能按数值等价替换。** 95 组图片全部检测和求解成功；"
            f"统一换算成“参考位姿减当前位姿”后，XY 向量差异 MAE 为 "
            f"**{difference['translation_vector_mm']['mae']:.3f} mm**，"
            f"角度差异 RMSE 为 **{difference['dtheta_deg']['rmse']:.3f}°**。\n\n"
            f"只有 {agreement['translation_le_1mm_and_angle_le_0_2deg']}/"
            f"{agreement['total']} 组同时满足平移差不超过 1 mm、角度差不超过 0.2°。"
        ),
        "method": (
            "## 对比口径\n\n"
            "- 新链：ArUco 检测 → cornerSubPix → solvePnP ITERATIVE → "
            "solvePnPRefineLM → `gTc*cTt`。\n"
            "- 旧链：像素中心/角度相对参考差 → 像素比例尺 → 旧 2D 手眼矩阵。\n"
            "- 因当前 pkg5 在线接口直接返回 `gTc*cTt` 的绝对目标位姿，报告额外计算了"
            "“新 3D 参考绝对位姿 - 新 3D 当前绝对位姿”，再与旧相对补偿做同口径比较。"
        ),
        "diagnosis": (
            "## 差异来源\n\n"
            "ArUco/PnP 本身不是主要问题：在相机坐标系内，新 PnP 相对位移与旧 2D "
            f"位移的 X/Y RMSE 仅 **{camera_difference['dx_mm']['rmse']:.3f} mm** / "
            f"**{camera_difference['dy_mm']['rmse']:.3f} mm**。\n\n"
            "主要差异发生在“相机坐标 → 机器人坐标”：旧数据拟合出的平面映射包含 "
            f"Y 反射，等效角约 **{old_angle:.2f}°**；新 gTc 是正常旋转，等效角约 "
            f"**{new_angle:.2f}°**。两套坐标定义不兼容，因此角度趋势能保持，XY 输出却会明显变化。"
        ),
        "recommendation": (
            "## 建议\n\n"
            "1. 不能用“与旧数值一样”作为新 3D 链验收条件。\n"
            "2. 上线前先确定接口语义：机器人需要的是 `gTc*cTt` 绝对位姿，还是"
            "`参考 - 当前` 的补偿量；两者不能混用。\n"
            "3. 用现场已知的 ±X、±Y 机械位移做方向验收，确认新 gTc 的机器人 X/Y "
            "符号和轴定义后，再做闭环补偿测试。\n"
            "4. 若必须保持旧机器人坐标定义，需要在 3D 输出之后增加明确的坐标系转换，"
            "而不是退回旧 2D 检测。"
        ),
        "limits": (
            "## 限制\n\n"
            "该批调试图片没有逐帧机器人真值位姿，因此本报告只能判断新旧算法是否一致，"
            "不能仅凭旧输出断言哪套机器人坐标结果更准确。新手眼标定的内部残差良好，"
            "但仍应通过现场已知位移和实际补偿闭环验证外部准确度。"
        ),
    }

    pose = base_diagnostics["nominal_robot_pose"]
    markdown = {
        "title": "# 20260723 新旧二次补偿对比报告",
        "summary": (
            "## 技术结论：正确坐标链下新旧结果基本一致\n\n"
            "**高度已经由完整 3D PnP 处理；上一版的大差异来自比较坐标系错误。** "
            "95 组图片全部完成 ArUco 检测和位姿求解，失败 0 组。补上标定基准姿态的 "
            "`bRg`，并把目标误差转换成机器人基座坐标中的反向补偿后，新旧 XY "
            f"差异 MAE 为 **{base_difference['translation_vector_mm']['mae']:.3f} mm**，"
            f"RMSE 为 **{base_difference['translation_vector_mm']['rmse']:.3f} mm**，"
            f"最大差异为 **{base_difference['translation_vector_mm']['max_abs']:.3f} mm**。"
            f"角度差异 MAE 为 **{difference['dtheta_deg']['mae']:.3f}°**。"
        ),
        "corrected_finding": (
            "## 补上 bRg 后，机器人 XY 与旧结果恢复一致\n\n"
            "下图展示新 3D 基座补偿减旧 2D 补偿的残差。X、Y 和 XY 向量的误差均已"
            "降到亚毫米级，证明检测与手眼标定结果可以延续旧机器人运动方向；此前"
            "十几毫米的差异不是算法精度下降，而是把夹爪坐标中的目标位移直接拿去与"
            "基座坐标中的机器人补偿指令比较。"
        ),
        "height_finding": (
            "## Z 高度已处理，且不是本次大差异来源\n\n"
            f"`solvePnP + solvePnPRefineLM` 为每张图重新估计完整 X、Y、Z。该批参考图"
            f"与当前图的 Z 差 MAE 为 **{height['reference_minus_current_z_mm']['mae']:.3f} mm**，"
            f"RMSE 为 **{height['reference_minus_current_z_mm']['rmse']:.3f} mm**，"
            f"最大为 **{height['reference_minus_current_z_mm']['max_abs']:.3f} mm**。"
            "当前 gTc 的相机 Z 轴到机器人 XY 的系数分别为 "
            f"`{height['gTc_z_axis_xy_coefficients'][0]:.5f}` 和 "
            f"`{height['gTc_z_axis_xy_coefficients'][1]:.5f}`，因此 Z 对 XY 的耦合"
            f"平均只有 **{height['z_to_robot_xy_coupling_vector_mm']['mean']:.3f} mm**，"
            f"最大只有 **{height['z_to_robot_xy_coupling_vector_mm']['max_abs']:.3f} mm**。"
        ),
        "scope": (
            "## 数据范围与比较定义\n\n"
            "- 数据：2026-07-23 调试目录中的 95 组当前图、15 组工位参考图和 95 份旧补偿结果。\n"
            "- 图像分辨率：1280×800；在线 ArUco：DICT_5X5_50，边长 0.150 m。\n"
            "- 新视觉链：ArUco → cornerSubPix → solvePnP ITERATIVE → "
            "solvePnPRefineLM。\n"
            "- 旧输出：参考图与当前图的 2D 差值，经动态像素比例尺和旧平面手眼矩阵转换"
            "得到机器人基座补偿。\n"
            f"- 参考图对应关系逐组完全匹配：中心误差最大 "
            f"**{pairing['center_error_px']['max_abs']:.3f} px**，角度误差最大 "
            f"**{pairing['angle_error_deg']['max_abs']:.3f}°**。"
        ),
        "method": (
            "## 正确的完整坐标链\n\n"
            "`cTt` 表示目标在相机坐标系中的位姿；`gTc*cTt` 只得到目标在夹爪坐标系"
            "中的位姿，并不是机器人基座坐标中的补偿指令。本次按标定基准姿态 "
            f"`RX={pose['rx']:.3f} rad、RY={pose['ry']:.3f} rad、"
            f"RZ={pose['rz']:.3f} rad` 构造 `bRg`。\n\n"
            "平移比较采用：`Δp_g = p_g,ref - p_g,current`，"
            "`Δp_robot = -bRg * Δp_g`。负号表示机器人需要反向移动来消除目标在相机"
            "画面中的误差。角度采用参考相对当前的旋转差。"
        ),
        "pnp_validation": (
            "## 相机坐标交叉验证也支持同一结论\n\n"
            "在进入手眼和基座坐标转换之前，新 PnP 相对位移与旧动态比例尺位移已经高度"
            f"一致：相机 X/Y 的 RMSE 分别为 **{camera_difference['dx_mm']['rmse']:.3f} mm** "
            f"和 **{camera_difference['dy_mm']['rmse']:.3f} mm**。这说明 ArUco 检测、"
            "亚像素角点与 PnP 深度估计没有造成此前看到的十几毫米差异。"
        ),
        "limits": (
            "## 适用条件、稳健性与限制\n\n"
            "本次基座转换使用标定数据中的基准机器人姿态，适用于在线拍照时 RX、RY、RZ "
            "保持该固定姿态的情况。如果在线姿态发生变化，必须使用当次机器人实际姿态"
            "重新计算 bRg；仅固定使用标定姿态会重新引入方向误差。\n\n"
            "这批历史图片没有逐帧独立测量的机器人真值，因此本报告证明的是“新旧输出"
            "一致性”，不是对绝对机器人定位精度的最终认证。最终上线仍需用已知 ±X、±Y "
            "位移和闭环回零测试确认外部精度。"
        ),
        "recommendation": (
            "## 代码修改建议\n\n"
            "1. 保留完整 X、Y、Z 和旋转的 PnP 结果，不删除高度 Z。\n"
            "2. 在线补偿不能停在 `gTc*cTt`；输出给机器人前必须转换到机器人实际接收的坐标系。\n"
            "3. 若拍照姿态固定，将固定 bRg 和姿态单位/欧拉角顺序写入标定结果并校验。\n"
            "4. 若姿态可能变化，Java 每次传当前 X、Y、Z、RX、RY、RZ，Python 实时构造 bTg。\n"
            "5. 接口中明确区分“目标绝对位姿”和“相对参考的机器人补偿量”，避免再次混用。"
        ),
        "further": (
            "## 上线前仍需确认的问题\n\n"
            "- 机器人控制器接收的 dx、dy 是基座坐标、工具坐标还是用户坐标？\n"
            "- 在线拍照时 RX、RY、RZ 是否严格固定为标定基准姿态？\n"
            "- dθ 的正方向、单位以及机器人执行时的旋转中心是否已与 Java 接口统一？\n"
            "- 是否需要在 Python 端直接输出最终机器人补偿，还是由 Java 使用当前 bTg 完成转换？"
        ),
        "detail": (
            "## 最大残差样本仍处于亚毫米级\n\n"
            "下表列出正确基座坐标口径下 XY 差异最大的 15 组，用于逐组复核。即使是最大"
            f"样本，新旧 XY 差异也只有 **{base_difference['translation_vector_mm']['max_abs']:.3f} mm**。"
        ),
    }
    # 兼容下方原始 artifact 构造，随后会统一替换为新的完整 blocks 顺序。
    markdown["diagnosis"] = markdown["height_finding"]

    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    artifact = {
        "surface": "report",
        "manifest": {
            "version": 1,
            "surface": "report",
            "title": "20260723 新旧二次补偿对比报告",
            "description": "pkg5 完整 3D 补偿链与 pkg3 历史 2D 补偿结果的离线诊断。",
            "generatedAt": generated_at,
            "cards": [
                {
                    "id": "quality_card",
                    "description": "批量处理完整性与关键差异指标。",
                    "dataset": "metrics",
                    "metrics": [
                        {"label": "成功处理", "field": "processed", "format": "number"},
                        {"label": "失败", "field": "failed", "format": "number"},
                        {"label": "XY差异MAE(mm)", "field": "xy_mae_mm", "format": "number"},
                        {
                            "label": "角度差异RMSE(°)",
                            "field": "angle_rmse_deg",
                            "format": "number",
                        },
                    ],
                }
            ],
            "charts": [
                {
                    "id": "robot_error_chart",
                    "title": "同口径下新旧机器人 XY 差异",
                    "subtitle": "新3D相对补偿减旧2D相对补偿；单位 mm。",
                    "type": "bar",
                    "dataset": "robot_errors",
                    "valueFormat": "number",
                    "encodings": {
                        "x": {"field": "axis", "type": "nominal", "label": "分量"},
                        "y": {
                            "field": "value_mm",
                            "type": "quantitative",
                            "label": "误差 (mm)",
                        },
                        "color": {"field": "stat", "type": "nominal", "label": "统计量"},
                        "tooltip": [
                            {
                                "field": "value_mm",
                                "type": "quantitative",
                                "label": "误差 (mm)",
                                "format": "number",
                            }
                        ],
                    },
                },
                {
                    "id": "camera_error_chart",
                    "title": "相机坐标系内新 PnP 与旧 2D 位移差异",
                    "subtitle": "差异显著小于机器人坐标输出，说明检测/PnP 不是主因。",
                    "type": "bar",
                    "dataset": "camera_errors",
                    "valueFormat": "number",
                    "encodings": {
                        "x": {"field": "axis", "type": "nominal", "label": "分量"},
                        "y": {
                            "field": "value_mm",
                            "type": "quantitative",
                            "label": "误差 (mm)",
                        },
                        "color": {"field": "stat", "type": "nominal", "label": "统计量"},
                    },
                },
            ],
            "tables": [
                {
                    "id": "largest_cases",
                    "title": "XY 差异最大的 15 组",
                    "subtitle": "新值按参考减当前统一为相对补偿口径。",
                    "dataset": "largest_cases",
                    "defaultSort": {"field": "translation_error_mm", "direction": "desc"},
                    "columns": [
                        {"field": "case", "label": "时间"},
                        {"field": "old_dx_mm", "label": "旧X(mm)", "format": "number"},
                        {"field": "old_dy_mm", "label": "旧Y(mm)", "format": "number"},
                        {"field": "new_dx_mm", "label": "新X(mm)", "format": "number"},
                        {"field": "new_dy_mm", "label": "新Y(mm)", "format": "number"},
                        {
                            "field": "translation_error_mm",
                            "label": "XY差(mm)",
                            "format": "number",
                        },
                        {
                            "field": "angle_error_deg",
                            "label": "角度差(°)",
                            "format": "number",
                        },
                    ],
                }
            ],
            "sources": [
                {
                    "id": "comparison_cases",
                    "label": "95 组离线重跑明细",
                    "path": "outputs/compensation_compare_20260723/comparison_cases.csv",
                },
                {
                    "id": "comparison_summary",
                    "label": "批量统计与诊断摘要",
                    "path": "outputs/compensation_compare_20260723/comparison_summary.json",
                },
                {
                    "id": "handeye_calibration",
                    "label": "当前完整 3D 手眼标定结果",
                    "path": "outputs/handeye_20260730/handeye_calibration_result.json",
                },
            ],
            "blocks": [
                {"id": "summary", "type": "markdown", "body": markdown["summary"]},
                {"id": "metrics", "type": "metric-strip", "cardIds": ["quality_card"]},
                {"id": "method", "type": "markdown", "body": markdown["method"]},
                {"id": "robot_chart", "type": "chart", "chartId": "robot_error_chart"},
                {"id": "diagnosis", "type": "markdown", "body": markdown["diagnosis"]},
                {"id": "camera_chart", "type": "chart", "chartId": "camera_error_chart"},
                {"id": "recommendation", "type": "markdown", "body": markdown["recommendation"]},
                {"id": "limits", "type": "markdown", "body": markdown["limits"]},
                {"id": "table", "type": "table", "tableId": "largest_cases"},
            ],
        },
        "snapshot": {
            "version": 1,
            "generatedAt": generated_at,
            "status": "ready",
            "datasets": {
                "metrics": metrics,
                "robot_errors": error_rows,
                "camera_errors": camera_error_rows,
                "largest_cases": top_rows,
            },
            "accessIssues": [],
        },
        "sources": [
            {
                "id": "comparison_cases",
                "file": {
                    "path": "outputs/compensation_compare_20260723/comparison_cases.csv",
                    "description": "95 组新旧补偿逐项对比明细。",
                },
            },
            {
                "id": "comparison_summary",
                "file": {
                    "path": "outputs/compensation_compare_20260723/comparison_summary.json",
                    "description": "批量统计、相关性、拟合矩阵和失败记录。",
                },
            },
            {
                "id": "handeye_calibration",
                "file": {
                    "path": "outputs/handeye_20260730/handeye_calibration_result.json",
                    "description": "2026-07-30 生成的当前相机内参与 gTc。",
                },
            },
        ],
        "package_info": {
            "originUrl": "artifact://compensation-compare-20260723",
            "controls": {"edit": False, "refresh": False},
        },
    }
    artifact["manifest"].pop("cards", None)
    artifact["manifest"]["description"] = (
        "pkg5 完整 3D 补偿链在机器人基座坐标中的正确复核，含 Z 高度贡献诊断。"
    )
    artifact["manifest"]["charts"][0]["title"] = "基座坐标下新旧机器人 XY 残差"
    artifact["manifest"]["charts"][0]["subtitle"] = (
        "补上 bRg 和机器人反向补偿后，95 组样本的 MAE/RMSE；单位 mm。"
    )
    artifact["manifest"]["charts"][1]["title"] = "相机坐标下新 PnP 与旧动态比例尺残差"
    artifact["manifest"]["charts"][1]["subtitle"] = (
        "95 组参考-当前相对位移的 X/Y MAE 与 RMSE；单位 mm。"
    )
    artifact["manifest"]["charts"].append(
        {
            "id": "height_effect_chart",
            "title": "Z 高度差及其对机器人 XY 的耦合",
            "subtitle": "参考-当前 Z 与经 gTc 投影到 XY 的影响；95 组，单位 mm。",
            "type": "bar",
            "dataset": "height_effects",
            "valueFormat": "number",
            "encodings": {
                "x": {
                    "field": "component",
                    "type": "nominal",
                    "label": "分量",
                },
                "y": {
                    "field": "value_mm",
                    "type": "quantitative",
                    "label": "数值 (mm)",
                },
                "color": {
                    "field": "stat",
                    "type": "nominal",
                    "label": "统计量",
                },
                "tooltip": [
                    {
                        "field": "value_mm",
                        "type": "quantitative",
                        "label": "数值 (mm)",
                        "format": "number",
                    }
                ],
            },
        }
    )
    artifact["manifest"]["tables"][0]["title"] = "基座坐标残差最大的 15 组"
    artifact["manifest"]["tables"][0]["subtitle"] = (
        "新值为补上 bRg 后的机器人基座补偿；按 XY 差异降序。"
    )
    artifact["snapshot"]["datasets"]["height_effects"] = height_error_rows
    artifact["manifest"]["blocks"] = [
        {"id": "title", "type": "markdown", "body": markdown["title"]},
        {"id": "summary", "type": "markdown", "body": markdown["summary"]},
        {
            "id": "corrected_finding",
            "type": "markdown",
            "body": markdown["corrected_finding"],
        },
        {"id": "robot_chart", "type": "chart", "chartId": "robot_error_chart"},
        {
            "id": "height_finding",
            "type": "markdown",
            "body": markdown["height_finding"],
        },
        {"id": "height_chart", "type": "chart", "chartId": "height_effect_chart"},
        {"id": "scope", "type": "markdown", "body": markdown["scope"]},
        {"id": "method", "type": "markdown", "body": markdown["method"]},
        {
            "id": "pnp_validation",
            "type": "markdown",
            "body": markdown["pnp_validation"],
        },
        {"id": "camera_chart", "type": "chart", "chartId": "camera_error_chart"},
        {"id": "limits", "type": "markdown", "body": markdown["limits"]},
        {
            "id": "recommendation",
            "type": "markdown",
            "body": markdown["recommendation"],
        },
        {"id": "further", "type": "markdown", "body": markdown["further"]},
        {"id": "detail", "type": "markdown", "body": markdown["detail"]},
        {"id": "table", "type": "table", "tableId": "largest_cases"},
    ]
    widget_queries = {
        "robot_errors": "SELECT axis, stat, value_mm FROM robot_errors",
        "camera_errors": "SELECT axis, stat, value_mm FROM camera_errors",
        "height_effects": (
            "SELECT component, stat, value_mm FROM height_effects"
        ),
        "largest_cases": (
            "SELECT case, old_dx_mm, old_dy_mm, new_dx_mm, new_dy_mm, "
            "translation_error_mm, angle_error_deg FROM largest_cases "
            "ORDER BY translation_error_mm DESC LIMIT 15"
        ),
    }
    for chart in artifact["manifest"]["charts"]:
        chart["source"] = {"query": {"sql": widget_queries[chart["dataset"]]}}
    for table in artifact["manifest"]["tables"]:
        table["source"] = {"query": {"sql": widget_queries[table["dataset"]]}}
    artifact["manifest"]["blocks"] = [
        block
        for block in artifact["manifest"]["blocks"]
        if block["type"] != "metric-strip"
    ]
    (args.comparison_dir / "artifact.json").write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(args.comparison_dir / "artifact.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
