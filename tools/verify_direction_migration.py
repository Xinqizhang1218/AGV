from __future__ import annotations

import json
import math
from pathlib import Path

from agv_vision.config.settings import AppSettings
from agv_vision.core.image_io import read_image
from agv_vision.vision.aruco_detector import ArucoReferenceDetector


ROOT = Path(r"D:\code\AGV\pkg3_260522")
REQUEST_JSON = ROOT / "examples" / "拍照位姿" / "t_pose_eye_hand_request.json"
HANDEYE_RESULT_JSON = ROOT / "data" / "verify_handeye_20260626" / "handeye_result.json"
TEST_DIR = ROOT / "examples" / "拍照位姿" / "2026.626_test"
OUT_JSON = ROOT / "data" / "verify_direction_migration" / "direction_migration_result.json"


def normalize_angle_deg(angle: float) -> float:
    while angle > 180:
        angle -= 360
    while angle <= -180:
        angle += 360
    return float(angle)


def rmse(values: list[float]) -> float:
    if not values:
        return float("nan")
    return math.sqrt(sum(v * v for v in values) / len(values))


def main() -> int:
    with open(HANDEYE_RESULT_JSON, "r", encoding="utf-8") as f:
        handeye_result = json.load(f)
    with open(REQUEST_JSON, "r", encoding="utf-8") as f:
        request = json.load(f)

    angle_calibration = handeye_result["result"]["angle_calibration"]
    direction = float(angle_calibration["direction"])

    items = []
    for item in request["imagePointList"]:
        name = Path(item["imagePath"]).name
        if name.lower().startswith("626test"):
            path = TEST_DIR / name
            if path.exists():
                items.append(
                    {
                        "sampleId": item["sampleId"],
                        "imagePath": str(path),
                        "imageName": name,
                        "rz": float(item["rz"]),
                    }
                )

    if len(items) < 2:
        raise RuntimeError("测试集样本不足，至少需要 2 张 626test 图片")

    settings = AppSettings.from_yaml(ROOT / "agv_vision" / "config" / "settings.yaml")
    detector = ArucoReferenceDetector(settings.aruco)

    detected = []
    for item in items:
        image = read_image(item["imagePath"])
        if image is None:
            raise RuntimeError(f"图片读取失败: {item['imagePath']}")
        ref = detector.detect(image, station_id="direction_migration_test")
        detected.append({**item, "vision_angle": float(ref.board_angle_deg)})

    # 用第一张作为“跨机台基准图”
    base = detected[0]
    rows = []
    errors_with_handeye_direction: list[float] = []
    errors_with_inverse_direction: list[float] = []
    for cur in detected[1:]:
        dtheta_vision = normalize_angle_deg(base["vision_angle"] - cur["vision_angle"])
        dtheta_robot_actual = normalize_angle_deg(base["rz"] - cur["rz"])
        dtheta_robot_pred = normalize_angle_deg(direction * dtheta_vision)
        dtheta_robot_pred_inv = normalize_angle_deg(-direction * dtheta_vision)

        err = normalize_angle_deg(dtheta_robot_pred - dtheta_robot_actual)
        err_inv = normalize_angle_deg(dtheta_robot_pred_inv - dtheta_robot_actual)
        errors_with_handeye_direction.append(err)
        errors_with_inverse_direction.append(err_inv)

        rows.append(
            {
                "sampleId": cur["sampleId"],
                "imageName": cur["imageName"],
                "baseRzDeg": base["rz"],
                "curRzDeg": cur["rz"],
                "baseVisionDeg": base["vision_angle"],
                "curVisionDeg": cur["vision_angle"],
                "dthetaVisionDeg": dtheta_vision,
                "dthetaRobotActualDeg": dtheta_robot_actual,
                "dthetaRobotPredDeg": dtheta_robot_pred,
                "dthetaRobotPredDegInverseDirection": dtheta_robot_pred_inv,
                "errorDegUsingHandeyeDirection": err,
                "errorDegUsingInverseDirection": err_inv,
            }
        )

    rmse_forward = rmse(errors_with_handeye_direction)
    rmse_inverse = rmse(errors_with_inverse_direction)
    best = "handeye_direction" if rmse_forward <= rmse_inverse else "inverse_direction"

    print(f"角度迁移验证样本数: {len(detected)} (基准 + 对比 {len(detected)-1})")
    print(f"来自 ChArUco 手眼标定的 direction = {int(direction)}")
    print("-" * 110)
    print(f"{'sample':<8}{'dV(vision)':>12}{'dR(actual)':>12}{'pred(dir)':>12}{'err(dir)':>12}{'pred(-dir)':>12}{'err(-dir)':>12}")
    print("-" * 110)
    for r in rows:
        print(
            f"{r['sampleId']:<8}"
            f"{r['dthetaVisionDeg']:>12.3f}"
            f"{r['dthetaRobotActualDeg']:>12.3f}"
            f"{r['dthetaRobotPredDeg']:>12.3f}"
            f"{r['errorDegUsingHandeyeDirection']:>12.3f}"
            f"{r['dthetaRobotPredDegInverseDirection']:>12.3f}"
            f"{r['errorDegUsingInverseDirection']:>12.3f}"
        )
    print("-" * 110)
    print(f"RMSE using direction={int(direction)}   : {rmse_forward:.4f} deg")
    print(f"RMSE using direction={int(-direction)}  : {rmse_inverse:.4f} deg")
    print(f"best_direction_choice: {best}")

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    out = {
        "base_sample": base,
        "direction_from_handeye": int(direction),
        "rmse_using_handeye_direction_deg": rmse_forward,
        "rmse_using_inverse_direction_deg": rmse_inverse,
        "best_direction_choice": best,
        "rows": rows,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"结果已保存: {OUT_JSON}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
