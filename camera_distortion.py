"""
ChArUco 相机内参标定

功能：
1. 批量读取标定图片
2. 检测 ChArUco 角点
3. 使用亚像素角点进行相机内参标定
4. 输出每张图片的重投影误差
5. 自动筛选高误差图片并二次标定
6. 保存 camera_matrix、dist_coeffs 到 YAML
7. 保存角点检测可视化图片

依赖：
    pip install opencv-contrib-python pyyaml numpy
"""

from pathlib import Path
import cv2
import numpy as np
import yaml


# ============================================================
# 1. 配置区 —— 这里一定要按照你的实际 ChArUco 板修改
# ============================================================

# 图片文件夹
IMAGE_DIR = Path(r"C:\Users\Dell\Desktop/260821")

# 输出目录
OUTPUT_DIR = Path(r"C:\Users\Dell\Desktop/260821/camera_calibration_output1")

# ChArUco 棋盘参数
#
# 注意：
# squares_x / squares_y 是“方格数量”，不是内部角点数量
#
# 比如 5×5 ChArUco：
# squares_x = 5
# squares_y = 5
#
SQUARES_X = 5
SQUARES_Y = 5

# 每个棋盘格边长，单位：米
# 示例：10 mm = 0.010 m


SQUARE_LENGTH_M = 0.030

# ArUco marker 黑色方块边长，单位：米
# 示例：7 mm = 0.007 m
MARKER_LENGTH_M = 0.022

# 字典类型
# 必须与你打印 ChArUco 板使用的字典一致
ARUCO_DICT = cv2.aruco.DICT_4X4_50

# 至少检测到多少个 ChArUco 棋盘角点才接受该图片
MIN_CHARUCO_CORNERS = 8

# 单张图片重投影误差超过这个值时认为是异常图
# 建议第一遍先用 0.5 px
MAX_REPROJECTION_ERROR_PX = 0.5

# 是否自动删除高误差样本后再重新标定
AUTO_REFINE = True

# 支持的图片格式
IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tif",
    ".tiff",
}


# ============================================================
# 2. 创建 ChArUco Board
# ============================================================

def create_charuco_board():
    dictionary = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)

    # OpenCV 新版 API
    board = cv2.aruco.CharucoBoard(
        (SQUARES_X, SQUARES_Y),
        SQUARE_LENGTH_M,
        MARKER_LENGTH_M,
        dictionary,
    )

    return dictionary, board


# ============================================================
# 3. 检测一张图片中的 ChArUco 角点
# ============================================================

def detect_charuco(image, dictionary, board):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # ArUco 检测参数
    detector_params = cv2.aruco.DetectorParameters()

    detector = cv2.aruco.ArucoDetector(
        dictionary,
        detector_params,
    )

    marker_corners, marker_ids, rejected = detector.detectMarkers(gray)

    if marker_ids is None or len(marker_ids) == 0:
        return None

    # 提高 ArUco marker 四角精度
    criteria = (
        cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
        50,
        0.001,
    )

    refined_marker_corners = []

    for corners in marker_corners:
        refined = corners.copy()

        cv2.cornerSubPix(
            gray,
            refined,
            winSize=(5, 5),
            zeroZone=(-1, -1),
            criteria=criteria,
        )

        refined_marker_corners.append(refined)

    # 从 ArUco marker 插值得到 ChArUco 棋盘角点
    num_corners, charuco_corners, charuco_ids = \
        cv2.aruco.interpolateCornersCharuco(
            refined_marker_corners,
            marker_ids,
            gray,
            board,
        )

    if charuco_ids is None or charuco_corners is None:
        return None

    if len(charuco_ids) < MIN_CHARUCO_CORNERS:
        return None

    # 再对 ChArUco chessboard corners 做一次亚像素优化
    refined_charuco = charuco_corners.copy()

    cv2.cornerSubPix(
        gray,
        refined_charuco,
        winSize=(5, 5),
        zeroZone=(-1, -1),
        criteria=criteria,
    )

    return {
        "charuco_corners": refined_charuco,
        "charuco_ids": charuco_ids,
        "marker_corners": refined_marker_corners,
        "marker_ids": marker_ids,
    }


# ============================================================
# 4. 根据 ChArUco ID 获取实际世界坐标
# ============================================================

def get_object_points(board, charuco_ids):
    """
    board.getChessboardCorners():
        返回全部 ChArUco 棋盘角点的三维坐标

    charuco_ids:
        当前图片检测到的角点 ID
    """

    chessboard_corners = board.getChessboardCorners()

    ids = charuco_ids.flatten().astype(int)

    object_points = chessboard_corners[ids]

    return np.asarray(object_points, dtype=np.float32)


# ============================================================
# 5. 相机标定
# ============================================================

def calibrate(samples, image_size):
    all_object_points = []
    all_image_points = []

    for sample in samples:
        all_object_points.append(
            sample["object_points"].astype(np.float32)
        )

        all_image_points.append(
            sample["image_points"].reshape(-1, 2).astype(np.float32)
        )

    # 使用标准 pinhole 模型：
    #
    # fx fy cx cy
    # k1 k2 p1 p2 k3
    #
    rms, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
        objectPoints=all_object_points,
        imagePoints=all_image_points,
        imageSize=image_size,
        cameraMatrix=None,
        distCoeffs=None,
        flags=0,
    )

    return (
        rms,
        camera_matrix,
        dist_coeffs,
        rvecs,
        tvecs,
    )


# ============================================================
# 6. 计算每张图片重投影误差
# ============================================================

def calculate_reprojection_errors(
    samples,
    camera_matrix,
    dist_coeffs,
    rvecs,
    tvecs,
):
    errors = []

    for i, sample in enumerate(samples):

        projected_points, _ = cv2.projectPoints(
            sample["object_points"],
            rvecs[i],
            tvecs[i],
            camera_matrix,
            dist_coeffs,
        )

        projected_points = projected_points.reshape(-1, 2)
        detected_points = sample["image_points"].reshape(-1, 2)

        diff = projected_points - detected_points

        # 每个点二维欧氏距离
        point_errors = np.linalg.norm(
            diff,
            axis=1,
        )

        # 当前图片 RMS
        rmse = np.sqrt(
            np.mean(
                point_errors ** 2
            )
        )

        errors.append(float(rmse))

    return errors


# ============================================================
# 7. 保存 YAML
# ============================================================

def save_yaml(
    output_path,
    camera_matrix,
    dist_coeffs,
    image_size,
    rms,
    sample_count,
):
    data = {
        "image_width": int(image_size[0]),
        "image_height": int(image_size[1]),

        "camera_matrix": camera_matrix.tolist(),

        "dist_coeffs": dist_coeffs.reshape(-1).tolist(),

        "rms_px": float(rms),

        "sample_count": int(sample_count),

        "charuco": {
            "squares_x": SQUARES_X,
            "squares_y": SQUARES_Y,
            "square_length_m": SQUARE_LENGTH_M,
            "marker_length_m": MARKER_LENGTH_M,
        },
    }

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as f:

        yaml.safe_dump(
            data,
            f,
            allow_unicode=True,
            sort_keys=False,
        )


# ============================================================
# 8. 保存可视化图片
# ============================================================

def save_detection_image(
    image,
    detection,
    output_path,
):
    vis = image.copy()

    cv2.aruco.drawDetectedMarkers(
        vis,
        detection["marker_corners"],
        detection["marker_ids"],
    )

    cv2.aruco.drawDetectedCornersCharuco(
        vis,
        detection["charuco_corners"],
        detection["charuco_ids"],
    )

    cv2.imwrite(
        str(output_path),
        vis,
    )


# ============================================================
# 9. 打印结果
# ============================================================

def print_result(
    title,
    rms,
    camera_matrix,
    dist_coeffs,
    samples,
    errors,
):
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)

    print()
    print(f"有效图片数量：{len(samples)}")

    print()
    print(f"OpenCV calibration RMS：{rms:.6f} px")

    print()
    print("camera_matrix:")
    print(camera_matrix)

    print()

    print("dist_coeffs:")
    print(dist_coeffs.reshape(-1))

    print()

    fx = camera_matrix[0, 0]
    fy = camera_matrix[1, 1]
    cx = camera_matrix[0, 2]
    cy = camera_matrix[1, 2]

    print("关键内参：")

    print(f"fx = {fx:.6f}")
    print(f"fy = {fy:.6f}")
    print(f"cx = {cx:.6f}")
    print(f"cy = {cy:.6f}")

    print()

    print("每张图片重投影 RMSE：")

    for sample, error in sorted(
        zip(samples, errors),
        key=lambda x: x[1],
        reverse=True,
    ):

        flag = ""

        if error > MAX_REPROJECTION_ERROR_PX:
            flag = "  <-- 高误差"

        print(
            f"{sample['path'].name:<40}"
            f"{error:>10.4f} px"
            f"{flag}"
        )

    print()

    print(
        f"平均单图 RMSE："
        f"{np.mean(errors):.4f} px"
    )

    print(
        f"最大单图 RMSE："
        f"{np.max(errors):.4f} px"
    )

    print(
        f"最小单图 RMSE："
        f"{np.min(errors):.4f} px"
    )


# ============================================================
# 10. 主程序
# ============================================================

def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    detection_dir = OUTPUT_DIR / "detections"

    detection_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    dictionary, board = create_charuco_board()

    image_paths = sorted([
        p
        for p in IMAGE_DIR.iterdir()
        if p.is_file()
        and p.suffix.lower() in IMAGE_EXTENSIONS
    ])

    if not image_paths:
        raise RuntimeError(
            f"没有在目录中找到图片：{IMAGE_DIR}"
        )

    print(f"共找到 {len(image_paths)} 张图片")

    samples = []

    image_size = None

    for index, image_path in enumerate(
        image_paths,
        start=1,
    ):
        image = cv2.imread(
            str(image_path)
        )

        if image is None:
            print(
                f"[跳过] 无法读取："
                f"{image_path.name}"
            )
            continue

        h, w = image.shape[:2]

        current_size = (w, h)

        if image_size is None:
            image_size = current_size

        elif current_size != image_size:
            print(
                f"[跳过] 图片尺寸不同："
                f"{image_path.name} "
                f"{current_size} != {image_size}"
            )
            continue

        detection = detect_charuco(
            image,
            dictionary,
            board,
        )

        if detection is None:
            print(
                f"[失败] "
                f"{index}/{len(image_paths)} "
                f"{image_path.name}"
            )
            continue

        object_points = get_object_points(
            board,
            detection["charuco_ids"],
        )

        image_points = detection[
            "charuco_corners"
        ].reshape(-1, 2)

        sample = {
            "path": image_path,
            "object_points": object_points,
            "image_points": image_points,
        }

        samples.append(sample)

        print(
            f"[成功] "
            f"{index}/{len(image_paths)} "
            f"{image_path.name} "
            f"corners={len(image_points)}"
        )

        save_detection_image(
            image,
            detection,
            detection_dir / image_path.name,
        )

    if len(samples) < 10:
        raise RuntimeError(
            f"有效标定图片只有 {len(samples)} 张，"
            f"建议至少 15～20 张。"
        )

    # ========================================================
    # 第一次标定
    # ========================================================

    (
        rms,
        camera_matrix,
        dist_coeffs,
        rvecs,
        tvecs,
    ) = calibrate(
        samples,
        image_size,
    )

    errors = calculate_reprojection_errors(
        samples,
        camera_matrix,
        dist_coeffs,
        rvecs,
        tvecs,
    )

    print_result(
        "第一次相机内参标定",
        rms,
        camera_matrix,
        dist_coeffs,
        samples,
        errors,
    )

    # ========================================================
    # 筛选异常图片
    # ========================================================

    final_samples = samples

    if AUTO_REFINE:

        good_samples = []

        removed_samples = []

        for sample, error in zip(
            samples,
            errors,
        ):
            if error <= MAX_REPROJECTION_ERROR_PX:
                good_samples.append(sample)
            else:
                removed_samples.append(
                    (sample, error)
                )

        if removed_samples:
            print()
            print("=" * 80)
            print("准备剔除以下高误差图片")
            print("=" * 80)

            for sample, error in removed_samples:
                print(
                    f"{sample['path'].name}: "
                    f"{error:.4f} px"
                )

        if len(good_samples) >= 10:
            final_samples = good_samples

    # ========================================================
    # 二次标定
    # ========================================================

    if len(final_samples) != len(samples):

        (
            rms,
            camera_matrix,
            dist_coeffs,
            rvecs,
            tvecs,
        ) = calibrate(
            final_samples,
            image_size,
        )

        errors = calculate_reprojection_errors(
            final_samples,
            camera_matrix,
            dist_coeffs,
            rvecs,
            tvecs,
        )

        print_result(
            "剔除异常图片后的最终标定",
            rms,
            camera_matrix,
            dist_coeffs,
            final_samples,
            errors,
        )

    # ========================================================
    # 保存最终结果
    # ========================================================

    yaml_path = (
        OUTPUT_DIR /
        "camera_intrinsics.yaml"
    )

    save_yaml(
        yaml_path,
        camera_matrix,
        dist_coeffs,
        image_size,
        rms,
        len(final_samples),
    )

    print()
    print("=" * 80)
    print("标定完成")
    print("=" * 80)

    print(
        f"结果已保存："
        f"{yaml_path}"
    )

    print(
        f"角点可视化："
        f"{detection_dir}"
    )


if __name__ == "__main__":
    main()