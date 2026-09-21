"""依次返回目标位姿、运行一轮视觉补偿，默认重复 30 次。

不带 --execute 时只做离线配置检查，不连接设备。复用两个现有脚本，
不重试失败动作、不自动清除异常握手。正常完成但视觉未收敛的轮次会继续。
"""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

import auto_cross_machine_calibration as calibration
import write_plc_target_pose as return_motion


TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TOOLS_DIR.parent


class Tee:
    """同时输出到终端和当前步骤日志。"""

    def __init__(self, terminal, log):
        self.terminal = terminal
        self.log = log

    def write(self, text):
        self.terminal.write(text)
        self.log.write(text)
        self.flush()
        return len(text)

    def flush(self):
        self.terminal.flush()
        self.log.flush()


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--return-profile", type=Path,
                        default=TOOLS_DIR / "cross_machine_station_001.json")
    parser.add_argument("--profile", type=Path,
                        default=PROJECT_DIR / "cross_machine_station_002_09212.json")
    parser.add_argument("--handeye-json", type=Path,
                        default=TOOLS_DIR / "capture_images6cm09212/handeye_api.json")
    parser.add_argument("--cycles", type=int, default=30)
    parser.add_argument("--output-dir", type=Path,
                        default=PROJECT_DIR / "outputs/repeat_cross_machine")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-same-camera", action="store_true")
    parser.add_argument("--confirm-single-pose-task", action="store_true")
    return parser


def preflight(args):
    """在任何运动之前同时验证两个配置及手眼一致性。"""
    if args.cycles < 1:
        raise ValueError("--cycles 必须至少为 1")
    for name in ("return_profile", "profile", "handeye_json"):
        path = getattr(args, name).expanduser().resolve()
        if not path.is_file():
            raise ValueError(f"文件不存在：{path}")
        setattr(args, name, path)
    returning = calibration.load_profile(args.return_profile)
    vision = calibration.load_profile(args.profile)
    calibration.validate_profile(returning)
    calibration.validate_profile(vision)
    handeye = calibration.extract_handeye_document(
        calibration.read_json(args.handeye_json))
    for key in ("cameraMatrix", "distCoeffs", "gTc"):
        if not np.array_equal(np.asarray(handeye["pose3d"][key]),
                              np.asarray(vision.handeye["pose3d"][key])):
            raise ValueError(f"{key} 与视觉基准不一致，请先重新采集对应基准")
    if (returning.motion.plc_ip, returning.motion.plc_port) != (
            vision.motion.plc_ip, vision.motion.plc_port):
        raise ValueError("返回配置和视觉配置的 PLC 地址不同")
    calibration.validate_absolute_target(
        returning.observation_pose, returning.safety, "返回目标")
    calibration.validate_absolute_target(
        returning.observation_pose, vision.safety, "视觉初始位置")
    distance, angle = calibration.pose_errors(
        returning.observation_pose, vision.observation_pose)
    if (distance > vision.motion.position_tolerance_m
            or angle > vision.motion.orientation_tolerance_deg):
        raise ValueError(
            f"返回目标与视觉观察位姿不匹配：{distance * 1000:.4f}mm / "
            f"{angle:.4f}deg；请核对两个 profile")
    if args.execute and not (
            args.confirm_same_camera and args.confirm_single_pose_task):
        raise ValueError("执行需同时提供 --confirm-same-camera 和 "
                         "--confirm-single-pose-task")
    return vision


def run_return(profile):
    # 同进程调用使 Ctrl+C 沿现有 finally 清理路径传播，不留下后台子进程。
    original_argv = sys.argv
    try:
        sys.argv = [str(TOOLS_DIR / "write_plc_target_pose.py"),
                    "--profile", str(profile), "--execute",
                    "--confirm-single-pose-task"]
        return return_motion.main()
    finally:
        sys.argv = original_argv


def run_vision(args, report_path):
    command = ["run", "--profile", str(args.profile),
               "--handeye-json", str(args.handeye_json),
               "--start-from-current-pose", "--rounds", "1",
               "--confirm-same-camera", "--confirm-single-pose-task",
               "--report", str(report_path), "--execute"]
    parsed = calibration.build_argument_parser().parse_args(command)
    return calibration.run_automatic_calibration(parsed)


def check_finished_report(report_path, exit_code):
    """只接受正常结束的整轮报告；退出码 1 不能单独当成可继续证据。"""
    report = calibration.read_json(report_path)
    status = report.get("status")
    expected = {"VISUAL_PASS": 0, "FAIL_NOT_CONVERGED": 1}
    trials = report.get("trials", [])
    if (status not in expected or exit_code != expected[status]
            or report.get("error") or not report.get("finished_at")
            or len(trials) != 1 or trials[0].get("status") != status
            or not trials[0].get("final")):
        raise RuntimeError(f"本轮没有正常完成，停止后续循环：{report_path}")
    return status


def run_logged(log_path, function, *args):
    with log_path.open("w", encoding="utf-8") as log:
        with contextlib.redirect_stdout(Tee(sys.stdout, log)), \
                contextlib.redirect_stderr(Tee(sys.stderr, log)):
            try:
                return function(*args)
            except BaseException as exc:
                print(f"[STOP] {type(exc).__name__}: {exc}", file=sys.stderr)
                raise


def execute_cycles(args, vision):
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output = args.output_dir.expanduser().resolve() / run_id
    output.mkdir(parents=True, exist_ok=False)
    # 固定本次输入快照，防止 30 轮期间编辑源配置造成参数混用。
    for name in ("return_profile", "profile", "handeye_json"):
        source = getattr(args, name)
        target = output / f"{name}.json"
        target.write_bytes(source.read_bytes())
        setattr(args, name, target)
    # 相对图像目录的语义依赖启动目录，记录绝对解释便于查找。
    image_dir = Path(vision.vision_image_dir).expanduser()
    summary = {"status": "RUNNING", "requested_cycles": args.cycles,
               "started_at": datetime.now().isoformat(),
               "vision_image_dir": str(image_dir),
               "working_directory": str(Path.cwd()), "cycles": []}
    summary_path = output / "loop_summary.json"

    def save():
        temporary = output / "loop_summary.tmp"
        temporary.write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                             encoding="utf-8")
        temporary.replace(summary_path)

    save()
    print(f"[LOOP] 报告与日志：{output}")
    try:
        for index in range(1, args.cycles + 1):
            folder = output / f"cycle_{index:03d}"
            folder.mkdir()
            record = {"cycle": index, "status": "RETURNING",
                      "started_at": datetime.now().isoformat(),
                      "report": str(folder / "calibration_report.json")}
            summary["cycles"].append(record)
            save()
            print(f"\n[LOOP] 第 {index}/{args.cycles} 轮：返回目标位姿")
            code = run_logged(folder / "return.log", run_return, args.return_profile)
            if code != 0:
                raise RuntimeError(f"返回步骤失败，退出码 {code}")
            record["status"] = "CALIBRATING"
            save()
            print(f"[LOOP] 第 {index}/{args.cycles} 轮：视觉补偿")
            report_path = Path(record["report"])
            code = run_logged(folder / "vision.log", run_vision, args, report_path)
            record["status"] = check_finished_report(report_path, code)
            record["finished_at"] = datetime.now().isoformat()
            save()
            print(f"[LOOP] 第 {index}/{args.cycles} 轮完成：{record['status']}")
        summary["status"] = "COMPLETED"
    except BaseException as exc:
        summary["status"] = "ABORTED"
        summary["error"] = f"{type(exc).__name__}: {exc}"
        if summary["cycles"]:
            summary["cycles"][-1]["status"] = "ABORTED"
        print("[STOP] 不再启动下一轮，也不追加 PLC 清零或重试。"
              "若运动中断，请现场核对机器人和 D1002 状态。")
        raise
    finally:
        summary["finished_at"] = datetime.now().isoformat()
        save()
        print(f"[LOOP] 汇总：{summary_path}")
    return 0


def main():
    args = build_parser().parse_args()
    vision = preflight(args)
    print(f"返回配置：{args.return_profile}\n视觉配置：{args.profile}\n"
          f"手眼文件：{args.handeye_json}\n循环次数：{args.cycles}\n"
          f"图片目录：{vision.vision_image_dir}")
    if not args.execute:
        print("[DRY-RUN] 离线检查通过；未连接 PLC 或视觉服务。")
        return 0
    return execute_cycles(args, vision)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("[SYSTEM] 用户中断。", file=sys.stderr)
        raise SystemExit(130)
    except Exception as exc:
        print(f"[ERROR] {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(2)
