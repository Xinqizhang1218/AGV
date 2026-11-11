import math

import cv2
import numpy as np

from agv_vision.core.models import (
    ArucoMarkerPose2D,
    CharucoObservation,
    HandEyeSample,
    StationReference,
)
from agv_vision.vision.compensator import CompensationCalculator
from agv_vision.vision.handeye_calibrator import PlanarHandEyeCalibrator
from agv_vision.vision.pose3d import (
    euler_xyz_to_rotation,
    make_transform,
    solve_charuco_reference_pose_lm,
)


def _rotation_to_euler_xyz(rotation: np.ndarray) -> tuple[float, float, float]:
    ry = math.asin(float(np.clip(-rotation[2, 0], -1.0, 1.0)))
    rx = math.atan2(rotation[2, 1], rotation[2, 2])
    rz = math.atan2(rotation[1, 0], rotation[0, 0])
    return rx, ry, rz


def _rotation_error_deg(first: np.ndarray, second: np.ndarray) -> float:
    relative = first @ second.T
    cosine = float(np.clip((np.trace(relative) - 1.0) / 2.0, -1.0, 1.0))
    return math.degrees(math.acos(cosine))


def test_charuco_station_reference_pose_uses_all_combined_corners() -> None:
    camera_matrix = np.array(
        [[920.0, 0.0, 640.0], [0.0, 915.0, 400.0], [0.0, 0.0, 1.0]],
        dtype=np.float64,
    )
    object_points = np.array(
        [
            [0.03, 0.03], [0.06, 0.03], [0.09, 0.03],
            [0.03, 0.06], [0.06, 0.06], [0.09, 0.06],
        ],
        dtype=np.float32,
    )
    expected_rvec = np.array([[0.08], [-0.05], [0.03]], dtype=np.float64)
    expected_tvec = np.array([[0.01], [-0.02], [0.8]], dtype=np.float64)
    image_points, _ = cv2.projectPoints(
        np.column_stack([object_points, np.zeros(len(object_points))]),
        expected_rvec,
        expected_tvec,
        camera_matrix,
        np.zeros(5),
    )
    image_points = image_points.reshape(-1, 2)
    reference = StationReference(
        station_id='station-001',
        board_center_x=float(image_points[:, 0].mean()),
        board_center_y=float(image_points[:, 1].mean()),
        board_angle_deg=0.0,
        marker_count=0,
        markers=[],
        marker_length_m=0.004,
        preferred_origin_id=2,
        reference_type='charuco',
        charuco_corners=[
            {'id': index, 'x': float(point[0]), 'y': float(point[1])}
            for index, point in enumerate(image_points)
        ],
        charuco_object_points_m=object_points.tolist(),
    )
    actual = solve_charuco_reference_pose_lm(
        reference,
        camera_matrix,
        np.zeros(5),
    )
    expected_rotation, _ = cv2.Rodrigues(expected_rvec)
    assert np.allclose(actual[:3, 3], expected_tvec.reshape(3), atol=1e-5)
    assert _rotation_error_deg(actual[:3, :3], expected_rotation) < 0.01


def test_full_charuco_camera_pnp_handeye_pipeline() -> None:
    camera_matrix = np.array(
        [[920.0, 0.0, 640.0], [0.0, 915.0, 400.0], [0.0, 0.0, 1.0]],
        dtype=np.float64,
    )
    gtc_expected = make_transform(
        euler_xyz_to_rotation(math.radians(4), math.radians(-7), math.radians(12)),
        np.array([0.045, -0.018, 0.082]),
    )
    btt = make_transform(
        euler_xyz_to_rotation(0.1, -0.05, 0.25),
        np.array([0.45, -0.20, 0.12]),
    )
    board_xy = np.array(
        [[x * 0.03, y * 0.03] for y in range(5) for x in range(6)],
        dtype=np.float32,
    )
    board_xyz = np.column_stack([board_xy, np.zeros(len(board_xy), dtype=np.float32)])
    samples: list[HandEyeSample] = []
    views = [
        (-16, -10, -12, -0.08, -0.05, 0.72),
        (-12, 13, 8, 0.03, -0.04, 0.76),
        (15, -8, 18, -0.04, 0.04, 0.80),
        (10, 14, -20, 0.06, 0.02, 0.74),
        (-18, 7, 25, -0.02, 0.06, 0.83),
        (8, -15, -28, 0.07, -0.02, 0.78),
        (17, 11, 5, -0.06, 0.01, 0.86),
        (-9, -17, 30, 0.01, -0.06, 0.81),
        (13, 5, -8, 0.05, 0.05, 0.75),
        (-14, 16, 15, -0.05, -0.01, 0.84),
    ]
    for index, (rx_deg, ry_deg, rz_deg, tx, ty, tz) in enumerate(views):
        ctt = make_transform(
            euler_xyz_to_rotation(
                math.radians(rx_deg), math.radians(ry_deg), math.radians(rz_deg)
            ),
            np.array([tx, ty, tz]),
        )
        btg = btt @ np.linalg.inv(ctt) @ np.linalg.inv(gtc_expected)
        rvec, _ = cv2.Rodrigues(ctt[:3, :3])
        image_points, _ = cv2.projectPoints(
            board_xyz, rvec, ctt[:3, 3], camera_matrix, np.zeros(5)
        )
        image_points = image_points.reshape(-1, 2)
        marker_object_points = board_xyz[:28].reshape(7, 4, 3)
        marker_image_points = image_points[:28].reshape(7, 4, 2)
        robot_rx, robot_ry, robot_rz = _rotation_to_euler_xyz(btg[:3, :3])
        samples.append(
            HandEyeSample(
                sample_id=f'p{index:02d}',
                robot_x_m=float(btg[0, 3]),
                robot_y_m=float(btg[1, 3]),
                observation=CharucoObservation(
                    image_points=image_points.tolist(),
                    board_points_m=board_xy.tolist(),
                    corner_count=len(board_xy),
                    marker_image_points=marker_image_points.tolist(),
                    marker_object_points_m=marker_object_points.tolist(),
                    marker_ids=list(range(7)),
                ),
                meta={
                    'z': float(btg[2, 3]),
                    'rx': robot_rx,
                    'ry': robot_ry,
                    'rz': robot_rz,
                    'image_width_px': 1280,
                    'image_height_px': 800,
                },
            )
        )

    result = PlanarHandEyeCalibrator().solve(samples)
    pose3d = result.angle_calibration['pose3d']
    gtc_actual = np.asarray(pose3d['gTc'])
    assert pose3d['handEyeMethod'] in ('Tsai', 'Park')
    assert np.linalg.norm(gtc_actual[:3, 3] - gtc_expected[:3, 3]) < 0.003
    assert _rotation_error_deg(gtc_actual[:3, :3], gtc_expected[:3, :3]) < 0.5

    fixed_result = PlanarHandEyeCalibrator(
        camera_matrix=camera_matrix.tolist(),
        dist_coeffs=[0.0, 0.0, 0.0, 0.0, 0.0],
        image_size=[1280, 800],
        calibration_rms_px=0.0,
        intrinsics_source='synthetic-test',
    ).solve(samples)
    fixed_pose3d = fixed_result.angle_calibration['pose3d']
    fixed_gtc = np.asarray(fixed_pose3d['gTc'])
    assert fixed_pose3d['pipeline'].startswith('Fixed-intrinsics-')
    assert fixed_pose3d['intrinsicsSource'] == 'synthetic-test'
    assert fixed_pose3d['cameraMatrix'] == camera_matrix.tolist()
    assert np.linalg.norm(fixed_gtc[:3, 3] - gtc_expected[:3, 3]) < 0.003
    assert _rotation_error_deg(fixed_gtc[:3, :3], gtc_expected[:3, :3]) < 0.5


def test_online_aruco_pnp_lm_gtc_ctt_compensation() -> None:
    camera_matrix = np.array(
        [[900.0, 0.0, 640.0], [0.0, 900.0, 400.0], [0.0, 0.0, 1.0]]
    )
    marker_length = 0.15
    half = marker_length / 2.0
    object_points = np.array(
        [[-half, half, 0], [half, half, 0], [half, -half, 0], [-half, -half, 0]],
        dtype=np.float32,
    )
    rotation = euler_xyz_to_rotation(0.0, 0.0, math.radians(18.0))
    rvec, _ = cv2.Rodrigues(rotation)
    translation = np.array([0.11, -0.035, 0.85])
    corners, _ = cv2.projectPoints(object_points, rvec, translation, camera_matrix, np.zeros(5))
    corners = corners.reshape(4, 2)
    marker = ArucoMarkerPose2D(
        marker_id=0,
        center_x=float(corners[:, 0].mean()),
        center_y=float(corners[:, 1].mean()),
        angle_deg=18.0,
        corners=corners.tolist(),
    )
    current = StationReference(
        station_id='s',
        board_center_x=marker.center_x,
        board_center_y=marker.center_y,
        board_angle_deg=18.0,
        marker_count=1,
        markers=[marker],
        marker_length_m=marker_length,
        preferred_origin_id=0,
    )
    reference_rvec = np.zeros((3, 1), dtype=np.float64)
    reference_translation = np.array([0.0, 0.0, 0.85])
    reference_corners, _ = cv2.projectPoints(
        object_points,
        reference_rvec,
        reference_translation,
        camera_matrix,
        np.zeros(5),
    )
    reference_corners = reference_corners.reshape(4, 2)
    reference_marker = ArucoMarkerPose2D(
        marker_id=0,
        center_x=float(reference_corners[:, 0].mean()),
        center_y=float(reference_corners[:, 1].mean()),
        angle_deg=0.0,
        corners=reference_corners.tolist(),
    )
    reference = StationReference(
        station_id='s',
        board_center_x=640.0,
        board_center_y=400.0,
        board_angle_deg=0.0,
        marker_count=1,
        markers=[reference_marker],
        marker_length_m=marker_length,
        preferred_origin_id=0,
    )
    result = CompensationCalculator(3000.0).compute(
        reference,
        current,
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        None,
        {
            'pose3d': {
                'cameraMatrix': camera_matrix.tolist(),
                'distCoeffs': [0.0] * 5,
                'gTc': np.eye(4).tolist(),
            }
        },
    )
    assert abs(result.dx_m_robot - 0.11) < 1e-5
    assert abs(result.dy_m_robot + 0.035) < 1e-5
    assert abs(result.dtheta_deg - 18.0) < 1e-4


def test_existing_java_handeye_fields_carry_pose3d_unchanged() -> None:
    import pytest

    pytest.importorskip('fastapi')
    from agv_vision.api.app import (
        _handeye_result_to_java_data,
        _normalize_handeye_payload,
    )

    pose3d = {
        'version': 1,
        'cameraMatrix': np.eye(3).tolist(),
        'distCoeffs': [0.0] * 5,
        'gTc': np.eye(4).tolist(),
    }
    java_payload = _handeye_result_to_java_data(
        {
            'matrix_2x3': [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
            'rmse_m': 0.0001,
            'sample_count': 10,
            'calibration_type': 'charuco_calibrateCamera_pnp_handeye_tsai_park_3d',
            'calibration_pixels_per_m': None,
            'angle_calibration': {'pose3d': pose3d},
        }
    )
    assert set(java_payload) == {'rmseM', 'sampleCount', 'pose3d'}
    normalized = _normalize_handeye_payload({'handeye': java_payload})
    assert normalized['angle_calibration']['pose3d'] == pose3d
