"""只读 PLC D100-D111，解析机械臂当前六轴坐标。

D100-D111 共 12 个 holding register，每两个 word 组成一个 float32：
X、Y、Z 的单位为 m，RX、RY、RZ 的单位为 rad。

本脚本不会写入任何 PLC 寄存器。
"""

from __future__ import annotations

import argparse
import math
import struct
import sys
import time
from datetime import datetime
from typing import Any

from pymodbus.client import ModbusTcpClient


DEFAULT_PLC_IP = "192.168.1.88"
DEFAULT_PLC_PORT = 502
DEFAULT_TIMEOUT_SECONDS = 3.0
DEFAULT_WATCH_INTERVAL_SECONDS = 0.5
ACTUAL_POSE_START_REGISTER = 100
ACTUAL_POSE_REGISTER_COUNT = 12
POSE_FIELD_NAMES = ("X", "Y", "Z", "RX", "RY", "RZ")
WORD_ORDER_LOW_HIGH = "low_high"
WORD_ORDER_HIGH_LOW = "high_low"


def check_modbus_result(result: Any, action: str) -> None:
    """检查 pymodbus 返回值。"""
    if result is None:
        raise RuntimeError(f"{action}失败：PLC 返回 None")
    if hasattr(result, "isError") and result.isError():
        raise RuntimeError(f"{action}失败：{result}")


def words_to_float(
    first_word: int,
    second_word: int,
    word_order: str,
) -> float:
    """将两个 16 位寄存器按指定字序解析为 float32。"""
    if word_order == WORD_ORDER_LOW_HIGH:
        low_word, high_word = first_word, second_word
    elif word_order == WORD_ORDER_HIGH_LOW:
        high_word, low_word = first_word, second_word
    else:
        raise ValueError(f"不支持的 word 顺序：{word_order}")

    return struct.unpack(
        ">f",
        struct.pack(">HH", high_word, low_word),
    )[0]


def registers_to_pose(registers: list[int], word_order: str) -> list[float]:
    """将 D100-D111 的 12 个 word 解析为六轴坐标。"""
    if len(registers) != ACTUAL_POSE_REGISTER_COUNT:
        raise RuntimeError(
            "D100-D111 应返回 "
            f"{ACTUAL_POSE_REGISTER_COUNT} 个 word，实际为 {len(registers)}"
        )

    pose = [
        words_to_float(
            registers[index],
            registers[index + 1],
            word_order,
        )
        for index in range(0, ACTUAL_POSE_REGISTER_COUNT, 2)
    ]
    if not all(math.isfinite(value) for value in pose):
        raise RuntimeError(f"D100-D111 解析结果包含 NaN 或 Inf：{pose}")
    return pose


def read_current_pose(
    client: ModbusTcpClient,
    word_order: str,
) -> tuple[list[int], list[float]]:
    """读取一次 D100-D111，不执行任何写操作。"""
    result = client.read_holding_registers(
        address=ACTUAL_POSE_START_REGISTER,
        count=ACTUAL_POSE_REGISTER_COUNT,
    )
    check_modbus_result(result, "读取 D100-D111")
    registers = getattr(result, "registers", None)
    if not isinstance(registers, list):
        raise RuntimeError(f"D100-D111 返回格式异常：{registers}")

    raw_registers = [int(value) for value in registers]
    pose = registers_to_pose(raw_registers, word_order)
    return raw_registers, pose


def print_pose(registers: list[int], pose: list[float], show_raw: bool) -> None:
    """输出读取时间、原始寄存器和六轴坐标。"""
    timestamp = datetime.now().isoformat(timespec="milliseconds")
    print(f"\n[{timestamp}] D100-D111 机械臂当前坐标")
    if show_raw:
        print(f"原始 12 word：{registers}")

    for index, (field_name, value) in enumerate(
        zip(POSE_FIELD_NAMES, pose)
    ):
        if index < 3:
            print(
                f"{field_name:>2} = {value: .9f} m"
                f"  ({value * 1000.0: .3f} mm)"
            )
        else:
            print(
                f"{field_name:>2} = {value: .9f} rad"
                f"  ({math.degrees(value): .3f} deg)"
            )
    print(f"pose = {pose}")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "只读 PLC D100-D111，并解析为 X/Y/Z/RX/RY/RZ；"
            "不会写入任何寄存器"
        )
    )
    parser.add_argument("--plc-ip", default=DEFAULT_PLC_IP)
    parser.add_argument("--plc-port", type=int, default=DEFAULT_PLC_PORT)
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="PLC 通信超时秒数，默认 3",
    )
    parser.add_argument(
        "--word-order",
        choices=(WORD_ORDER_LOW_HIGH, WORD_ORDER_HIGH_LOW),
        default=WORD_ORDER_LOW_HIGH,
        help="float32 的两个 word 顺序，默认 low_high",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="同时显示 D100-D111 的原始 12 个 word",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="持续读取；默认只读取一次",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_WATCH_INTERVAL_SECONDS,
        help="持续读取间隔秒数，默认 0.5",
    )
    return parser


def main() -> int:
    args = build_argument_parser().parse_args()
    if not 1 <= args.plc_port <= 65535:
        raise ValueError("--plc-port 必须在 1-65535 范围内")
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        raise ValueError("--timeout 必须是有限正数")
    if not math.isfinite(args.interval) or args.interval <= 0:
        raise ValueError("--interval 必须是有限正数")

    client = ModbusTcpClient(
        args.plc_ip,
        port=args.plc_port,
        timeout=args.timeout,
        retries=0,
    )
    print(f"[PLC] 连接 {args.plc_ip}:{args.plc_port} ...")
    try:
        if not client.connect():
            raise RuntimeError(
                f"无法连接 PLC：{args.plc_ip}:{args.plc_port}"
            )
        print("[PLC] 连接成功；当前为只读模式")

        while True:
            registers, pose = read_current_pose(client, args.word_order)
            print_pose(registers, pose, args.raw)
            if not args.watch:
                return 0
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n[SYSTEM] 用户停止持续读取")
        return 130
    finally:
        client.close()
        print("[PLC] 连接已关闭")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"\n[ERROR] {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(2)
