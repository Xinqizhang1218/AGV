from __future__ import annotations

import importlib
import os
import sys
import threading
import types
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from agv_vision.core.exceptions import SourceError
from agv_vision.core.frame_source import BaseFrameSource
from agv_vision.core.models import FrameBundle


class DahengColorSource(BaseFrameSource):
    """Daheng Galaxy SDK (gxipy) frame source."""

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
        self.gx: Any = None
        self.manager: Any = None
        self.device: Any = None
        self._dll_dir_handles: list[Any] = []
        self._grab_lock = threading.RLock()

    def _load_sdk(self):
        if self.sdk_python_path:
            path = Path(self.sdk_python_path)
            if not path.is_dir():
                raise SourceError(f"大恒 SDK python_path 不是有效目录: {path}")
            candidates = [path, path / "Development" / "Samples" / "Python"]
            for candidate in candidates:
                if candidate.is_dir() and str(candidate) not in sys.path:
                    sys.path.insert(0, str(candidate))
            is_64_bit = sys.maxsize > 2**32
            genicam_root = path / "GenICam"
            if genicam_root.is_dir():
                os.environ["GALAXY_GENICAM_ROOT"] = str(genicam_root)
            # DeviceManager uses this variable to find the GenTL .cti libraries.
            # Override stale SDK paths for this process only.
            gentl_dir = path / "GenTL" / ("Win64" if is_64_bit else "Win32")
            if gentl_dir.is_dir():
                gentl_env = (
                    "GENICAM_GENTL64_PATH" if is_64_bit else "GENICAM_GENTL32_PATH"
                )
                os.environ[gentl_env] = str(gentl_dir)
            dll_candidates = [
                path / "APIDll" / ("Win64" if is_64_bit else "Win32"),
                path / "GenICam" / "bin" / ("Win64_x64" if is_64_bit else "Win32_i86"),
                gentl_dir,
            ]
            for dll_dir in dll_candidates:
                if not dll_dir.is_dir():
                    continue
                dll_path = str(dll_dir)
                os.environ["PATH"] = dll_path + os.pathsep + os.environ.get("PATH", "")
                if hasattr(os, "add_dll_directory"):
                    self._dll_dir_handles.append(os.add_dll_directory(dll_path))
        try:
            if "numpy.compat" not in sys.modules:
                try:
                    importlib.import_module("numpy.compat")
                except ModuleNotFoundError:
                    compat = types.ModuleType("numpy.compat")
                    compat.long = int
                    sys.modules["numpy.compat"] = compat
                    np.compat = compat
            return importlib.import_module("gxipy")
        except Exception as exc:
            installer = f"，安装包: {self.sdk_installer}" if self.sdk_installer else ""
            raise SourceError("无法导入大恒 gxipy。请先安装 Galaxy SDK，并把包含 gxipy 的目录配置到 "
                              f"camera.daheng.python_path{installer}。原始错误: {exc}") from exc

    @staticmethod
    def _try_set(node: Any, value: Any) -> None:
        try:
            if node is not None and node.is_implemented() and node.is_writable():
                node.set(value)
        except Exception:
            pass

    def open(self) -> None:
        self.gx = self._load_sdk()
        try:
            self.manager = self.gx.DeviceManager()
            count, _ = self.manager.update_device_list()
            if count == 0:
                raise SourceError("未检测到大恒相机")
            if self.serial_number:
                self.device = self.manager.open_device_by_sn(self.serial_number)
            elif self.ip_address:
                self.device = self.manager.open_device_by_ip(self.ip_address)
            else:
                self.device = self.manager.open_device_by_index(1)
            self._try_set(getattr(self.device, "TriggerMode", None), self.gx.GxSwitchEntry.OFF)
            self._try_set(getattr(self.device, "Width", None), self.width)
            self._try_set(getattr(self.device, "Height", None), self.height)
            self._try_set(getattr(self.device, "AcquisitionFrameRateMode", None), self.gx.GxSwitchEntry.ON)
            self._try_set(getattr(self.device, "AcquisitionFrameRate", None), float(self.fps))
            auto = self.gx.GxAutoEntry.CONTINUOUS if self.auto_exposure else self.gx.GxAutoEntry.OFF
            self._try_set(getattr(self.device, "ExposureAuto", None), auto)
            if not self.auto_exposure and self.exposure is not None:
                self._try_set(getattr(self.device, "ExposureTime", None), float(self.exposure))
            if self.gain is not None:
                self._try_set(getattr(self.device, "Gain", None), float(self.gain))
            white = self.gx.GxAutoEntry.CONTINUOUS if self.auto_white_balance else self.gx.GxAutoEntry.OFF
            self._try_set(getattr(self.device, "BalanceWhiteAuto", None), white)
            # The service captures on demand instead of continuously consuming frames.
            # Keep only one SDK buffer so old frames cannot accumulate while idle.
            self.device.data_stream[0].set_acquisition_buffer_number(1)
            self.device.stream_on()
        except SourceError:
            self.close()
            raise
        except Exception as exc:
            self.close()
            raise SourceError(f"打开大恒相机失败: {exc}") from exc

    def grab(self) -> FrameBundle:
        with self._grab_lock:
            if self.device is None:
                raise SourceError("大恒图像源尚未打开")
            try:
                stream = self.device.data_stream[0]
                # Drop queued frames and wait for the first frame captured after
                # this request, rather than returning an image left in the queue.
                stream.flush_queue()
                raw = stream.get_image(timeout=self.timeout_ms)
                if raw is None or raw.get_status() != self.gx.GxFrameStatusList.SUCCESS:
                    raise SourceError("大恒相机等待帧超时或帧状态异常")
                image = self._to_bgr(raw)
                return FrameBundle(
                    color=image,
                    timestamp_ms=getattr(raw, "get_timestamp", lambda: None)(),
                    meta={"source": "daheng", "width": int(raw.get_width()),
                          "height": int(raw.get_height()),
                          "frame_id": getattr(raw, "get_frame_id", lambda: None)()},
                )
            except SourceError:
                raise
            except Exception as exc:
                raise SourceError(f"大恒相机取图失败: {exc}") from exc

    def _to_bgr(self, raw: Any):
        try:
            rgb = raw.convert("RGB")
            array = None if rgb is None else rgb.get_numpy_array()
            if array is not None:
                return cv2.cvtColor(array, cv2.COLOR_RGB2BGR)
        except Exception:
            pass
        array = raw.get_numpy_array()
        if array is None:
            raise SourceError("大恒相机图像转换失败")
        if array.ndim == 2:
            return cv2.cvtColor(array, cv2.COLOR_GRAY2BGR)
        if array.ndim == 3 and array.shape[2] == 3:
            return array.copy()
        raise SourceError(f"大恒相机返回了不支持的图像形状: {array.shape}")

    def close(self) -> None:
        with self._grab_lock:
            if self.device is not None:
                try:
                    self.device.stream_off()
                except Exception:
                    pass
                try:
                    self.device.close_device()
                except Exception:
                    pass
            self.device = None
            self.manager = None
