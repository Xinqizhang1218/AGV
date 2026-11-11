"""PLC owns all motion; optional ARCS SDK is used only for inverse kinematics.

Pose convention: base -> flange, metres, R = Rz(rz) @ Ry(ry) @ Rx(rx).
No automatic reset, power-on, error clearing, or motion replay on timeout.
ARCS algorithm reference:
https://docs.aubo-robotics.cn/arcs_api/en/group__RobotAlgorithm.html
"""
from __future__ import annotations

import math
import os
import struct
import time

import cv2
import numpy as np


def pose_matrix(pose):
    values = np.asarray(pose, dtype=float)
    if values.shape != (6,) or not np.isfinite(values).all():
        raise ValueError("位姿必须为六个有限数，单位 m/rad")
    x, y, z = values[3:]
    cx, cy, cz = np.cos([x, y, z])
    sx, sy, sz = np.sin([x, y, z])
    result = np.eye(4)
    result[:3, :3] = np.array([
        [cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx],
        [sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx],
        [-sy, cy * sx, cy * cx],
    ])
    result[:3, 3] = values[:3]
    return result


def matrix_pose(matrix):
    rotation = matrix[:3, :3]
    if abs(rotation[2, 0]) > 0.9999:
        raise ValueError("候选欧拉角接近奇异表示，拒绝")
    return [*matrix[:3, 3].tolist(), math.atan2(rotation[2, 1], rotation[2, 2]),
            math.asin(float(np.clip(-rotation[2, 0], -1, 1))),
            math.atan2(rotation[1, 0], rotation[0, 0])]


def pose_error(first, second):
    first_matrix, second_matrix = pose_matrix(first), pose_matrix(second)
    angle = np.linalg.norm(cv2.Rodrigues(first_matrix[:3, :3].T @ second_matrix[:3, :3])[0])
    return float(np.linalg.norm(first_matrix[:3, 3] - second_matrix[:3, 3])), math.degrees(angle)


def pose_words(pose):
    pose_matrix(pose)
    words = []
    for value in pose:
        high, low = struct.unpack(">HH", struct.pack(">f", value))
        words.extend([low, high])
    return words


def words_pose(words):
    if len(words) != 12:
        raise RuntimeError("实际位姿读取不足 12 words")
    pose = [struct.unpack(">f", struct.pack(">HH", words[i + 1], words[i]))[0]
            for i in range(0, 12, 2)]
    pose_matrix(pose)
    return pose


def check_target(target, current, anchor, limits):
    """Check endpoint constraints; this does not check collision or swept path."""
    pose_matrix(target)
    for index, (low, high) in enumerate(limits["pose_bounds"]):
        value = target[index]
        if index >= 3:
            value += 2 * math.pi * round(((low + high) / 2 - value) / (2 * math.pi))
        if not low <= value <= high:
            raise ValueError(f"第 {index + 1} 轴目标超出允许范围")
    for reference, prefix in ((current, "step"), (anchor, "total")):
        position, angle = pose_error(reference, target)
        if position > limits[f"max_{prefix}_translation_m"] + 1e-9:
            raise ValueError(f"{prefix} 平移超限")
        if angle > limits[f"max_{prefix}_rotation_deg"] + 1e-9:
            raise ValueError(f"{prefix} 旋转超限")


class RobotClient:
    def __init__(self, config):
        self.config = config
        self.motion = config["motion"]
        self.client = None
        self.rpc = None
        self.interface = None
        self.held = False
        self.anchor = None

    def connect(self):
        from pymodbus.client import ModbusTcpClient
        self.client = ModbusTcpClient(self.motion["ip"], port=self.motion["port"],
                                     timeout=self.motion["io_timeout_s"], retries=0)
        if not self.client.connect():
            raise RuntimeError("PLC 连接失败")
        self.anchor = self.wait_stable(None, held=False)
        ik = self.config["ik"]
        if ik["mode"] == "arcs":
            # SDK generation and Euler/base conventions must be checked on site.
            import pyaubo_sdk
            self.rpc = pyaubo_sdk.RpcClient()
            self.rpc.setRequestTimeout(int(self.motion["io_timeout_s"] * 1000))
            self.rpc.connect(ik["ip"], ik["port"])
            if not self.rpc.hasConnected():
                raise RuntimeError("ARCS 连接失败")
            self.rpc.login(os.environ[ik["username_env"]], os.environ[ik["password_env"]])
            if not self.rpc.hasLogined():
                raise RuntimeError("ARCS 登录失败")
            if ik["robot_name"] not in self.rpc.getRobotNames():
                raise RuntimeError("ARCS robot_name 不匹配")
            self.interface = self.rpc.getRobotInterface(ik["robot_name"])

    @staticmethod
    def checked(result):
        if result is None or result.isError():
            raise RuntimeError("PLC 通信失败；若为写操作，结果未知，不自动重试")
        return result

    def read_words(self, address, count):
        words = self.checked(self.client.read_holding_registers(address=address, count=count)).registers
        if len(words) != count:
            raise RuntimeError("PLC 返回寄存器数量错误")
        return words

    def read_pose(self):
        return words_pose(self.read_words(100, 12))

    def state(self):
        start = self.read_words(1002, 1)[0]
        status = self.read_words(1008, 12)
        if any(status[index] for index in (0, 1, 10, 11)):
            raise RuntimeError("PLC 复位/暂停/报警/异常，停止调度")
        arrived = status[4]
        if start not in (0, 1) or arrived not in (0, 1):
            raise RuntimeError("PLC 握手状态无效")
        return start, arrived

    def verify(self, target, held):
        if self.state() != ((1, 1) if held else (0, 0)):
            raise RuntimeError("拍照或准备期间握手状态改变")
        actual = self.read_pose()
        position, angle = pose_error(actual, target)
        if position > self.motion["position_tolerance_m"] or angle > self.motion["rotation_tolerance_deg"]:
            raise RuntimeError("实际位姿离开保持位置")
        return actual

    def wait_stable(self, target, held):
        deadline = time.monotonic() + self.motion["motion_timeout_s"]
        reference = target if target is not None else self.read_pose()
        stable_since = None
        while time.monotonic() < deadline:
            state = self.state()
            if state[0] != int(held):
                raise RuntimeError("启动位与预期不符，停止调度")
            actual = self.read_pose()
            position, angle = pose_error(actual, reference)
            stable = (state[1] == int(held)
                      and position <= self.motion["position_tolerance_m"]
                      and angle <= self.motion["rotation_tolerance_deg"])
            if stable:
                if stable_since is None:
                    stable_since = time.monotonic()
                if time.monotonic() - stable_since >= self.motion["stable_s"]:
                    return actual
            else:
                stable_since = None
                if target is None:
                    reference = actual
            time.sleep(self.motion["poll_s"])
        raise TimeoutError("等待到位/稳定超时，不重发运动命令")

    def reachable(self, target):
        if self.interface is None:
            return True, "仅使用已人工验证的局部运动范围；未检查逆解"
        joints = np.asarray(self.interface.getRobotState().getJointPositions(), dtype=float)
        if joints.shape != (6,) or not np.isfinite(joints).all():
            raise RuntimeError("SDK 关节反馈无效")
        # Explicit zero TCP offset: target is FLANGE pose, never active-tool pose.
        solution, error = self.interface.getRobotAlgorithm().inverseKinematics1(
            joints.tolist(), target, [0.0] * 6)
        if error != 0:
            if error in (-23, -24, -27):
                return False, f"逆解未通过，错误码 {error}"
            raise RuntimeError(f"逆解接口/状态异常 {error}")
        solution = np.asarray(solution, dtype=float)
        if solution.shape != (6,) or not np.isfinite(solution).all():
            raise RuntimeError("逆解结果无效")
        # Do not modulo-wrap joint travel: a full revolution is not a small step.
        if np.max(np.abs(solution - joints)) > math.radians(self.config["ik"]["max_joint_step_deg"]):
            return False, "逆解关节变化过大"
        return True, "逆解通过；未做碰撞检查"

    def move(self, target):
        current = self.wait_stable(None, held=False)
        check_target(target, current, self.anchor, self.config["limits"])
        allowed, reason = self.reachable(target)
        if not allowed:
            return False, reason
        self.verify(current, held=False)
        words = pose_words(target)
        self.checked(self.client.write_registers(address=1020, values=words))
        if self.read_words(1020, 12) != words:
            raise RuntimeError("目标寄存器读回不一致，未启动")
        self.verify(current, held=False)
        self.held = True  # A write timeout is ambiguous; never clear in finally.
        self.checked(self.client.write_register(address=1002, value=1))
        self.wait_stable(target, held=True)
        return True, reason

    def release(self, target):
        if not self.held:
            return
        self.verify(target, held=True)
        self.checked(self.client.write_register(address=1002, value=0))
        self.wait_stable(target, held=False)
        self.held = False

    def close(self):
        # Closing communication is NOT an emergency stop and never clears D1002.
        if self.client is not None:
            self.client.close()
        if self.rpc is not None:
            self.rpc.disconnect()
