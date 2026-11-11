import os
import sys
import time
import struct
import ctypes
import json
import tempfile
import argparse
import math
from pathlib import Path
from datetime import datetime

# ============================================================
# 配置
# ============================================================

PLC_IP = "192.168.1.88"
PLC_PORT = 502
PLC_TIMEOUT_SECONDS = 3.0

HIK_IP = "192.168.1.118"

# PLC 寄存器
POSE_START_REGISTER = 1020     # D1020-D1031，共 12 word
START_REGISTER = 1002          # PC->PLC：机台标定启动；D1012 禁止写入
# 寄存器表同时列有 D1040-D1051 终点，尚未确认 D1002 是否自动执行两段运动。
# 仅在 PLC 侧确认该启动只执行 D1020-D1031 目标后设为 True；禁止靠试跑猜测。
START_TASK_SINGLE_POSE_CONFIRMED = True
ARRIVAL_REGISTER = 1012        # PLC->PC：0 未完成，1 完成
ACTUAL_POSE_START_REGISTER = 100  # D100-D111：实际 XYZ(m)、RX/RY/RZ(rad)
STATUS_START_REGISTER = 1008   # 一次读取 D1008-D1019：复位、暂停、到位、报警
MOTION_TIMEOUT_SECONDS = 120.0
MOTION_POLL_SECONDS = 0.10
POSITION_TOLERANCE_M = 0.0005    # 0.5 mm；到位判定容差，不代表手眼标定精度
ORIENTATION_TOLERANCE_DEG = 0.2

# 写入后只轮询读回，不重复写坐标；通信异常立即停止。
POSE_VERIFY_TIMEOUT_SECONDS = 3.0
POSE_VERIFY_POLL_SECONDS = 0.10

# 到位判定：D1012=1 且实际位姿进入容差后，
# 连续稳定多久才认为“本轮已经真正到位”
ARRIVAL_STABLE_SECONDS = 0.5

# 已确认到位后，继续保持 D1002=1，
# 再等待多久消除机械振动后拍照。
# 这段时间会持续检查 D1002、D1012 和实际位姿；
# 如果机器人自己开始返回，会立即报错，而不是继续盲等。
PHOTO_HOLD_SECONDS = 2.0

# float32 两个 word 的顺序
# 你刚才的 P01 已经验证成功，所以固定为 low_high
WORD_ORDER = "low_high"

# 拍照保存目录
SAVE_DIR = Path(__file__).resolve().parent / "capture_images_points40_retest_20261012"

# 海康取图超时
HIK_FRAME_TIMEOUT_MS = 3000


# 40 offline candidate poses designed from the 20260930 captures.
# XYZ offsets are in the robot base frame; angles add to Euler components.
# Every offset is relative to BASE_POSE, never to the previous point.
# Assumes unchanged P01, board placement, camera mounting, focus and resolution.
# Image framing predictions do NOT validate robot reachability or motion paths.
POINTS_SOURCE = "points40_candidate_v1_20260930 / outputs/handeye_points40_20260930/points40_design.json"
# XYZ: m; RX/RY/RZ: rad (screenshot values).
BASE_POSE = [-0.46131240, 0.00933142, 0.52924360, -3.14098950, -0.00000311, 0.75732857]

# dx/dy/dz: mm; drx/dry/drz: deg.
POINT_OFFSETS_MM_DEG = {
    "P01": [0, 0, 0, 0, 0, 0],  # baseline
    "P02": [-16, -27, 0, 0, 0, 0],  # coverage
    "P03": [-16, -4, 0, 0, 0, 0],  # coverage
    "P04": [-15, 19, 0, 0, 0, 0],  # coverage
    "P05": [2, 19, 0, 0, 0, 0],  # coverage
    "P06": [19, 19, 0, 0, 0, 0],  # coverage
    "P07": [18, -4, 0, 0, 0, 0],  # coverage
    "P08": [18, -28, 0, 0, 0, 0],  # coverage
    "P09": [1, -28, 0, 0, 0, 0],  # coverage
    "P10": [1, -4, -15, 0, 0, 0],  # depth
    "P11": [2, -4, 20, 0, 0, 0],  # depth
    "P12": [-17, 15, 0, -4, 0, 0],  # tilt_4
    "P13": [20, -24, 0, 4, 0, 0],  # tilt_4
    "P14": [-18, -23, 0, 0, -4, 0],  # tilt_4
    "P15": [21, 15, 0, 0, 4, 0],  # tilt_4
    "P16": [-20, 35, 0, -8, 0, 0],  # tilt_8 x从-36改到-20
    "P17": [20, -44, 0, 8, 0, 0],  # tilt_8 x从40改20
    "P18": [-38, -41, 0, 0, -8, 0],  # tilt_8
    "P19": [42, 34, 0, 0, 8, 0],  # tilt_8
    "P20": [-30, 57, 10, -12, 0, 0],  # tilt_12 x从-56改到-30
    "P21": [30, -67, 10, 12, 0, 0],  # tilt_12 x从61改到30
    "P22": [-59, -40, 10, 0, -12, 0],  # tilt_12 y从-61改到-40
    "P23": [65, 40, 10, 0, 12, 0],  # tilt_12 y从56改成40
    "P24": [2, -19, 0, 0, 0, -8],  # roll
    "P25": [-1, 10, 0, 0, 0, 8],  # roll
    "P26": [0, -33, 0, 0, 0, -16],  # roll
    "P27": [-5, 24, 0, 0, 0, 16],  # roll
    "P28": [-67, -3, 10, -7, -7, 0],  # combined
    "P29": [0, 67, 10, -7, 7, 0],  # combined x从3变成10
    "P30": [60, -7, 10, 7, 7, 0],  # combined x从73变成60
    "P31": [-20, -73, 10, 7, -7, 0],  # combined x从0变成-20
    "P32": [-40, -17, 10, -5, -5, 0],  # tilted_coverage x从-59变成-40 y从-17变成0
    "P33": [0, 61, 10, -5, 5, 0],  # tilted_coverage x从-9变成0
    "P34": [40, 9, 10, 5, 5, 0],  # tilted_coverage x从65变成40
    "P35": [-5, -68, 10, 5, -5, 0],  # tilted_coverage x从12变成-5
    "P36": [0, 29, -15, -6, 4, -8],  # depth_combined
    "P37": [0, -35, -15, 6, -4, 8],  # depth_combined x从14变成0
    "P38": [-40, 15, 20, -6, -4, 8],  # depth_combined x从-52变成-40
    "P39": [40, -38, 20, 6, 4, -8],  # depth_combined x从51变成40
    "P40": [10, 45, 10, -8, 5, -10],  # depth_combined x从0变成10 
}


def build_absolute_points():
    """Convert offsets relative to P01 from mm/deg into absolute m/rad poses."""
    return {
        name: [BASE_POSE[i] + offset[i] / 1000.0 for i in range(3)]
        + [BASE_POSE[i] + math.radians(offset[i]) for i in range(3, 6)]
        for name, offset in POINT_OFFSETS_MM_DEG.items()
    }


POINTS = build_absolute_points()


# ============================================================
# PLC / Modbus
# ============================================================

def save_image_unicode(save_path, image):
    """先在内存编码，再用Python写文件，兼容Windows中文路径。"""
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    ok, encoded = cv2.imencode(save_path.suffix, image)
    if not ok:
        raise RuntimeError(f"图片编码失败：{save_path}")
    try:
        payload = encoded.tobytes()
        with save_path.open("wb") as output:
            if output.write(payload) != len(payload):
                raise OSError("图片未完整写入")
    except OSError as error:
        raise RuntimeError(f"保存图片失败：{save_path}；{error}") from error


def verify_save_directory():
    """在连接设备前验证临时图片写入及移动，不触碰已有采集文件。"""
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    pending_dir = SAVE_DIR / "_unverified"
    pending_dir.mkdir(exist_ok=True)
    source_path = None
    destination_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=pending_dir, suffix=".jpg", delete=False) as probe:
            source_path = Path(probe.name)
        save_image_unicode(source_path, np.zeros((8, 8, 3), dtype=np.uint8))
        with tempfile.NamedTemporaryFile(dir=SAVE_DIR, suffix=".jpg", delete=False) as probe:
            destination_path = Path(probe.name)
        source_path.replace(destination_path)
        if destination_path.stat().st_size == 0:
            raise RuntimeError("试写图片为空")
    finally:
        for path in (source_path, destination_path):
            if path is not None:
                path.unlink(missing_ok=True)
    print("[SYSTEM] 图片保存目录试写通过（支持中文路径）")


def float_to_words(value: float):
    """
    float32 -> 2 x uint16

    已按现场验证：
    low word 在前，high word 在后。
    """
    raw = struct.pack(">f", float(value))
    high_word, low_word = struct.unpack(">HH", raw)

    if WORD_ORDER == "low_high":
        return [low_word, high_word]
    elif WORD_ORDER == "high_low":
        return [high_word, low_word]
    else:
        raise ValueError(f"未知 WORD_ORDER: {WORD_ORDER}")


def pose_to_registers(pose):
    """6 个 float -> 12 个 Modbus word"""
    if len(pose) != 6:
        raise ValueError("pose 必须是 [X, Y, Z, RX, RY, RZ] 共 6 个数")

    words = []
    for value in pose:
        words.extend(float_to_words(value))
    return words


def registers_to_pose(words):
    """按目标寄存器相同字序解码实际反馈；现场单位须为 m/rad。"""
    if len(words) != 12:
        raise RuntimeError(f"实际位姿反馈需要 12 个 word，收到 {len(words)} 个")
    pose = []
    for i in range(0, 12, 2):
        if WORD_ORDER == "low_high":
            low_word, high_word = words[i:i + 2]
        elif WORD_ORDER == "high_low":
            high_word, low_word = words[i:i + 2]
        else:
            raise ValueError(f"未知 WORD_ORDER: {WORD_ORDER}")
        pose.append(struct.unpack(">f", struct.pack(">HH", high_word, low_word))[0])
    if not np.all(np.isfinite(pose)):
        raise RuntimeError(f"实际位姿反馈含 NaN/Inf：{pose}")
    return pose


def pose_errors(actual_pose, target_pose):
    """位置用三维距离；姿态按 Rz*Ry*Rx 比较，避免 +/-pi 跳变误判。"""
    def rotation_from_euler(angles):
        rx, ry, rz = angles
        sx, sy, sz = np.sin([rx, ry, rz])
        cx, cy, cz = np.cos([rx, ry, rz])
        rotation_x = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
        rotation_y = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
        rotation_z = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
        return rotation_z @ rotation_y @ rotation_x

    position_error = float(np.linalg.norm(
        np.asarray(actual_pose[:3]) - np.asarray(target_pose[:3])
    ))
    relative_rotation = (
        rotation_from_euler(actual_pose[3:]).T
        @ rotation_from_euler(target_pose[3:])
    )
    cosine = np.clip((np.trace(relative_rotation) - 1.0) / 2.0, -1.0, 1.0)
    angle_error = float(np.degrees(np.arccos(cosine)))
    return position_error, angle_error


class RobotPLC:
    def __init__(self):
        self.client = ModbusTcpClient(
            PLC_IP,
            port=PLC_PORT,
            timeout=PLC_TIMEOUT_SECONDS,
            retries=0,  # 写入响应丢失时结果未知，禁止库自动重发运动请求。
        )
        self._pose_verified = False
        self._saw_not_arrived = False
        self._motion_deadline = None
        self.last_actual_pose = None
        self._operator_ready = False

    def connect(self):
        print(f"[PLC] 连接 {PLC_IP}:{PLC_PORT} ...")

        if not self.client.connect():
            raise RuntimeError(f"无法连接 PLC：{PLC_IP}:{PLC_PORT}")

        print("[PLC] Modbus TCP 连接成功")

    def close(self):
        try:
            self.client.close()
        except Exception:
            pass

        print("[PLC] 连接已关闭")

    @staticmethod
    def _check_result(result, action):
        if result is None:
            raise RuntimeError(f"{action}：返回 None")

        if hasattr(result, "isError") and result.isError():
            raise RuntimeError(f"{action}失败：{result}")

    def write_pose(self, point_name):
        self._pose_verified = False
        pose = POINTS[point_name]
        words = pose_to_registers(pose)

        print()
        print("=" * 72)
        print(f"[PLC] 写入 {point_name}")
        print(
            f"[PLC] X={pose[0]:.6f}, Y={pose[1]:.6f}, Z={pose[2]:.6f}, "
            f"RX={pose[3]:.6f}, RY={pose[4]:.6f}, RZ={pose[5]:.6f}"
        )

        for i, word in enumerate(words):
            print(f"[PLC] D{POSE_START_REGISTER + i} = {word}")

        result = self.client.write_registers(
            address=POSE_START_REGISTER,
            values=words,
        )
        self._check_result(result, "写 D1020-D1031")

        print("[PLC] 写入请求返回正常，开始读回 D1020-D1031 核对...")
        self.verify_pose_words(words)
        self._pose_verified = True

    def verify_pose_words(self, expected_words):
        """确认目标缓冲区与发送值逐 word 一致；不把它当作实际位姿反馈。"""
        deadline = time.monotonic() + POSE_VERIFY_TIMEOUT_SECONDS

        while True:
            result = self.client.read_holding_registers(
                address=POSE_START_REGISTER,
                count=len(expected_words),
            )
            self._check_result(result, "读回 D1020-D1031")
            actual_words = getattr(result, "registers", None)
            if actual_words is None or len(actual_words) != len(expected_words):
                raise RuntimeError(
                    f"坐标读回长度异常：expected={len(expected_words)}, "
                    f"actual={actual_words}；停止流程，不发送启动请求。"
                )

            if list(actual_words) == list(expected_words):
                print("[PLC] D1020-D1031 读回校验通过（12/12 word 一致）")
                return

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                differences = ", ".join(
                    f"D{POSE_START_REGISTER + i}: 目标={expected}, 读回={actual}"
                    for i, (expected, actual) in enumerate(
                        zip(expected_words, actual_words)
                    )
                    if expected != actual
                )
                raise RuntimeError(
                    f"坐标读回校验超时（{POSE_VERIFY_TIMEOUT_SECONDS:.1f}s）："
                    f"{differences}；停止流程，不发送启动请求。"
                )

            time.sleep(min(POSE_VERIFY_POLL_SECONDS, remaining))

    def trigger_move(self):
        """
        D1002 = 1 启动，并保持到本轮目标到位且稳定。
        """
        if not START_TASK_SINGLE_POSE_CONFIRMED:
            raise RuntimeError(
                "尚未确认 D1002 是否只执行 D1020-D1031 目标；"
                "请先核对 D1040-D1051 终点是否会被自动执行。"
            )
        if not self._pose_verified:
            raise RuntimeError("坐标尚未通过读回校验，禁止发送启动请求。")
        # 启动前检查互锁，并记录到位信号，防止把上一点残留的 1 当成新完成。
        self._saw_not_arrived = self.read_motion_status() == 0
        # 一次校验只允许一次启动尝试，异常后不能复用校验状态重发。
        self._pose_verified = False
        self._motion_deadline = time.monotonic() + MOTION_TIMEOUT_SECONDS
        result = self.client.write_register(
            address=START_REGISTER,
            value=1,
        )
        self._check_result(result, "写 D1002=1")

        print("[PLC] D1002 = 1，将保持到目标到位并稳定")

    def reset_start_signal(self):
        """运动完成或流程异常时将保持型启动信号复位。"""
        result = self.client.write_register(
            address=START_REGISTER,
            value=0,
        )
        self._check_result(result, "写 D1002=0")

        print("[PLC] D1002 已复位为 0")

    def read_start_signal(self):
        """读取 D1002，确认 PLC 侧仍保持本轮启动/保持信号。"""
        result = self.client.read_holding_registers(
            address=START_REGISTER,
            count=1,
        )
        self._check_result(result, "读取 D1002")
        words = getattr(result, "registers", None)
        if words is None or len(words) != 1:
            raise RuntimeError(f"D1002 读取异常：{words}")
        return int(words[0])

    def read_motion_status(self, allow_reset=False):
        result = self.client.read_holding_registers(
            address=STATUS_START_REGISTER, count=12
        )
        self._check_result(result, "读取 D1008-D1019 状态")
        words = getattr(result, "registers", None)
        if words is None or len(words) != 12:
            raise RuntimeError(f"状态反馈长度异常：{words}")
        for address, description in (
            (1008, "机器人复位中"),
            (1009, "任务暂停中"),
            (1018, "系统报警"),
            (1019, "机器人状态异常"),
        ):
            value = words[address - STATUS_START_REGISTER]
            if address == 1008:
                if value not in (0, 1):
                    raise RuntimeError(f"D1008 状态异常：{value}")
                self._reset_in_progress = value == 1
                if allow_reset:
                    continue
            if value != 0:
                raise RuntimeError(f"{description}：D{address}={value}，停止采集流程")
        arrived = words[ARRIVAL_REGISTER - STATUS_START_REGISTER]
        if arrived not in (0, 1):
            raise RuntimeError(f"D1012 到位反馈值异常：{arrived}")
        return arrived

    def check_idle(self):
        if not self._operator_ready:
            raise RuntimeError("尚未人工确认机械臂已返回、PLC可接收下一点。")
        if self.read_start_signal() != 0:
            raise RuntimeError("D1002 尚未清零，禁止覆盖目标；请现场核对上一轮状态。")
        if self.read_motion_status() != 0:
            raise RuntimeError("D1012 尚未恢复为0，禁止写入下一点。")

    def wait_cycle_reset(self):
        """人工确认返回完成；回车后仍检查已有互锁，不推断自动返回完成。"""
        self._operator_ready = False
        while True:
            answer = input(
                "\n[人工确认] 请确认机械臂已返回并停止、PLC可以接收下一点。"
                "确认后按回车；输入 q 回车退出："
            ).strip().lower()
            if answer == "q":
                raise SystemExit("用户结束采集，未发送下一点。")
            if answer:
                print("仅直接按回车表示确认；输入 q 表示退出。")
                continue
            # 人工确认不覆盖启动残留、复位、暂停或报警状态。
            if self.read_start_signal() != 0:
                print("[PLC] D1002仍非0，请现场处理后重新确认。")
                continue
            if self.read_motion_status() != 0:
                print("[PLC] D1012仍非0，请等待本轮反馈撤销后重新确认。")
                continue
            self._operator_ready = True
            print("[SYSTEM] 人工确认及已有互锁检查通过。")
            return

    def check_photo_pose(self, point_name):
        if self.read_start_signal() != 1 or self.read_motion_status() != 1:
            raise RuntimeError("取图前后握手状态异常，本张不作为有效标定图。")
        pose = self.read_actual_pose()
        distance, angle = pose_errors(pose, POINTS[point_name])
        if distance > POSITION_TOLERANCE_M or angle > ORIENTATION_TOLERANCE_DEG:
            raise RuntimeError("取图前后实际位姿偏离目标，本张不作为有效标定图。")
        return pose

    def read_actual_pose(self):
        result = self.client.read_holding_registers(
            address=ACTUAL_POSE_START_REGISTER, count=12
        )
        self._check_result(result, "读取 D100-D111 实际位姿")
        words = getattr(result, "registers", None)
        if words is None:
            raise RuntimeError("实际位姿反馈缺少 registers")
        return registers_to_pose(words)

    def wait_for_arrival(self, point_name):
        """
        等待本轮真正到位。

        条件：
        1. D1002 仍为 1；
        2. 本轮曾见过 D1012=0，随后 D1012=1；
        3. D100-D111 实际位姿进入目标容差；
        4. 上述状态连续保持 ARRIVAL_STABLE_SECONDS。

        注意：
        正常返回时绝不清 D1002。
        """
        if self._motion_deadline is None:
            raise RuntimeError("尚未发送启动请求，不能等待本轮到位")

        target_pose = POINTS[point_name]
        stable_since = None
        next_log_time = 0.0
        last_state = "尚未读取反馈"

        while time.monotonic() < self._motion_deadline:
            start_value = self.read_start_signal()
            if start_value != 1:
                raise RuntimeError(
                    f"{point_name} 等待到位期间 D1002={start_value}，"
                    "本轮保持信号已丢失；Python 未主动清零。"
                )

            arrived = self.read_motion_status()
            actual_pose = self.read_actual_pose()
            position_error, angle_error = pose_errors(actual_pose, target_pose)
            now = time.monotonic()

            if arrived == 0:
                self._saw_not_arrived = True

            last_state = (
                f"D1002={start_value}, D1012={arrived}, "
                f"已见未完成={self._saw_not_arrived}, "
                f"位置误差={position_error:.6f}m, "
                f"姿态误差={angle_error:.3f}deg"
            )

            is_at_target = (
                self._saw_not_arrived
                and arrived == 1
                and position_error <= POSITION_TOLERANCE_M
                and angle_error <= ORIENTATION_TOLERANCE_DEG
            )

            if is_at_target:
                if stable_since is None:
                    stable_since = now

                if now - stable_since >= ARRIVAL_STABLE_SECONDS:
                    self.last_actual_pose = actual_pose
                    self._motion_deadline = None
                    print(
                        f"[PLC] {point_name} 已到位并稳定 "
                        f"{ARRIVAL_STABLE_SECONDS:.1f}s：{last_state}"
                    )
                    print(f"[PLC] 到位实际位姿：{actual_pose}")
                    return
            else:
                stable_since = None

            if now >= next_log_time:
                print(f"[PLC] 等待 {point_name} 到位：{last_state}")
                next_log_time = now + 1.0

            time.sleep(MOTION_POLL_SECONDS)

        self._motion_deadline = None
        raise RuntimeError(
            f"{point_name} 到位超时（{MOTION_TIMEOUT_SECONDS:.1f}s）：{last_state}。"
        )

    def hold_for_photo(self, point_name):
        """
        已到位后继续保持 D1002=1，并持续检查机器人没有离开目标。
        到 PHOTO_HOLD_SECONDS 后才允许相机拍照。

        如果 PLC/机器人在 D1002 仍为 1 时自行返回，
        这里会立即检测到并报错。
        """
        target_pose = POINTS[point_name]
        hold_start = time.monotonic()
        next_log_time = 0.0

        while True:
            now = time.monotonic()
            elapsed = now - hold_start

            start_value = self.read_start_signal()
            arrived = self.read_motion_status()
            actual_pose = self.read_actual_pose()
            position_error, angle_error = pose_errors(actual_pose, target_pose)

            if start_value != 1:
                raise RuntimeError(
                    f"{point_name} 拍照等待期间 D1002={start_value}。"
                    "Python 尚未发送 D1002=0，说明保持信号已被其他逻辑改变。"
                )

            if arrived != 1:
                raise RuntimeError(
                    f"{point_name} 拍照等待期间 D1012 从 1 变成 {arrived}，"
                    "机器人/PLC 已退出到位状态；此时 D1002 仍保持为 1。"
                )

            if (
                position_error > POSITION_TOLERANCE_M
                or angle_error > ORIENTATION_TOLERANCE_DEG
            ):
                raise RuntimeError(
                    f"{point_name} 拍照等待期间机器人开始离开目标："
                    f"位置误差={position_error:.6f}m，"
                    f"姿态误差={angle_error:.3f}deg；"
                    "D1002 仍为 1，因此返回动作并非本段 Python 清零触发。"
                )

            if now >= next_log_time:
                remaining = max(0.0, PHOTO_HOLD_SECONDS - elapsed)
                print(
                    f"[PLC] {point_name} 保持目标等待拍照："
                    f"D1002=1, D1012=1, "
                    f"位置误差={position_error:.6f}m, "
                    f"姿态误差={angle_error:.3f}deg, "
                    f"剩余 {remaining:.1f}s"
                )
                next_log_time = now + 0.5

            if elapsed >= PHOTO_HOLD_SECONDS:
                self.last_actual_pose = actual_pose
                print(
                    f"[PLC] {point_name} 已保持 "
                    f"{PHOTO_HOLD_SECONDS:.1f}s，可拍照"
                )
                return

            time.sleep(MOTION_POLL_SECONDS)

    def move_to(self, point_name):
        """
        移动到目标并等待到位稳定。

        重要：正常到位后这里【不】清 D1002。
        D1002 必须保持为 1，直到相机拍照完成，避免 PLC 在拍照前让机械臂返回。
        """
        self.last_actual_pose = None
        self.check_idle()
        self.write_pose(point_name)
        self.check_idle()
        self._operator_ready = False
        self.trigger_move()
        self.wait_for_arrival(point_name)

        print(f"[PLC] {point_name} 已到位，D1002 继续保持为 1")



# ============================================================
# 海康 MVS
# ============================================================

def load_hik_mvs():
    """
    查找并导入海康 MVS Python SDK。

    如果自动找不到，可设置环境变量：
    MVS_PYTHON_PATH=<MvImport 所在目录>
    """
    candidate_paths = []

    env_path = os.environ.get("MVS_PYTHON_PATH")
    if env_path:
        candidate_paths.append(env_path)

    candidate_paths.extend([
        # 当前项目常见放法
        str(Path.cwd() / "MvImport"),
        str(Path.cwd() / "MVS" / "MvImport"),

        # Windows MVS 常见路径
        r"D:\sdk\hik\MvImport",
        r"C:\Program Files\MVS\Development\Samples\Python\MvImport",

        # Linux 常见路径
        "/opt/MVS/Samples/64/Python/MvImport",
        "/opt/MVS/Samples/x86_64/Python/MvImport",
    ])

    for path in candidate_paths:
        if not path:
            continue

        sdk_file = os.path.join(path, "MvCameraControl_class.py")
        if os.path.isfile(sdk_file):
            if path not in sys.path:
                sys.path.insert(0, path)

            import MvCameraControl_class as mvs
            print(f"[HIK] 使用 MVS Python SDK：{path}")
            return mvs

    # 如果本来就已经在 PYTHONPATH 中
    try:
        import MvCameraControl_class as mvs
        print("[HIK] 已从 PYTHONPATH 导入 MvCameraControl_class")
        return mvs
    except ImportError:
        pass

    raise RuntimeError(
        "没有找到 MvCameraControl_class.py。\n"
        "请找到海康 MVS 的 MvImport 目录，然后设置：\n"
        'PowerShell: $env:MVS_PYTHON_PATH="你的\\MvImport\\路径"\n'
        "再重新运行本程序。"
    )


class HikCamera:
    def __init__(self, target_ip):
        self.target_ip = target_ip
        self.mvs = None
        self.cam = None
        self.payload_size = 0
        self.buffer = None
        self.opened = False

    @staticmethod
    def int_ip_to_str(ip_int):
        return (
            f"{(ip_int >> 24) & 0xFF}."
            f"{(ip_int >> 16) & 0xFF}."
            f"{(ip_int >> 8) & 0xFF}."
            f"{ip_int & 0xFF}"
        )

    def open(self):
        self.mvs = load_hik_mvs()
        mvs = self.mvs

        # 部分新版 SDK 需要初始化
        if hasattr(mvs.MvCamera, "MV_CC_Initialize"):
            ret = mvs.MvCamera.MV_CC_Initialize()
            if ret != 0:
                print(f"[HIK] MV_CC_Initialize 返回 0x{ret:x}")

        device_list = mvs.MV_CC_DEVICE_INFO_LIST()

        ret = mvs.MvCamera.MV_CC_EnumDevices(
            mvs.MV_GIGE_DEVICE,
            device_list
        )
        if ret != 0:
            raise RuntimeError(f"枚举 GigE 相机失败：0x{ret:x}")

        print(f"[HIK] 枚举到 {device_list.nDeviceNum} 台 GigE 相机")

        target_info = None

        for i in range(device_list.nDeviceNum):
            dev_ptr = device_list.pDeviceInfo[i]

            # pDeviceInfo[i] 是指向 MV_CC_DEVICE_INFO 的指针。
            # 海康 Python 封装的 MV_CC_CreateHandle() 内部还会对传入参数执行 byref()，
            # 因此这里必须传“结构体本身”，不能把原始指针直接传进去。
            info = ctypes.cast(
                dev_ptr,
                ctypes.POINTER(mvs.MV_CC_DEVICE_INFO)
            ).contents

            if info.nTLayerType != mvs.MV_GIGE_DEVICE:
                continue

            ip_int = int(info.SpecialInfo.stGigEInfo.nCurrentIp)
            ip_str = self.int_ip_to_str(ip_int)

            print(f"[HIK] camera[{i}] = {ip_str}")

            if ip_str == self.target_ip:
                target_info = info
                break

        if target_info is None:
            raise RuntimeError(
                f"没有找到海康相机 {self.target_ip}。\n"
                "请检查网卡 IP、相机 IP、MVS 是否能看到相机。"
            )

        self.cam = mvs.MvCamera()

        ret = self.cam.MV_CC_CreateHandle(target_info)
        if ret != 0:
            raise RuntimeError(f"创建相机句柄失败：0x{ret:x}")

        try:
            ret = self.cam.MV_CC_OpenDevice(mvs.MV_ACCESS_Exclusive, 0)
        except TypeError:
            ret = self.cam.MV_CC_OpenDevice()

        if ret != 0:
            raise RuntimeError(
                f"打开相机失败：0x{ret:x}\n"
                "如果 MVS 客户端正打开此相机，请先关闭 MVS 取流。"
            )

        self.opened = True
        print(f"[HIK] 已打开相机 {self.target_ip}")

        # 连续模式
        ret = self.cam.MV_CC_SetEnumValueByString("TriggerMode", "Off")
        if ret != 0:
            print(f"[HIK] 设置 TriggerMode=Off 返回 0x{ret:x}")

        # 直接要求 RGB8Packed，方便转 OpenCV 保存
        ret = self.cam.MV_CC_SetEnumValueByString("PixelFormat", "RGB8Packed")
        if ret != 0:
            raise RuntimeError(
                f"设置 PixelFormat=RGB8Packed 失败：0x{ret:x}"
            )

        # 获取 PayloadSize
        value_cls = getattr(mvs, "MVCC_INTVALUE_EX", None)
        if value_cls is None:
            value_cls = mvs.MVCC_INTVALUE

        st_param = value_cls()

        if hasattr(self.cam, "MV_CC_GetIntValueEx"):
            ret = self.cam.MV_CC_GetIntValueEx("PayloadSize", st_param)
        else:
            ret = self.cam.MV_CC_GetIntValue("PayloadSize", st_param)

        if ret != 0:
            raise RuntimeError(f"读取 PayloadSize 失败：0x{ret:x}")

        self.payload_size = int(st_param.nCurValue)
        self.buffer = (ctypes.c_ubyte * self.payload_size)()

        ret = self.cam.MV_CC_StartGrabbing()
        if ret != 0:
            raise RuntimeError(f"StartGrabbing 失败：0x{ret:x}")

        print("[HIK] 已开始取流")

    def capture(self, save_path):
        if not self.opened:
            raise RuntimeError("相机尚未打开")

        mvs = self.mvs

        # 清除旧帧，尽量拿到触发时刻之后的新图
        if hasattr(self.cam, "MV_CC_ClearImageBuffer"):
            ret = self.cam.MV_CC_ClearImageBuffer()
            if ret != 0:
                raise RuntimeError(f"清除旧帧失败：0x{ret:x}")
        else:
            raise RuntimeError("SDK 不支持清除旧帧，不能确认本张图像的新鲜度")

        frame_info = mvs.MV_FRAME_OUT_INFO_EX()

        ret = self.cam.MV_CC_GetOneFrameTimeout(
            self.buffer,
            self.payload_size,
            frame_info,
            HIK_FRAME_TIMEOUT_MS
        )

        if ret != 0:
            raise RuntimeError(f"取图失败：0x{ret:x}")

        self.last_frame_metadata = {
            name: int(getattr(frame_info, name))
            for name in ("nFrameNum", "nDevTimeStampHigh", "nDevTimeStampLow", "nHostTimeStamp")
            if hasattr(frame_info, name)
        }
        width = int(frame_info.nWidth)
        height = int(frame_info.nHeight)
        data_len = int(frame_info.nFrameLen)

        expected = width * height * 3

        if data_len < expected:
            raise RuntimeError(
                f"图像数据长度异常：frame_len={data_len}, "
                f"expected>={expected}。请确认 PixelFormat=RGB8Packed。"
            )

        array = np.ctypeslib.as_array(self.buffer)
        rgb = array[:expected].reshape(height, width, 3).copy()
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

        save_path = Path(save_path)
        save_image_unicode(save_path, bgr)

        print(f"[HIK] 已保存：{save_path}")
        return save_path

    def close(self):
        if self.cam is None:
            return

        try:
            self.cam.MV_CC_StopGrabbing()
        except Exception:
            pass

        try:
            self.cam.MV_CC_CloseDevice()
        except Exception:
            pass

        try:
            self.cam.MV_CC_DestroyHandle()
        except Exception:
            pass

        self.opened = False
        print("[HIK] 相机已关闭")


# ============================================================
# 主流程
# ============================================================

def run_one_point(plc, camera, point_name):
    print()
    print("#" * 72)
    print(f"[SYSTEM] 开始 {point_name}")
    print("#" * 72)

    # 1. 写 D1020-D1031
    # 2. D1002 = 1
    # 3. 等 D1012 = 1 + 实际位姿到位
    # move_to() 正常返回后，D1002 仍然保持为 1。
    plc.move_to(point_name)

    plc.hold_for_photo(point_name)
    before_pose = plc.check_photo_pose(point_name)
    before_time = datetime.now().isoformat(timespec="microseconds")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    save_path = SAVE_DIR / f"{point_name}_{timestamp}.jpg"
    # 未通过反馈复核的图片单独隔离，不混入有效标定图。
    pending_path = SAVE_DIR / "_unverified" / save_path.name
    camera.capture(pending_path)
    after_pose = plc.check_photo_pose(point_name)
    after_time = datetime.now().isoformat(timespec="microseconds")
    distance, angle = pose_errors(after_pose, before_pose)
    if distance > POSITION_TOLERANCE_M or angle > ORIENTATION_TOLERANCE_DEG:
        raise RuntimeError("取图前后位姿变化超限，图片保留在 _unverified")
    metadata = {
        "point_name": point_name,
        "image": save_path.name,
        "units": {"position": "m", "orientation": "rad"},
        "orientation_convention": "Rz*Ry*Rx",
        "points_source": POINTS_SOURCE,
        "point_set_status": "candidate_requires_field_validation",
        "base_pose": BASE_POSE,
        "offset_mm_deg": POINT_OFFSETS_MM_DEG[point_name],
        "offset_convention": "base_frame_xyz_plus_euler_component_offsets",
        "target_pose": POINTS[point_name],
        "actual_pose_before": before_pose,
        "actual_pose_after": after_pose,
        "time_before": before_time,
        "time_after": after_time,
        "frame": camera.last_frame_metadata,
        "validation": "before_after_checks_not_hardware_synchronized",
    }
    save_path.with_suffix(".json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    pending_path.replace(save_path)
    print(f"[SYSTEM] {point_name} 取图及前后反馈复核完成：{save_path}")
    # 仅在成功保存并复核后释放；异常不擅自发送可能触发返回的指令。
    plc.reset_start_signal()
    plc.wait_cycle_reset()
    print(f"[SYSTEM] {point_name} 本轮结束，可以进入下一点")


def main():
    parser = argparse.ArgumentParser(description="AUBO + HIK 点位采图；默认单点 P01")
    parser.add_argument("point", nargs="?", default="P01", type=str.upper,
                        choices=[*POINTS, "ALL"])
    parser.add_argument("--dry-run", action="store_true",
                        help="仅打印绝对目标位姿，不连接 PLC/相机，不写入寄存器")
    args = parser.parse_args()
    command = args.point
    if args.dry_run:
        print("point,x_m,y_m,z_m,rx_rad,ry_rad,rz_rad")
        for point_name in POINTS if command == "ALL" else [command]:
            print(point_name + "," + ",".join(f"{value:.9f}" for value in POINTS[point_name]))
        return

    # 离线预览无需安装现场相机和 Modbus 依赖。
    global cv2, np, ModbusTcpClient
    import cv2
    import numpy as np
    from pymodbus.client import ModbusTcpClient

    if not START_TASK_SINGLE_POSE_CONFIRMED:
        raise SystemExit(
            "启动前核对：D1002 是机台标定启动，D1012 是只读到位反馈。\n"
            "寄存器表还包含 D1040-D1051 终点，请先确认 D1002 是否仅移动到 "
            "D1020-D1031。确认仅执行此目标后，再将 "
            "START_TASK_SINGLE_POSE_CONFIRMED 设置为 True；当前未连接或写入 PLC。"
        )

    verify_save_directory()

    print("=" * 72)
    print("AUBO + HIK 自动采图")
    print(f"PLC        : {PLC_IP}:{PLC_PORT}")
    print(f"HIK        : {HIK_IP}")
    print(f"Pose       : D1020-D1031")
    print(f"Start      : D{START_REGISTER}=1 保持至拍照完成后复位")
    print(f"Verify     : 坐标写入后读回校验，超时 {POSE_VERIFY_TIMEOUT_SECONDS} s")
    print(f"Arrival    : D{ARRIVAL_REGISTER}=1 + D100-D111 实际位姿校验")
    print(f"Timeout    : {MOTION_TIMEOUT_SECONDS} s")
    print(f"Stable     : 到位连续稳定确认 {ARRIVAL_STABLE_SECONDS} s")
    print(f"PhotoHold  : 到位后保持 D1002=1 再等待 {PHOTO_HOLD_SECONDS} s 拍照")
    print(f"Save dir   : {SAVE_DIR.resolve()}")
    print(f"Task       : {command}")
    print(f"Points     : {len(POINTS)}; {POINTS_SOURCE}")
    print(f"Base P01   : {BASE_POSE}")
    print("Candidate  : 40 点新候选；先低速逐点验证，尤其 ±12° 倾角和组合姿态")
    print("Geometry   : 使用本次 P01、板位置、相机安装和焦距；任何变化需重新核对视野")
    print("Next point : 每轮拍照释放D1002后，人工确认返回完成，按回车继续")
    print("=" * 72)

    plc = RobotPLC()
    camera = HikCamera(HIK_IP)

    try:
        plc.connect()
        camera.open()
        print("[SYSTEM] 首次写入目标前，请确认设备已准备好。")
        plc.wait_cycle_reset()

        if command == "ALL":
            print()
            print(f"警告：ALL 会依次执行 {len(POINTS)} 个点位。")
            print("请确保所有点均已在低速下逐点验证路径安全。")
            print()

            for point_name in POINTS:
                run_one_point(plc, camera, point_name)
        else:
            run_one_point(plc, camera, command)

    except BaseException:
        print("[SYSTEM] 流程已中断，不再写目标或重发启动。")
        print("[SYSTEM] 未自动清 D1002；清零可能触发返回。关闭连接不代表机械臂停止，请现场核对。")
        raise

    finally:
        camera.close()
        plc.close()


if __name__ == "__main__":
    main()
