"""Bounded, illuminated comparison of MVS copy and SDK-owned buffer APIs.

Run inside the stopped service's Compose environment via stdin. No PLC/API calls.
Uses current camera/light settings; does not change SDK structure definitions.
"""
import ctypes
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

from agv_vision.config.settings import AppSettings
from agv_vision.core.hikvision_source import HikvisionColorSource
from agv_vision.core.nodka_light import NodkaLight


def pixel_stats(data):
    return dict(size=int(data.size), minimum=int(data.min()), maximum=int(data.max()),
                mean=float(data.mean()), nonzero=int(np.count_nonzero(data)))


def inspect_frame(source, info, data, label, output_dir):
    fields = {name: int(getattr(info, name, -1)) for name in (
        "nWidth", "nHeight", "enPixelType", "nFrameNum", "nFrameLen",
        "nFrameLenEx", "nLostPacket",
    )}
    print(label, "FIELDS", json.dumps(fields), flush=True)
    print(label, "RAW", json.dumps(pixel_stats(data)), flush=True)
    data.tofile(output_dir / (label + ".raw"))
    (output_dir / (label + ".json")).write_text(json.dumps(fields), encoding="utf-8")


def capture(source, label, output_dir):
    sdk, camera = source.sdk, source.camera
    source._check(camera.MV_CC_ClearImageBuffer(), "ClearImageBuffer")
    source._check(camera.MV_CC_SetCommandValue("TriggerSoftware"), "TriggerSoftware")
    if label == "copy":
        raw = (ctypes.c_ubyte * source.payload_size)()
        # Nonzero sentinel distinguishes an untouched destination from written zeros.
        ctypes.memset(raw, 0xA5, len(raw))
        info = sdk.MV_FRAME_OUT_INFO_EX()
        source._check(camera.MV_CC_GetOneFrameTimeout(raw, len(raw), info, source.timeout_ms),
                      "GetOneFrameTimeout")
        data = np.ctypeslib.as_array(raw)
        print("copy SENTINEL", int(np.count_nonzero(data == 0xA5)), "/", len(raw), flush=True)
        if not 0 < int(info.nFrameLen) <= len(raw):
            raise RuntimeError(f"Invalid copied frame length: {info.nFrameLen}")
        inspect_frame(source, info, data[:int(info.nFrameLen)], label, output_dir)
    else:
        frame = sdk.MV_FRAME_OUT()
        source._check(camera.MV_CC_GetImageBuffer(frame, source.timeout_ms), "GetImageBuffer")
        try:
            length = int(frame.stFrameInfo.nFrameLen)
            if not frame.pBufAddr or not 0 < length <= source.payload_size:
                raise RuntimeError(f"Invalid SDK buffer pointer/length: {length}")
            data = np.frombuffer(ctypes.string_at(frame.pBufAddr, length), dtype=np.uint8)
            inspect_frame(source, frame.stFrameInfo, data, label, output_dir)
        finally:
            source._check(camera.MV_CC_FreeImageBuffer(frame), "FreeImageBuffer")


def main():
    logging.basicConfig(level=logging.INFO)
    config = AppSettings.from_yaml("agv_vision/config/settings_online.yaml")
    if config.mode.lower() != "online" or config.camera.vendor != "hikvision" or not config.light.enabled:
        raise RuntimeError("Requires online Hikvision with existing light configuration enabled")
    camera_config, light_config = config.camera, config.light
    profile = camera_config.hikvision
    output_dir = Path("data") / ("hik_diagnostic_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
    output_dir.mkdir(parents=True, exist_ok=False)
    print("OUTPUT", output_dir.resolve(), flush=True)
    # Fresh stream per API: do not mix the two acquisition APIs in one stream.
    for label in ("copy", "sdk_buffer"):
        source = HikvisionColorSource(
            width=profile.width or camera_config.width,
            height=profile.height or camera_config.height,
            fps=profile.fps or camera_config.fps,
            timeout_ms=camera_config.timeout_ms,
            serial_number=profile.serial_number, ip_address=profile.ip_address,
            auto_exposure=camera_config.auto_exposure, exposure=camera_config.exposure,
            gain=camera_config.gain, auto_white_balance=camera_config.auto_white_balance,
            sdk_python_path=profile.python_path,
        )
        source.software_trigger = True
        light = NodkaLight(light_config.library_path, light_config.config_path,
                           light_config.port, light_config.channel_mask, light_config.brightness)
        try:
            light.open()
            source.open()
            print(label, "SDK", source.sdk.__file__, flush=True)
            for key in ("ExposureTime", "Gain"):
                value = source.sdk.MVCC_FLOATVALUE()
                result = source.camera.MV_CC_GetFloatValue(key, value)
                print(label, key, hex(result & 0xFFFFFFFF), value.fCurValue, flush=True)
            light.turn_on()
            time.sleep(light_config.settle_ms / 1000.0)
            capture(source, label, output_dir)
        finally:
            # Stop on any failure; do not replay a failed transaction.
            try:
                light.close()
            finally:
                source.close()
    print("DONE: two captures completed; normal service remains stopped", flush=True)


if __name__ == "__main__":
    main()
