# import cv2

# img = cv2.imread(r"examples\offline_images\handeye\handeye_01.png")
# gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# dict_names = {
#     "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
#     "DICT_4X4_100": cv2.aruco.DICT_4X4_100,
#     "DICT_4X4_250": cv2.aruco.DICT_4X4_250,
#     "DICT_4X4_1000": cv2.aruco.DICT_4X4_1000,

#     "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
#     "DICT_5X5_100": cv2.aruco.DICT_5X5_100,
#     "DICT_5X5_250": cv2.aruco.DICT_5X5_250,
#     "DICT_5X5_1000": cv2.aruco.DICT_5X5_1000,

#     "DICT_6X6_50": cv2.aruco.DICT_6X6_50,
#     "DICT_6X6_100": cv2.aruco.DICT_6X6_100,
#     "DICT_6X6_250": cv2.aruco.DICT_6X6_250,
#     "DICT_6X6_1000": cv2.aruco.DICT_6X6_1000,

#     "DICT_7X7_50": cv2.aruco.DICT_7X7_50,
#     "DICT_7X7_100": cv2.aruco.DICT_7X7_100,
#     "DICT_7X7_250": cv2.aruco.DICT_7X7_250,
#     "DICT_7X7_1000": cv2.aruco.DICT_7X7_1000,

#     "DICT_ARUCO_ORIGINAL": cv2.aruco.DICT_ARUCO_ORIGINAL,

#     "DICT_APRILTAG_16h5": cv2.aruco.DICT_APRILTAG_16h5,
#     "DICT_APRILTAG_25h9": cv2.aruco.DICT_APRILTAG_25h9,
#     "DICT_APRILTAG_36h10": cv2.aruco.DICT_APRILTAG_36h10,
#     "DICT_APRILTAG_36h11": cv2.aruco.DICT_APRILTAG_36h11,
# }

# for name, d in dict_names.items():
#     aruco_dict = cv2.aruco.getPredefinedDictionary(d)
#     corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict)
#     count = 0 if ids is None else len(ids)
#     print(f"{name:<24} marker_count = {count}")
#     if ids is not None:
#         print(" ids =", ids.flatten().tolist())
import cv2

img_path = r"D:\code\AGV\agv_vision_pkg_v2\examples\offline_images\station_reference\ref.png"   # 改成你的实际文件名
img = cv2.imread(img_path)
if img is None:
    raise FileNotFoundError(img_path)

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict)

print("ids =", ids)
print("count =", 0 if ids is None else len(ids))

if ids is not None:
    vis = cv2.aruco.drawDetectedMarkers(img.copy(), corners, ids)
    cv2.imwrite("aruco_ref_debug.jpg", vis)
    print("saved: aruco_ref_debug.jpg")