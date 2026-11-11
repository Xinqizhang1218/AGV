"""受限局部探索手眼标定。只新增文件，不启用/覆盖正式标定参数。

从 pkg5_260728 运行：
  python auto_handeye/main.py                 # 配置/候选策略预览，不联网
  python auto_handeye/main.py --self-test     # 离线故障与合成数据验证
  python auto_handeye/main.py --capture-current
  python auto_handeye/main.py --run --execute
  python auto_handeye/main.py --solve outputs任务目录
  python auto_handeye/main.py --run --execute --resume outputs任务目录 --confirm-same-setup

安装依赖沿用项目环境：numpy、opencv-contrib-python、PyYAML、requests、
pydantic、pymodbus；启用 arcs 时另装与控制器匹配的官方 pyaubo_sdk。
先填写 config.yaml 中的现场确认和范围。逆解不等同于路径碰撞检查。
只在共享图片目录可读时运行；不创建第二个相机句柄。
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import math
import sys
import time
import uuid
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import requests
import yaml

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from robot_client import RobotClient, check_target, matrix_pose, pose_error, pose_matrix
from agv_vision.config.settings import AppSettings, CharucoSettings
from agv_vision.core.exceptions import CalibrationError, DetectorError
from agv_vision.core.models import CharucoObservation, HandEyeSample
from agv_vision.vision.charuco_detector import CharucoBoardDetector
from agv_vision.vision.handeye_calibrator import PlanarHandEyeCalibrator
from agv_vision.vision.pose3d import robot_pose_to_transform, solve_charuco_poses


class CalibrationSettings(AppSettings):
    """Support both committed legacy charuco and newer separate board profiles."""
    handeye_charuco: CharucoSettings | None = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.handeye_charuco is None:
            self.handeye_charuco = self.charuco.model_copy(deep=True)


def write_json(path, payload):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    temporary.replace(path)


def positive(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} 必须为有限正数")


def load_config(path, live=False, moving=False):
    path = Path(path).resolve()
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    # Require explicit schema instead of silently accepting misspelled thresholds.
    template = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    if not isinstance(config, dict) or config.keys() != template.keys():
        raise ValueError("配置顶层字段与 config.yaml 不一致")
    for section, values in template.items():
        if not isinstance(config[section], dict) or config[section].keys() != values.keys():
            raise ValueError(f"配置字段不完整或拼写错误：{section}")
        for key, default in values.items():
            value = config[section][key]
            if isinstance(default, bool):
                if not isinstance(value, bool):
                    raise ValueError(f"{section}.{key} 必须是布尔值")
            elif isinstance(default, (float, int)):
                positive(value, f"{section}.{key}")
                if isinstance(default, int) and not isinstance(value, int):
                    raise ValueError(f"{section}.{key} 必须是整数")
            elif isinstance(default, str) and not isinstance(value, str):
                raise ValueError(f"{section}.{key} 必须是字符串")
    if config["ik"]["mode"] not in ("disabled", "arcs"):
        raise ValueError("ik.mode 只支持 disabled/arcs")
    if config["motion"]["poll_s"] > 0.2 or config["motion"]["stable_s"] < 0.5:
        raise ValueError("poll_s <= 0.2 且 stable_s >= 0.5")
    if any(config[section]["port"] > 65535 for section in ("motion", "ik")):
        raise ValueError("端口必须在 1-65535")
    for section, key in (("quality", "max_saturated_fraction"), ("quality", "min_hull_fraction"),
                         ("planner", "minimum_scale")):
        if config[section][key] > 1:
            raise ValueError(f"{section}.{key} 必须 <= 1")
    calibration = config["calibration"]
    if calibration["min_training_samples"] < 5 or calibration["min_validation_samples"] < 2 or calibration["validation_every"] < 2:
        raise ValueError("训练样本至少5，预留验证至少2，validation_every至少2")
    if calibration["required_stable_updates"] < 2:
        raise ValueError("至少需要两次不同训练集的稳定更新")
    if config["planner"]["max_samples"] < calibration["min_training_samples"] + calibration["min_validation_samples"]:
        raise ValueError("max_samples 小于要求的训练和验证数量")
    bounds = config["limits"]["pose_bounds"]
    if bounds is not None:
        array = np.asarray(bounds, dtype=float)
        if array.shape != (6, 2) or not np.isfinite(array).all() or np.any(array[:, 0] >= array[:, 1]):
            raise ValueError("pose_bounds 必须为六组有限的递增上下限")
    config["vision"]["settings_path"] = str((path.parent / config["vision"]["settings_path"]).resolve())
    if live:
        for section, keys in {
            "vision": ("settings_match_confirmed", "fresh_capture_confirmed"),
            "motion": ("flange_pose_confirmed", "exclusive_control_confirmed"),
        }.items():
            for key in keys:
                if config[section][key] is not True:
                    raise ValueError(f"现场配置未确认：{section}.{key}")
        if not config["motion"]["ip"]:
            raise ValueError("请填写 PLC IP")
        for key in ("server_image_dir", "local_image_dir"):
            if not config["vision"][key]:
                raise ValueError(f"请填写共享图片目录 vision.{key}")
        if not Path(config["vision"]["local_image_dir"]).is_absolute():
            raise ValueError("local_image_dir 必须是绝对路径")
        if not Path(config["vision"]["local_image_dir"]).is_dir():
            raise ValueError("共享图片目录不存在")
    if moving:
        if bounds is None:
            raise ValueError("自动运动必须先填写 pose_bounds")
        for key in ("single_pose_handshake_confirmed", "local_paths_verified"):
            if config["motion"][key] is not True:
                raise ValueError(f"自动运动尚未确认 motion.{key}")
        if config["ik"]["mode"] == "arcs":
            if not config["ik"]["sdk_convention_confirmed"] or not config["ik"]["ip"] or not config["ik"]["robot_name"]:
                raise ValueError("ARCS 版本/坐标约定和连接参数未确认")
    return config


def make_calibrator(settings):
    intrinsics = settings.camera.intrinsics
    if not intrinsics.enabled:
        return PlanarHandEyeCalibrator()
    return PlanarHandEyeCalibrator(
        camera_matrix=intrinsics.camera_matrix, dist_coeffs=intrinsics.dist_coeffs,
        image_size=intrinsics.image_size, calibration_rms_px=intrinsics.calibration_rms_px,
        intrinsics_source=intrinsics.source)


def sample_from_record(record):
    payload = dict(record["sample"])
    payload["observation"] = CharucoObservation(**payload["observation"])
    return HandEyeSample(**payload)


def evaluate_image(image, observation, board, quality):
    """Use a planar homography to check the OUTER board, including unseen margins."""
    points = np.asarray(observation.image_points, np.float32)
    objects = np.asarray(observation.board_points_m, np.float32)
    height, width = image.shape[:2]
    metrics = {"corner_count": len(points)}
    reasons = []
    if len(points) < quality["min_corners"]:
        reasons.append("角点不足")
    homography, _ = cv2.findHomography(objects, points, 0)
    if homography is None or not np.isfinite(homography).all():
        return False, ["角点分布退化，无法估计整板轮廓"], metrics
    outer = np.float32([[0, 0], [board.squares_x * board.square_length_m, 0],
                        [board.squares_x * board.square_length_m, board.squares_y * board.square_length_m],
                        [0, board.squares_y * board.square_length_m]])
    projected = cv2.perspectiveTransform(outer.reshape(1, -1, 2), homography).reshape(-1, 2)
    if not np.isfinite(projected).all() or np.max(np.abs(projected)) > 1e7:
        return False, ["整板投影异常"], metrics
    margin = float(min(projected[:, 0].min(), projected[:, 1].min(),
                       width - 1 - projected[:, 0].max(), height - 1 - projected[:, 1].max()))
    hull_fraction = float(cv2.contourArea(cv2.convexHull(points)) / (width * height))
    metrics.update(border_px=margin, hull_fraction=hull_fraction,
                   center_normalized=(points.mean(axis=0) / [width, height]).tolist())
    if margin < quality["min_border_px"]:
        reasons.append("整板靠近边缘或出画")
    if hull_fraction < quality["min_hull_fraction"]:
        reasons.append("角点覆盖过小")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mask = np.zeros_like(gray)
    cv2.fillConvexPoly(mask, cv2.convexHull(points).astype(np.int32), 255)
    pixels = mask > 0
    if not pixels.any():
        return False, ["标定板区域无效"], metrics
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F)[pixels].var())
    saturation = float(np.mean(gray[pixels] >= 250))
    metrics.update(laplacian_variance=sharpness, saturated_fraction=saturation)
    if sharpness < quality["min_laplacian_variance"]:
        reasons.append("板区域模糊")
    if saturation > quality["max_saturated_fraction"]:
        reasons.append("板区域高亮比例过大")
    return not reasons, reasons, metrics


class VisionClient:
    def __init__(self, config, settings):
        self.config = config
        self.settings = settings
        self.http = requests.Session()
        self.detector = CharucoBoardDetector(settings.handeye_charuco)

    def check(self):
        response = self.http.get(self.config["vision"]["base_url"].rstrip("/") + "/health",
                                 timeout=self.config["vision"]["timeout_s"])
        response.raise_for_status()
        health = response.json()
        if health.get("ok") is not True or health.get("mode") != "online":
            raise RuntimeError("视觉服务未处于 online 模式")
        return health

    def capture(self, sample_id, actual_pose):
        vision = self.config["vision"]
        filename = f"{sample_id}_{uuid.uuid4().hex}.png"
        local_path = Path(vision["local_image_dir"]) / filename
        server_path = vision["server_image_dir"].rstrip("/\\") + "/" + filename
        for index in range(vision["discard_frames"] + 1):
            image_path = server_path if index == vision["discard_frames"] else server_path + f".discard{index}.png"
            response = self.http.post(vision["base_url"].rstrip("/") + "/api/v1/agv/photo",
                                      json={"data": {"imagePath": image_path}}, timeout=vision["timeout_s"])
            response.raise_for_status()
            payload = response.json()
            if payload.get("code") != 0:
                raise RuntimeError(f"拍照接口失败：{payload.get('msg')}")
        if not local_path.is_file():
            raise RuntimeError(f"共享目录未找到本次图片：{local_path}")
        image = cv2.imdecode(np.fromfile(local_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise RuntimeError("本次图片无法解码")
        try:
            observation = self.detector.detect(image)
        except DetectorError as exc:
            return {"accepted": False, "reasons": [str(exc)], "image_path": str(local_path)}
        accepted, reasons, metrics = evaluate_image(image, observation, self.settings.handeye_charuco, self.config["quality"])
        sample = HandEyeSample(sample_id, actual_pose[0], actual_pose[1], observation,
                               image_path=str(local_path), meta={
                                   **dict(zip(("z", "rx", "ry", "rz"), actual_pose[2:])),
                                   "image_width_px": image.shape[1], "image_height_px": image.shape[0]})
        return {"accepted": accepted, "reasons": reasons, "metrics": metrics,
                "sample": asdict(sample), "image_path": str(local_path), "server_image_path": server_path}


def duplicate(pose, records, config):
    planner = config["planner"]
    return any(position < planner["duplicate_translation_m"] and angle < planner["duplicate_rotation_deg"]
               for position, angle in (pose_error(pose, record["actual_pose"]) for record in records))


def choose_candidate(state, current, config, board):
    planner = config["planner"]
    accepted = state["samples"]
    candidates = []
    reference_rotation = pose_matrix(state["anchor"])[:3, :3]
    rotation_vectors = np.array([
        cv2.Rodrigues(reference_rotation.T @ pose_matrix(item["actual_pose"])[:3, :3])[0].ravel()
        / math.radians(planner["rotation_step_deg"]) for item in accepted])
    rotation_mean = rotation_vectors.mean(axis=0)
    centered = rotation_vectors - rotation_mean
    information = centered.T @ centered + np.eye(3) * 0.25
    information_logdet = np.linalg.slogdet(information)[1]
    # Expand from known usable samples, but never exceed the current step limit.
    for record in accepted:
        origin = record["actual_pose"]
        for axis in range(6):
            for sign in (-1, 1):
                direction = f"{axis}:{sign}"
                scale = state["scales"].get(direction, 1.0)
                if scale < planner["minimum_scale"]:
                    continue
                key = f"{record['id']}:{direction}:{scale:.6f}"
                if key in state["tried"]:
                    continue
                target_matrix = pose_matrix(origin)
                step = planner["translation_step_m"] if axis < 3 else math.radians(planner["rotation_step_deg"])
                if axis < 3:
                    target_matrix[axis, 3] += sign * step * scale
                else:
                    rotation_vector = np.zeros(3)
                    rotation_vector[axis - 3] = sign * step * scale
                    target_matrix[:3, :3] = target_matrix[:3, :3] @ cv2.Rodrigues(rotation_vector)[0]
                try:
                    target = matrix_pose(target_matrix)
                    # Keep Euler representation near the current pose (not a 2*pi jump).
                    for index in range(3, 6):
                        target[index] += 2 * math.pi * round((current[index] - target[index]) / (2 * math.pi))
                    check_target(target, current, state["anchor"], config["limits"])
                except ValueError:
                    continue
                if duplicate(target, accepted, config):
                    continue
                novelty = min(position / planner["translation_step_m"] + angle / planner["rotation_step_deg"]
                              for position, angle in (pose_error(target, item["actual_pose"]) for item in accepted))
                axis_count = sum(item.get("axis") == axis for item in accepted)
                score = novelty + (2.0 if axis >= 3 else 0.5) / (1 + axis_count)
                vector = cv2.Rodrigues(reference_rotation.T @ target_matrix[:3, :3])[0].ravel()
                delta = vector / math.radians(planner["rotation_step_deg"]) - rotation_mean
                expanded = information + len(accepted) / (len(accepted) + 1) * np.outer(delta, delta)
                score += 3.0 * (np.linalg.slogdet(expanded)[1] - information_logdet)
                prediction = state.get("prediction")
                if prediction and state.get("stable_updates", 0) >= 1:
                    camera_from_board = np.linalg.inv(target_matrix @ np.array(prediction["gTc"])) @ np.array(prediction["bTt"])
                    corners = np.float32([[0, 0, 0], [board.squares_x * board.square_length_m, 0, 0],
                                          [board.squares_x * board.square_length_m, board.squares_y * board.square_length_m, 0],
                                          [0, board.squares_y * board.square_length_m, 0]])
                    camera_points = (camera_from_board[:3, :3] @ corners.T).T + camera_from_board[:3, 3]
                    if np.any(camera_points[:, 2] <= 0):
                        continue
                    projected, _ = cv2.projectPoints(corners, cv2.Rodrigues(camera_from_board[:3, :3])[0],
                                                    camera_from_board[:3, 3], np.array(prediction["cameraMatrix"]),
                                                    np.array(prediction["distCoeffs"]))
                    points = projected.reshape(-1, 2)
                    width, height = prediction["image_size"]
                    margin = config["quality"]["min_border_px"]
                    if not np.isfinite(points).all() or np.any(points < margin) or np.any(points > [width - margin, height - margin]):
                        continue
                    center = points.mean(axis=0) / [width, height]
                    centers = [item.get("metrics", {}).get("center_normalized", [0.5, 0.5]) for item in accepted]
                    score += min(float(np.linalg.norm(center - other)) for other in centers)
                travel, angle = pose_error(current, target)
                score -= 0.05 * (travel / planner["translation_step_m"] + angle / planner["rotation_step_deg"])
                candidates.append((score, {"key": key, "direction": direction, "axis": axis, "pose": target}))
    return max(candidates, key=lambda item: item[0])[1] if candidates else None


def rotation_excitation(samples):
    reference = robot_pose_to_transform(samples[0])[:3, :3]
    vectors = np.array([cv2.Rodrigues(reference.T @ robot_pose_to_transform(sample)[:3, :3])[0].ravel()
                        for sample in samples])
    singular = np.linalg.svd(vectors - vectors.mean(axis=0), compute_uv=False) / math.sqrt(len(samples))
    return math.degrees(float(singular[1]))


def solve_records(records, settings, config):
    training = [sample_from_record(item) for item in records if item["role"] == "training"]
    validation = [sample_from_record(item) for item in records if item["role"] == "validation"]
    thresholds = config["calibration"]
    if len(training) < thresholds["min_training_samples"]:
        raise CalibrationError("训练样本数量不足")
    excitation = rotation_excitation(training)
    if excitation < thresholds["min_rotation_excitation_deg"]:
        raise CalibrationError(f"独立旋转方向不足，第二主方向 {excitation:.3f}deg")
    result = asdict(make_calibrator(settings).solve(training))
    pose3d = result["angle_calibration"]["pose3d"]
    camera_matrix = np.array(pose3d["cameraMatrix"])
    distortion = np.array(pose3d["distCoeffs"])
    gtc = np.array(pose3d["gTc"])
    all_samples = training + validation
    camera_poses = solve_charuco_poses(all_samples, camera_matrix, distortion)
    board_poses = [robot_pose_to_transform(sample) @ gtc @ camera_pose
                   for sample, camera_pose in zip(all_samples, camera_poses)]
    reference = np.eye(4)
    reference[:3, 3] = np.mean([pose[:3, 3] for pose in board_poses[:len(training)]], axis=0)
    u, _, vt = np.linalg.svd(sum(pose[:3, :3] for pose in board_poses[:len(training)]))
    reference[:3, :3] = u @ np.diag([1, 1, np.linalg.det(u @ vt)]) @ vt
    validation_errors = []
    reprojection_errors = []
    for index, (sample, camera_pose, board_pose) in enumerate(zip(all_samples, camera_poses, board_poses)):
        objects = np.array(sample.observation.marker_object_points_m, dtype=np.float32).reshape(-1, 3)
        image_points = np.array(sample.observation.marker_image_points, dtype=np.float32).reshape(-1, 2)
        projected, _ = cv2.projectPoints(objects, cv2.Rodrigues(camera_pose[:3, :3])[0], camera_pose[:3, 3], camera_matrix, distortion)
        rms = float(np.sqrt(np.mean(np.sum((projected.reshape(-1, 2) - image_points) ** 2, axis=1))))
        reprojection_errors.append(rms)
        if index >= len(training):
            validation_errors.append({"sample_id": sample.sample_id,
                                      "translation_m": float(np.linalg.norm(board_pose[:3, 3] - reference[:3, 3])),
                                      "rotation_deg": math.degrees(float(np.linalg.norm(cv2.Rodrigues(reference[:3, :3].T @ board_pose[:3, :3])[0])))})
    metrics = pose3d["handEyeCandidates"][pose3d["handEyeMethod"]]
    passed = (len(validation) >= thresholds["min_validation_samples"]
              and metrics["translationRmseM"] <= thresholds["max_translation_rmse_m"]
              and metrics["rotationRmseDeg"] <= thresholds["max_rotation_rmse_deg"]
              and max(reprojection_errors) <= thresholds["max_reprojection_px"]
              and all(item["translation_m"] <= thresholds["max_validation_translation_m"]
                      and item["rotation_deg"] <= thresholds["max_validation_rotation_deg"] for item in validation_errors))
    report = {"candidate": result, "quality_passed": bool(passed), "training_count": len(training),
              "validation_count": len(validation), "rotation_excitation_deg": excitation,
              "max_reprojection_px": max(reprojection_errors), "validation_errors": validation_errors,
              "independent_accuracy_verified": False}
    prediction = {"gTc": gtc.tolist(), "bTt": reference.tolist(), "cameraMatrix": camera_matrix.tolist(),
                  "distCoeffs": distortion.tolist(),
                  "image_size": [training[0].meta["image_width_px"], training[0].meta["image_height_px"]]}
    return report, prediction


def monitored_capture(robot, vision, target, sample_id):
    before = robot.verify(target, robot.held)
    error = None
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(vision.capture, sample_id, before)
        while not future.done():
            try:
                robot.verify(target, robot.held)
            except Exception as exc:
                error = exc
                break
            time.sleep(robot.motion["poll_s"])
        # Bounded HTTP requests finish before any subsequent motion is possible.
        result = future.result()
    if error:
        raise RuntimeError("采图期间位姿/握手异常，图像作废") from error
    after = robot.verify(target, robot.held)
    position, angle = pose_error(before, after)
    if position > robot.motion["position_tolerance_m"] or angle > robot.motion["rotation_tolerance_deg"]:
        raise RuntimeError("拍照前后位姿不一致，图像作废")
    result.update(actual_pose=before, actual_pose_after=after, captured_at=datetime.now().isoformat())
    return result


def update_solution(state, settings, config, output):
    training_count = sum(item["role"] == "training" for item in state["samples"])
    if training_count < config["calibration"]["min_training_samples"]:
        return False
    try:
        report, prediction = solve_records(state["samples"], settings, config)
    except CalibrationError as exc:
        state["solve_error"] = str(exc)
        state["stable_updates"] = 0
        state["prediction"] = None
        return False
    previous = state.get("prediction")
    thresholds = config["calibration"]
    if training_count != state.get("last_training_count"):
        is_stable = False
        if previous:
            delta = np.linalg.inv(np.array(previous["gTc"])) @ np.array(prediction["gTc"])
            is_stable = (np.linalg.norm(delta[:3, 3]) <= thresholds["max_solution_translation_change_m"]
                         and math.degrees(np.linalg.norm(cv2.Rodrigues(delta[:3, :3])[0])) <= thresholds["max_solution_rotation_change_deg"])
        state["stable_updates"] = state.get("stable_updates", 0) + 1 if is_stable else 0
        state["last_training_count"] = training_count
    state["prediction"] = prediction
    state["solve_error"] = None
    report["stable_updates"] = state.get("stable_updates", 0)
    report["passed"] = bool(report["quality_passed"] and report["stable_updates"] >= thresholds["required_stable_updates"])
    write_json(output / "handeye_candidate.json", report)
    state["latest_report"] = report
    return report["passed"]


def run_session(args, config, settings):
    fingerprint = hashlib.sha256((json.dumps(config, sort_keys=True) + json.dumps(settings.model_dump(), sort_keys=True)).encode()).hexdigest()
    if args.resume:
        output = Path(args.resume).resolve()
        state = json.loads((output / "session.json").read_text(encoding="utf-8"))
        if state["fingerprint"] != fingerprint:
            raise ValueError("配置/相机参数/标定板配置已变化，拒绝混用旧样本")
        if not state["samples"] or state["status"] == "passed":
            raise ValueError("无有效样本或任务已通过，请新建任务")
    else:
        output = ROOT / "outputs" / (datetime.now().strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8])
        output.mkdir(parents=True)
        state = {"fingerprint": fingerprint, "samples": [], "tried": [], "scales": {},
                 "attempts": 0, "stable_updates": 0, "elapsed_s": 0, "status": "created"}
        write_json(output / "config_snapshot.json", config)
        write_json(output / "vision_settings_snapshot.json", settings.model_dump())
    robot, vision = RobotClient(config), VisionClient(config, settings)
    started = time.monotonic()
    previous_elapsed = state.get("elapsed_s", 0)

    def persist(event):
        state["elapsed_s"] = previous_elapsed + time.monotonic() - started
        write_json(output / "session.json", state)
        with (output / "events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"time": datetime.now().isoformat(), **event}, ensure_ascii=False, allow_nan=False) + "\n")

    try:
        state["health"] = vision.check()
        robot.connect()
        current = robot.read_pose()
        if args.resume:
            check_target(current, current, state["anchor"], config["limits"])
            # No implicit recovery movement: operator restores last saved idle pose.
            distance, angle = pose_error(current, state["last_idle_pose"])
            if distance > config["motion"]["position_tolerance_m"] or angle > config["motion"]["rotation_tolerance_deg"]:
                raise ValueError("恢复前请人工核对并回到上次保存的空闲位置；程序不会自动回位")
            robot.anchor = state["anchor"]
        else:
            state["anchor"] = current
            if args.run:
                check_target(current, current, current, config["limits"])
        state["status"] = "running"
        state["last_idle_pose"] = current
        persist({"event": "start", "actual_pose": current})
        while True:
            if state["attempts"] >= config["planner"]["max_attempts"] or len(state["samples"]) >= config["planner"]["max_samples"]:
                state["status"] = "limit_reached_not_passed"
                break
            if previous_elapsed + time.monotonic() - started > config["planner"]["max_minutes"] * 60:
                state["status"] = "time_limit_not_passed"
                break
            candidate = None
            if state["samples"]:
                candidate = choose_candidate(state, current, config, settings.handeye_charuco)
                if candidate is None:
                    state["status"] = "no_candidate_not_passed"
                    break
                state["tried"].append(candidate["key"])
                state["attempts"] += 1
                persist({"event": "before_move", "candidate": candidate})
                moved, reason = robot.move(candidate["pose"])
                if not moved:
                    state["scales"][candidate["direction"]] = state["scales"].get(candidate["direction"], 1) * 0.5
                    persist({"event": "unreachable", "reason": reason, "candidate": candidate})
                    continue
                current = candidate["pose"]
            else:
                state["attempts"] += 1
            accepted = False
            for retry in range(config["quality"]["retries"] + 1):
                sample_id = f"p{state['attempts']:03d}_r{retry}"
                result = monitored_capture(robot, vision, current, sample_id)
                result.update(id=sample_id, target_pose=current, axis=candidate["axis"] if candidate else None)
                if result["accepted"] and duplicate(result["actual_pose"], state["samples"], config):
                    result.update(accepted=False, reasons=["与已有样本位姿重复"])
                persist({"event": "capture", "result": result})
                print(f"{sample_id}: {'接收' if result['accepted'] else '不接收'} {result['reasons']}", flush=True)
                if result["accepted"]:
                    result["role"] = "validation" if (len(state["samples"]) + 1) % config["calibration"]["validation_every"] == 0 else "training"
                    state["samples"].append(result)
                    accepted = True
                    break
                if result["reasons"] == ["与已有样本位姿重复"]:
                    break
            robot.release(current)
            current = robot.wait_stable(None, held=False)
            state["last_idle_pose"] = current
            if not accepted:
                if candidate:
                    state["scales"][candidate["direction"]] = state["scales"].get(candidate["direction"], 1) * 0.5
                else:
                    state["status"] = "initial_view_rejected"
                    break
            persist({"event": "idle", "actual_pose": current})
            if args.capture_current:
                state["status"] = "current_sample_saved" if accepted else "initial_view_rejected"
                break
            if accepted and update_solution(state, settings, config, output):
                state["status"] = "passed"
                break
    except BaseException as exc:
        state["status"] = "interrupted_requires_inspection"
        state["error"] = f"{type(exc).__name__}: {exc}"
        state["motion_result_may_be_unknown"] = robot.held
        persist({"event": "error", "error": state["error"]})
        raise
    finally:
        persist({"event": "end", "status": state["status"]})
        try:
            robot.close()
        finally:
            vision.http.close()
        print(f"状态: {state['status']}；数据: {output}", flush=True)
    return 0 if state["status"] in ("passed", "current_sample_saved") else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=ROOT / "config.yaml")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--run", action="store_true")
    modes.add_argument("--capture-current", action="store_true")
    modes.add_argument("--solve", type=Path, metavar="SESSION_DIR")
    modes.add_argument("--self-test", action="store_true")
    parser.add_argument("--execute", action="store_true", help="显式启用自动运动")
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--confirm-same-setup", action="store_true", help="恢复时确认相机、板和机器人基座安装均未改变")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.run and not args.execute:
        parser.error("自动运动必须同时提供 --run --execute")
    if args.execute and not args.run or args.resume and not args.run:
        parser.error("--execute/--resume 只能与 --run 一起使用")
    if args.resume and not args.confirm_same_setup:
        parser.error("恢复任务需要 --confirm-same-setup，并人工核对上次空闲位置")
    config = load_config(args.config, live=args.run or args.capture_current, moving=args.run)
    if args.solve:
        state = json.loads((args.solve / "session.json").read_text(encoding="utf-8"))
        # Offline re-solving uses original camera/board settings, not today's installation.
        saved_settings = CalibrationSettings(**json.loads((args.solve / "vision_settings_snapshot.json").read_text(encoding="utf-8")))
        saved_config = json.loads((args.solve / "config_snapshot.json").read_text(encoding="utf-8"))
        report, _ = solve_records(state["samples"], saved_settings, saved_config)
        report["passed"] = False
        report["note"] = "离线重算只报告质量，不证明连续更新稳定性或现场精度"
        path = args.solve / f"offline_candidate_{uuid.uuid4().hex[:8]}.json"
        write_json(path, report)
        print(path)
        return 0
    settings = CalibrationSettings.from_yaml(config["vision"]["settings_path"])
    if not args.run and not args.capture_current:
        print("预览模式：未连接 PLC/相机。候选由当前合格样本附近自动生成，不使用40点表。")
        print("运动范围:", config["limits"]["pose_bounds"])
        print("逆解模式:", config["ik"]["mode"])
        print("配置文件:", args.config.resolve())
        return 0
    return run_session(args, config, settings)


def self_test():
    """Meaningful offline tests live here to keep the requested three-file layout."""
    import copy
    import tempfile
    import unittest
    from unittest.mock import Mock, patch
    from robot_client import pose_words, words_pose

    class OfflineTests(unittest.TestCase):
        def setUp(self):
            self.config = load_config(ROOT / "config.yaml")
            self.config["limits"]["pose_bounds"] = [[-1, 1]] * 6

        def test_pose_and_units(self):
            pose = [0.12, -0.25, 0.3, 0.1, -0.2, 0.3]
            np.testing.assert_allclose(words_pose(pose_words(pose)), pose, atol=1e-7)
            np.testing.assert_allclose(pose_matrix(matrix_pose(pose_matrix(pose))), pose_matrix(pose), atol=1e-10)
            with self.assertRaises(ValueError):
                pose_matrix([float("nan")] * 6)
            with self.assertRaises(ValueError):
                check_target([0.5, 0, 0, 0, 0, 0], [0] * 6, [0] * 6, self.config["limits"])

        def test_planner_shrink_and_duplicates(self):
            state = {"samples": [{"id": "p0", "actual_pose": [0] * 6}], "anchor": [0] * 6,
                     "scales": {}, "tried": []}
            candidate = choose_candidate(state, [0] * 6, self.config, None)
            self.assertIsNotNone(candidate)
            state["tried"].append(candidate["key"])
            state["scales"][candidate["direction"]] = 0.5
            next_candidate = choose_candidate(state, [0] * 6, self.config, None)
            self.assertNotEqual(candidate["key"], next_candidate["key"])
            self.assertTrue(duplicate([0] * 6, state["samples"], self.config))

        def test_write_timeout_never_replayed(self):
            robot = RobotClient(self.config)
            robot.anchor = [0] * 6
            robot.wait_stable = Mock(return_value=[0] * 6)
            robot.verify = Mock(return_value=[0] * 6)
            robot.reachable = Mock(return_value=(True, "test"))
            robot.client = Mock()
            robot.client.write_registers.side_effect = TimeoutError("unknown")
            with self.assertRaises(TimeoutError):
                robot.move([0.005, 0, 0, 0, 0, 0])
            robot.client.write_registers.assert_called_once()
            robot.client.write_register.assert_not_called()

        def test_readback_blocks_start(self):
            robot = RobotClient(self.config)
            robot.anchor = [0] * 6
            robot.wait_stable = Mock(return_value=[0] * 6)
            robot.verify = Mock(return_value=[0] * 6)
            robot.reachable = Mock(return_value=(True, "test"))
            robot.client = Mock()
            robot.client.write_registers.return_value.isError.return_value = False
            robot.read_words = Mock(return_value=[0] * 12)
            with self.assertRaises(RuntimeError):
                robot.move([0.005, 0, 0, 0, 0, 0])
            robot.client.write_register.assert_not_called()

        def test_default_live_motion_blocked(self):
            with self.assertRaises(ValueError):
                load_config(ROOT / "config.yaml", live=True, moving=True)

        def test_camera_drift_rejects_sample(self):
            robot = Mock()
            robot.held = False
            robot.motion = self.config["motion"]
            robot.verify.side_effect = [[0] * 6, RuntimeError("drift"), RuntimeError("drift")]
            vision = Mock()
            vision.capture.return_value = {"accepted": True}
            with self.assertRaises(RuntimeError):
                monitored_capture(robot, vision, [0] * 6, "test")

        def test_ik_failure_does_not_write(self):
            robot = RobotClient(self.config)
            robot.anchor = [0] * 6
            robot.wait_stable = Mock(return_value=[0] * 6)
            robot.reachable = Mock(return_value=(False, "unreachable"))
            robot.client = Mock()
            self.assertFalse(robot.move([0.005, 0, 0, 0, 0, 0])[0])
            robot.client.write_registers.assert_not_called()
            robot.client.write_register.assert_not_called()

        def test_motion_start_timeout_preserves_unknown_state(self):
            robot = RobotClient(self.config)
            robot.anchor = [0] * 6
            robot.wait_stable = Mock(return_value=[0] * 6)
            robot.verify = Mock(return_value=[0] * 6)
            robot.reachable = Mock(return_value=(True, "test"))
            robot.client = Mock()
            robot.client.write_registers.return_value.isError.return_value = False
            target = [0.005, 0, 0, 0, 0, 0]
            robot.read_words = Mock(return_value=pose_words(target))
            robot.client.write_register.side_effect = TimeoutError("unknown")
            with self.assertRaises(TimeoutError):
                robot.move(target)
            self.assertTrue(robot.held)
            robot.close()
            robot.client.write_register.assert_called_once_with(address=1002, value=1)

        def test_orchestration_limits_and_audit(self):
            config = copy.deepcopy(self.config)
            config["planner"]["max_attempts"] = 4
            settings = CalibrationSettings.from_yaml(config["vision"]["settings_path"])
            fake_robot = Mock()
            fake_robot.held = False
            fake_robot.motion = config["motion"]
            current = [0.] * 6
            fake_robot.read_pose.side_effect = lambda: current.copy()
            fake_robot.wait_stable.side_effect = lambda *a, **k: current.copy()
            fake_robot.verify.side_effect = lambda *a, **k: current.copy()

            def move(target):
                current[:] = target
                fake_robot.held = True
                return True, "mock"

            def release(target):
                fake_robot.held = False

            fake_robot.move.side_effect = move
            fake_robot.release.side_effect = release
            fake_vision = Mock()
            fake_vision.check.return_value = {"ok": True, "mode": "mock"}
            fake_vision.capture.side_effect = lambda sample_id, pose: {
                "accepted": True, "reasons": [], "sample": {}, "metrics": {}}
            args = argparse.Namespace(resume=None, run=True, capture_current=False)
            with tempfile.TemporaryDirectory() as temporary:
                module = sys.modules[__name__]
                with patch.object(module, "ROOT", Path(temporary)), patch.object(module, "RobotClient", return_value=fake_robot), patch.object(module, "VisionClient", return_value=fake_vision):
                    self.assertEqual(run_session(args, config, settings), 2)
                session_file = next(Path(temporary).glob("outputs/*/session.json"))
                state = json.loads(session_file.read_text(encoding="utf-8"))
                self.assertEqual(state["status"], "limit_reached_not_passed")
                self.assertEqual(len(state["samples"]), 4)
                self.assertEqual(fake_robot.move.call_count, 3)
                self.assertTrue(session_file.with_name("events.jsonl").exists())

        def test_image_border_and_blur(self):
            settings = CalibrationSettings.from_yaml(self.config["vision"]["settings_path"])
            detector = CharucoBoardDetector(settings.handeye_charuco)
            board_image = detector.board.generateImage((800, 600), marginSize=30)
            image = cv2.cvtColor(board_image, cv2.COLOR_GRAY2BGR)
            observation = detector.detect(image)
            quality = copy.deepcopy(self.config["quality"])
            quality["max_saturated_fraction"] = 0.99
            passed, reasons, _ = evaluate_image(image, observation, settings.handeye_charuco, quality)
            self.assertTrue(passed, reasons)
            quality["min_border_px"] = 200
            self.assertFalse(evaluate_image(image, observation, settings.handeye_charuco, quality)[0])
            quality["min_border_px"] = 1
            blurred = np.full_like(image, 128)
            self.assertIn("板区域模糊", evaluate_image(blurred, observation, settings.handeye_charuco, quality)[1])

        def test_synthetic_handeye_and_heldout_failure(self):
            settings = CalibrationSettings.from_yaml(self.config["vision"]["settings_path"])
            camera_matrix = np.array([[900., 0, 640], [0, 900., 480], [0, 0, 1]])
            settings.camera.intrinsics.enabled = True
            settings.camera.intrinsics.camera_matrix = camera_matrix.tolist()
            settings.camera.intrinsics.dist_coeffs = [0.] * 5
            settings.camera.intrinsics.image_size = [1280, 960]
            settings.camera.intrinsics.calibration_rms_px = 0.0
            detector = CharucoBoardDetector(settings.handeye_charuco)
            objects = detector.board.getChessboardCorners()
            marker_objects = np.array(detector.board.getObjPoints())
            gtc = pose_matrix([0.025, -0.015, 0.045, 0.05, -0.08, 0.03])
            btt = pose_matrix([0, 0, 0.7, 0, 0, 0])
            records = []
            planner_state = {"samples": records, "anchor": [0.] * 6, "scales": {}, "tried": []}
            pose = [0.] * 6
            for index in range(32):
                candidate = None
                if index:
                    candidate = choose_candidate(planner_state, pose, self.config, settings.handeye_charuco)
                    self.assertIsNotNone(candidate)
                    planner_state["tried"].append(candidate["key"])
                    pose = candidate["pose"]
                ctt = np.linalg.inv(pose_matrix(pose) @ gtc) @ btt
                rotation = cv2.Rodrigues(ctt[:3, :3])[0]
                points = cv2.projectPoints(objects, rotation, ctt[:3, 3], camera_matrix, np.zeros(5))[0].reshape(-1, 2)
                markers = cv2.projectPoints(marker_objects.reshape(-1, 3), rotation, ctt[:3, 3], camera_matrix, np.zeros(5))[0].reshape(-1, 4, 2)
                observation = CharucoObservation(points.tolist(), objects[:, :2].tolist(), len(points),
                                                markers.tolist(), marker_objects.tolist(),
                                                detector.board.getIds().ravel().tolist(), list(range(len(points))))
                sample = HandEyeSample(str(index), pose[0], pose[1], observation,
                                       meta={**dict(zip(("z", "rx", "ry", "rz"), pose[2:])),
                                             "image_width_px": 1280, "image_height_px": 960})
                records.append({"sample": asdict(sample), "role": "validation" if index % 5 == 4 else "training",
                                "id": str(index), "actual_pose": pose, "axis": candidate["axis"] if candidate else None})
            report, _ = solve_records(records, settings, self.config)
            self.assertTrue(report["quality_passed"], report)
            np.testing.assert_allclose(report["candidate"]["angle_calibration"]["pose3d"]["gTc"], gtc, atol=1e-4)
            records[4]["sample"]["robot_x_m"] += 0.02
            report, _ = solve_records(records, settings, self.config)
            self.assertFalse(report["quality_passed"])
            self.assertFalse(report["independent_accuracy_verified"])

    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(OfflineTests))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"停止：{type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
