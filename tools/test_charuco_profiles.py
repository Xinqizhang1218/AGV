"""双板配置回归：使用合成图像与离线服务，不连接相机或机器人。"""
import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import cv2
import numpy as np
from pydantic import ValidationError

from agv_vision.config.settings import AppSettings, CharucoSettings
from agv_vision.core.models import FrameBundle
from agv_vision.core.service import AGVVisionService


def board_config(square_length_m, min_corners=5):
    return dict(dictionary_name='DICT_4X4_50', squares_x=5, squares_y=5,
                square_length_m=square_length_m, marker_length_m=square_length_m * 2 / 3,
                min_corners=min_corners)


class CharucoProfilesTest(unittest.TestCase):
    def make_service(self, handeye_size=0.03):
        settings = AppSettings(
            handeye_charuco=board_config(handeye_size),
            station_charuco=board_config(0.01),
            debug={'save_debug_images': False, 'save_result_json': False},
        )
        service = AGVVisionService(settings, logging.getLogger('dual_board_test'))
        service._save_image = Mock(return_value=None)
        service._save_debug_case = Mock(return_value={})
        return service

    @staticmethod
    def image(service, shift=0):
        board = service.station_charuco_detector.board.generateImage((600, 600))
        image = np.full((800, 1000), 255, dtype=np.uint8)
        image[100:700, 200 + shift:800 + shift] = board
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    def test_legacy_profiles_are_independent_copies(self):
        settings = AppSettings(charuco=board_config(0.02))
        self.assertEqual(settings.handeye_charuco, settings.station_charuco)
        settings.handeye_charuco.square_length_m = 0.03
        self.assertEqual(settings.station_charuco.square_length_m, 0.02)
        self.assertEqual(settings.charuco.square_length_m, 0.02)

    def test_explicit_profile_overrides_legacy_only_for_its_role(self):
        settings = AppSettings(charuco=board_config(0.02), station_charuco=board_config(0.01))
        self.assertEqual(settings.handeye_charuco.square_length_m, 0.02)
        self.assertEqual(settings.station_charuco.square_length_m, 0.01)
        with self.assertRaises(ValidationError):
            AppSettings(station_charuco=None)

    def test_invalid_geometry_is_rejected(self):
        for values in ({'square_length_m': 0}, {'marker_length_m': 0.04},
                       {'marker_length_m': float('nan')}, {'squares_x': 1},
                       {'min_corners': 17}):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                CharucoSettings(**(board_config(0.03) | values))

    def test_handeye_sample_and_station_reference_use_different_scales(self):
        service = self.make_service()
        image = self.image(service)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'board.png'
            path.write_bytes(cv2.imencode('.png', image)[1].tobytes())
            sample = service.build_handeye_sample_from_image('sample', str(path), 0, 0)
        reference, _ = service._detect_station_reference(image, 'station', 'charuco')
        handeye_points = np.array(sample['observation']['board_points_m'])
        station_points = np.array(reference.charuco_object_points_m)
        np.testing.assert_allclose(handeye_points, station_points * 3, atol=1e-7)

    def test_station_compensation_is_independent_of_handeye_board_size(self):
        results = []
        for size in (0.03, 0.06):
            service = self.make_service(size)
            service.source = Mock()
            service.source.grab.return_value = FrameBundle(color=self.image(service))
            reference = service.collect_station_reference('station')
            # Exercise the actual compact Java reference round trip.
            import agv_vision.api.app as api
            with patch.object(api, 'settings', service.settings):
                compact = api._reference_to_java_data(reference, 'station')
                self.assertEqual(set(compact), {'stationId', 'imagePath', 'markerId', 'corners'})
                reference = api._normalize_reference_payload({'reference': compact})
            service.source.grab.return_value = FrameBundle(color=self.image(service, 12))
            pose3d = dict(cameraMatrix=[[1000, 0, 500], [0, 1000, 400], [0, 0, 1]],
                          distCoeffs=[0] * 5, gTc=np.eye(4).tolist())
            result = service.compensate(reference, {'angle_calibration': {'pose3d': pose3d}})
            results.append(result['compensation'])
        self.assertAlmostEqual(abs(results[0]['dx_m_robot']), 0.001, delta=0.00001)
        for key in ('dx_m_robot', 'dy_m_robot', 'dtheta_robot_deg'):
            self.assertAlmostEqual(results[0][key], results[1][key], places=10)
        np.testing.assert_allclose(results[0]['robot_command']['deltaTransform'],
                                   results[1]['robot_command']['deltaTransform'], atol=1e-10)

    def test_api_corner_threshold_and_marker_size_use_station_profile(self):
        import agv_vision.api.app as api
        settings = AppSettings(handeye_charuco=board_config(0.03, 12),
                               station_charuco=board_config(0.01, 5))
        corners = [dict(id=i, x=i * 10.0, y=20.0) for i in range(5)]
        with patch.object(api, 'settings', settings):
            normalized = api._normalize_reference_payload({'reference': {'corners': corners}})
            self.assertAlmostEqual(normalized['marker_length_m'], 0.01 * 2 / 3)
            with self.assertRaises(ValueError):
                api._normalize_reference_payload({'reference': {'corners': corners[:4]}})

    def test_repository_configs_have_two_profiles(self):
        for name in ('settings.yaml', 'settings_online.yaml', 'settings_http_test.yaml'):
            with self.subTest(name=name):
                settings = AppSettings.from_yaml(Path(__file__).parent / 'agv_vision/config' / name)
                self.assertIn('handeye_charuco', settings.model_fields_set)
                self.assertIn('station_charuco', settings.model_fields_set)


if __name__ == '__main__':
    unittest.main()
