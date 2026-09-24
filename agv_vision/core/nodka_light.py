"""Nodka NKLC software-switch control through the small native ABI bridge."""
from __future__ import annotations

import argparse
import ctypes
import logging
import math
from pathlib import Path
import sys
import threading
import time

from agv_vision.core.exceptions import SourceError


class LightResult(ctypes.Structure):
    _fields_ = [("sdk_return", ctypes.c_int32)] + [
        (name, ctypes.c_uint32) for name in (
            "received", "error", "error_id", "port", "device", "channel",
            "mode", "brightness", "on",
        )
    ]


class NodkaLight:
    """One controller per process; all commands serialized and read back.

    SDK synchronous calls own the serial timeout. No blind retry on failure.
    A successful readback confirms controller parameters, not physical light.
    """
    _owner_lock = threading.Lock()

    def __init__(self, library_path: str, config_path: str, port: int,
                 channel_mask: int, brightness: int = 50):
        if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
            raise ValueError("port must be an explicit Linux SDK port number (0..65535)")
        if channel_mask not in (1, 2, 4, 8):
            raise ValueError("channel_mask must select one channel: 1, 2, 4, or 8")
        if isinstance(brightness, bool) or not isinstance(brightness, int) or not 0 <= brightness <= 100:
            raise ValueError("brightness must be an integer in 0..100")
        self.library_path = Path(library_path).resolve()
        self.config_path = Path(config_path).resolve()
        self.port = port
        self.channel_mask = channel_mask
        self.brightness = brightness
        self._library = None
        self._initialized = False
        self._port_attempted = False
        self._owns_library = False
        self._lock = threading.RLock()

    def _load_library(self):
        if sys.platform != "linux":
            raise SourceError("NKLC Linux SDK requires Linux; Windows cannot load this .so")
        for path in (self.library_path, self.config_path):
            if not path.is_file():
                raise SourceError(f"NKLC file missing: {path}")
        library = ctypes.CDLL(str(self.library_path))
        result_pointer = ctypes.POINTER(LightResult)
        signatures = {
            "agv_light_init": ([ctypes.c_char_p], ctypes.c_int),
            "agv_light_deinit": ([], None),
            "agv_light_open": ([ctypes.c_uint16, result_pointer], None),
            "agv_light_close": ([ctypes.c_uint16, result_pointer], None),
            "agv_light_set": ([ctypes.c_uint32, ctypes.c_uint8, ctypes.c_uint8,
                               ctypes.c_uint8, result_pointer], None),
            "agv_light_get": ([ctypes.c_uint32, ctypes.c_uint8, result_pointer], None),
        }
        for name, (arguments, result) in signatures.items():
            function = getattr(library, name)
            function.argtypes = arguments
            function.restype = result
        return library

    def _command(self, name: str, *arguments: int) -> LightResult:
        result = LightResult()
        getattr(self._library, name)(*arguments, ctypes.byref(result))
        if result.sdk_return < 0 or not result.received or result.error or result.error_id:
            raise SourceError(
                f"{name} failed: return={result.sdk_return}, callback={result.received}, "
                f"error={result.error}, error_id={result.error_id}; device state unconfirmed"
            )
        return result

    def open(self) -> None:
        with self._lock:
            if self._initialized:
                return
            if not self._owner_lock.acquire(blocking=False):
                raise SourceError("Only one NodkaLight instance may own NKLC in this process")
            self._owns_library = True
            try:
                self._library = self._load_library()
                code = self._library.agv_light_init(str(self.config_path).encode())
                if code != 0:
                    raise SourceError(f"NKLC initialization failed: {code}")
                self._initialized = True
                self._port_attempted = True
                result = self._command("agv_light_open", self.port)
                if result.port != self.port or result.device != 1:
                    raise SourceError("NKLC open callback returned unexpected port/device")
                self.turn_off()
            except BaseException:
                try:
                    self.close()
                except Exception:
                    logging.getLogger(__name__).exception("NKLC startup cleanup failed")
                raise

    def _set_switch(self, is_on: bool) -> None:
        with self._lock:
            if not self._initialized or not self._port_attempted:
                raise SourceError("NKLC controller is not open")
            result = self._command("agv_light_set", 1, self.channel_mask,
                                   self.brightness, int(is_on))
            if result.channel != self.channel_mask:
                raise SourceError("NKLC set callback channel mismatch")
            state = self._command("agv_light_get", 1, self.channel_mask)
            if (state.channel, state.mode, state.brightness, state.on) != (
                    self.channel_mask, 0, self.brightness, int(is_on)):
                raise SourceError("NKLC readback mismatch; light state unconfirmed")

    def turn_on(self) -> None:
        self._set_switch(True)

    def turn_off(self) -> None:
        self._set_switch(False)

    def close(self) -> None:
        with self._lock:
            errors = []
            try:
                if self._initialized and self._port_attempted:
                    for action in (self.turn_off,
                                   lambda: self._command("agv_light_close", self.port)):
                        try:
                            action()
                        except Exception as exc:
                            errors.append(str(exc))
                if self._initialized:
                    # Header declares int; older manual declares void. Do not
                    # interpret this value as a portable success indicator.
                    self._library.agv_light_deinit()
            finally:
                self._initialized = False
                self._port_attempted = False
                if self._owns_library:
                    self._owns_library = False
                    self._owner_lock.release()
            if errors:
                raise SourceError("NKLC cleanup failed: " + "; ".join(errors))


class IlluminatedFrameSource:
    """Serialize the entire light/exposure transaction and always attempt off."""
    def __init__(self, source, light: NodkaLight, settle_ms: int):
        self.source = source
        self.light = light
        self.settle_ms = settle_ms
        self._lock = threading.RLock()
        self._faulted = False

    def open(self):
        with self._lock:
            self.light.open()
            try:
                self.source.open()
                self._faulted = False
            except BaseException:
                try:
                    self.light.close()
                except Exception:
                    logging.getLogger(__name__).exception("NKLC camera-start cleanup failed")
                raise

    def grab(self):
        with self._lock:
            if self._faulted:
                raise SourceError("Light capture faulted; close and reopen after checking hardware")
            try:
                self.light.turn_on()
                time.sleep(self.settle_ms / 1000.0)
                frame = self.source.grab()
            except BaseException:
                self._faulted = True
                try:
                    self.light.turn_off()
                except Exception:
                    logging.getLogger(__name__).exception("NKLC off failed after capture failure")
                raise
            try:
                self.light.turn_off()  # Off failure must not be reported as success.
            except BaseException:
                self._faulted = True
                raise
            return frame

    def close(self):
        with self._lock:
            try:
                self.light.close()
            finally:
                self.source.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="NKLC: turn on, wait, then turn off (Linux)")
    parser.add_argument("--library", required=True, help="libagv_nodka_light.so path")
    parser.add_argument("--config", required=True, help="model-specific nkio_config.ini")
    parser.add_argument("--port", type=int, required=True, help="actual Linux SDK port number")
    parser.add_argument("--channel-mask", type=lambda text: int(text, 0), required=True)
    parser.add_argument("--brightness", type=int, default=50)
    parser.add_argument("--seconds", type=float, default=3)
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or not 0 < args.seconds <= 3600:
        parser.error("--seconds must be finite and in (0, 3600]")
    light = NodkaLight(args.library, args.config, args.port, args.channel_mask, args.brightness)
    try:
        light.open()
        light.turn_on()
        print("Light ON command/readback confirmed", flush=True)
        time.sleep(args.seconds)
    finally:
        light.close()
    print("Light OFF command/readback confirmed", flush=True)


if __name__ == "__main__":
    main()
