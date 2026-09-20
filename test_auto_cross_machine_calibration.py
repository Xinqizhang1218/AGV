"""离线回归：不连接 PLC、相机或 HTTP 服务。"""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import auto_cross_machine_calibration as calibration


class AutomaticValidationTests(unittest.TestCase):
    def setUp(self):
        self.pose = [-0.51485, 0.00473, 0.47268, -3.141, 0.0, 0.757]
        self.profile = calibration.CalibrationProfile('test', self.pose, {}, {})
        self.profile.safety.workspace_limits_m = {
            'x': [-0.65, -0.35], 'y': [-0.15, 0.15], 'z': [0.35, 0.60]}
        self.profile.safety.orientation_limits_rad = {
            'rx': [-3.20, -3.00], 'ry': [-0.20, 0.20], 'rz': [0.50, 1.00]}
        self.profile.convergence.verification_interval_seconds = 0

    def response(self, residual):
        pose = [residual, 0, 0, 0, 0, 0]
        result = calibration.CompensationResult(
            pose, calibration.resolve_delta_target_pose(self.pose, pose, 1),
            abs(residual), 0, 'test', 'image.jpg', {})
        record = {'actual_pose_before': self.pose, 'residual_xyz_mm': [residual * 1000, 0, 0],
                  'residual_xy_mm': abs(residual) * 1000,
                  'residual_position_m': abs(residual), 'residual_orientation_deg': 0}
        return result, record

    def execute(self, responses, targets):
        robot = Mock()
        robot.move_and_hold.return_value = (self.pose, self.pose)
        report = {'trials': [], 'observations': []}
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(calibration, 'request_and_verify_compensation', side_effect=responses):
                code = calibration.execute_validation_trials(
                    self.profile, robot, Mock(), targets, 'test', report,
                    Path(directory) / 'report.json')
        return code, report, robot

    def test_pi_boundary_preserves_robot_branch(self):
        target = calibration.resolve_delta_target_pose(self.pose, [0.001, 0, 0, -0.002, 0, 0], 1)
        self.assertAlmostEqual(target[3], -3.143)
        calibration.validate_candidate_target(target, self.pose, self.pose, self.profile.safety)
        self.assertAlmostEqual(calibration.pose_errors(self.pose, target)[1], 0.114591559, places=6)

    def test_independent_rounds_reset_and_do_not_count_confirmations(self):
        responses = [self.response(v) for v in [0.002, 0.0002, 0.0001, 0.003, 0.0003, 0.0002]]
        code, report, robot = self.execute(responses, [self.pose, self.pose])
        self.assertEqual(code, 0)
        self.assertEqual(robot.move_and_hold.call_count, 4)
        self.assertEqual(robot.release_and_wait_return.call_count, 4)
        self.assertEqual(robot.move_and_hold.call_args_list[2].args[1], self.pose)
        self.assertEqual(report['summary']['after_first_correction']['sample_count'], 2)
        self.assertEqual(report['summary']['final']['sample_count'], 2)
        self.assertAlmostEqual(report['summary']['after_first_correction']['metrics']['xyz_mm']['max_abs'], 0.3)
        self.assertEqual(len(report['observations']), 6)

    def test_non_convergence_is_counted_and_next_round_runs(self):
        self.profile.convergence.max_corrections = 0
        code, report, robot = self.execute(
            [self.response(0.01), self.response(0), self.response(0)], [self.pose, self.pose])
        self.assertEqual(code, 1)
        self.assertEqual(report['summary']['not_converged_count'], 1)
        self.assertEqual(report['summary']['passed_count'], 1)
        self.assertEqual(report['summary']['after_first_correction']['sample_count'], 0)
        self.assertEqual(robot.release_and_wait_return.call_count, 2)

    def test_motion_failure_does_not_release_or_advance(self):
        robot = Mock()
        robot.move_and_hold.side_effect = RuntimeError('PLC response unknown')
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, 'unknown'):
                calibration.execute_validation_trials(
                    self.profile, robot, Mock(), [self.pose, self.pose], 'test',
                    {'trials': [], 'observations': []}, Path(directory) / 'report.json')
        robot.release_and_wait_return.assert_not_called()
        self.assertEqual(robot.move_and_hold.call_count, 1)

    def test_reject_unsafe_offset_before_motion(self):
        with self.assertRaises(RuntimeError):
            calibration.build_trial_targets(self.profile, [[0.1, 0, 0, 0, 0, 0]])


if __name__ == '__main__':
    unittest.main()
