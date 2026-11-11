"""Debug charuco detection on the 5 failing 626test images."""
from pathlib import Path
import argparse
import cv2
import numpy as np

from agv_vision.config.settings import AppSettings
from agv_vision.vision.common import get_aruco_dictionary

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description='按手眼板或工位板配置检查 ChArUco 识别')
parser.add_argument('--purpose', choices=('handeye', 'station'), default='handeye')
parser.add_argument('--config', type=Path, default=ROOT / 'agv_vision/config/settings.yaml')
parser.add_argument('--image-dir', type=Path, default=ROOT / 'examples/拍照位姿/2026.626_test')
parser.add_argument('--output-dir', type=Path, default=None)
args = parser.parse_args()
TEST_DIR = args.image_dir
OUT = args.output_dir or ROOT / 'data' / 'debug_fail' / args.purpose
OUT.mkdir(parents=True, exist_ok=True)

settings = AppSettings.from_yaml(args.config)
board_settings = getattr(settings, f'{args.purpose}_charuco')
aruco = cv2.aruco
dictionary = get_aruco_dictionary(board_settings.dictionary_name)
board = aruco.CharucoBoard(
    (board_settings.squares_x, board_settings.squares_y),
    board_settings.square_length_m,
    board_settings.marker_length_m,
    dictionary,
)
params = aruco.DetectorParameters()
params.adaptiveThreshConstant = board_settings.adaptive_thresh_constant
params.minMarkerPerimeterRate = board_settings.min_marker_perimeter_rate
params.maxMarkerPerimeterRate = board_settings.max_marker_perimeter_rate
ch_params = aruco.CharucoParameters()
detector = aruco.CharucoDetector(board, ch_params, params)

for img_path in sorted(TEST_DIR.glob('*.jpg')):
    data = np.fromfile(str(img_path), dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    cc, ci, mc, mi = detector.detectBoard(gray)
    marker_count = 0 if mi is None else len(mi)
    corner_count = 0 if ci is None else len(ci)
    print(f'{img_path.name}: size={w}x{h} markers={marker_count} corners={corner_count}')
    if mi is not None:
        print(f'   marker_ids={mi.flatten().tolist()}')
    # save a copy with detected markers drawn
    vis = img.copy()
    if mc is not None:
        vis = aruco.drawDetectedMarkers(vis, mc, mi)
    if cc is not None:
        vis = aruco.drawDetectedCorners2D(vis, cc, ci)
    cv2.imwrite(str(OUT / img_path.name), vis)

    # also try other dictionaries in case the board uses a different dict
    for dict_name, dict_enum in [
        ('DICT_4X4_50', cv2.aruco.DICT_4X4_50),
        ('DICT_5X5_50', cv2.aruco.DICT_5X5_50),
        ('DICT_5X5_100', cv2.aruco.DICT_5X5_100),
        ('DICT_ARUCO_ORIGINAL', cv2.aruco.DICT_ARUCO_ORIGINAL),
        ('DICT_APRILTAG_36h11', cv2.aruco.DICT_APRILTAG_36h11),
    ]:
        d = aruco.getPredefinedDictionary(dict_enum)
        det = aruco.ArucoDetector(d, aruco.DetectorParameters())
        corners, ids, _ = det.detectMarkers(gray)
        c = 0 if ids is None else len(ids)
        if c > 0:
            print(f'   try {dict_name}: markers={c} ids={ids.flatten().tolist()}')
