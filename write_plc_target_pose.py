"""安全写入 PLC 目标位姿，并可驱动机械臂回到基准观察位姿。

默认从 cross_machine_station_001.json 读取 observation_pose。
脚本先读取并检查 D100-D111 当前位姿；只有同时提供 --execute 和
--confirm-single-pose-task 时，才会写 D1020-D1031、置 D1002=1，
等待 D1012=1 且实际位姿稳定到位，最后清除 D1002 并等待空闲。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from auto_cross_machine_calibration import (
    RobotPLC,
    load_profile,
    pose_errors,
    validate_absolute_target,
    validate_pose,
)


DEFAULT_PROFILE_PATH = Path("cross_machine_station_001.json")
CYCLE_NAME = "RETURN_TO_REFERENCE"


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "将六轴目标写入 D1020-D1031，并通过 D1002/D1012 握手驱动机械臂；"
            "默认目标为 profile.observation_pose，默认仅预览"
        )
    )
    parser.add_argument(
        "--profile",
        type=Path,
        default=DEFAULT_PROFILE_PATH,
        help=(
            "跨机台 profile JSON，默认 cross_machine_station_001.json；"
            "PLC 参数和安全范围也从该文件读取"
        ),
    )
    parser.add_argument(
        "--pose",
        type=float,
        nargs=6,
        metavar=("X", "Y", "Z", "RX", "RY", "RZ"),
        help=(
            "可选目标位姿，覆盖 profile.observation_pose；"
            "XYZ 单位 m，RX/RY/RZ 单位 rad"
        ),
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="真实写 PLC 并执行运动；不提供时只读取、校验和预览",
    )
    parser.add_argument(
        "--confirm-single-pose-task",
        action="store_true",
        help="确认 D1002 只执行 D1020-D1031 中的单一目标",
    )
    return parser


def validate_return_step(
    current_pose: list[float],
    target_pose: list[float],
    profile_path: Path,
    max_translation_m: float,
    max_orientation_deg: float,
) -> tuple[float, float]:
    """验证本次返回运动没有超过 profile 的单步安全阈值。"""
    position_error, orientation_error = pose_errors(
        current_pose,
        target_pose,
    )
    if position_error > max_translation_m:
        raise RuntimeError(
            "返回基准位姿的单步平移超过安全阈值："
            f"{position_error:.6f}m > {max_translation_m:.6f}m；"
            f"请检查 {profile_path} 或改用经现场确认的中间点"
        )
    if orientation_error > max_orientation_deg:
        raise RuntimeError(
            "返回基准位姿的单步姿态变化超过安全阈值："
            f"{orientation_error:.3f}deg > {max_orientation_deg:.3f}deg；"
            f"请检查 {profile_path} 或改用经现场确认的中间点"
        )
    return position_error, orientation_error


def print_motion_preview(
    current_pose: list[float],
    target_pose: list[float],
    position_error: float,
    orientation_error: float,
) -> None:
    print(f"[TARGET] 当前位姿：{current_pose}")
    print(f"[TARGET] 目标位姿：{target_pose}")
    print(
        "[TARGET] 预计运动："
        f"平移={position_error * 1000.0:.3f}mm，"
        f"姿态={orientation_error:.3f}deg"
    )


def main() -> int:
    args = build_argument_parser().parse_args()
    profile_path = args.profile.resolve()
    profile = load_profile(profile_path)
    target_pose = validate_pose(
        args.pose if args.pose is not None else profile.observation_pose,
        "target_pose",
    )
    validate_absolute_target(
        target_pose,
        profile.safety,
        "target_pose",
    )

    if args.execute and not args.confirm_single_pose_task:
        raise RuntimeError(
            "真实运动必须同时提供 --confirm-single-pose-task，"
            "确认 D1002 只执行 D1020-D1031 中的单一目标"
        )

    profile.motion.start_task_single_pose_confirmed = bool(
        args.confirm_single_pose_task
    )
    robot = RobotPLC(profile.motion, profile.safety)
    try:
        robot.connect()
        current_pose = robot.wait_for_idle_stability(
            f"{CYCLE_NAME} 运动前"
        )
        position_error, orientation_error = validate_return_step(
            current_pose=current_pose,
            target_pose=target_pose,
            profile_path=profile_path,
            max_translation_m=profile.safety.max_step_translation_m,
            max_orientation_deg=profile.safety.max_step_orientation_deg,
        )
        print_motion_preview(
            current_pose,
            target_pose,
            position_error,
            orientation_error,
        )

        is_at_target = (
            position_error <= profile.motion.position_tolerance_m
            and orientation_error
            <= profile.motion.orientation_tolerance_deg
        )
        if is_at_target:
            print("[RESULT] 机械臂已经位于基准观察位姿，无需写入或运动")
            return 0
        if not args.execute:
            print(
                "[DRY-RUN] 未写入 PLC。确认现场安全后，"
                "增加 --execute --confirm-single-pose-task 执行"
            )
            return 0

        robot.write_pose(CYCLE_NAME, target_pose)
        robot.ensure_idle()
        saw_not_arrived = robot.trigger_move()
        arrived_pose = robot.wait_for_arrival(
            CYCLE_NAME,
            target_pose,
            saw_not_arrived,
        )
        final_pose = robot.release_and_wait_idle(
            CYCLE_NAME,
            arrived_pose,
        )
        final_position_error, final_orientation_error = pose_errors(
            final_pose,
            target_pose,
        )
        print(f"[RESULT] 最终实际位姿：{final_pose}")
        print(
            "[RESULT] 已回到基准观察位姿："
            f"位置误差={final_position_error * 1000.0:.3f}mm，"
            f"姿态误差={final_orientation_error:.3f}deg"
        )
        return 0
    finally:
        if robot.is_cycle_active:
            print(
                "[SAFETY] 运动循环未完整结束；D1002 或机器人状态可能不确定。"
                "程序未追加运动指令，请现场确认机械臂状态。",
                file=sys.stderr,
            )
        robot.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n[SYSTEM] 用户中断。", file=sys.stderr)
        raise SystemExit(130)
    except Exception as exc:
        print(f"\n[ERROR] {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(2)
