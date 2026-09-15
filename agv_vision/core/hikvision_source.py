from __future__ import annotations

import ctypes
import importlib
import os
import socket
import sys
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from agv_vision.core.exceptions import SourceError
from agv_vision.core.frame_source import BaseFrameSource
from agv_vision.core.models import FrameBundle


class HikvisionColorSource(BaseFrameSource):
    """Hikrobot MVS SDK frame source."""

    def __init__(self, width: int, height: int, fps: int, timeout_ms: int = 2000,
                 serial_number: str | None = None, ip_address: str | None = None,
                 auto_exposure: bool = True, exposure: int | None = None,
                 gain: int | None = None, auto_white_balance: bool = True,
                 white_balance: int | None = None, sdk_installer: str | None = None,
                 sdk_python_path: str | None = None):
        self.width, self.height, self.fps = width, height, fps
        self.timeout_ms = timeout_ms
        self.serial_number, self.ip_address = serial_number, ip_address
        self.auto_exposure, self.exposure, self.gain = auto_exposure, exposure, gain
        self.auto_white_balance, self.white_balance = auto_white_balance, white_balance
        self.sdk_installer, self.sdk_python_path = sdk_installer, sdk_python_path
        self.sdk: Any = None
        self.camera: Any = None
        self.payload_size = 0
        self.opened = False
        self.grabbing = False

    def _candidate_python_paths(self) -> list[Path]:
        paths: list[Path] = []
        if self.sdk_python_path:
            paths.append(Path(self.sdk_python_path))
        for env_name in ("MVS_HOME", "MVCAM_SDK_PATH"):
            if os.environ.get(env_name):
                paths.append(Path(os.environ[env_name]) / "Development" / "Samples" / "Python" / "MvImport")
        for root in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
            if root:
                paths.append(Path(root) / "MVS" / "Development" / "Samples" / "Python" / "MvImport")
        return paths

    def _load_sdk(self):
        if self.sdk_python_path and not Path(self.sdk_python_path).is_dir():
            raise SourceError(f"海康 SDK python_path 不是有效目录: {self.sdk_python_path}")
        for path in self._candidate_python_paths():
            if path.is_dir() and str(path) not in sys.path:
                sys.path.insert(0, str(path))
        try:
            return importlib.import_module("MvCameraControl_class")
        except Exception as exc:
            installer = f"，安装包: {self.sdk_installer}" if self.sdk_installer else ""
            raise SourceError("无法导入海康 MvCameraControl_class。请先安装 MVS SDK，并把 MvImport 目录配置到 "
                              f"camera.hikvision.python_path{installer}。原始错误: {exc}") from exc

    @staticmethod
    def _decode_c_string(value: Any) -> str:
        return bytes(value).split(b"\0", 1)[0].decode("utf-8", errors="ignore")

    def _device_identity(self, info: Any) -> tuple[str | None, str | None]:
        if info.nTLayerType == getattr(self.sdk, "MV_GIGE_DEVICE", -1):
            data = info.SpecialInfo.stGigEInfo
            serial = self._decode_c_string(data.chSerialNumber)
            ip = socket.inet_ntoa(int(data.nCurrentIp).to_bytes(4, "big"))
            return serial, ip
        if info.nTLayerType == getattr(self.sdk, "MV_USB_DEVICE", -1):
            data = info.SpecialInfo.stUsb3VInfo
            return self._decode_c_string(data.chSerialNumber), None
        return None, None

    def _check(self, code: int, action: str) -> None:
        if code != 0:
            raise SourceError(f"{action}失败，MVS 错误码=0x{code & 0xFFFFFFFF:08X}")

    def _set(self, method: str, key: str, value: Any) -> None:
        try:
            getattr(self.camera, method)(key, value)
        except Exception:
            pass

    def open(self) -> None:
        self.sdk = self._load_sdk()
        try:
            device_list = self.sdk.MV_CC_DEVICE_INFO_LIST()
            transport = self.sdk.MV_GIGE_DEVICE | self.sdk.MV_USB_DEVICE
            self._check(self.sdk.MvCamera.MV_CC_EnumDevices(transport, device_list), "枚举海康相机")
            if device_list.nDeviceNum == 0:
                raise SourceError("未检测到海康相机")
            selected = None
            for index in range(device_list.nDeviceNum):
                info = ctypes.cast(device_list.pDeviceInfo[index],
                                   ctypes.POINTER(self.sdk.MV_CC_DEVICE_INFO)).contents
                serial, ip = self._device_identity(info)
                if self.serial_number and serial != self.serial_number:
                    continue
                if self.ip_address and ip != self.ip_address:
                    continue
                selected = info
                break
            if selected is None:
                raise SourceError(f"未找到指定海康相机: {self.serial_number or self.ip_address}")

            self.camera = self.sdk.MvCamera()
            self._check(self.camera.MV_CC_CreateHandle(selected), "创建海康相机句柄")
            access = getattr(self.sdk, "MV_ACCESS_Exclusive", 1)
            self._check(self.camera.MV_CC_OpenDevice(access, 0), "打开海康相机")
            self.opened = True

            self._set("MV_CC_SetEnumValue", "TriggerMode", getattr(self.sdk, "MV_TRIGGER_MODE_OFF", 0))
            self._set("MV_CC_SetIntValue", "Width", self.width)
            self._set("MV_CC_SetIntValue", "Height", self.height)
            self._set("MV_CC_SetBoolValue", "AcquisitionFrameRateEnable", True)
            self._set("MV_CC_SetFloatValue", "AcquisitionFrameRate", float(self.fps))
            auto = (getattr(self.sdk, "MV_EXPOSURE_AUTO_MODE_CONTINUOUS", 2)
                    if self.auto_exposure else getattr(self.sdk, "MV_EXPOSURE_AUTO_MODE_OFF", 0))
            self._set("MV_CC_SetEnumValue", "ExposureAuto", auto)
            if not self.auto_exposure and self.exposure is not None:
                self._set("MV_CC_SetFloatValue", "ExposureTime", float(self.exposure))
            if self.gain is not None:
                self._set("MV_CC_SetFloatValue", "Gain", float(self.gain))
            self._set("MV_CC_SetEnumValue", "BalanceWhiteAuto", 1 if self.auto_white_balance else 0)

            value_type = getattr(self.sdk, "MVCC_INTVALUE_EX", None)
            value_type = value_type or getattr(self.sdk, "MVCC_INTVALUE")
            value = value_type()
            self._check(self.camera.MV_CC_GetIntValue("PayloadSize", value), "读取海康 PayloadSize")
            self.payload_size = int(value.nCurValue)
            self._check(self.camera.MV_CC_StartGrabbing(), "启动海康取流")
            self.grabbing = True
        except SourceError:
            self.close()
            raise
        except Exception as exc:
            self.close()
            raise SourceError(f"打开海康相机失败: {exc}") from exc

    def grab(self) -> FrameBundle:
        if self.camera is None or not self.grabbing:
            raise SourceError("海康图像源尚未打开")
        info = self.sdk.MV_FRAME_OUT_INFO_EX()
        ctypes.memset(ctypes.byref(info), 0, ctypes.sizeof(info))
        raw = (ctypes.c_ubyte * self.payload_size)()
        code = self.camera.MV_CC_GetOneFrameTimeout(raw, self.payload_size, info, self.timeout_ms)
        self._check(code, "海康相机取图")
        image = self._to_bgr(raw, info)
        return FrameBundle(
            color=image,
            timestamp_ms=int(getattr(info, "nHostTimeStamp", 0)) or None,
            meta={"source": "hikvision", "width": int(info.nWidth),
                  "height": int(info.nHeight), "pixel_type": int(info.enPixelType),
                  "frame_id": int(info.nFrameNum)},
        )

    def _to_bgr(self, raw: Any, info: Any):
        width, height = int(info.nWidth), int(info.nHeight)
        pixel_type, length = int(info.enPixelType), int(info.nFrameLen)
        source = np.ctypeslib.as_array(raw)[:length]
        if pixel_type == getattr(self.sdk, "PixelType_Gvsp_Mono8", -1):
            return cv2.cvtColor(source.reshape(height, width), cv2.COLOR_GRAY2BGR)
        if pixel_type == getattr(self.sdk, "PixelType_Gvsp_RGB8_Packed", -1):
            return cv2.cvtColor(source.reshape(height, width, 3), cv2.COLOR_RGB2BGR)
        if pixel_type == getattr(self.sdk, "PixelType_Gvsp_BGR8_Packed", -1):
            return source.reshape(height, width, 3).copy()

        target = getattr(self.sdk, "PixelType_Gvsp_BGR8_Packed", None)
        convert_type = getattr(self.sdk, "MV_CC_PIXEL_CONVERT_PARAM_EX", None)
        convert_type = convert_type or getattr(self.sdk, "MV_CC_PIXEL_CONVERT_PARAM", None)
        if target is None or convert_type is None:
            raise SourceError(f"海康图像像素格式不受支持: 0x{pixel_type:08X}")
        output_size = width * height * 3
        output = (ctypes.c_ubyte * output_size)()
        param = convert_type()
        ctypes.memset(ctypes.byref(param), 0, ctypes.sizeof(param))
        param.nWidth, param.nHeight = width, height
        param.pSrcData = ctypes.cast(raw, ctypes.POINTER(ctypes.c_ubyte))
        param.nSrcDataLen, param.enSrcPixelType = length, pixel_type
        param.enDstPixelType = target
        param.pDstBuffer = ctypes.cast(output, ctypes.POINTER(ctypes.c_ubyte))
        param.nDstBufferSize = output_size
        self._check(self.camera.MV_CC_ConvertPixelType(param), "转换海康图像像素格式")
        output_length = int(getattr(param, "nDstLen", output_size))
        return np.ctypeslib.as_array(output)[:output_length].reshape(height, width, 3).copy()

    def close(self) -> None:
        if self.camera is not None and self.grabbing:
            try:
                self.camera.MV_CC_StopGrabbing()
            except Exception:
                pass
        self.grabbing = False
        if self.camera is not None and self.opened:
            try:
                self.camera.MV_CC_CloseDevice()
            except Exception:
                pass
        self.opened = False
        if self.camera is not None:
            try:
                self.camera.MV_CC_DestroyHandle()
            except Exception:
                pass
        self.camera = None
        self.payload_size = 0
