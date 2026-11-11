from __future__ import annotations

import numpy as np

from agv_vision.core.exceptions import CalibrationError
from agv_vision.core.models import HandEyeCalibrationResult, HandEyeSample
from agv_vision.vision.pose3d import build_pose3d_calibration


class PlanarHandEyeCalibrator:
    """保留原类名和调用接口，内部只执行完整 3D 手眼标定。"""

    RMSE_WARNING_M = 0.001
    MAX_ACCEPTABLE_RMSE_M = 0.010
    MAX_ACCEPTABLE_ROTATION_RMSE_DEG = 5.0

    def __init__(
        self,
        camera_matrix=None,
        dist_coeffs=None,
        image_size=None,
        calibration_rms_px: float | None = None,
        intrinsics_source: str | None = None,
    ):
        self.camera_matrix = camera_matrix
        self.dist_coeffs = dist_coeffs
        self.image_size = image_size
        self.calibration_rms_px = calibration_rms_px
        self.intrinsics_source = intrinsics_source

    def solve(self, samples: list[HandEyeSample]) -> HandEyeCalibrationResult:
        if len(samples) < 5:
            raise CalibrationError('完整 3D 手眼标定至少需要 5 组 ChArUco + 六轴姿态样本')
        for sample in samples:
            missing = [
                field for field in ('z', 'rx', 'ry', 'rz')
                if (sample.meta or {}).get(field) is None
            ]
            if missing:
                raise CalibrationError(f'样本 {sample.sample_id} 缺少六轴姿态字段: {missing}')

        pose3d, handeye_rmse_m = build_pose3d_calibration(
            samples,
            fixed_camera_matrix=self.camera_matrix,
            fixed_dist_coeffs=self.dist_coeffs,
            fixed_image_size=self.image_size,
            fixed_calibration_rms_px=self.calibration_rms_px,
            fixed_intrinsics_source=self.intrinsics_source,
        )
        selected_method = pose3d['handEyeMethod']
        selected_metrics = pose3d['handEyeCandidates'][selected_method]
        rotation_rmse_deg = float(selected_metrics['rotationRmseDeg'])
        if (
            handeye_rmse_m > self.MAX_ACCEPTABLE_RMSE_M
            or rotation_rmse_deg > self.MAX_ACCEPTABLE_ROTATION_RMSE_DEG
        ):
            raise CalibrationError(
                '手眼标定质量不合格：'
                f'固定标定板平移 RMSE={handeye_rmse_m * 1000:.3f}mm '
                f'(上限 {self.MAX_ACCEPTABLE_RMSE_M * 1000:.1f}mm)，'
                f'旋转 RMSE={rotation_rmse_deg:.3f}deg '
                f'(上限 {self.MAX_ACCEPTABLE_ROTATION_RMSE_DEG:.1f}deg)；'
                '请确认 x/y/z 使用米、rx/ry/rz 使用弧度，并增加不同方向的 RX/RY 倾斜姿态后重新采集'
            )
        gtc = np.asarray(pose3d['gTc'], dtype=np.float64)
        matrix_2x3 = [
            [float(gtc[0, 0]), float(gtc[0, 1]), float(gtc[0, 3])],
            [float(gtc[1, 0]), float(gtc[1, 1]), float(gtc[1, 3])],
        ]
        return HandEyeCalibrationResult(
            matrix_2x3=matrix_2x3,
            rmse_m=float(handeye_rmse_m),
            sample_count=len(samples),
            calibration_type='charuco_calibrateCamera_pnp_handeye_tsai_park_3d',
            angle_calibration={'pose3d': pose3d},
        )
