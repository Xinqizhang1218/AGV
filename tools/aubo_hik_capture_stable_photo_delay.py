# -*- coding: utf-8 -*-
"""
aubo_hik_capture.py

流程：
1. 通过 Modbus TCP 向 PLC 写 D1020-D1031（X/Y/Z/RX/RY/RZ，6 个 float32，共 12 个 word）
2. 读回 D1020-D1031，12 个 word 全部一致后才允许发送启动请求
3. 写 D1002 = 1，并在本轮运动期间保持
4. 等待 D1012 本轮到位，且 D100-D111 实际位姿连续稳定 STABLE_CONFIRM_SECONDS；此时保持 D1002 = 1
5. 到位后继续保持 D1002 = 1，额外静置 PHOTO_DELAY_SECONDS 消振
6. 海康 GigE 相机 192.168.1.118 拍照并保存，保存完成后才写 D1002 = 0
7. 支持单点 P01 / P02 ... / P50，也支持 ALL

当前现场参数：
PLC / Modbus TCP: 192.168.1.88:502
海康相机:        192.168.1.118

重要：
- 已按现场验证使用 low_high word order。
- XYZ 写入 PLC 的单位为 m，姿态单位为 rad。
- 目标寄存器读回一致仅确认坐标写入，不代表机械臂已启动或已到位。
- D1012 是 PLC 到位反馈，只读；D1002 才是机台标定启动请求。
- 到位后先连续稳定 STABLE_CONFIRM_SECONDS 秒确认到位，再额外静置 PHOTO_DELAY_SECONDS 秒消振。
- 写入/读回异常会终止本轮，不自动重发目标或运动启动指令。
"""

import os
import sys
import time
import struct
import ctypes
from pathlib import Path
from datetime import datetime

import cv2
import numpy as np
from pymodbus.client import ModbusTcpClient


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

# 到位判定：D1012=1 且实际位姿满足容差后，
# 连续稳定多久才认为“机械臂真正到位”
STABLE_CONFIRM_SECONDS = 0.5

# 已确认到位以后，继续保持 D1002=1，
# 再额外静置多久用于机械结构消振，然后才拍照
PHOTO_DELAY_SECONDS = 4.0

# 拍照完成后 D1002=0，等待 PLC/机械臂完成本轮复位再进入下一点。
RESET_TIMEOUT_SECONDS = 20.0
RESET_STABLE_SECONDS = 0.6
RESET_POSITION_DELTA_M = 0.0005       # 连续采样位置变化 < 0.5 mm
RESET_ORIENTATION_DELTA_DEG = 0.2     # 连续采样姿态变化 < 0.2 deg

# float32 两个 word 的顺序
# 你刚才的 P01 已经验证成功，所以固定为 low_high
WORD_ORDER = "low_high"

# 拍照保存目录
SAVE_DIR = Path("./capture_images3cm5s")

# 海康取图超时
HIK_FRAME_TIMEOUT_MS = 3000


# ============================================================
# 50 个机械臂位姿
# XYZ：m
# RX RY RZ：rad
# ============================================================

POINTS = {
    "P01": [-0.51485,  0.00473, 0.47268, -3.141000,  0.000000,  0.757000],
    "P02": [-0.52025, -0.02568, 0.47314, -3.141000,  0.000000,  0.757000],
    "P03": [-0.51770,  0.04294, 0.47204, -3.141000,  0.000000,  0.757000],
    "P04": [-0.54300,  0.00937, 0.47245, -3.141000,  0.000000,  0.757000],
    "P05": [-0.49492,  0.00759, 0.47274, -3.141000,  0.000000,  0.757000],
    "P06": [-0.54427, -0.02477, 0.47300, -3.141000,  0.000000,  0.757000],
    "P07": [-0.54172,  0.04377, 0.47190, -3.141000,  0.000000,  0.757000],
    "P08": [-0.49620, -0.02657, 0.47329, -3.141000,  0.000000,  0.757000],
    "P09": [-0.49364,  0.04202, 0.47219, -3.141000,  0.000000,  0.757000],

    "P10": [-0.51888,  0.00820, 0.46057, -3.141000,  0.000000,  0.757000],
    "P11": [-0.51909,  0.00875, 0.48463, -3.141000,  0.000000,  0.757000],

    "P12": [-0.51898, -0.06325, 0.46774, -2.987705, -0.143272,  0.745978],
    "P13": [-0.51898,  0.07964, 0.46243,  2.988890,  0.143272,  0.745978],

    "P14": [-0.44963,  0.00848, 0.44519, -2.996052,  0.151712,  0.768036],
    "P15": [-0.59252,  0.00848, 0.48498,  2.997237, -0.151712,  0.768036],

    "P16": [-0.52373,  0.02809, 0.47260, -3.141000,  0.000000,  0.966440],
    "P17": [-0.51842, -0.01169, 0.47260, -3.141000,  0.000000,  0.547560],

    "P18": [-0.47231, -0.03947, 0.45438, -2.943967,  0.006519,  0.747865],
    "P19": [-0.56752, -0.03947, 0.48102, -3.136305, -0.197084,  0.766315],
    "P20": [-0.47280,  0.05618, 0.45086,  3.137490,  0.197084,  0.766315],
    "P21": [-0.56702,  0.05618, 0.47750,  2.945152, -0.006519,  0.747865],

    "P22": [-0.51888, -0.06101, 0.45592, -2.987705, -0.143272,  0.745978],
    "P23": [-0.51909,  0.08241, 0.47414,  2.988890,  0.143272,  0.745978],

    "P24": [-0.45203,  0.00820, 0.43341, -2.996052,  0.151712,  0.768036],
    "P25": [-0.59512,  0.00875, 0.49673,  2.997237, -0.151712,  0.768036],

    "P26": [-0.46880, -0.01932, 0.45438, -2.943967,  0.006519,  0.887491],
    "P27": [-0.57287, -0.04569, 0.48102, -3.136305, -0.197084,  0.626689],
    "P28": [-0.46577,  0.03585, 0.45086,  3.137490,  0.197084,  0.626689],
    "P29": [-0.57590,  0.06222, 0.47750,  2.945152, -0.006519,  0.887491],

    "P30": [-0.57984, -0.02497, 0.49524,  3.096858, -0.198214,  0.875398],
    "P31": [-0.51898, -0.02751, 0.47205, -3.064748, -0.071846, 0.754258],
    "P32": [-0.51898,  0.04433, 0.46938,  3.065933,  0.071846, 0.754258],

    "P33": [-0.48359,  0.00848, 0.46071, -3.068945,  0.076055, 0.759743],
    "P34": [-0.55543,  0.00848, 0.48072,  3.070131, -0.076055, 0.759743],

    "P35": [-0.52084,  0.01841, 0.47260, -3.141000,  0.000000, 0.861720],
    "P36": [-0.51817, -0.00159, 0.47260, -3.141000,  0.000000, 0.652280],

    "P37": [-0.48364, -0.02751, 0.46017, -2.993110,  0.004591, 0.751847],
    "P38": [-0.55537, -0.02751, 0.48017, -3.137177, -0.147911, 0.762210],

    "P39": [-0.48392,  0.04433, 0.45751,  3.138362,  0.147911, 0.762210],
    "P40": [-0.55509,  0.04433, 0.47752,  2.994296, -0.004591, 0.751847],

    "P41": [-0.51502, -0.02581, 0.47103, -3.039194, -0.095722, 0.891746],
    "P42": [-0.51150,  0.04227, 0.46748,  3.040379,  0.095722, 0.612493],

    "P43": [-0.47525,  0.02820, 0.45594, -3.044782,  0.101338, 0.901510],
    "P44": [-0.56642,  0.00182, 0.48257,  3.045968, -0.101338, 0.622257],

    "P45": [-0.52481, -0.05244, 0.47103, -3.039194, -0.095722, 0.612493],
    "P46": [-0.52833,  0.06891, 0.46748,  3.040379,  0.095722, 0.891746],

    "P47": [-0.47170, -0.01149, 0.45594, -3.044782,  0.101338, 0.622257],
    "P48": [-0.56997,  0.01488, 0.48257,  3.045968, -0.101338, 0.901510],

    "P49": [-0.48115, -0.03249, 0.44625, -2.993833,  0.029183, 0.666544],
    "P50": [-0.55523,  0.05742, 0.48738,  2.993505,  0.020022, 0.837434],
}


# ============================================================
# PLC / Modbus
# ============================================================

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

    def read_motion_status(self):
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
            if value != 0:
                raise RuntimeError(f"{description}：D{address}={value}，停止采集流程")
        arrived = words[ARRIVAL_REGISTER - STATUS_START_REGISTER]
        if arrived not in (0, 1):
            raise RuntimeError(f"D1012 到位反馈值异常：{arrived}")
        return arrived

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
        """本轮到位信号 + 实际位姿误差 + 连续稳定时间，三者同时满足才返回。"""
        if self._motion_deadline is None:
            raise RuntimeError("尚未发送启动请求，不能等待本轮到位")
        target_pose = POINTS[point_name]
        stable_since = None
        next_log_time = 0.0
        last_state = "尚未读取反馈"
        while time.monotonic() < self._motion_deadline:
            arrived = self.read_motion_status()
            actual_pose = self.read_actual_pose()
            position_error, angle_error = pose_errors(actual_pose, target_pose)
            now = time.monotonic()
            if now >= self._motion_deadline:
                break
            if arrived == 0:
                self._saw_not_arrived = True
            last_state = (
                f"D1012={arrived}, 已见未完成={self._saw_not_arrived}, "
                f"位置误差={position_error:.6f}m, 姿态误差={angle_error:.3f}deg"
            )
            is_at_target = (
                self._saw_not_arrived and arrived == 1
                and position_error <= POSITION_TOLERANCE_M
                and angle_error <= ORIENTATION_TOLERANCE_DEG
            )
            if is_at_target:
                if stable_since is None:
                    stable_since = now
                if now - stable_since >= STABLE_CONFIRM_SECONDS:
                    # 拍照前再确认没有进入报警/暂停或到位信号撤销。
                    if self.read_motion_status() != 1:
                        stable_since = None
                        continue
                    if time.monotonic() >= self._motion_deadline:
                        break
                    self.last_actual_pose = actual_pose
                    self._motion_deadline = None
                    print(f"[PLC] {point_name} 到位并稳定 {STABLE_CONFIRM_SECONDS:.1f}s：{last_state}")
                    print(f"[PLC] 拍照前实际位姿：{actual_pose}")
                    return
            else:
                stable_since = None
            if now >= next_log_time:
                print(f"[PLC] 等待 {point_name} 到位：{last_state}")
                next_log_time = now + 1.0
            time.sleep(min(MOTION_POLL_SECONDS, self._motion_deadline - now))

        self._motion_deadline = None
        raise RuntimeError(
            f"{point_name} 到位超时（{MOTION_TIMEOUT_SECONDS:.1f}s）：{last_state}。"
            "不拍照、不下发下一点；检查启动逻辑、反馈复位及实际位姿单位/字序。"
        )

    def move_to(self, point_name):
        """
        移动到目标并等待到位稳定。

        重要：正常到位后这里【不】清 D1002。
        D1002 必须保持为 1，直到相机拍照完成，避免 PLC 在拍照前让机械臂返回。
        """
        self.last_actual_pose = None
        self.read_motion_status()
        self.write_pose(point_name)
        try:
            self.trigger_move()
            self.wait_for_arrival(point_name)
        except BaseException:
            # 异常时必须尽量撤销启动信号。
            try:
                self.reset_start_signal()
            except Exception as reset_error:
                print(f"[PLC] 警告：异常退出时 D1002 复位失败：{reset_error}")
            raise

        print(f"[PLC] {point_name} 已到位并稳定，保持 D1002=1，等待相机拍照")

    def wait_cycle_reset(self):
        """
        拍照后 D1002=0，再等待本轮 PLC/机械臂真正结束。

        条件：
        1. D1012 已恢复为 0；
        2. D100-D111 实际位姿连续稳定 RESET_STABLE_SECONDS。

        这样可避免 ALL 模式在机械臂还在返回/复位时就写入下一个点。
        """
        deadline = time.monotonic() + RESET_TIMEOUT_SECONDS
        previous_pose = None
        stable_since = None
        next_log_time = 0.0
        last_state = "尚未读取复位状态"

        while time.monotonic() < deadline:
            arrived = self.read_motion_status()
            actual_pose = self.read_actual_pose()
            now = time.monotonic()

            if previous_pose is None:
                position_delta = float('inf')
                angle_delta = float('inf')
            else:
                position_delta, angle_delta = pose_errors(actual_pose, previous_pose)

            last_state = (
                f"D1012={arrived}, 位姿变化={position_delta:.6f}m, "
                f"姿态变化={angle_delta:.3f}deg"
            )

            # 只有到位反馈已经撤销，才开始统计“复位后稳定”。
            if (
                arrived == 0
                and position_delta <= RESET_POSITION_DELTA_M
                and angle_delta <= RESET_ORIENTATION_DELTA_DEG
            ):
                if stable_since is None:
                    stable_since = now
                elif now - stable_since >= RESET_STABLE_SECONDS:
                    print(f"[PLC] 本轮复位完成：{last_state}")
                    return
            else:
                stable_since = None

            if now >= next_log_time:
                print(f"[PLC] 等待本轮复位：{last_state}")
                next_log_time = now + 1.0

            previous_pose = actual_pose
            time.sleep(MOTION_POLL_SECONDS)

        raise RuntimeError(
            f"拍照后等待本轮复位超时（{RESET_TIMEOUT_SECONDS:.1f}s）：{last_state}。"
            "停止 ALL 流程，避免在机械臂仍在返回时发送下一点。"
        )


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
            try:
                self.cam.MV_CC_ClearImageBuffer()
            except Exception:
                pass

        frame_info = mvs.MV_FRAME_OUT_INFO_EX()

        ret = self.cam.MV_CC_GetOneFrameTimeout(
            self.buffer,
            self.payload_size,
            frame_info,
            HIK_FRAME_TIMEOUT_MS
        )

        if ret != 0:
            raise RuntimeError(f"取图失败：0x{ret:x}")

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
        save_path.parent.mkdir(parents=True, exist_ok=True)

        if not cv2.imwrite(str(save_path), bgr):
            raise RuntimeError(f"保存图片失败：{save_path}")

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

    # 1. 写坐标 -> D1002=1 -> 等待目标到位并连续稳定 STABLE_CONFIRM_SECONDS。
    #    move_to() 正常返回时 D1002 仍保持为 1，机械臂应继续停在目标处。
    plc.move_to(point_name)

    try:
        # 2. 已确认到位，但此时仍保持 D1002=1。
        #    再额外静置 PHOTO_DELAY_SECONDS，用于机械结构消振。
        print(
            f"[SYSTEM] {point_name} 已确认到位，"
            f"保持 D1002=1，额外静置 {PHOTO_DELAY_SECONDS:.1f}s 消振"
        )

        time.sleep(PHOTO_DELAY_SECONDS)

        # 3. 静置完成以后再生成文件名并拍照。
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        save_path = SAVE_DIR / f"{point_name}_{timestamp}.jpg"

        print(f"[SYSTEM] {point_name} 消振结束，开始拍照")
        camera.capture(save_path)
        print(f"[SYSTEM] {point_name} 图像已保存：{save_path}")

    finally:
        # 4. 无论拍照成功还是失败，都要撤销本轮启动信号。
        #    注意：必须在拍照之后才允许 D1002=0。
        plc.reset_start_signal()

    # 5. 等 PLC/机械臂完成本轮返回/复位，再允许 ALL 进入下一点。
    plc.wait_cycle_reset()
    print(f"[SYSTEM] {point_name} 本轮结束，可进入下一点")


def main():
    # 默认只跑 P01
    command = "P01"
    if len(sys.argv) >= 2:
        command = sys.argv[1].strip().upper()

    if command != "ALL" and command not in POINTS:
        print("用法：")
        print("  python aubo_hik_capture.py P01")
        print("  python aubo_hik_capture.py P12")
        print("  python aubo_hik_capture.py ALL")
        raise SystemExit(f"未知点位：{command}")

    # 在连接设备/写入任何寄存器前阻止未经确认的多段运动任务。
    if not START_TASK_SINGLE_POSE_CONFIRMED:
        raise SystemExit(
            "启动前核对：D1002 是机台标定启动，D1012 是只读到位反馈。\n"
            "寄存器表还包含 D1040-D1051 终点，请先确认 D1002 是否仅移动到 "
            "D1020-D1031。确认仅执行此目标后，再将 "
            "START_TASK_SINGLE_POSE_CONFIRMED 设置为 True；当前未连接或写入 PLC。"
        )

    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("AUBO + HIK 自动采图")
    print(f"PLC        : {PLC_IP}:{PLC_PORT}")
    print(f"HIK        : {HIK_IP}")
    print(f"Pose       : D1020-D1031")
    print(f"Start      : D{START_REGISTER}=1 保持至拍照完成后复位")
    print(f"Verify     : 坐标写入后读回校验，超时 {POSE_VERIFY_TIMEOUT_SECONDS} s")
    print(f"Arrival    : D{ARRIVAL_REGISTER}=1 + D100-D111 实际位姿校验")
    print(f"Timeout    : {MOTION_TIMEOUT_SECONDS} s")
    print(f"Stable     : 到位后连续稳定确认 {STABLE_CONFIRM_SECONDS} s")
    print(f"PhotoDelay : 确认到位后额外静置 {PHOTO_DELAY_SECONDS} s")
    print(f"Save dir   : {SAVE_DIR.resolve()}")
    print(f"Task       : {command}")
    print("=" * 72)

    plc = RobotPLC()
    camera = HikCamera(HIK_IP)

    try:
        plc.connect()
        camera.open()

        if command == "ALL":
            print()
            print("警告：ALL 会依次执行 P01-P50。")
            print("请确保 50 个点均已在低速下逐点验证路径安全。")
            print()

            for i in range(1, 51):
                run_one_point(plc, camera, f"P{i:02d}")
        else:
            run_one_point(plc, camera, command)

    except KeyboardInterrupt:
        print("\n[SYSTEM] 用户中断程序")

        # 尽量把启动位复位
        try:
            plc.client.write_register(address=START_REGISTER, value=0)
        except Exception:
            pass

    finally:
        camera.close()
        plc.close()


if __name__ == "__main__":
    main()
