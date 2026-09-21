"""离线验证循环调度；所有运动及视觉执行入口均替换为模拟函数。"""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import repeat_cross_machine_calibration as loop


class RepeatCalibrationTests(unittest.TestCase):
    def exercise(self, failure=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input.json"
            source.write_text("{}", encoding="utf-8")
            args = SimpleNamespace(output_dir=root, return_profile=source,
                                   profile=source, handeye_json=source, cycles=30)
            vision = SimpleNamespace(vision_image_dir="D:/data/test")
            calls = []

            def returning(_profile):
                calls.append("return")
                if failure == "return":
                    raise RuntimeError("simulated PLC timeout")
                return 0

            def observing(_args, report):
                calls.append("vision")
                if failure == "interrupt":
                    raise KeyboardInterrupt()
                status = "FAIL_NOT_CONVERGED"
                data = {"status": status, "finished_at": "test",
                        "trials": [{"status": status, "final": {"test": True}}]}
                if failure == "aborted":
                    data["status"] = "ABORTED"
                report.write_text(json.dumps(data), encoding="utf-8")
                return 1

            caught = None
            with patch.object(loop, "run_return", side_effect=returning), \
                    patch.object(loop, "run_vision", side_effect=observing), \
                    contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(io.StringIO()):
                try:
                    loop.execute_cycles(args, vision)
                except BaseException as exc:
                    caught = exc
            summary = json.loads(next(root.rglob("loop_summary.json")).read_text(
                encoding="utf-8"))
            return calls, caught, summary

    def test_thirty_complete_nonconverged_rounds(self):
        calls, caught, summary = self.exercise()
        self.assertIsNone(caught)
        self.assertEqual(calls, ["return", "vision"] * 30)
        self.assertEqual(summary["status"], "COMPLETED")
        self.assertEqual(len(summary["cycles"]), 30)
        self.assertEqual(len({r["report"] for r in summary["cycles"]}), 30)

    def test_return_timeout_prevents_vision_and_next_cycle(self):
        calls, caught, summary = self.exercise("return")
        self.assertEqual(calls, ["return"])
        self.assertIsInstance(caught, RuntimeError)
        self.assertEqual(summary["status"], "ABORTED")

    def test_exit_one_with_aborted_report_stops(self):
        calls, caught, summary = self.exercise("aborted")
        self.assertEqual(calls, ["return", "vision"])
        self.assertIsInstance(caught, RuntimeError)
        self.assertEqual(summary["status"], "ABORTED")

    def test_interrupt_prevents_next_cycle(self):
        calls, caught, summary = self.exercise("interrupt")
        self.assertEqual(calls, ["return", "vision"])
        self.assertIsInstance(caught, KeyboardInterrupt)
        self.assertEqual(summary["status"], "ABORTED")


if __name__ == "__main__":
    unittest.main()
