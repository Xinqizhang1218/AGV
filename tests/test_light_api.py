"""Offline contract and light ownership tests; no SDK or camera is opened."""
import asyncio
import importlib
import json
import logging
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import Mock, patch

from agv_vision.config.settings import AppSettings
from agv_vision.core.exceptions import SourceError
from agv_vision.core.nodka_light import IlluminatedFrameSource, LightStatusError, NodkaLight
from agv_vision.core.service import AGVVisionService
from test_nodka_light import FakeBridge


class AsgiClient:
    """Exercise the real ASGI app without adding an httpx dependency."""

    def __init__(self, app):
        self.app = app

    def request(self, method, path, payload=None):
        async def run():
            sent_request = False
            complete = asyncio.Event()
            messages = []

            async def receive():
                nonlocal sent_request
                if not sent_request:
                    sent_request = True
                    return {'type': 'http.request', 'body': json.dumps(payload).encode()
                            if method == 'POST' else b'', 'more_body': False}
                await complete.wait()
                return {'type': 'http.disconnect'}

            async def send(message):
                messages.append(message)
                if message['type'] == 'http.response.body' and not message.get('more_body', False):
                    complete.set()

            scope = {'type': 'http', 'asgi': {'version': '3.0', 'spec_version': '2.0'},
                     'http_version': '1.1', 'method': method, 'scheme': 'http',
                     'path': path, 'raw_path': path.encode(), 'query_string': b'',
                     'root_path': '', 'headers': [(b'content-type', b'application/json')],
                     'client': ('test', 1), 'server': ('test', 80)}
            try:
                await self.app(scope, receive, send)
            except Exception:
                if not any(m['type'] == 'http.response.start' and m['status'] == 500 for m in messages):
                    raise
            status = next(m['status'] for m in messages if m['type'] == 'http.response.start')
            body = b''.join(m.get('body', b'') for m in messages if m['type'] == 'http.response.body')
            return SimpleNamespace(status_code=status, json=lambda: json.loads(body))

        return asyncio.run(asyncio.wait_for(run(), timeout=5))

    def post(self, path, json=None):
        return self.request('POST', path, json)

    def get(self, path):
        return self.request('GET', path)


class LightHoldTests(unittest.TestCase):
    def setUp(self):
        self.bridge = FakeBridge()
        self.light = NodkaLight('fake.so', 'fake.ini', 3, 1, 50)
        self.light._load_library = lambda: self.bridge
        self.camera = SimpleNamespace(open=Mock(), close=Mock(), grab=Mock(return_value='frame'))
        self.source = IlluminatedFrameSource(self.camera, self.light, 1000)
        self.source.open()
        self.bridge.events.clear()

    def tearDown(self):
        self.bridge.fail = None
        self.source.close()

    def test_hold_then_release_restores_auto_capture(self):
        with patch('agv_vision.core.nodka_light.time.sleep') as sleep:
            self.source.control_light('on')
            self.assertEqual(sleep.call_args.args, (1.0,))
            self.assertEqual(self.source.get_light_status(), {'state': 'on', 'held': True})
            self.bridge.events.clear()
            self.source.grab()
            self.source.grab()
            self.assertNotIn('set', self.bridge.events)
            self.assertEqual(sleep.call_count, 1)
            self.assertEqual(self.bridge.on, 1)
            self.source.control_light('off')
            self.source.grab()
            self.assertEqual(self.source.get_light_status(), {'state': 'off', 'held': False})
            self.assertEqual(sleep.call_count, 2)

    def test_repeated_commands_do_not_stack_holds(self):
        with patch('agv_vision.core.nodka_light.time.sleep'):
            self.source.control_light('on')
            self.source.control_light('on')
            self.source.control_light('off')
            self.source.control_light('off')
        self.assertEqual(self.source.get_light_status(), {'state': 'off', 'held': False})

    def test_query_failure_preserves_hold_and_does_not_switch(self):
        with patch('agv_vision.core.nodka_light.time.sleep'):
            self.source.control_light('on')
        self.bridge.events.clear()
        self.bridge.fail = 'get_error'
        with self.assertRaises(LightStatusError) as caught:
            self.source.get_light_status()
        self.assertEqual(caught.exception.status, {'state': 'unknown', 'held': True})
        self.assertEqual(self.bridge.events, ['get'])
        self.bridge.fail = None
        with self.assertRaises(LightStatusError):
            self.source.get_light_status()
        with self.assertRaises(SourceError):
            self.source.grab()
        # Off is still allowed for cleanup; it does not reset the fault latch.
        self.source.control_light('off')
        self.assertEqual(self.bridge.on, 0)
        with self.assertRaises(SourceError):
            self.source.control_light('on')

    def test_capture_failure_cancels_hold_and_turns_off(self):
        with patch('agv_vision.core.nodka_light.time.sleep'):
            self.source.control_light('on')
        self.camera.grab.side_effect = SourceError('camera failed')
        with self.assertRaisesRegex(SourceError, 'camera failed'):
            self.source.grab()
        self.assertFalse(self.source._held)
        self.assertEqual(self.bridge.on, 0)

    def test_missing_light_during_hold_prevents_capture(self):
        with patch('agv_vision.core.nodka_light.time.sleep'):
            self.source.control_light('on')
        self.bridge.on = 0
        with self.assertRaises(SourceError):
            self.source.grab()
        self.camera.grab.assert_not_called()
        self.assertFalse(self.source._held)

    def test_command_failure_never_reports_success(self):
        for action in ('on', 'off'):
            with self.subTest(action=action):
                self.bridge.fail = 'set_error'
                with self.assertRaises(SourceError):
                    self.source.control_light(action)
                self.assertFalse(self.source._held)
                self.assertTrue(self.source._faulted)
                self.bridge.fail = None
                self.source.close()
                self.source.open()

    def test_reopen_resets_hold_but_open_is_not_fault_reset(self):
        with patch('agv_vision.core.nodka_light.time.sleep'):
            self.source.control_light('on')
        self.source.open()
        self.assertTrue(self.source.get_light_status()['held'])
        self.source._faulted = True
        with self.assertRaises(SourceError):
            self.source.open()
        self.source.close()
        self.source.open()
        self.assertEqual(self.source.get_light_status(), {'state': 'off', 'held': False})

    def test_off_waits_until_exposure_finishes(self):
        entered = threading.Event()
        release = threading.Event()
        off_started = threading.Event()
        off_done = threading.Event()

        def grab():
            entered.set()
            if not release.wait(3):
                raise RuntimeError('test capture timed out')
            self.assertEqual(self.bridge.on, 1)
            return 'frame'

        def turn_off():
            off_started.set()
            self.source.control_light('off')
            off_done.set()

        self.camera.grab.side_effect = grab
        with patch('agv_vision.core.nodka_light.time.sleep'):
            self.source.control_light('on')
        with ThreadPoolExecutor(max_workers=2) as pool:
            capture = pool.submit(self.source.grab)
            try:
                self.assertTrue(entered.wait(1))
                off = pool.submit(turn_off)
                self.assertTrue(off_started.wait(1))
                self.assertFalse(off_done.wait(0.05))
            finally:
                release.set()
            self.assertEqual(capture.result(timeout=2), 'frame')
            off.result(timeout=2)
        self.assertEqual(self.bridge.on, 0)

    def test_status_rejects_invalid_controller_readback(self):
        original_get = self.bridge.agv_light_get

        def wrong_channel(*args):
            original_get(*args)
            args[-1]._obj.channel = 8

        with patch.object(self.bridge, 'agv_light_get', side_effect=wrong_channel):
            with self.assertRaisesRegex(SourceError, 'readback invalid'):
                self.light.read_state()

    def test_closed_controller_rejects_commands_and_queries(self):
        self.source.close()
        for action in ('on', 'off'):
            with self.assertRaises(SourceError):
                self.source.control_light(action)
        with self.assertRaises(LightStatusError) as caught:
            self.source.get_light_status()
        self.assertEqual(caught.exception.status, {'state': 'unknown', 'held': False})


class LightApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory()
        settings = AppSettings()
        settings.debug.debug_dir = cls.folder.name
        # Import under offline settings regardless of the operator's environment.
        with patch.object(AppSettings, 'from_yaml', return_value=settings), patch(
            'agv_vision.utils.logging_utils.setup_logging', return_value=Mock(spec=logging.Logger)
        ):
            cls.api = importlib.import_module('agv_vision.api.app')

    @classmethod
    def tearDownClass(cls):
        cls.folder.cleanup()

    def setUp(self):
        self.service = AGVVisionService.__new__(AGVVisionService)
        self.bridge = FakeBridge()
        light = NodkaLight('fake.so', 'fake.ini', 3, 1)
        light._load_library = lambda: self.bridge
        camera = SimpleNamespace(open=Mock(), close=Mock(), grab=Mock(return_value='frame'))
        self.source = IlluminatedFrameSource(camera, light, 0)
        self.source.open()
        self.service.source = self.source
        self.service_patch = patch.object(self.api, 'service', self.service)
        self.service_patch.start()
        # No lifespan/startup: prevents any hardware or offline-image acquisition.
        self.client = AsgiClient(self.api.app)

    def tearDown(self):
        self.service_patch.stop()
        self.bridge.fail = None
        self.source.close()

    def test_control_and_query_contract(self):
        for action in ('on', 'off'):
            response = self.client.post('/api/v1/agv/light/control', json={
                'data': {'action': action}, 'timestamp': 123456,
            })
            self.assertEqual(response.status_code, 200)
            body = response.json()
            self.assertEqual(set(body), {'code', 'msg', 'data', 'timestamp'})
            self.assertEqual((body['code'], body['data'], body['timestamp']), (0, {}, 123456))
            state = self.client.get('/api/v1/agv/light/status').json()
            self.assertEqual(state['code'], 0)
            self.assertEqual(state['data'], {'state': action, 'held': action == 'on'})

    def test_invalid_requests_do_not_touch_hardware(self):
        self.bridge.events.clear()
        for body in ({}, {'action': 'on'}, {'data': []}, {'data': {'action': 'ON'}},
                     {'data': {'action': True}}, {'data': {'action': []}}, [], None):
            with self.subTest(body=body):
                response = self.client.post('/api/v1/agv/light/control', json=body)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()['code'], 400)
        self.assertEqual(self.bridge.events, [])

    def test_query_failure_and_control_failure_contract(self):
        self.source.control_light('on')
        self.bridge.fail = 'get_error'
        response = self.client.get('/api/v1/agv/light/status')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], 400)
        self.assertEqual(response.json()['data'], {'state': 'unknown', 'held': True})
        response = self.client.post('/api/v1/agv/light/control', json={'data': {'action': 'off'}})
        self.assertEqual(response.json()['code'], 400)
        self.assertEqual(response.json()['data'], {})

    def test_disabled_or_offline_source_is_not_fake_success(self):
        self.service.source = object()
        response = self.client.post('/api/v1/agv/light/control', json={'data': {'action': 'on'}})
        self.assertEqual(response.json()['code'], 400)
        response = self.client.get('/api/v1/agv/light/status')
        self.assertEqual(response.json()['code'], 400)
        self.assertEqual(response.json()['data'], {'state': 'unknown', 'held': False})

    def test_unexpected_error_is_http_500(self):
        with patch.object(self.service, 'control_light', side_effect=RuntimeError('unexpected')):
            response = self.client.post('/api/v1/agv/light/control', json={'data': {'action': 'on'}})
        self.assertEqual(response.status_code, 500)


if __name__ == '__main__':
    unittest.main()
