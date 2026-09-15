import ctypes

import numpy as np
import pytest
from pydantic import ValidationError

from agv_vision.config.settings import AppSettings, CameraSettings
from agv_vision.core.daheng_source import DahengColorSource
from agv_vision.core.hikvision_source import HikvisionColorSource
from agv_vision.core.orbbec_source import OrbbecColorSource
from agv_vision.core.service import AGVVisionService


def build_source(settings: AppSettings):
    service = AGVVisionService.__new__(AGVVisionService)
    service.settings = settings
    return service._build_source()


@pytest.mark.parametrize(
    ("vendor", "expected_type"),
    [
        ("orbbec", OrbbecColorSource),
        ("daheng", DahengColorSource),
        ("hikvision", HikvisionColorSource),
    ],
)
def test_online_camera_vendor_selects_source(vendor, expected_type):
    settings = AppSettings(mode="online", camera=CameraSettings(vendor=vendor))
    assert isinstance(build_source(settings), expected_type)


def test_vendor_specific_selector_does_not_reuse_orbbec_ip():
    settings = AppSettings(
        mode="online",
        camera=CameraSettings(
            vendor="daheng",
            ip_address="192.168.1.101",
            daheng={"serial_number": "DH123", "ip_address": None},
        ),
    )
    source = build_source(settings)
    assert source.serial_number == "DH123"
    assert source.ip_address is None


@pytest.mark.parametrize("vendor", ["orbbec", "daheng", "hikvision"])
def test_each_vendor_uses_its_own_resolution(vendor):
    settings = AppSettings(
        mode="online",
        camera=CameraSettings(
            vendor=vendor,
            width=640,
            height=480,
            fps=10,
            **{vendor: {"width": 2448, "height": 2048, "fps": 20}},
        ),
    )
    source = build_source(settings)
    assert (source.width, source.height, source.fps) == (2448, 2048, 20)


def test_invalid_camera_vendor_is_rejected():
    with pytest.raises(ValidationError):
        CameraSettings(vendor="unknown")


def test_online_yaml_contains_both_sdk_installers():
    settings = AppSettings.from_yaml("agv_vision/config/settings_online.yaml")
    assert settings.camera.daheng.installer_path.endswith("Galaxy_Windows_CN_32bits-64bits_2.6.2607.9201.exe")
    assert settings.camera.hikvision.installer_path.endswith("MVS_SDK_V4_7_0_3_MVFG_V2_7_0_2_VC90_Runtime_STD_251113.exe")
    assert settings.camera.daheng.python_path == r"D:\sdk\大恒\GalaxySDK"
    assert settings.camera.hikvision.python_path == r"D:\sdk\hik\MvImport"


def test_hikvision_mono8_is_converted_to_bgr():
    source = HikvisionColorSource(2, 2, 15)
    source.sdk = type("Sdk", (), {"PixelType_Gvsp_Mono8": 1})
    info = type("Info", (), {"nWidth": 2, "nHeight": 2, "enPixelType": 1, "nFrameLen": 4})()
    raw = (ctypes.c_ubyte * 4)(0, 64, 128, 255)
    image = source._to_bgr(raw, info)
    assert image.shape == (2, 2, 3)
    assert np.array_equal(image[:, :, 0], np.array([[0, 64], [128, 255]], dtype=np.uint8))
