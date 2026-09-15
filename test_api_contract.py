from __future__ import annotations

import math
import sys
import types

import numpy as np
import pytest

try:
    import fastapi  # noqa: F401
except ModuleNotFoundError:
    fastapi_stub = types.ModuleType('fastapi')

    class _FastAPI:
        def __init__(self, *args, **kwargs):
            pass

        @staticmethod
        def _decorator(*args, **kwargs):
            return lambda function: function

        get = _decorator
        post = _decorator
        middleware = _decorator
        on_event = _decorator

    class _HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail

    fastapi_stub.Body = lambda default=..., **kwargs: default
    fastapi_stub.FastAPI = _FastAPI
    fastapi_stub.HTTPException = _HTTPException
    fastapi_stub.Request = type('Request', (), {})
    fastapi_stub.Response = type('Response', (), {})
    sys.modules['fastapi'] = fastapi_stub

import agv_vision.api.app as api_module
from agv_vision.core.models import CharucoObservation, HandEyeSample
from agv_vision.vision.pose3d import euler_xyz_to_rotation, robot_pose_to_transform


POSE3D = {
    'version': 1,
    'cameraMatrix': [
        [1000.0, 0.0, 640.0],
        [0.0, 1000.0, 360.0],
        [0.0, 0.0, 1.0],
    ],
    'distCoeffs': [0.0, 0.0, 0.0, 0.0, 0.0],
    'gTc': [
        [1.0, 0.0, 0.0, 0.01],
        [0.0, 1.0, 0.0, 0.02],
        [0.0, 0.0, 1.0, 0.03],
        [0.0, 0.0, 0.0, 1.0],
    ],
    'imageSize': [1920, 1080],
    'cameraCalibrationRmsPx': 0.25,
    'handEyeMethod': 'Tsai',
    'handEyeCandidates': {'Tsai': {'ok': True}},
    'robotEulerConvention': 'Rz*Ry*Rx; rad input',
}


def _handeye_data() -> dict:
    return {
        'rmseM': 0.0004,
        'sampleCount': 12,
        'pose3d': POSE3D,
    }


def _reference_data() -> dict:
    return {
        'stationId': 'station-001',
        'imagePath': 'D:/data/reference.jpg',
        'markerLengthM': 999.0,
        'markerId': 0,
        'corners': [
            [600.0, 470.0],
            [750.0, 470.0],
            [750.0, 620.0],
            [600.0, 620.0],
        ],
    }


def test_handeye_java_response_is_minimal_but_debug_input_stays_full() -> None:
    response = api_module._handeye_result_to_java_data(
        {
            'matrix_2x3': [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
            'rmse_m': 0.0004,
            'sample_count': 12,
            'calibration_type': 'charuco_calibrateCamera_pnp_handeye_tsai_park_3d',
            'calibration_pixels_per_m': 3000.0,
            'angle_calibration': {'pose3d': POSE3D},
        }
    )

    assert set(response) == {'rmseM', 'sampleCount', 'pose3d'}
    assert set(response['pose3d']) == {
        'version', 'cameraMatrix', 'distCoeffs', 'gTc'
    }


def test_reference_java_response_uses_minimal_camel_case_marker() -> None:
    response = api_module._reference_to_java_data(
        {
            'image_path': 'D:/data/reference.jpg',
            'preferred_origin_id': 0,
            'marker_length_m': 0.15,
            'board_center_x': 675.0,
            'markers': [
                {
                    'marker_id': 0,
                    'center_x': 675.0,
                    'center_y': 545.0,
                    'angle_deg': 0.0,
                    'corners': [[600.0, 470.0], [750.0, 470.0], [750.0, 620.0], [600.0, 620.0]],
                }
            ],
        },
        'station-001',
    )

    assert set(response) == {'stationId', 'imagePath', 'markerId', 'corners'}
    assert response['markerId'] == 0
    assert response['corners'] == [
        [600.0, 470.0],
        [750.0, 470.0],
        [750.0, 620.0],
        [600.0, 620.0],
    ]


def test_reference_request_ignores_java_marker_length_and_rebuilds_internal_marker() -> None:
    normalized = api_module._normalize_reference_payload(
        {'stationId': 'station-001', 'reference': _reference_data()}
    )

    assert normalized['marker_length_m'] == api_module.settings.aruco.marker_length_m
    assert normalized['marker_length_m'] != 999.0
    assert normalized['markers'][0]['marker_id'] == 0
    assert normalized['markers'][0]['center_x'] == pytest.approx(675.0)
    assert normalized['markers'][0]['center_y'] == pytest.approx(545.0)


def test_charuco_reference_uses_combined_id_xy_corners() -> None:
    charuco_corners = [
        {'id': 0, 'x': 620.3, 'y': 481.7},
        {'id': 1, 'x': 651.2, 'y': 480.9},
        {'id': 2, 'x': 682.4, 'y': 480.1},
        {'id': 5, 'x': 621.1, 'y': 512.6},
        {'id': 6, 'x': 652.0, 'y': 511.8},
    ]
    normalized = api_module._normalize_reference_payload(
        {
            'reference': {
                'stationId': 'station-001',
                'imagePath': 'D:/data/reference.jpg',
                'markerId': 2,
                'corners': charuco_corners,
            }
        }
    )
    assert normalized['reference_type'] == 'charuco'
    assert normalized['preferred_origin_id'] == 2
    assert normalized['charuco_corners'] == charuco_corners
    assert normalized['markers'] == []

    response = api_module._reference_to_java_data(normalized, 'station-001')
    assert set(response) == {
        'stationId', 'imagePath', 'markerId', 'corners'
    }
    assert response['markerId'] == 2
    assert response['corners'] == charuco_corners


def test_legacy_charuco_corners_field_remains_accepted() -> None:
    charuco_corners = [
        {'id': corner_id, 'x': 620.0 + corner_id, 'y': 480.0 + corner_id}
        for corner_id in range(8)
    ]
    normalized = api_module._normalize_reference_payload(
        {
            'reference': {
                'stationId': 'station-001',
                'markerId': 2,
                'charucoCorners': charuco_corners,
            }
        }
    )

    assert normalized['reference_type'] == 'charuco'
    assert normalized['charuco_corners'] == charuco_corners


def test_handeye_request_no_longer_requires_matrix2x3() -> None:
    normalized = api_module._normalize_handeye_payload({'handeye': _handeye_data()})
    assert normalized['angle_calibration']['pose3d']['gTc'] == POSE3D['gTc']
    assert 'matrix_2x3' not in normalized


def test_handeye_robot_angles_are_always_interpreted_as_radians() -> None:
    sample = HandEyeSample(
        sample_id='p01',
        robot_x_m=0.0,
        robot_y_m=0.0,
        observation=CharucoObservation(
            image_points=[],
            board_points_m=[],
            corner_count=0,
        ),
        meta={'z': 0.0, 'rx': 0.0, 'ry': 0.0, 'rz': 10.0},
    )

    transform = robot_pose_to_transform(sample)
    assert np.allclose(transform[:3, :3], euler_xyz_to_rotation(0.0, 0.0, 10.0))


def test_secondary_response_only_returns_task_and_target_pose(monkeypatch) -> None:
    identity = [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]

    def fake_compensate(reference_payload, handeye_payload, image_path):
        return {
            'compensation': {
                'robot_command': {
                    'deltaTransform': identity,
                    'deltaTranslationM': [0.001, -0.002, 0.003],
                    'deltaRpyRad': [0.01, -0.02, 0.03],
                    'selectedMarkerId': 0,
                }
            },
            'image_path': image_path,
        }

    monkeypatch.setattr(api_module.service, 'compensate', fake_compensate)
    response = api_module.api_secondary_compensation(
        {
            'sn': 'station-001',
            'timestamp': 1780000000000,
            'data': {
                'stationId': 'station-001',
                'taskId': 'task-001',
                'imagePath': 'D:/data/current.jpg',
                'currentFlangePose': {
                    'x': 0.18,
                    'y': 0.25,
                    'z': 0.31598,
                    'rx': -3.14,
                    'ry': 0.0,
                    'rz': -0.175,
                },
                'handeye': _handeye_data(),
                'reference': _reference_data(),
            },
        }
    )

    assert response['code'] == 0
    assert set(response['data']) == {'taskId', 'targetFlangePose'}
    assert response['data']['targetFlangePose']['translationUnit'] == 'm'
    assert response['data']['targetFlangePose']['rotationUnit'] == 'rad'


def test_safety_rejects_large_translation() -> None:
    identity = [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]
    target_pose = {
        'x': 0.0, 'y': 0.0, 'z': 0.0,
        'rx': 0.0, 'ry': 0.0, 'rz': 0.0,
    }
    too_far = api_module.settings.compensation.max_translation_m * 2.0

    with pytest.raises(ValueError, match='补偿平移量超过安全阈值'):
        api_module._validate_compensation_safety(
            {
                'targetFlangePose': target_pose,
                'baseTranslationDeltaM': [too_far, 0.0, 0.0],
            },
            {'deltaTransform': identity},
        )
