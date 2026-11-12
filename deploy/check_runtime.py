"""Check container files/libraries without opening cameras or switching lights."""
import ctypes
import os
from pathlib import Path
import stat

from agv_vision.config.settings import AppSettings


def main():
    settings = AppSettings.from_yaml('agv_vision/config/settings_online.yaml')
    if settings.camera.vendor != 'hikvision':
        raise SystemExit('This Docker image is configured for Hikvision, not other camera SDKs')
    python_path = Path(settings.camera.hikvision.python_path or '')
    if not (python_path / 'MvCameraControl_class.py').is_file():
        raise SystemExit(f'MvImport missing: {python_path}')
    runtime = Path(os.environ.get('MVCAM_COMMON_RUNENV', '/opt/MVS/lib'))
    libraries = [runtime / '64' / 'libMvCameraControl.so']
    if settings.light.enabled:
        if not Path(settings.light.config_path).is_file():
            raise SystemExit(f'Light INI missing: {settings.light.config_path}')
        libraries.append(Path(settings.light.library_path).resolve())
        device = os.environ.get('NODKA_SERIAL_DEVICE')
        if not device or not Path(device).exists() or not stat.S_ISCHR(Path(device).stat().st_mode):
            raise SystemExit(f'Mapped serial character device missing: {device}')
        print(f'SERIAL: {device}')
    for library in libraries:
        ctypes.CDLL(str(library))
        print(f'LOAD OK: {library}')
    print('File/library checks passed; camera/light hardware has NOT been operated.')


if __name__ == '__main__':
    main()
