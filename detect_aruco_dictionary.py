import cv2
from pathlib import Path

# ===== 改成你的图片路径 =====
IMG_PATH = r"D:\code\AGV\agv_vision_pkg_v2\examples\offline_images\station_reference\ref.png"

# ===== 常见字典列表 =====
DICT_CANDIDATES = {
    "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
    "DICT_4X4_100": cv2.aruco.DICT_4X4_100,
    "DICT_4X4_250": cv2.aruco.DICT_4X4_250,
    "DICT_4X4_1000": cv2.aruco.DICT_4X4_1000,

    "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
    "DICT_5X5_100": cv2.aruco.DICT_5X5_100,
    "DICT_5X5_250": cv2.aruco.DICT_5X5_250,
    "DICT_5X5_1000": cv2.aruco.DICT_5X5_1000,

    "DICT_6X6_50": cv2.aruco.DICT_6X6_50,
    "DICT_6X6_100": cv2.aruco.DICT_6X6_100,
    "DICT_6X6_250": cv2.aruco.DICT_6X6_250,
    "DICT_6X6_1000": cv2.aruco.DICT_6X6_1000,

    "DICT_7X7_50": cv2.aruco.DICT_7X7_50,
    "DICT_7X7_100": cv2.aruco.DICT_7X7_100,
    "DICT_7X7_250": cv2.aruco.DICT_7X7_250,
    "DICT_7X7_1000": cv2.aruco.DICT_7X7_1000,

    "DICT_ARUCO_ORIGINAL": cv2.aruco.DICT_ARUCO_ORIGINAL,

    "DICT_APRILTAG_16h5": cv2.aruco.DICT_APRILTAG_16h5,
    "DICT_APRILTAG_25h9": cv2.aruco.DICT_APRILTAG_25h9,
    "DICT_APRILTAG_36h10": cv2.aruco.DICT_APRILTAG_36h10,
    "DICT_APRILTAG_36h11": cv2.aruco.DICT_APRILTAG_36h11,
}


def detect_with_dictionary(gray, dict_name, dict_id):
    aruco_dict = cv2.aruco.getPredefinedDictionary(dict_id)

    # 新版 API
    params = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(aruco_dict, params)

    corners, ids, rejected = detector.detectMarkers(gray)

    count = 0 if ids is None else len(ids)
    id_list = [] if ids is None else ids.flatten().tolist()
    return corners, ids, rejected, count, id_list


def main():
    img_path = Path(IMG_PATH)
    if not img_path.exists():
        raise FileNotFoundError(f"图片不存在: {img_path}")

    image = cv2.imread(str(img_path))
    if image is None:
        raise RuntimeError(f"图片读取失败: {img_path}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 可选：增强一下灰度图，对拍照偏灰的图更稳
    gray_eq = cv2.equalizeHist(gray)

    results = []
    best = None

    print(f"\n开始检测图片: {img_path}\n")

    for dict_name, dict_id in DICT_CANDIDATES.items():
        corners, ids, rejected, count, id_list = detect_with_dictionary(gray_eq, dict_name, dict_id)

        result = {
            "dict_name": dict_name,
            "count": count,
            "ids": id_list,
            "corners": corners,
            "ids_raw": ids,
        }
        results.append(result)

        print(f"{dict_name:<24} marker_count = {count}  ids = {id_list}")

        if best is None or count > best["count"]:
            best = result

    print("\n================ 最佳结果 ================\n")
    print(f"最佳字典: {best['dict_name']}")
    print(f"识别数量: {best['count']}")
    print(f"识别ID:   {best['ids']}")

    # 保存最佳检测可视化图
    vis = image.copy()
    if best["ids_raw"] is not None and len(best["corners"]) > 0:
        cv2.aruco.drawDetectedMarkers(vis, best["corners"], best["ids_raw"])

    out_path = img_path.with_name(img_path.stem + "_aruco_detect_debug.png")
    cv2.imwrite(str(out_path), vis)
    print(f"\n已保存 debug 图: {out_path}")


if __name__ == "__main__":
    main()