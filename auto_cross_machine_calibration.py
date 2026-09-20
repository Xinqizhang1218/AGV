"""AUBO + 视觉服务跨机台自动补偿、移动与复拍验证。

本文件独立运行，不修改现有机械臂采图和视觉服务代码。机械臂握手沿用
``aubo_hik_capture_handshake_d1002.py`` 已验证的寄存器协议：

* D1020-D1031：六轴目标位姿，float32，低 word 在前；
* D1002：启动并保持，拍照完成后清零；
* D1012：到位反馈；
* D100-D111：实际六轴位姿。

视觉图像由现有 FastAPI 视觉服务采集，避免本程序和视觉服务同时独占海康相机。

典型用法：

1. 在基准机台采集跨机台基准并生成配置：

   python auto_cross_machine_calibration.py collect-reference ^
     --station-id station_001 ^
     --observation-pose -0.51485 0.00473 0.47268 -3.141 0 0.757 ^
     --handeye-json handeye_response.json ^
     --profile cross_machine_station_001.json ^
     --workspace-x -0.65 -0.35 --workspace-y -0.15 0.15 ^
     --workspace-z 0.35 0.60 ^
     --orientation-rx -3.20 -3.00 --orientation-ry -0.20 0.20 ^
     --orientation-rz 0.50 1.00 ^
     --confirm-single-pose-task ^
     --execute

2. 在目标机台自动执行“拍照 -> 补偿 -> 移动 -> 复拍 -> 残差验收”：

   python auto_cross_machine_calibration.py run ^
     --profile cross_machine_station_001.json ^
     --confirm-single-pose-task ^
     --execute

重要：

* 当前项目的 secondary_compensation 接口固定返回六轴增量；脚本只接受
  ``vision_response_pose_mode=delta``，不会猜测或切换响应语义。
* 必须显式传 ``--execute`` 才会连接 PLC 和下发运动。
* 默认用每轮运动前的实际位姿确认自动返回；如果 PLC 固定返回某个点，请在
  profile 的 ``motion.expected_return_pose`` 填入该六轴位姿。
* 异常时不会擅自清 D1002，因为清零可能触发返回动作；必须由现场人员核对。
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import struct
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import requests
from pymodbus.client import ModbusTcpClient


POSE_START_REGISTER = 1020
START_REGISTER = 1002
ARRIVAL_REGISTER = 1012
ACTUAL_POSE_START_REGISTER = 100
STATUS_START_REGISTER = 1008
STATUS_REGISTER_COUNT = 12
WORD_ORDER = "low_high"
POSE_FIELD_NAMES = ("x", "y", "z", "rx", "ry", "rz")
POSITION_UNIT = "m"
ORIENTATION_UNIT = "rad"
PROFILE_SCHEMA_VERSION = 1
MAX_SAFETY_POLL_SECONDS = 0.2
MIN_ARRIVAL_STABLE_SECONDS = 0.2
MIN_RETURN_STABLE_SECONDS = 0.2
MIN_PHOTO_HOLD_SECONDS = 0.5


@dataclass
class MotionConfig:
    plc_ip: str = "192.168.1.88"
    plc_port: int = 502
    plc_timeout_seconds: float = 3.0
    motion_timeout_seconds: float = 120.0
    return_timeout_seconds: float = 120.0
    poll_seconds: float = 0.10
    position_tolerance_m: float = 0.0005
    orientation_tolerance_deg: float = 0.2
    arrival_stable_seconds: float = 0.5
    return_stable_seconds: float = 0.5
    photo_hold_seconds: float = 2.0
    pose_verify_timeout_seconds: float = 3.0
    expected_return_pose: list[float] | None = None
    start_task_single_pose_confirmed: bool = False


@dataclass
class ConvergenceConfig:
    max_corrections: int = 3
    max_residual_position_m: float = 0.0005
    max_residual_orientation_deg: float = 0.2
    required_consecutive_passes: int = 2
    verification_interval_seconds: float = 0.5
    damping: float = 1.0


@dataclass
class SafetyConfig:
    max_step_translation_m: float = 0.05
    max_step_orientation_deg: float = 10.0
    max_total_translation_m: float = 0.08
    max_total_orientation_deg: float = 15.0
    workspace_limits_m: dict[str, list[float]] | None = None
    orientation_limits_rad: dict[str, list[float]] | None = None


@dataclass
class CalibrationProfile:
    station_id: str
    observation_pose: list[float]
    reference: dict[str, Any]
    handeye: dict[str, Any]
    vision_base_url: str = "http://127.0.0.1:8088"
    vision_response_pose_mode: str = "delta"
    vision_image_dir: str = "outputs/auto_cross_machine"
    motion: MotionConfig = field(default_factory=MotionConfig)
    convergence: ConvergenceConfig = field(default_factory=ConvergenceConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    schema_version: int = PROFILE_SCHEMA_VERSION
    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds")
    )


@dataclass
class CompensationResult:
    response_pose: list[float]
    target_pose: list[float]
    residual_position_m: float
    residual_orientation_deg: float
    task_id: str
    image_path: str
    raw_response: dict[str, Any]


def now_milliseconds() -> int:
    return int(time.time() * 1000)


def normalize_angle_rad(angle: float) -> float:
    return math.atan2(math.sin(angle), math.cos(angle))


def safe_path_component(value: str) -> str:
    safe_value = "".join(
        character
        if character.isalnum() or character in ("-", "_")
        else "_"
        for character in value
    )
    return safe_value or "unnamed"


def validate_pose(pose: list[float] | tuple[float, ...], name: str) -> list[float]:
    if len(pose) != 6:
        raise ValueError(f"{name} 必须包含 [X, Y, Z, RX, RY, RZ] 共 6 个数")
    values = [float(value) for value in pose]
    if not all(math.isfinite(value) for value in values):
        raise ValueError(f"{name} 包含 NaN 或 Inf")
    return values


def rotation_from_euler(angles: list[float] | tuple[float, ...]) -> np.ndarray:
    rx, ry, rz = angles
    sx, sy, sz = np.sin([rx, ry, rz])
    cx, cy, cz = np.cos([rx, ry, rz])
    rotation_x = np.array(
        [[1.0, 0.0, 0.0], [0.0, cx, -sx], [0.0, sx, cx]],
        dtype=np.float64,
    )
    rotation_y = np.array(
        [[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]],
        dtype=np.float64,
    )
    rotation_z = np.array(
        [[cz, -sz, 0.0], [sz, cz, 0.0], [0.0, 0.0, 1.0]],
        dtype=np.float64,
    )
    return rotation_z @ rotation_y @ rotation_x


def pose_errors(actual_pose: list[float], target_pose: list[float]) -> tuple[float, float]:
    actual = np.asarray(validate_pose(actual_pose, "actual_pose"), dtype=np.float64)
    target = np.asarray(validate_pose(target_pose, "target_pose"), dtype=np.float64)
    position_error = float(np.linalg.norm(actual[:3] - target[:3]))
    relative_rotation = (
        rotation_from_euler(actual[3:]).T
        @ rotation_from_euler(target[3:])
    )
    cosine = float(
        np.clip((np.trace(relative_rotation) - 1.0) / 2.0, -1.0, 1.0)
    )
    orientation_error_deg = float(np.degrees(np.arccos(cosine)))
    return position_error, orientation_error_deg


def float_to_words(value: float) -> list[int]:
    raw = struct.pack(">f", float(value))
    high_word, low_word = struct.unpack(">HH", raw)
    if WORD_ORDER == "low_high":
        return [low_word, high_word]
    if WORD_ORDER == "high_low":
        return [high_word, low_word]
    raise ValueError(f"未知 WORD_ORDER：{WORD_ORDER}")


def words_to_float(first_word: int, second_word: int) -> float:
    if WORD_ORDER == "low_high":
        low_word, high_word = first_word, second_word
    elif WORD_ORDER == "high_low":
        high_word, low_word = first_word, second_word
    else:
        raise ValueError(f"未知 WORD_ORDER：{WORD_ORDER}")
    return struct.unpack(">f", struct.pack(">HH", high_word, low_word))[0]


def pose_to_registers(pose: list[float]) -> list[int]:
    words: list[int] = []
    for value in validate_pose(pose, "pose"):
        words.extend(float_to_words(value))
    return words


def registers_to_pose(words: list[int]) -> list[float]:
    if len(words) != 12:
        raise RuntimeError(f"实际位姿需要 12 个 word，收到 {len(words)} 个")
    pose = [
        words_to_float(words[index], words[index + 1])
        for index in range(0, 12, 2)
    ]
    return validate_pose(pose, "PLC实际位姿")


def pose_to_api_dict(pose: list[float]) -> dict[str, float | str]:
    values = validate_pose(pose, "pose")
    result: dict[str, float | str] = {
        field_name: values[index]
        for index, field_name in enumerate(POSE_FIELD_NAMES)
    }
    result["translationUnit"] = POSITION_UNIT
    result["rotationUnit"] = ORIENTATION_UNIT
    return result


def api_dict_to_pose(payload: dict[str, Any], name: str) -> list[float]:
    if not isinstance(payload, dict):
        raise ValueError(f"{name} 必须是 JSON 对象")
    translation_unit = str(payload.get("translationUnit", POSITION_UNIT)).lower()
    rotation_unit = str(payload.get("rotationUnit", ORIENTATION_UNIT)).lower()
    if translation_unit != POSITION_UNIT:
        raise ValueError(f"{name}.translationUnit 必须是 m")
    if rotation_unit != ORIENTATION_UNIT:
        raise ValueError(f"{name}.rotationUnit 必须是 rad")
    try:
        pose = [float(payload[field_name]) for field_name in POSE_FIELD_NAMES]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{name} 必须包含有效的 x/y/z/rx/ry/rz") from exc
    return validate_pose(pose, name)


def resolve_delta_target_pose(
    current_pose: list[float],
    response_pose: list[float],
    damping: float,
) -> list[float]:
    current = validate_pose(current_pose, "current_pose")
    response = validate_pose(response_pose, "response_pose")
    if not 0.0 < damping <= 1.0:
        raise ValueError("damping 必须在 (0, 1] 范围内")

    target = [
        current[index] + response[index] * damping
        for index in range(6)
    ]

    for index in range(3, 6):
        target[index] = normalize_angle_rad(target[index])
    return validate_pose(target, "target_pose")


def unwrap_api_document(payload: Any, document_name: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError(f"{document_name} JSON 顶层必须是对象")
    if "code" in payload:
        try:
            code = int(payload["code"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{document_name}.code 无效") from exc
        if code != 0:
            raise ValueError(
                f"{document_name} 业务失败：code={code}, msg={payload.get('msg')}"
            )
        data = payload.get("data")
        if not isinstance(data, dict):
            raise ValueError(f"{document_name}.data 必须是对象")
        return data
    return payload


def extract_handeye_document(payload: Any) -> dict[str, Any]:
    document = unwrap_api_document(payload, "handeye")
    candidates = [
        document.get("handeye"),
        document.get("handEye"),
        document,
    ]
    handeye = next(
        (
            candidate
            for candidate in candidates
            if isinstance(candidate, dict)
            and isinstance(candidate.get("pose3d"), dict)
        ),
        None,
    )
    if handeye is None:
        raise ValueError("手眼 JSON 中没有找到 pose3d")
    pose3d = handeye["pose3d"]
    for field_name in ("cameraMatrix", "distCoeffs", "gTc"):
        if field_name not in pose3d:
            raise ValueError(f"handeye.pose3d 缺少 {field_name}")
    return handeye


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"JSON 文件不存在：{path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON 格式错误：{path}：{exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"JSON 顶层必须是对象：{path}")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def nested_dataclass(config_type: type, payload: Any, field_name: str) -> Any:
    if payload is None:
        return config_type()
    if not isinstance(payload, dict):
        raise ValueError(f"profile.{field_name} 必须是对象")
    try:
        return config_type(**payload)
    except TypeError as exc:
        raise ValueError(f"profile.{field_name} 字段无效：{exc}") from exc


def load_profile(path: Path) -> CalibrationProfile:
    payload = read_json(path)
    schema_version = int(payload.get("schema_version", 0))
    if schema_version != PROFILE_SCHEMA_VERSION:
        raise ValueError(
            f"profile.schema_version={schema_version}，"
            f"当前仅支持 {PROFILE_SCHEMA_VERSION}"
        )
    try:
        profile = CalibrationProfile(
            station_id=str(payload["station_id"]),
            observation_pose=validate_pose(
                payload["observation_pose"], "profile.observation_pose"
            ),
            reference=dict(payload["reference"]),
            handeye=extract_handeye_document(payload["handeye"]),
            vision_base_url=str(
                payload.get("vision_base_url", "http://127.0.0.1:8088")
            ),
            vision_response_pose_mode=str(
                payload.get("vision_response_pose_mode", "delta")
            ).lower(),
            vision_image_dir=str(
                payload.get(
                    "vision_image_dir",
                    "outputs/auto_cross_machine",
                )
            ),
            motion=nested_dataclass(
                MotionConfig, payload.get("motion"), "motion"
            ),
            convergence=nested_dataclass(
                ConvergenceConfig,
                payload.get("convergence"),
                "convergence",
            ),
            safety=nested_dataclass(
                SafetyConfig, payload.get("safety"), "safety"
            ),
            schema_version=schema_version,
            created_at=str(payload.get("created_at", "")),
        )
    except KeyError as exc:
        raise ValueError(f"profile 缺少字段：{exc.args[0]}") from exc
    validate_profile(profile)
    return profile


def validate_profile(profile: CalibrationProfile) -> None:
    if not profile.station_id.strip():
        raise ValueError("profile.station_id 不能为空")
    validate_pose(profile.observation_pose, "profile.observation_pose")
    if profile.vision_response_pose_mode != "delta":
        raise ValueError(
            "当前 secondary_compensation 接口只返回 delta；"
            "profile.vision_response_pose_mode 必须固定为 delta"
        )
    if not isinstance(profile.reference, dict) or not profile.reference:
        raise ValueError("profile.reference 不能为空")
    extract_handeye_document(profile.handeye)
    validate_motion_config(profile.motion)
    validate_convergence_config(profile.convergence)
    validate_safety_config(profile.safety)
    validate_absolute_target(
        profile.observation_pose,
        profile.safety,
        "profile.observation_pose",
    )
    if profile.motion.expected_return_pose is not None:
        validate_absolute_target(
            profile.motion.expected_return_pose,
            profile.safety,
            "motion.expected_return_pose",
        )


def validate_motion_config(motion: MotionConfig) -> None:
    if not 1 <= int(motion.plc_port) <= 65535:
        raise ValueError("motion.plc_port 必须在 1-65535 范围内")
    for name in (
        "plc_timeout_seconds",
        "motion_timeout_seconds",
        "return_timeout_seconds",
        "poll_seconds",
        "position_tolerance_m",
        "orientation_tolerance_deg",
        "pose_verify_timeout_seconds",
    ):
        if not math.isfinite(float(getattr(motion, name))) or float(
            getattr(motion, name)
        ) <= 0:
            raise ValueError(f"motion.{name} 必须是有限正数")
    if motion.poll_seconds > MAX_SAFETY_POLL_SECONDS:
        raise ValueError(
            "motion.poll_seconds 不能超过 "
            f"{MAX_SAFETY_POLL_SECONDS:.3f}s"
        )
    minimum_periods = {
        "arrival_stable_seconds": MIN_ARRIVAL_STABLE_SECONDS,
        "return_stable_seconds": MIN_RETURN_STABLE_SECONDS,
        "photo_hold_seconds": MIN_PHOTO_HOLD_SECONDS,
    }
    for name, minimum in minimum_periods.items():
        value = float(getattr(motion, name))
        if not math.isfinite(value) or value < minimum:
            raise ValueError(
                f"motion.{name} 不能小于 {minimum:.3f}s"
            )
    if motion.expected_return_pose is not None:
        motion.expected_return_pose = validate_pose(
            motion.expected_return_pose,
            "motion.expected_return_pose",
        )


def validate_convergence_config(convergence: ConvergenceConfig) -> None:
    if (
        isinstance(convergence.max_corrections, bool)
        or not isinstance(convergence.max_corrections, int)
        or convergence.max_corrections < 0
    ):
        raise ValueError("max_corrections 不能小于 0")
    if (
        isinstance(convergence.required_consecutive_passes, bool)
        or not isinstance(convergence.required_consecutive_passes, int)
        or convergence.required_consecutive_passes < 1
    ):
        raise ValueError("required_consecutive_passes 必须至少为 1")
    for name in (
        "max_residual_position_m",
        "max_residual_orientation_deg",
    ):
        value = float(getattr(convergence, name))
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"convergence.{name} 必须是有限正数")
    interval = float(convergence.verification_interval_seconds)
    if not math.isfinite(interval) or interval < 0:
        raise ValueError(
            "convergence.verification_interval_seconds 必须是有限非负数"
        )
    damping = float(convergence.damping)
    if not math.isfinite(damping) or not 0.0 < damping <= 1.0:
        raise ValueError("damping 必须在 (0, 1] 范围内")


def validate_safety_config(safety: SafetyConfig) -> None:
    for name in (
        "max_step_translation_m",
        "max_step_orientation_deg",
        "max_total_translation_m",
        "max_total_orientation_deg",
    ):
        value = float(getattr(safety, name))
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"safety.{name} 必须是有限正数")
    validate_workspace_limits(safety.workspace_limits_m)
    validate_orientation_limits(safety.orientation_limits_rad)


def validate_workspace_limits(
    workspace_limits_m: dict[str, list[float]] | None,
) -> None:
    if workspace_limits_m is None:
        raise ValueError(
            "safety.workspace_limits_m 不能为空；"
            "真实运动前必须配置 x/y/z 绝对安全范围"
        )
    if not isinstance(workspace_limits_m, dict):
        raise ValueError("workspace_limits_m 必须是对象")
    for axis in ("x", "y", "z"):
        limits = workspace_limits_m.get(axis)
        if (
            not isinstance(limits, list)
            or len(limits) != 2
            or not all(math.isfinite(float(value)) for value in limits)
            or float(limits[0]) >= float(limits[1])
        ):
            raise ValueError(
                f"workspace_limits_m.{axis} 必须是 [最小值, 最大值]"
            )


def validate_orientation_limits(
    orientation_limits_rad: dict[str, list[float]] | None,
) -> None:
    if orientation_limits_rad is None:
        raise ValueError(
            "safety.orientation_limits_rad 不能为空；"
            "真实运动前必须配置 rx/ry/rz 绝对安全范围"
        )
    if not isinstance(orientation_limits_rad, dict):
        raise ValueError("orientation_limits_rad 必须是对象")
    for axis in ("rx", "ry", "rz"):
        limits = orientation_limits_rad.get(axis)
        if (
            not isinstance(limits, list)
            or len(limits) != 2
            or not all(math.isfinite(float(value)) for value in limits)
            or float(limits[0]) >= float(limits[1])
        ):
            raise ValueError(
                f"orientation_limits_rad.{axis} 必须是 [最小值, 最大值]"
            )


def validate_absolute_target(
    target_pose: list[float],
    safety: SafetyConfig,
    target_name: str = "target_pose",
) -> None:
    pose = validate_pose(target_pose, target_name)
    validate_workspace_limits(safety.workspace_limits_m)
    validate_orientation_limits(safety.orientation_limits_rad)
    assert safety.workspace_limits_m is not None
    assert safety.orientation_limits_rad is not None
    for index, axis in enumerate(("x", "y", "z")):
        lower, upper = [
            float(value) for value in safety.workspace_limits_m[axis]
        ]
        if not lower <= pose[index] <= upper:
            raise RuntimeError(
                f"{target_name}.{axis}={pose[index]:.6f}m "
                f"超出绝对安全范围 [{lower:.6f}, {upper:.6f}]m"
            )
    for index, axis in enumerate(("rx", "ry", "rz"), start=3):
        lower, upper = [
            float(value) for value in safety.orientation_limits_rad[axis]
        ]
        if not lower <= pose[index] <= upper:
            raise RuntimeError(
                f"{target_name}.{axis}={pose[index]:.6f}rad "
                f"超出绝对安全范围 [{lower:.6f}, {upper:.6f}]rad"
            )


class RobotPLC:
    def __init__(self, config: MotionConfig, safety: SafetyConfig):
        self.config = config
        self.safety = safety
        self.client = ModbusTcpClient(
            config.plc_ip,
            port=config.plc_port,
            timeout=config.plc_timeout_seconds,
            retries=0,
        )
        self.is_connected = False
        self.is_start_asserted = False
        self.is_cycle_active = False

    @staticmethod
    def _check_result(result: Any, action: str) -> None:
        if result is None:
            raise RuntimeError(f"{action}：返回 None")
        if hasattr(result, "isError") and result.isError():
            raise RuntimeError(f"{action}失败：{result}")

    def connect(self) -> None:
        print(
            f"[PLC] 连接 {self.config.plc_ip}:{self.config.plc_port} ..."
        )
        if not self.client.connect():
            raise RuntimeError(
                f"无法连接 PLC：{self.config.plc_ip}:{self.config.plc_port}"
            )
        self.is_connected = True
        print("[PLC] Modbus TCP 连接成功")

    def close(self) -> None:
        try:
            self.client.close()
        finally:
            self.is_connected = False
            print("[PLC] 连接已关闭")

    def read_registers(self, address: int, count: int, action: str) -> list[int]:
        result = self.client.read_holding_registers(address=address, count=count)
        self._check_result(result, action)
        words = getattr(result, "registers", None)
        if words is None or len(words) != count:
            raise RuntimeError(f"{action}长度异常：{words}")
        return [int(word) for word in words]

    def read_start_signal(self) -> int:
        value = self.read_registers(
            START_REGISTER, 1, f"读取 D{START_REGISTER}"
        )[0]
        if value not in (0, 1):
            raise RuntimeError(f"D{START_REGISTER} 状态异常：{value}")
        return value

    def read_motion_status(self, allow_reset: bool = False) -> tuple[int, int]:
        words = self.read_registers(
            STATUS_START_REGISTER,
            STATUS_REGISTER_COUNT,
            "读取 D1008-D1019 状态",
        )
        reset_in_progress = words[1008 - STATUS_START_REGISTER]
        if reset_in_progress not in (0, 1):
            raise RuntimeError(f"D1008 状态异常：{reset_in_progress}")
        for address, description in (
            (1009, "任务暂停中"),
            (1018, "系统报警"),
            (1019, "机器人状态异常"),
        ):
            value = words[address - STATUS_START_REGISTER]
            if value != 0:
                raise RuntimeError(
                    f"{description}：D{address}={value}，停止自动标定"
                )
        if reset_in_progress and not allow_reset:
            raise RuntimeError("机器人复位中：D1008=1")
        arrived = words[ARRIVAL_REGISTER - STATUS_START_REGISTER]
        if arrived not in (0, 1):
            raise RuntimeError(f"D{ARRIVAL_REGISTER} 状态异常：{arrived}")
        return arrived, reset_in_progress

    def read_actual_pose(self) -> list[float]:
        return registers_to_pose(
            self.read_registers(
                ACTUAL_POSE_START_REGISTER,
                12,
                "读取 D100-D111 实际位姿",
            )
        )

    def ensure_idle(self) -> None:
        start_value = self.read_start_signal()
        arrived, reset_in_progress = self.read_motion_status(allow_reset=True)
        if start_value != 0:
            raise RuntimeError(
                f"D{START_REGISTER}={start_value}，禁止覆盖当前运动目标"
            )
        if arrived != 0:
            raise RuntimeError(
                f"D{ARRIVAL_REGISTER}={arrived}，上一轮到位反馈尚未撤销"
            )
        if reset_in_progress != 0:
            raise RuntimeError("D1008=1，机械臂仍在返回/复位过程中")

    def wait_for_idle_stability(self, action: str) -> list[float]:
        """确认空闲反馈和实际位姿连续稳定后，才允许写入下一目标。"""
        deadline = time.monotonic() + self.config.return_timeout_seconds
        stable_since: float | None = None
        stable_reference: list[float] | None = None
        last_state = "尚未读取"
        while time.monotonic() < deadline:
            self.ensure_idle()
            actual_pose = self.read_actual_pose()
            validate_absolute_target(
                actual_pose,
                self.safety,
                f"{action}.current_pose",
            )
            now = time.monotonic()
            if stable_reference is None:
                stable_reference = actual_pose
                stable_since = now
            position_change, orientation_change = pose_errors(
                actual_pose,
                stable_reference,
            )
            last_state = (
                f"位置变化={position_change:.6f}m, "
                f"姿态变化={orientation_change:.3f}deg"
            )
            if (
                position_change <= self.config.position_tolerance_m
                and orientation_change
                <= self.config.orientation_tolerance_deg
            ):
                if (
                    stable_since is not None
                    and now - stable_since
                    >= self.config.return_stable_seconds
                ):
                    print(f"[PLC] {action}空闲且位姿稳定：{last_state}")
                    return actual_pose
            else:
                stable_reference = actual_pose
                stable_since = now
            time.sleep(self.config.poll_seconds)
        raise RuntimeError(
            f"{action}等待空闲位姿稳定超时：{last_state}"
        )

    def write_pose(self, cycle_name: str, target_pose: list[float]) -> None:
        target = validate_pose(target_pose, "target_pose")
        validate_absolute_target(
            target,
            self.safety,
            f"{cycle_name}.target_pose",
        )
        words = pose_to_registers(target)
        print(
            f"[PLC] 写入 {cycle_name}："
            f"X={target[0]:.6f}, Y={target[1]:.6f}, Z={target[2]:.6f}, "
            f"RX={target[3]:.6f}, RY={target[4]:.6f}, RZ={target[5]:.6f}"
        )
        result = self.client.write_registers(
            address=POSE_START_REGISTER,
            values=words,
        )
        self._check_result(result, "写 D1020-D1031")
        self.verify_pose_words(words)

    def verify_pose_words(self, expected_words: list[int]) -> None:
        deadline = (
            time.monotonic() + self.config.pose_verify_timeout_seconds
        )
        while True:
            actual_words = self.read_registers(
                POSE_START_REGISTER,
                len(expected_words),
                "读回 D1020-D1031",
            )
            if actual_words == expected_words:
                print("[PLC] 目标位姿 12/12 word 读回一致")
                return
            if time.monotonic() >= deadline:
                differences = ", ".join(
                    f"D{POSE_START_REGISTER + index}: "
                    f"目标={expected}, 读回={actual}"
                    for index, (expected, actual) in enumerate(
                        zip(expected_words, actual_words)
                    )
                    if expected != actual
                )
                raise RuntimeError(f"目标位姿读回校验超时：{differences}")
            time.sleep(self.config.poll_seconds)

    def trigger_move(self) -> bool:
        if not self.config.start_task_single_pose_confirmed:
            raise RuntimeError(
                "尚未显式确认 D1002 只执行 D1020-D1031 单一目标；"
                "禁止启动可能包含 D1040-D1051 的未知任务"
            )
        arrived, _ = self.read_motion_status()
        saw_not_arrived = arrived == 0
        # 写运动启动请求的响应若丢失，PLC 是否收到请求是不确定的。
        # 因此在发送前就标记，异常时必须提示现场检查。
        self.is_cycle_active = True
        self.is_start_asserted = True
        result = self.client.write_register(address=START_REGISTER, value=1)
        self._check_result(result, "写 D1002=1")
        if self.read_start_signal() != 1:
            raise RuntimeError("D1002=1 写入后读回不一致")
        print("[PLC] D1002=1，开始运动并保持至视觉拍照完成")
        return saw_not_arrived

    def wait_for_arrival(
        self,
        cycle_name: str,
        target_pose: list[float],
        saw_not_arrived: bool,
    ) -> list[float]:
        deadline = time.monotonic() + self.config.motion_timeout_seconds
        stable_since: float | None = None
        next_log_time = 0.0
        last_state = "尚未读取"

        while time.monotonic() < deadline:
            if self.read_start_signal() != 1:
                raise RuntimeError(
                    f"{cycle_name} 等待到位期间 D1002 不再为 1"
                )
            arrived, _ = self.read_motion_status()
            actual_pose = self.read_actual_pose()
            position_error, orientation_error = pose_errors(
                actual_pose, target_pose
            )
            now = time.monotonic()
            if arrived == 0:
                saw_not_arrived = True
            is_at_target = (
                saw_not_arrived
                and arrived == 1
                and position_error <= self.config.position_tolerance_m
                and orientation_error <= self.config.orientation_tolerance_deg
            )
            last_state = (
                f"D1012={arrived}, 已见未到位={saw_not_arrived}, "
                f"位置误差={position_error:.6f}m, "
                f"姿态误差={orientation_error:.3f}deg"
            )
            if is_at_target:
                if stable_since is None:
                    stable_since = now
                if (
                    now - stable_since
                    >= self.config.arrival_stable_seconds
                ):
                    print(f"[PLC] {cycle_name} 已到位并稳定：{last_state}")
                    return actual_pose
            else:
                stable_since = None
            if now >= next_log_time:
                print(f"[PLC] 等待 {cycle_name} 到位：{last_state}")
                next_log_time = now + 1.0
            time.sleep(self.config.poll_seconds)

        raise RuntimeError(
            f"{cycle_name} 到位超时 "
            f"({self.config.motion_timeout_seconds:.1f}s)：{last_state}"
        )

    def wait_photo_hold(
        self,
        cycle_name: str,
        target_pose: list[float],
    ) -> list[float]:
        hold_started = time.monotonic()
        next_log_time = 0.0
        while True:
            now = time.monotonic()
            start_value = self.read_start_signal()
            arrived, _ = self.read_motion_status()
            actual_pose = self.read_actual_pose()
            position_error, orientation_error = pose_errors(
                actual_pose, target_pose
            )
            if start_value != 1 or arrived != 1:
                raise RuntimeError(
                    f"{cycle_name} 拍照保持状态丢失："
                    f"D1002={start_value}, D1012={arrived}"
                )
            if (
                position_error > self.config.position_tolerance_m
                or orientation_error > self.config.orientation_tolerance_deg
            ):
                raise RuntimeError(
                    f"{cycle_name} 拍照前已离开目标："
                    f"位置误差={position_error:.6f}m，"
                    f"姿态误差={orientation_error:.3f}deg"
                )
            elapsed = now - hold_started
            if elapsed >= self.config.photo_hold_seconds:
                print(
                    f"[PLC] {cycle_name} 已稳定保持 "
                    f"{self.config.photo_hold_seconds:.1f}s，可以拍照"
                )
                return actual_pose
            if now >= next_log_time:
                remaining = self.config.photo_hold_seconds - elapsed
                print(
                    f"[PLC] {cycle_name} 等待拍照，剩余 {remaining:.1f}s"
                )
                next_log_time = now + 0.5
            time.sleep(self.config.poll_seconds)

    def verify_held_pose(
        self,
        target_pose: list[float],
        action: str,
    ) -> list[float]:
        start_value = self.read_start_signal()
        arrived, _ = self.read_motion_status()
        actual_pose = self.read_actual_pose()
        position_error, orientation_error = pose_errors(
            actual_pose, target_pose
        )
        if start_value != 1 or arrived != 1:
            raise RuntimeError(
                f"{action}时握手异常：D1002={start_value}, D1012={arrived}"
            )
        if (
            position_error > self.config.position_tolerance_m
            or orientation_error > self.config.orientation_tolerance_deg
        ):
            raise RuntimeError(
                f"{action}时位姿偏离目标："
                f"位置误差={position_error:.6f}m，"
                f"姿态误差={orientation_error:.3f}deg"
            )
        return actual_pose

    def move_and_hold(
        self,
        cycle_name: str,
        target_pose: list[float],
    ) -> tuple[list[float], list[float]]:
        cycle_start_pose = self.wait_for_idle_stability(
            f"{cycle_name} 运动前"
        )
        return_pose = (
            validate_pose(
                self.config.expected_return_pose,
                "motion.expected_return_pose",
            )
            if self.config.expected_return_pose is not None
            else cycle_start_pose
        )
        return_source = (
            "配置的固定返回位姿"
            if self.config.expected_return_pose is not None
            else "本轮运动前实际位姿"
        )
        print(f"[PLC] {return_source}：{return_pose}")
        self.write_pose(cycle_name, target_pose)
        self.ensure_idle()
        saw_not_arrived = self.trigger_move()
        self.wait_for_arrival(cycle_name, target_pose, saw_not_arrived)
        actual_pose = self.wait_photo_hold(cycle_name, target_pose)
        return actual_pose, return_pose

    def release_and_wait_return(
        self,
        cycle_name: str,
        return_pose: list[float],
    ) -> list[float]:
        if not self.is_start_asserted:
            raise RuntimeError("当前未记录 D1002=1，拒绝发送清零")
        result = self.client.write_register(address=START_REGISTER, value=0)
        self._check_result(result, "写 D1002=0")
        if self.read_start_signal() != 0:
            raise RuntimeError("D1002=0 写入后读回不一致")
        self.is_start_asserted = False
        print(
            f"[PLC] {cycle_name} 拍照完成，D1002=0，"
            "等待返回本轮起始位姿"
        )

        deadline = time.monotonic() + self.config.return_timeout_seconds
        stable_since: float | None = None
        next_log_time = 0.0
        last_state = "尚未读取"
        while time.monotonic() < deadline:
            start_value = self.read_start_signal()
            arrived, reset_in_progress = self.read_motion_status(
                allow_reset=True
            )
            actual_pose = self.read_actual_pose()
            position_error, orientation_error = pose_errors(
                actual_pose, return_pose
            )
            now = time.monotonic()
            has_returned = (
                start_value == 0
                and arrived == 0
                and reset_in_progress == 0
                and position_error <= self.config.position_tolerance_m
                and orientation_error <= self.config.orientation_tolerance_deg
            )
            last_state = (
                f"D1002={start_value}, D1008={reset_in_progress}, "
                f"D1012={arrived}, 返回位置误差={position_error:.6f}m, "
                f"返回姿态误差={orientation_error:.3f}deg"
            )
            if has_returned:
                if stable_since is None:
                    stable_since = now
                if now - stable_since >= self.config.return_stable_seconds:
                    self.is_cycle_active = False
                    print(
                        f"[PLC] {cycle_name} 已自动返回并稳定：{last_state}"
                    )
                    return actual_pose
            else:
                stable_since = None
            if now >= next_log_time:
                print(f"[PLC] 等待 {cycle_name} 返回：{last_state}")
                next_log_time = now + 1.0
            time.sleep(self.config.poll_seconds)

        raise RuntimeError(
            f"{cycle_name} 自动返回超时 "
            f"({self.config.return_timeout_seconds:.1f}s)：{last_state}"
        )


class VisionClient:
    def __init__(self, base_url: str, timeout_seconds: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()

    def close(self) -> None:
        self.session.close()

    def health_check(self) -> dict[str, Any]:
        url = f"{self.base_url}/api/v1/health"
        try:
            response = self.session.get(url, timeout=self.timeout_seconds)
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise RuntimeError(f"视觉服务健康检查失败：{url}：{exc}") from exc
        data = unwrap_api_document(payload, "视觉健康检查")
        mode = str(data.get("mode") or "").strip().lower()
        if mode != "online":
            raise RuntimeError(
                "视觉服务不是 online 模式，禁止驱动真实 PLC："
                f"mode={mode or 'missing'}"
            )
        print(f"[VISION] 服务在线且模式为 online：{url}")
        return data

    def post_api(
        self,
        endpoint: str,
        body: dict[str, Any],
        action: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.post(
                url,
                json=body,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise RuntimeError(f"{action}请求失败：{url}：{exc}") from exc
        try:
            data = unwrap_api_document(payload, action)
        except ValueError as exc:
            raise RuntimeError(str(exc)) from exc
        return data, payload

    def collect_reference(
        self,
        station_id: str,
        image_path: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        body = {
            "sn": station_id,
            "timestamp": now_milliseconds(),
            "data": {
                "stationId": station_id,
                "imagePath": image_path,
            },
        }
        return self.post_api(
            "/api/v1/agv/cross_calibration",
            body,
            "跨机台基准采集",
        )

    def request_compensation(
        self,
        station_id: str,
        task_id: str,
        image_path: str,
        current_pose: list[float],
        handeye: dict[str, Any],
        reference: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        body = {
            "sn": station_id,
            "timestamp": now_milliseconds(),
            "data": {
                "stationId": station_id,
                "taskId": task_id,
                "imagePath": image_path,
                "currentFlangePose": pose_to_api_dict(current_pose),
                "handeye": handeye,
                "reference": reference,
            },
        }
        return self.post_api(
            "/api/v1/agv/secondary_compensation",
            body,
            "二次补偿",
        )


def execute_vision_request_while_monitoring(
    robot: RobotPLC,
    target_pose: list[float],
    action: str,
    request_callable: Any,
) -> Any:
    """HTTP 拍照期间持续轮询 PLC，任何离位都使本张结果无效。"""
    monitor_error: BaseException | None = None
    request_error: BaseException | None = None
    request_result: Any = None
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(request_callable)
        while True:
            if monitor_error is None:
                try:
                    robot.verify_held_pose(target_pose, f"{action}期间")
                except BaseException as exc:
                    monitor_error = exc
            if future.done():
                break
            time.sleep(robot.config.poll_seconds)
        try:
            request_result = future.result()
        except BaseException as exc:
            request_error = exc

    if monitor_error is not None:
        raise RuntimeError(
            f"{action}期间机械臂状态或位姿异常，本张图像作废："
            f"{type(monitor_error).__name__}: {monitor_error}"
        ) from monitor_error
    if request_error is not None:
        raise request_error
    return request_result


def validate_candidate_target(
    candidate_pose: list[float],
    current_pose: list[float],
    observation_pose: list[float],
    safety: SafetyConfig,
) -> None:
    validate_absolute_target(
        candidate_pose,
        safety,
        "candidate_target_pose",
    )
    step_position, step_orientation = pose_errors(
        current_pose, candidate_pose
    )
    total_position, total_orientation = pose_errors(
        observation_pose, candidate_pose
    )
    if step_position > safety.max_step_translation_m:
        raise RuntimeError(
            "视觉单步补偿超过安全阈值："
            f"{step_position:.6f}m > {safety.max_step_translation_m:.6f}m"
        )
    if step_orientation > safety.max_step_orientation_deg:
        raise RuntimeError(
            "视觉单步姿态补偿超过安全阈值："
            f"{step_orientation:.3f}deg > "
            f"{safety.max_step_orientation_deg:.3f}deg"
        )
    if total_position > safety.max_total_translation_m:
        raise RuntimeError(
            "累计目标偏离名义观察位姿超过安全阈值："
            f"{total_position:.6f}m > "
            f"{safety.max_total_translation_m:.6f}m"
        )
    if total_orientation > safety.max_total_orientation_deg:
        raise RuntimeError(
            "累计目标姿态偏离名义观察位姿超过安全阈值："
            f"{total_orientation:.3f}deg > "
            f"{safety.max_total_orientation_deg:.3f}deg"
        )

def build_compensation_result(
    profile: CalibrationProfile,
    data: dict[str, Any],
    raw_response: dict[str, Any],
    current_pose: list[float],
    task_id: str,
    image_path: str,
) -> CompensationResult:
    response_pose = api_dict_to_pose(
        data.get("targetFlangePose"),
        "response.data.targetFlangePose",
    )
    full_correction_target = resolve_delta_target_pose(
        current_pose,
        response_pose,
        1.0,
    )
    target_pose = resolve_delta_target_pose(
        current_pose,
        response_pose,
        profile.convergence.damping,
    )
    residual_position, residual_orientation = pose_errors(
        current_pose, full_correction_target
    )
    return CompensationResult(
        response_pose=response_pose,
        target_pose=target_pose,
        residual_position_m=residual_position,
        residual_orientation_deg=residual_orientation,
        task_id=str(data.get("taskId") or task_id),
        image_path=image_path,
        raw_response=raw_response,
    )


def is_converged(
    result: CompensationResult,
    convergence: ConvergenceConfig,
) -> bool:
    return (
        result.residual_position_m
        <= convergence.max_residual_position_m
        and result.residual_orientation_deg
        <= convergence.max_residual_orientation_deg
    )


def make_vision_image_path(
    profile: CalibrationProfile,
    run_id: str,
    sequence: int,
    label: str,
) -> str:
    filename = f"{sequence:02d}_{label}.jpg"
    return (
        Path(profile.vision_image_dir)
        / safe_path_component(profile.station_id)
        / run_id
        / filename
    ).as_posix()


def request_and_verify_compensation(
    profile: CalibrationProfile,
    robot: RobotPLC,
    vision: VisionClient,
    target_pose: list[float],
    run_id: str,
    sequence: int,
    label: str,
) -> tuple[CompensationResult, dict[str, Any]]:
    before_pose = robot.verify_held_pose(target_pose, "视觉拍照前")
    image_path = make_vision_image_path(
        profile, run_id, sequence, label
    )
    task_id = f"{profile.station_id}_{run_id}_{sequence:02d}_{label}"
    data, raw_response = execute_vision_request_while_monitoring(
        robot=robot,
        target_pose=target_pose,
        action="视觉补偿拍照",
        request_callable=lambda: vision.request_compensation(
            station_id=profile.station_id,
            task_id=task_id,
            image_path=image_path,
            current_pose=before_pose,
            handeye=profile.handeye,
            reference=profile.reference,
        ),
    )
    after_pose = robot.verify_held_pose(target_pose, "视觉拍照后")
    capture_position_error, capture_orientation_error = pose_errors(
        before_pose, after_pose
    )
    if (
        capture_position_error > profile.motion.position_tolerance_m
        or capture_orientation_error
        > profile.motion.orientation_tolerance_deg
    ):
        raise RuntimeError(
            "视觉拍照前后机械臂位姿变化超限："
            f"{capture_position_error:.6f}m, "
            f"{capture_orientation_error:.3f}deg"
        )
    result = build_compensation_result(
        profile=profile,
        data=data,
        raw_response=raw_response,
        current_pose=before_pose,
        task_id=task_id,
        image_path=image_path,
    )
    record = {
        "sequence": sequence,
        "label": label,
        "time": datetime.now().isoformat(timespec="microseconds"),
        "target_pose": target_pose,
        "actual_pose_before": before_pose,
        "actual_pose_after": after_pose,
        "capture_pose_change_m": capture_position_error,
        "capture_pose_change_deg": capture_orientation_error,
        "capture_validation": (
            "continuous_plc_polling_not_hardware_synchronized"
        ),
        "vision_response_pose_mode": profile.vision_response_pose_mode,
        "vision_response_pose": result.response_pose,
        "candidate_target_pose": result.target_pose,
        "residual_position_m": result.residual_position_m,
        "residual_orientation_deg": result.residual_orientation_deg,
        "passed": is_converged(result, profile.convergence),
        "task_id": result.task_id,
        "image_path": result.image_path,
        "raw_response": raw_response,
    }
    print(
        f"[VISION] {label} 残差："
        f"位置={result.residual_position_m * 1000.0:.3f}mm，"
        f"姿态={result.residual_orientation_deg:.3f}deg，"
        f"结果={'PASS' if record['passed'] else '需要继续补偿'}"
    )
    return result, record


def profile_to_dict(profile: CalibrationProfile) -> dict[str, Any]:
    return asdict(profile)


def collect_reference(args: argparse.Namespace) -> int:
    if not args.execute:
        raise ValueError(
            "未传 --execute：为防止误运动，本程序没有连接 PLC 或相机"
        )
    if not args.confirm_single_pose_task:
        raise ValueError(
            "未传 --confirm-single-pose-task："
            "尚未确认 D1002 只执行 D1020-D1031，禁止运动"
        )
    profile_path = Path(args.profile).expanduser().resolve()
    if profile_path.exists() and not args.overwrite:
        raise ValueError(
            f"配置已存在：{profile_path}；确认覆盖时传 --overwrite"
        )
    handeye = extract_handeye_document(
        read_json(Path(args.handeye_json).expanduser().resolve())
    )
    motion = MotionConfig(
        plc_ip=args.plc_ip,
        plc_port=args.plc_port,
        start_task_single_pose_confirmed=True,
    )
    safety = SafetyConfig(
        workspace_limits_m={
            "x": list(args.workspace_x),
            "y": list(args.workspace_y),
            "z": list(args.workspace_z),
        },
        orientation_limits_rad={
            "rx": list(args.orientation_rx),
            "ry": list(args.orientation_ry),
            "rz": list(args.orientation_rz),
        },
    )
    observation_pose = validate_pose(
        args.observation_pose, "observation_pose"
    )
    profile = CalibrationProfile(
        station_id=args.station_id,
        observation_pose=observation_pose,
        reference={},
        handeye=handeye,
        vision_base_url=args.vision_url,
        vision_response_pose_mode="delta",
        vision_image_dir=args.vision_image_dir,
        motion=motion,
        safety=safety,
    )
    validate_motion_config(motion)
    validate_safety_config(safety)
    validate_absolute_target(
        observation_pose,
        safety,
        "observation_pose",
    )

    robot = RobotPLC(motion, safety)
    vision = VisionClient(profile.vision_base_url)
    try:
        vision.health_check()
        robot.connect()
        cycle_name = "REFERENCE"
        _, return_pose = robot.move_and_hold(
            cycle_name, profile.observation_pose
        )
        before_pose = robot.verify_held_pose(
            profile.observation_pose, "基准拍照前"
        )
        image_path = (
            Path(profile.vision_image_dir)
            / safe_path_component(profile.station_id)
            / "reference.jpg"
        ).as_posix()
        reference, raw_response = execute_vision_request_while_monitoring(
            robot=robot,
            target_pose=profile.observation_pose,
            action="跨机台基准拍照",
            request_callable=lambda: vision.collect_reference(
                profile.station_id,
                image_path,
            ),
        )
        after_pose = robot.verify_held_pose(
            profile.observation_pose, "基准拍照后"
        )
        position_change, orientation_change = pose_errors(
            before_pose, after_pose
        )
        if (
            position_change > motion.position_tolerance_m
            or orientation_change > motion.orientation_tolerance_deg
        ):
            raise RuntimeError("基准拍照前后机械臂位姿变化超限")
        profile.reference = reference
        validate_profile(profile)
        robot.release_and_wait_return(cycle_name, return_pose)
        payload = profile_to_dict(profile)
        payload["reference_capture"] = {
            "actual_pose_before": before_pose,
            "actual_pose_after": after_pose,
            "image_path": image_path,
            "capture_validation": (
                "continuous_plc_polling_not_hardware_synchronized"
            ),
            "raw_response": raw_response,
        }
        write_json(profile_path, payload)
        print(f"[SYSTEM] 跨机台配置已保存：{profile_path}")
        return 0
    except BaseException:
        if robot.is_cycle_active:
            print(
                "[SAFETY] 运动循环未完整结束；D1002 或返回动作状态可能不确定。"
                "程序未追加任何运动指令，请现场确认机械臂状态。"
            )
        raise
    finally:
        vision.close()
        if robot.is_connected:
            robot.close()


def run_automatic_calibration(args: argparse.Namespace) -> int:
    if not args.execute:
        raise ValueError(
            "未传 --execute：为防止误运动，本程序没有连接 PLC 或相机"
        )
    if not args.confirm_single_pose_task:
        raise ValueError(
            "未传 --confirm-single-pose-task："
            "尚未确认 D1002 只执行 D1020-D1031，禁止运动"
        )
    profile_path = Path(args.profile).expanduser().resolve()
    profile = load_profile(profile_path)
    profile.motion.start_task_single_pose_confirmed = True
    if args.handeye_json:
        profile.handeye = extract_handeye_document(
            read_json(Path(args.handeye_json).expanduser().resolve())
        )
    if args.plc_ip:
        profile.motion.plc_ip = args.plc_ip
    if args.plc_port is not None:
        profile.motion.plc_port = args.plc_port
    if args.vision_url:
        profile.vision_base_url = args.vision_url
    validate_profile(profile)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = (
        Path(args.report).expanduser().resolve()
        if args.report
        else Path("outputs")
        / "auto_cross_machine"
        / safe_path_component(profile.station_id)
        / run_id
        / "calibration_report.json"
    )
    report: dict[str, Any] = {
        "schema_version": 1,
        "run_id": run_id,
        "station_id": profile.station_id,
        "profile_path": str(profile_path),
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "status": "RUNNING",
        "vision_response_pose_mode": profile.vision_response_pose_mode,
        "thresholds": asdict(profile.convergence),
        "safety": asdict(profile.safety),
        "observations": [],
    }

    robot = RobotPLC(profile.motion, profile.safety)
    vision = VisionClient(profile.vision_base_url)
    target_pose = list(profile.observation_pose)
    sequence = 0
    try:
        vision.health_check()
        robot.connect()
        print("=" * 78)
        print("跨机台自动补偿启动")
        print(f"机台：{profile.station_id}")
        print(f"名义观察位姿：{profile.observation_pose}")
        print(
            "收敛阈值："
            f"{profile.convergence.max_residual_position_m * 1000.0:.3f}mm, "
            f"{profile.convergence.max_residual_orientation_deg:.3f}deg"
        )
        print(
            f"最多补偿 {profile.convergence.max_corrections} 次，"
            f"连续复拍 {profile.convergence.required_consecutive_passes} "
            "次合格才通过"
        )
        print("=" * 78)

        for correction_index in range(
            profile.convergence.max_corrections + 1
        ):
            cycle_name = f"C{correction_index:02d}"
            print(
                f"\n[SYSTEM] 第 {correction_index + 1} 轮，"
                f"下发目标：{target_pose}"
            )
            _, return_pose = robot.move_and_hold(cycle_name, target_pose)
            result, record = request_and_verify_compensation(
                profile=profile,
                robot=robot,
                vision=vision,
                target_pose=target_pose,
                run_id=run_id,
                sequence=sequence,
                label=f"correction_{correction_index:02d}",
            )
            sequence += 1
            report["observations"].append(record)

            consecutive_passes = 1 if is_converged(
                result, profile.convergence
            ) else 0
            while (
                consecutive_passes > 0
                and consecutive_passes
                < profile.convergence.required_consecutive_passes
            ):
                time.sleep(
                    profile.convergence.verification_interval_seconds
                )
                confirm_result, confirm_record = (
                    request_and_verify_compensation(
                        profile=profile,
                        robot=robot,
                        vision=vision,
                        target_pose=target_pose,
                        run_id=run_id,
                        sequence=sequence,
                        label=(
                            f"verify_{correction_index:02d}_"
                            f"{consecutive_passes:02d}"
                        ),
                    )
                )
                sequence += 1
                report["observations"].append(confirm_record)
                result = confirm_result
                record = confirm_record
                if is_converged(result, profile.convergence):
                    consecutive_passes += 1
                else:
                    consecutive_passes = 0

            if (
                consecutive_passes
                >= profile.convergence.required_consecutive_passes
            ):
                robot.release_and_wait_return(cycle_name, return_pose)
                report["status"] = "PASS"
                report["final_target_pose"] = target_pose
                report["final_residual_position_m"] = (
                    result.residual_position_m
                )
                report["final_residual_orientation_deg"] = (
                    result.residual_orientation_deg
                )
                report["correction_count"] = correction_index
                report["finished_at"] = datetime.now().isoformat(
                    timespec="seconds"
                )
                write_json(report_path, report)
                print(
                    "\n[SYSTEM] 跨机台自动补偿通过："
                    f"{result.residual_position_m * 1000.0:.3f}mm, "
                    f"{result.residual_orientation_deg:.3f}deg"
                )
                print(f"[SYSTEM] 报告：{report_path.resolve()}")
                return 0

            if correction_index >= profile.convergence.max_corrections:
                robot.release_and_wait_return(cycle_name, return_pose)
                report["status"] = "FAIL_NOT_CONVERGED"
                report["final_target_pose"] = target_pose
                report["final_residual_position_m"] = (
                    result.residual_position_m
                )
                report["final_residual_orientation_deg"] = (
                    result.residual_orientation_deg
                )
                report["correction_count"] = correction_index
                report["finished_at"] = datetime.now().isoformat(
                    timespec="seconds"
                )
                write_json(report_path, report)
                print(
                    "\n[SYSTEM] 已达到最大补偿次数，残差仍超限："
                    f"{result.residual_position_m * 1000.0:.3f}mm, "
                    f"{result.residual_orientation_deg:.3f}deg"
                )
                print(f"[SYSTEM] 报告：{report_path.resolve()}")
                return 1

            validate_candidate_target(
                candidate_pose=result.target_pose,
                current_pose=record["actual_pose_before"],
                observation_pose=profile.observation_pose,
                safety=profile.safety,
            )
            target_pose = result.target_pose
            robot.release_and_wait_return(cycle_name, return_pose)

        raise AssertionError("自动补偿循环意外结束")
    except BaseException as exc:
        report["status"] = "ABORTED"
        report["error"] = f"{type(exc).__name__}: {exc}"
        report["finished_at"] = datetime.now().isoformat(timespec="seconds")
        write_json(report_path, report)
        print(f"[SYSTEM] 异常报告：{report_path.resolve()}")
        if robot.is_cycle_active:
            print(
                "[SAFETY] 运动循环未完整结束；D1002 或返回动作状态可能不确定。"
                "程序未追加任何运动指令，请现场确认机械臂状态。"
            )
        raise
    finally:
        vision.close()
        if robot.is_connected:
            robot.close()


def check_profile(args: argparse.Namespace) -> int:
    path = Path(args.profile).expanduser().resolve()
    profile = load_profile(path)
    print(f"配置校验通过：{path}")
    print(f"机台：{profile.station_id}")
    print(f"名义观察位姿：{profile.observation_pose}")
    print(f"视觉服务：{profile.vision_base_url}")
    print(f"视觉返回模式：{profile.vision_response_pose_mode}")
    print(
        "注意：配置校验不连接 PLC、不连接相机，也不验证运动路径安全。"
    )
    return 0


def run_self_test() -> int:
    test_values = [-0.51485, 0.00473, 0.47268, -3.141, 0.0, 0.757]
    words = pose_to_registers(test_values)
    restored = registers_to_pose(words)
    if not np.allclose(test_values, restored, atol=1e-6):
        raise AssertionError(
            f"float word 编解码失败：{test_values} != {restored}"
        )

    current = [-0.5, 0.0, 0.47, -3.14, 0.0, 0.75]
    delta = [0.001, -0.002, 0.0001, 0.001, -0.002, 0.003]
    target = resolve_delta_target_pose(current, delta, 1.0)
    expected = [
        current[index] + delta[index]
        for index in range(6)
    ]
    expected[3:] = [normalize_angle_rad(value) for value in expected[3:]]
    if not np.allclose(target, expected, atol=1e-12):
        raise AssertionError(f"增量位姿计算失败：{target} != {expected}")

    position_error, orientation_error = pose_errors(current, current)
    if position_error > 1e-12 or orientation_error > 1e-9:
        raise AssertionError("相同位姿误差应为零")
    print("自检通过：word 编解码、增量位姿和位姿误差计算正常")
    return 0


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="跨机台自动补偿、机械臂移动和复拍残差验证"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    collect_parser = subparsers.add_parser(
        "collect-reference",
        help="在基准机台移动到观察位并采集跨机台基准",
    )
    collect_parser.add_argument("--station-id", required=True)
    collect_parser.add_argument(
        "--observation-pose",
        type=float,
        nargs=6,
        metavar=("X", "Y", "Z", "RX", "RY", "RZ"),
        required=True,
        help="名义观察位姿，XYZ=m，RX/RY/RZ=rad",
    )
    collect_parser.add_argument("--handeye-json", required=True)
    collect_parser.add_argument("--profile", required=True)
    collect_parser.add_argument(
        "--vision-url",
        default="http://127.0.0.1:8088",
    )
    collect_parser.add_argument(
        "--vision-image-dir",
        default="outputs/auto_cross_machine",
        help="视觉服务所在机器使用的图片目录",
    )
    collect_parser.add_argument(
        "--workspace-x",
        type=float,
        nargs=2,
        required=True,
        metavar=("MIN_X", "MAX_X"),
        help="机械臂 X 轴允许的绝对范围，单位 m",
    )
    collect_parser.add_argument(
        "--workspace-y",
        type=float,
        nargs=2,
        required=True,
        metavar=("MIN_Y", "MAX_Y"),
        help="机械臂 Y 轴允许的绝对范围，单位 m",
    )
    collect_parser.add_argument(
        "--workspace-z",
        type=float,
        nargs=2,
        required=True,
        metavar=("MIN_Z", "MAX_Z"),
        help="机械臂 Z 轴允许的绝对范围，单位 m",
    )
    collect_parser.add_argument(
        "--orientation-rx",
        type=float,
        nargs=2,
        required=True,
        metavar=("MIN_RX", "MAX_RX"),
        help="RX 允许的绝对范围，单位 rad",
    )
    collect_parser.add_argument(
        "--orientation-ry",
        type=float,
        nargs=2,
        required=True,
        metavar=("MIN_RY", "MAX_RY"),
        help="RY 允许的绝对范围，单位 rad",
    )
    collect_parser.add_argument(
        "--orientation-rz",
        type=float,
        nargs=2,
        required=True,
        metavar=("MIN_RZ", "MAX_RZ"),
        help="RZ 允许的绝对范围，单位 rad",
    )
    collect_parser.add_argument("--plc-ip", default="192.168.1.88")
    collect_parser.add_argument("--plc-port", type=int, default=502)
    collect_parser.add_argument("--overwrite", action="store_true")
    collect_parser.add_argument(
        "--confirm-single-pose-task",
        action="store_true",
        help="确认 D1002 只执行 D1020-D1031，不会执行未知第二段运动",
    )
    collect_parser.add_argument(
        "--execute",
        action="store_true",
        help="明确允许连接 PLC 并执行真实运动",
    )
    collect_parser.set_defaults(handler=collect_reference)

    run_parser = subparsers.add_parser(
        "run",
        help="执行自动拍照、补偿、移动、复拍和残差验收",
    )
    run_parser.add_argument("--profile", required=True)
    run_parser.add_argument(
        "--handeye-json",
        default=None,
        help="可选：用目标机台自己的手眼标定结果覆盖配置内 handeye",
    )
    run_parser.add_argument("--plc-ip", default=None)
    run_parser.add_argument("--plc-port", type=int, default=None)
    run_parser.add_argument("--vision-url", default=None)
    run_parser.add_argument("--report", default=None)
    run_parser.add_argument(
        "--confirm-single-pose-task",
        action="store_true",
        help="本次运行再次确认 D1002 只执行 D1020-D1031",
    )
    run_parser.add_argument(
        "--execute",
        action="store_true",
        help="明确允许连接 PLC 并执行真实运动",
    )
    run_parser.set_defaults(handler=run_automatic_calibration)

    check_parser = subparsers.add_parser(
        "check-profile",
        help="仅离线检查配置格式，不连接设备",
    )
    check_parser.add_argument("--profile", required=True)
    check_parser.set_defaults(handler=check_profile)

    self_test_parser = subparsers.add_parser(
        "self-test",
        help="执行不连接设备的基础算法自检",
    )
    self_test_parser.set_defaults(handler=lambda _args: run_self_test())
    return parser


def main() -> int:
    parser = build_argument_parser()
    args = parser.parse_args()
    try:
        return int(args.handler(args))
    except KeyboardInterrupt:
        print("\n[SYSTEM] 用户中断。", file=sys.stderr)
        return 130
    except Exception as exc:
        print(
            f"\n[ERROR] {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
