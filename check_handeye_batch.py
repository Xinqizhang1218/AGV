"""Quick check that handeye_batch images detect with current charuco settings."""
from pathlib import Path
import cv2

from agv_vision.config.settings import AppSettings
from agv_vision.core.image_io import read_image
from agv_vision.vision.charuco_detector import CharucoBoardDetector

ROOT = Path(r'D:\code\AGV\pkg3_260522')
IMG_DIR = ROOT / 'examples' / 'offline_images' / 'handeye_batch'

settings = AppSettings.from_yaml(ROOT / 'agv_vision' / 'config' / 'settings.yaml')
detector = CharucoBoardDetector(settings.charuco)

for img_path in sorted(IMG_DIR.glob('*.png')):
    img = read_image(img_path)
    try:
        obs = detector.detect(img)
        print(f'{img_path.name}: corners={obs.corner_count} center=({obs.board_center_px[0]:.1f},{obs.board_center_px[1]:.1f}) angle={obs.board_angle_deg:.2f} px/m={obs.pixel_scale_px_per_m:.3f}')
    except Exception as exc:
        print(f'{img_path.name}: FAIL {exc}')
