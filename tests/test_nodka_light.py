import ctypes
import logging
import tempfile
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pydantic import ValidationError

from agv_vision.config.settings import AppSettings
from agv_vision.core.exceptions import SourceError
from agv_vision.core.hikvision_source import HikvisionColorSource
from agv_vision.core.nodka_light import IlluminatedFrameSource, NodkaLight
from agv_vision.core.service import AGVVisionService


class FakeBridge:
    def __init__(self):
        self.events = []
        self.brightness = 0
        self.on = 0
        self.fail = None
        self.mismatch = False

    def agv_light_init(self, path):
        self.events.append('init')
        return 0

    def agv_light_deinit(self):
        self.events.append('deinit')

    def result(self, pointer, action):
        self.events.append(action)
        value = pointer._obj
        value.sdk_return = -1 if self.fail == action + '_return' else 1
        value.received = 0 if self.fail == action + '_missing' else 1
        value.error = 1 if self.fail == action + '_error' else 0
        value.error_id = 6 if value.error else 0
        return value

    def agv_light_open(self, port, pointer):
        value = self.result(pointer, 'open')
        value.port, value.device = port, 1

    def agv_light_close(self, port, pointer):
        self.result(pointer, 'close')

    def agv_light_set(self, device, channel, brightness, on, pointer):
        self.brightness, self.on = brightness, on
        self.result(pointer, 'set').channel = channel

    def agv_light_get(self, device, channel, pointer):
        value = self.result(pointer, 'get')
        value.channel = channel
        value.mode, value.brightness = 0, self.brightness
        value.on = 1 - self.on if self.mismatch else self.on


class NodkaLightTests(unittest.TestCase):
    def setUp(self):
        self.bridge = FakeBridge()
        self.light = NodkaLight('bridge.so', 'model.ini', 2, 1, 50)
        self.light._load_library = lambda: self.bridge

    def tearDown(self):
        self.bridge.fail = None
        self.bridge.mismatch = False
        self.light.close()

    def test_on_off_readback_and_cleanup(self):
        self.light.open()
        self.light.turn_on()
        self.assertEqual(self.bridge.on, 1)
        self.light.close()
        self.assertEqual(self.bridge.on, 0)
        self.assertEqual(self.bridge.events[-4:], ['set', 'get', 'close', 'deinit'])

    def test_sdk_callback_and_readback_failures(self):
        self.light.open()
        for failure in ('set_return', 'set_missing', 'set_error', 'get_error'):
            with self.subTest(failure=failure):
                self.bridge.fail = failure
                with self.assertRaises(SourceError):
                    self.light.turn_on()
        self.bridge.fail = None
        self.bridge.mismatch = True
        with self.assertRaisesRegex(SourceError, 'readback'):
            self.light.turn_on()

    def test_startup_failure_releases_library(self):
        self.bridge.fail = 'open_error'
        with self.assertRaises(SourceError):
            self.light.open()
        self.assertIn('deinit', self.bridge.events)
        self.bridge.fail = None
        self.light.open()

    def test_second_owner_rejected(self):
        self.light.open()
        other = NodkaLight('other.so', 'other.ini', 2, 2)
        with self.assertRaisesRegex(SourceError, 'one NodkaLight'):
            other.open()
        other.close()
        self.light.turn_on()

    def test_normalized_open_metadata_requires_successful_channel_read(self):
        original_open = self.bridge.agv_light_open

        def mismatched_open(port, pointer):
            original_open(port, pointer)
            pointer._obj.port = port - 1
            pointer._obj.device = 0
            pointer._obj.sdk_return = 0

        self.bridge.agv_light_open = mismatched_open
        self.light.open()
        self.assertEqual(self.bridge.events[:5], ['init', 'open', 'get', 'set', 'get'])
        self.light.turn_on()
        self.assertEqual(self.bridge.on, 1)

    def test_initial_read_failure_never_sends_switch_commands(self):
        self.bridge.fail = 'get_error'
        with self.assertRaises(SourceError):
            self.light.open()
        self.assertNotIn('set', self.bridge.events)
        self.assertEqual(self.bridge.events[-2:], ['close', 'deinit'])

    def test_initial_wrong_channel_never_sends_switch_commands(self):
        original_get = self.bridge.agv_light_get

        def wrong_channel(device, channel, pointer):
            original_get(device, channel, pointer)
            pointer._obj.channel = 8

        self.bridge.agv_light_get = wrong_channel
        with self.assertRaisesRegex(SourceError, 'initial channel readback invalid'):
            self.light.open()
        self.assertNotIn('set', self.bridge.events)
        self.assertEqual(self.bridge.events[-2:], ['close', 'deinit'])

    def test_cleanup_still_deinitializes_after_off_error(self):
        self.light.open()
        self.bridge.fail = 'set_error'
        with self.assertRaisesRegex(SourceError, 'cleanup'):
            self.light.close()
        self.assertEqual(self.bridge.events[-2:], ['close', 'deinit'])


class CaptureTests(unittest.TestCase):
    def make_source(self, failure=None):
        events = []

        def action(name):
            def run():
                events.append(name)
                if name == failure:
                    raise SourceError(name)
                if name == 'grab':
                    time.sleep(0.005)
                    return 'frame'
            return run

        light = SimpleNamespace(turn_on=action('on'), turn_off=action('off'),
                                open=action('light_open'), close=action('light_close'))
        camera = SimpleNamespace(grab=action('grab'), open=action('camera_open'),
                                 close=action('camera_close'))
        return IlluminatedFrameSource(camera, light, 0), events

    def test_order(self):
        source, events = self.make_source()
        self.assertEqual(source.grab(), 'frame')
        self.assertEqual(events, ['on', 'grab', 'off'])

    def test_failures_always_attempt_off_and_block_next_capture(self):
        for failure, expected in [('on', ['on', 'off']), ('grab', ['on', 'grab', 'off']),
                                  ('off', ['on', 'grab', 'off'])]:
            with self.subTest(failure=failure):
                source, events = self.make_source(failure)
                with self.assertRaises(SourceError):
                    source.grab()
                self.assertEqual(events, expected)
                with self.assertRaisesRegex(SourceError, 'faulted'):
                    source.grab()
                self.assertEqual(events, expected)

    def test_capture_requests_do_not_interleave(self):
        source, events = self.make_source()
        threads = [threading.Thread(target=source.grab) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(events, ['on', 'grab', 'off'] * 3)

    def test_camera_open_failure_closes_light(self):
        source, events = self.make_source('camera_open')
        with self.assertRaises(SourceError):
            source.open()
        self.assertEqual(events, ['light_open', 'camera_open', 'light_close'])

    def test_hikvision_clear_then_trigger_then_read(self):
        events = []

        class FrameInfo(ctypes.Structure):
            _fields_ = [(name, ctypes.c_uint32) for name in
                        ('nHostTimeStamp', 'nWidth', 'nHeight', 'enPixelType', 'nFrameNum')]

        def record(name):
            def call(*args):
                events.append(name)
                return 0
            return call

        camera = HikvisionColorSource(2, 2, 15)
        camera.camera = SimpleNamespace(MV_CC_ClearImageBuffer=record('clear'),
                                        MV_CC_SetCommandValue=record('trigger'),
                                        MV_CC_GetOneFrameTimeout=record('read'))
        camera.sdk = SimpleNamespace(MV_FRAME_OUT_INFO_EX=FrameInfo)
        camera.payload_size = 16
        camera.grabbing = True
        camera.software_trigger = True
        camera._to_bgr = lambda *args: 'image'
        camera.grab()
        self.assertEqual(events, ['clear', 'trigger', 'read'])
        events.clear()
        camera.camera.MV_CC_ClearImageBuffer = lambda: -1
        with self.assertRaises(SourceError):
            camera.grab()
        self.assertEqual(events, [])


class ConfigurationTests(unittest.TestCase):
    def test_enabled_requires_hardware_and_fixed_exposure(self):
        for options in ({}, {'port': 2}, {'port': 2, 'channel_mask': 1}):
            with self.assertRaises(ValidationError):
                AppSettings(mode='online', light={'enabled': True, **options})
        settings = AppSettings(mode='online', camera={'vendor': 'hikvision',
                                'auto_exposure': False, 'exposure': 10000},
                               light={'enabled': True, 'port': 2, 'channel_mask': 1})
        with tempfile.TemporaryDirectory() as folder:
            settings.debug.debug_dir = folder
            service = AGVVisionService(settings, logging.getLogger('test'))
            self.assertIsInstance(service.source, IlluminatedFrameSource)
            self.assertTrue(service.source.source.software_trigger)

    def test_offline_does_not_load_or_wrap_light(self):
        settings = AppSettings(light={'enabled': True})
        with tempfile.TemporaryDirectory() as folder:
            settings.debug.debug_dir = folder
            with patch.object(NodkaLight, '_load_library', side_effect=AssertionError):
                service = AGVVisionService(settings, logging.getLogger('test'))
                self.assertNotIsInstance(service.source, IlluminatedFrameSource)

    def test_default_preserves_continuous_hikvision(self):
        settings = AppSettings(mode='online', camera={'vendor': 'hikvision'})
        with tempfile.TemporaryDirectory() as folder:
            settings.debug.debug_dir = folder
            service = AGVVisionService(settings, logging.getLogger('test'))
            self.assertIsInstance(service.source, HikvisionColorSource)
            self.assertFalse(service.source.software_trigger)


if __name__ == '__main__':
    unittest.main()
