"""Debug charuco detection on the 5 failing 626test images."""
from pathlib import Path
import cv2
import numpy as np

from agv_vision.config.settings import AppSettings
from agv_vision.vision.common import get_aruco_dictionary

ROOT = Path(r'D:\code\AGV\pkg3_260522')
TEST_DIR = ROOT / 'examples' / '拍照位姿' / '2026.626_test'
OUT = ROOT / 'data' / 'verify_handeye_20260626' / 'debug_fail'
OUT.mkdir(parents=True, exist_ok=True)

settings = AppSettings.from_yaml(ROOT / 'agv_vision' / 'config' / 'settings.yaml')
aruco = cv2.aruco
dictionary = get_aruco_dictionary(settings.charuco.dictionary_name)
board = aruco.CharucoBoard(
    (settings.charuco.squares_x, settings.charuco.squares_y),
    settings.charuco.square_length_m,
    settings.charuco.marker_length_m,
    dictionary,
)
params = aruco.DetectorParameters()
params.adaptiveThreshConstant = settings.charuco.adaptive_thresh_constant
params.minMarkerPerimeterRate = settings.charuco.min_marker_perimeter_rate
params.maxMarkerPerimeterRate = settings.charuco.max_marker_perimeter_rate
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
