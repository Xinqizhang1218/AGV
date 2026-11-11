from __future__ import annotations

"""完整 3D 相机标定、手眼标定和在线 ArUco 位姿计算。

本文件统一使用 ``aTb`` 表示“从 b 坐标系变换到 a 坐标系”的 4x4 齐次矩阵：
``p_a = aTb @ p_b``。

坐标系：b=机器人基座，g=末端/夹爪，c=相机，t=标定板或在线目标。
因此 bTg 是末端在基座下的姿态，cTt 是目标在相机下的姿态，
gTc 是相机在末端下的姿态；在线链路为 ``gTt = gTc @ cTt``。
"""

# math 提供三角函数、角度转换和有限数检查。
import math
# Any 用于标注诊断字典中可能出现的不同数据类型。
from typing import Any

# OpenCV 负责相机标定、PnP、Rodrigues 变换和手眼标定。
import cv2
# NumPy 负责矩阵、向量以及数值有效性运算。
import numpy as np

# 标定阶段和在线检测阶段分别使用项目统一的业务异常。
from agv_vision.core.exceptions import CalibrationError, DetectorError
# HandEyeSample 是离线样本；StationReference 是在线检测到的工位参考。
from agv_vision.core.models import HandEyeSample, StationReference


def make_transform(rotation: np.ndarray, translation: np.ndarray) -> np.ndarray:
    """把 3x3 旋转矩阵和三维平移向量合成为 4x4 齐次变换矩阵。

    rotation 是旋转矩阵，translation 是 xyz 平移，返回可连乘的 float64 矩阵。
    """
    # 先生成单位矩阵，使最后一行固定为 [0, 0, 0, 1]。
    transform = np.eye(4, dtype=np.float64)
    # 整理为 3x3 后，写入齐次矩阵左上角。
    transform[:3, :3] = np.asarray(rotation, dtype=np.float64).reshape(3, 3)
    # 整理成长度 3 的向量，写入齐次矩阵最后一列。
    transform[:3, 3] = np.asarray(translation, dtype=np.float64).reshape(3)
    # 返回组装完成的坐标变换矩阵。
    return transform


def euler_xyz_to_rotation(rx: float, ry: float, rz: float) -> np.ndarray:
    """把 XYZ 固定轴欧拉角（弧度）转换为旋转矩阵。

    依次绕固定 X、Y、Z 轴旋转，作用到列向量上的总矩阵为 Rz @ Ry @ Rx。
    """
    # 预先计算 X 轴角度的正弦和余弦。
    sx, cx = math.sin(rx), math.cos(rx)
    # 预先计算 Y 轴角度的正弦和余弦。
    sy, cy = math.sin(ry), math.cos(ry)
    # 预先计算 Z 轴角度的正弦和余弦。
    sz, cz = math.sin(rz), math.cos(rz)
    # 构造绕 X 轴旋转 rx 的标准矩阵。
    rx_matrix = np.array([[1.0, 0.0, 0.0], [0.0, cx, -sx], [0.0, sx, cx]])
    # 构造绕 Y 轴旋转 ry 的标准矩阵。
    ry_matrix = np.array([[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]])
    # 构造绕 Z 轴旋转 rz 的标准矩阵。
    rz_matrix = np.array([[cz, -sz, 0.0], [sz, cz, 0.0], [0.0, 0.0, 1.0]])
    # 按固定轴 XYZ 约定连乘，得到最终旋转矩阵。
    return rz_matrix @ ry_matrix @ rx_matrix


def robot_pose_to_transform(sample: HandEyeSample) -> np.ndarray:
    """读取六轴机器人姿态并转换成 bTg。

    bTg 表示末端坐标系到基座坐标系；xyz 单位为米，欧拉角固定为弧度。
    """
    # meta 可能为 None；转为空字典后可统一处理缺少字段的情况。
    meta = sample.meta or {}
    # 所有输入显式转为 float，非法字符串会进入下面的异常处理。
    try:
        # 读取机器人 X 平移，单位为米。
        x = float(sample.robot_x_m)
        # 读取机器人 Y 平移，单位为米。
        y = float(sample.robot_y_m)
        # 读取机器人 Z 平移，单位为米。
        z = float(meta['z'])
        # 读取绕 X 轴的欧拉角。
        rx = float(meta['rx'])
        # 读取绕 Y 轴的欧拉角。
        ry = float(meta['ry'])
        # 读取绕 Z 轴的欧拉角。
        rz = float(meta['rz'])
    # 捕获缺字段、类型错误和数值转换失败。
    except (KeyError, TypeError, ValueError) as exc:
        # 转成项目统一异常，同时保留原异常原因。
        raise CalibrationError(f'样本 {sample.sample_id} 缺少有效的六轴机器人姿态') from exc

    # 把六个数放到同一序列，便于统一检查。
    values = (x, y, z, rx, ry, rz)
    # nan 和正负无穷都不能用于标定。
    if not all(math.isfinite(value) for value in values):
        # 报出样本编号，方便回查 Java 数据。
        raise CalibrationError(f'样本 {sample.sample_id} 的六轴机器人姿态包含非有限数值')

    # 先求旋转矩阵，再与 xyz 平移一起组装成 bTg。
    return make_transform(euler_xyz_to_rotation(rx, ry, rz), np.array([x, y, z]))


def _object_points(sample: HandEyeSample) -> np.ndarray:
    """取得 ChArUco 角点在标定板坐标系中的坐标，统一整理成 N x 3。"""
    # 转成 OpenCV 常用的 float32 数组。
    points = np.asarray(sample.observation.board_points_m, dtype=np.float32)
    # 必须是二维数组，每个点只能包含 xy 或 xyz。
    if points.ndim != 2 or points.shape[1] not in (2, 3):
        # 形状非法时立即指出对应样本。
        raise CalibrationError(f'样本 {sample.sample_id} 的 ChArUco 物点格式无效')
    # 二维平面坐标需要补成相机标定使用的三维坐标。
    if points.shape[1] == 2:
        # ChArUco 是平面板，输入只有 (x, y) 时补上 z=0。
        points = np.column_stack([points, np.zeros(len(points), dtype=np.float32)])
    # 连续内存可避免 OpenCV 拒绝非连续数组切片。
    return np.ascontiguousarray(points, dtype=np.float32)


def _image_points(sample: HandEyeSample) -> np.ndarray:
    """取得与物点一一对应的 ChArUco 图像像素坐标，统一整理成 N x 2。"""
    # 转成 float32，并让每个图像点固定为 (u, v)。
    points = np.asarray(sample.observation.image_points, dtype=np.float32).reshape(-1, 2)
    # 每个图像点必须有一个对应的标定板物点。
    if len(points) != len(sample.observation.board_points_m):
        # 数量不同表示二维/三维对应关系已损坏。
        raise CalibrationError(f'样本 {sample.sample_id} 的 ChArUco 图像点/物点数量不一致')
    # 返回 OpenCV 可直接使用的连续数组。
    return np.ascontiguousarray(points, dtype=np.float32)


def calibrate_camera_from_charuco(
    samples: list[HandEyeSample],
) -> tuple[np.ndarray, np.ndarray, float, tuple[int, int]]:
    """用多张 ChArUco 观测执行相机内参标定。

    返回相机矩阵 K、畸变系数、重投影 RMS（像素）和图像尺寸。
    calibrateCamera 要求所有标定图片的分辨率相同。
    """
    # 收集每张图片中 ChArUco 角点对应的三维板坐标。
    object_points: list[np.ndarray] = []
    # 收集与三维板坐标一一对应的二维像素坐标。
    image_points: list[np.ndarray] = []
    # 用集合记录尺寸，后面可直接判断是否出现多个分辨率。
    image_sizes: set[tuple[int, int]] = set()
    # 逐张解析离线手眼标定样本。
    for sample in samples:
        # 图像宽高位于样本扩展元数据中；None 按空字典处理。
        meta = sample.meta or {}
        # 宽高需要转成整数，任何缺失或非法输入都作为标定错误。
        try:
            # OpenCV 使用 (width, height) 顺序，而不是 (height, width)。
            size = (int(meta['image_width_px']), int(meta['image_height_px']))
        # 统一捕获缺字段、错误类型和无法转为整数。
        except (KeyError, TypeError, ValueError) as exc:
            # 附上样本编号，便于找到原始图片。
            raise CalibrationError(f'样本 {sample.sample_id} 缺少图像宽高') from exc
        # 零或负数不可能是合法图像尺寸。
        if size[0] <= 0 or size[1] <= 0:
            # 阻止无效尺寸继续传给 OpenCV。
            raise CalibrationError(f'样本 {sample.sample_id} 的图像宽高无效')
        # 保存当前图片分辨率。
        image_sizes.add(size)
        # 保存当前样本整理后的 N x 3 标定板物点。
        object_points.append(_object_points(sample))
        # 保存当前样本整理后的 N x 2 亚像素图像点。
        image_points.append(_image_points(sample))

    # 集合元素不是一个，说明样本图片的宽高不统一。
    if len(image_sizes) != 1:
        # calibrateCamera 不能把不同分辨率直接混在一次标定中。
        raise CalibrationError(f'相机标定图片分辨率不一致: {sorted(image_sizes)}')
    # 样本过少会让内参估计不稳定，因此设置最低数量。
    if len(samples) < 5:
        # 明确告诉调用端至少需要重新采集多少张。
        raise CalibrationError('calibrateCamera 至少需要 5 张有效 ChArUco 图片')

    # 已确认集合中只有一个尺寸，取出它传给 OpenCV。
    image_size = next(iter(image_sizes))
    # OpenCV 底层异常统一包装成项目标定异常。
    try:
        # 同时估计内参、畸变和每张图的外参；这里只保留在线 PnP 所需参数及 RMS。
        rms_px, camera_matrix, dist_coeffs, _, _ = cv2.calibrateCamera(
            # 每张图的三维标定板角点列表。
            object_points,
            # 每张图对应的二维亚像素角点列表。
            image_points,
            # 所有输入图片共有的 (width, height)。
            image_size,
            # 不提供初始相机矩阵，让 OpenCV 自行估计。
            None,
            # 不提供初始畸变系数，让 OpenCV 自行估计。
            None,
        )
    # cv2.error 包含 OpenCV 内部参数或数值求解失败信息。
    except cv2.error as exc:
        # 保留 OpenCV 原始信息，便于诊断采样质量。
        raise CalibrationError(f'calibrateCamera 失败: {exc}') from exc
    # RMS、焦距或主点出现 nan/inf，说明求解结果不可使用。
    if not math.isfinite(float(rms_px)) or not np.all(np.isfinite(camera_matrix)):
        # 不把坏内参写入后续在线配置。
        raise CalibrationError('calibrateCamera 返回了非有限参数')
    # K[0,0] 和 K[1,1] 分别是 fx、fy，物理上都必须为正。
    if camera_matrix[0, 0] <= 0.0 or camera_matrix[1, 1] <= 0.0:
        # 焦距非正说明标定结果明显无效。
        raise CalibrationError('calibrateCamera 返回了无效焦距')
    # 返回 K、畸变、像素 RMS 和图像尺寸，接口顺序保持不变。
    return camera_matrix, dist_coeffs, float(rms_px), image_size


def solve_charuco_poses(
    samples: list[HandEyeSample],
    camera_matrix: np.ndarray,
    dist_coeffs: np.ndarray,
) -> list[np.ndarray]:
    """为每个离线样本计算 cTt（标定板坐标系到相机坐标系）。

    函数名沿用现有接口，但 PnP 使用 ChArUco 板内 ArUco marker 的
    三维点/二维角点；图像角点已在检测阶段经过 cornerSubPix 优化。
    """
    # 每个样本最终产生一个 cTt，按 samples 原顺序保存。
    poses: list[np.ndarray] = []
    # 对每张离线图片独立执行一次 PnP。
    for sample in samples:
        # 读取板内所有已检测 marker 的二维图像角点。
        marker_image_points = sample.observation.marker_image_points
        # 读取同一批 marker 角点在标定板坐标系中的三维坐标。
        marker_object_points = sample.observation.marker_object_points_m
        # 两类点任一为空都无法建立 PnP 对应关系。
        if not marker_image_points or not marker_object_points:
            # 抛出当前样本错误，而不是让 reshape 给出难理解的异常。
            raise CalibrationError(
                f'样本 {sample.sample_id} 缺少 ChArUco 板内 ArUco marker 对应点'
            )
        # 二维点整理为连续的 N x 2 float32 数组。
        pnp_image_points = np.ascontiguousarray(
            np.asarray(marker_image_points, dtype=np.float32).reshape(-1, 2)
        )
        # 三维点整理为连续的 N x 3 float32 数组。
        pnp_object_points = np.ascontiguousarray(
            np.asarray(marker_object_points, dtype=np.float32).reshape(-1, 3)
        )
        # PnP 至少需要四组对应点，而且二维/三维数量必须相等。
        if len(pnp_image_points) != len(pnp_object_points) or len(pnp_image_points) < 4:
            # 对应点数量错误时停止当前整次标定。
            raise CalibrationError(f'样本 {sample.sample_id} 的 ArUco PnP 对应点无效')
        # ITERATIVE 最小化重投影误差；输出 rvec/tvec 的方向是 target -> camera。
        ok, rvec, tvec = cv2.solvePnP(
            # target 坐标系中的三维角点。
            pnp_object_points,
            # camera 图像中的二维像素角点。
            pnp_image_points,
            # 前一步 calibrateCamera 得到的相机内参 K。
            camera_matrix,
            # 前一步 calibrateCamera 得到的镜头畸变系数。
            dist_coeffs,
            # 使用经典迭代法优化重投影误差。
            flags=cv2.SOLVEPNP_ITERATIVE,
        )
        # ok=False 表示 OpenCV 没找到有效位姿。
        if not ok:
            # 指出失败样本和算法，方便单独检查该图像。
            raise CalibrationError(f'样本 {sample.sample_id} solvePnP ITERATIVE 失败')
        # Rodrigues 将 3x1 旋转向量转换为 3x3 旋转矩阵。
        rotation, _ = cv2.Rodrigues(rvec)
        # 将旋转和平移组成 cTt，并追加到与样本同序的列表。
        poses.append(make_transform(rotation, tvec))
    # 返回所有离线样本的 cTt，供 calibrateHandEye 使用。
    return poses


def _rotation_distance_rad(first: np.ndarray, second: np.ndarray) -> float:
    """计算两个旋转之间的 SO(3) 测地夹角，返回弧度。"""
    # first @ second.T 得到从 second 旋转到 first 的相对旋转。
    relative = first @ second.T
    # 对相对旋转 R，有 cos(theta)=(trace(R)-1)/2；clip 用于抑制浮点越界。
    cosine = float(np.clip((np.trace(relative) - 1.0) / 2.0, -1.0, 1.0))
    # acos 把余弦值恢复为 0 到 pi 范围内的旋转夹角。
    return math.acos(cosine)


def _evaluate_handeye(
    base_from_gripper: list[np.ndarray],
    camera_from_target: list[np.ndarray],
    gripper_from_camera: np.ndarray,
) -> dict[str, float]:
    """用“固定标定板在基座下应保持不动”评价手眼标定结果。

    每组都计算 bTt = bTg @ gTc @ cTt。gTc 越准确，各组 bTt 越一致，
    因此用 bTt 的平移和旋转离散程度比较 Tsai 与 Park。
    """
    # 这是离线手眼链路的核心坐标变换公式。
    # 列表中的每个元素都是同一个固定标定板在机器人基座下的估计位姿。
    base_from_target = [
        # 坐标链从 target 经 camera、gripper 最终变换到 base。
        base_gripper @ gripper_from_camera @ camera_target
        # zip 保证同一时刻的机器人姿态与相机观测配对计算。
        for base_gripper, camera_target in zip(base_from_gripper, camera_from_target)
    ]
    # 从每个 bTt 中提取最后一列 xyz，组成 N x 3 平移数组。
    translations = np.array([pose[:3, 3] for pose in base_from_target], dtype=np.float64)
    # 计算所有 bTt 平移的质心，作为固定标定板位置的平均估计。
    translation_center = translations.mean(axis=0)
    # 计算每组 xyz 到质心的三维欧氏距离均方根，单位为米。
    translation_rmse = float(
        np.sqrt(np.mean(np.sum((translations - translation_center) ** 2, axis=1)))
    )

    # 取第一组 bTt 的旋转作为旋转离散度比较基准。
    rotation_reference = base_from_target[0][:3, :3]
    # 逐组计算当前旋转与基准旋转之间的最短旋转夹角。
    rotation_errors = [
        _rotation_distance_rad(pose[:3, :3], rotation_reference)
        for pose in base_from_target
    ]
    # 对弧度误差计算 RMS，最后转换成更直观的角度值。
    rotation_rmse_deg = math.degrees(
        math.sqrt(sum(value * value for value in rotation_errors) / len(rotation_errors))
    )
    # 返回评价指标；调用方用它记录诊断信息并比较 Tsai/Park。
    return {
        # 固定标定板位置在不同样本间的平移 RMS，单位米。
        'translationRmseM': translation_rmse,
        # 固定标定板姿态在不同样本间的旋转 RMS，单位度。
        'rotationRmseDeg': float(rotation_rmse_deg),
        # 该分数只用于两种算法选优：radians(1 度)*0.0573 约等于 0.001 m。
        'selectionScore': translation_rmse + math.radians(rotation_rmse_deg) * 0.0573,
    }


def calibrate_handeye_tsai_park(
    samples: list[HandEyeSample],
    camera_from_target: list[np.ndarray],
) -> tuple[np.ndarray, str, dict[str, dict[str, Any]]]:
    """分别执行 Tsai/Park 手眼标定，选固定目标一致性更好的 gTc。

    OpenCV 输入 bTg（gripper2base）和 cTt（target2camera），输出 gTc。
    返回 ``(gTc, 选中的方法名, 两种方法的诊断指标)``。
    """
    # 少于五组姿态时，手眼方程数量和运动多样性通常不足。
    if len(samples) < 5:
        # 在进入 OpenCV 前给出明确的采样数量错误。
        raise CalibrationError('calibrateHandEye 至少需要 5 组有效姿态')
    # 把每条机器人六轴数据转换成 OpenCV 所需的 bTg。
    base_from_gripper = [robot_pose_to_transform(sample) for sample in samples]
    # 选择第一条机器人旋转作为后续相对运动的参考。
    reference_rotation = base_from_gripper[0][:3, :3]
    # 保存达到最小角度要求的单位旋转轴。
    motion_axes: list[np.ndarray] = []
    # 完整 3D 手眼标定需要不平行的旋转轴；只有绕同一根轴转会退化。
    # 从第二组开始，逐一与第一组比较旋转运动。
    for pose in base_from_gripper[1:]:
        # R_ref.T @ R_current 得到参考姿态到当前姿态的相对旋转。
        relative_rotation = reference_rotation.T @ pose[:3, :3]
        # Rodrigues 将相对旋转矩阵转换为“方向=轴、长度=角度”的旋转向量。
        rotation_vector, _ = cv2.Rodrigues(relative_rotation)
        # 旋转向量的二范数就是相对旋转角，单位弧度。
        angle = float(np.linalg.norm(rotation_vector))
        # 受现场视野限制，小于 5 度的运动不用于退化判断。
        if angle >= math.radians(5.0):
            # 除以角度得到长度为 1 的旋转轴方向。
            motion_axes.append(rotation_vector.reshape(3) / angle)
    # 至少需要两次明显旋转，才能继续判断旋转轴是否多样。
    if len(motion_axes) < 2:
        # 提示采集更多带旋转的六轴姿态。
        raise CalibrationError('calibrateHandEye 需要至少两次大于 5deg 的旋转运动')
    # 对所有单位旋转轴做奇异值分解，衡量它们覆盖了多少独立方向。
    axis_singular_values = np.linalg.svd(np.asarray(motion_axes), compute_uv=False)
    # 第二奇异值过小，说明有效旋转轴几乎只有一个方向。
    # 少于两个有效方向或第二奇异值太小，都属于近似单轴运动。
    if len(axis_singular_values) < 2 or axis_singular_values[1] < 0.1:
        # 单轴运动无法稳定恢复完整三维手眼外参。
        raise CalibrationError(
            '六轴姿态的旋转轴几乎平行，完整 3D 手眼标定退化；请增加 RX/RY 倾斜姿态'
        )
    # 从每个 bTg 中拆出 gripper2base 的 3x3 旋转矩阵。
    rotations_gripper_to_base = [pose[:3, :3] for pose in base_from_gripper]
    # 从每个 bTg 中拆出 3x1 平移列向量。
    translations_gripper_to_base = [pose[:3, 3].reshape(3, 1) for pose in base_from_gripper]
    # 从每个 cTt 中拆出 target2camera 的 3x3 旋转矩阵。
    rotations_target_to_camera = [pose[:3, :3] for pose in camera_from_target]
    # 从每个 cTt 中拆出 3x1 平移列向量。
    translations_target_to_camera = [pose[:3, 3].reshape(3, 1) for pose in camera_from_target]

    # 建立可读方法名到 OpenCV 枚举值的映射。
    methods = {
        # Tsai-Lenz 手眼标定方法。
        'Tsai': cv2.CALIB_HAND_EYE_TSAI,
        # Park-Martin 手眼标定方法。
        'Park': cv2.CALIB_HAND_EYE_PARK,
    }
    # 保存成功候选的 (选优分数, 方法名, gTc)。
    candidates: list[tuple[float, str, np.ndarray]] = []
    # 无论成功还是失败，都保存每种方法的诊断结果。
    diagnostics: dict[str, dict[str, Any]] = {}
    # Tsai 和 Park 使用完全相同的输入数据分别求解。
    for name, method in methods.items():
        # 单个方法失败时继续尝试另一个方法。
        try:
            # OpenCV 根据多组 bTg/cTt 求相机相对夹爪的固定外参。
            rotation, translation = cv2.calibrateHandEye(
                # 机器人端每组 gripper2base 旋转。
                rotations_gripper_to_base,
                # 机器人端每组 gripper2base 平移。
                translations_gripper_to_base,
                # 视觉端每组 target2camera 旋转。
                rotations_target_to_camera,
                # 视觉端每组 target2camera 平移。
                translations_target_to_camera,
                # 当前循环选择 Tsai 或 Park。
                method=method,
            )
            # OpenCV 分开返回旋转和平移，此处合成为 gTc。
            transform = make_transform(rotation, translation)
            # 即使 OpenCV 没抛异常，也必须拒绝含 nan/inf 的矩阵。
            if not np.all(np.isfinite(transform)):
                # 使用 ValueError 进入下面统一的候选失败记录。
                raise ValueError('non-finite result')
            # 用固定标定板一致性计算当前 gTc 的平移/旋转误差。
            metrics = _evaluate_handeye(base_from_gripper, camera_from_target, transform)
            # 保存成功状态以及本方法的全部质量指标。
            diagnostics[name] = {'ok': True, **metrics}
            # 加入可选候选，后面按 selectionScore 取最小值。
            candidates.append((metrics['selectionScore'], name, transform))
        # 捕获 OpenCV 求解错误和主动检测到的非有限结果。
        except (cv2.error, ValueError) as exc:
            # 某一种方法失败不会遮住另一种方法的结果。
            diagnostics[name] = {'ok': False, 'reason': str(exc)}

    # 候选列表为空，表示 Tsai 和 Park 都没有得到可用矩阵。
    if not candidates:
        # 把两种失败原因一起返回，便于分析采样数据。
        raise CalibrationError(f'calibrateHandEye Tsai/Park 均失败: {diagnostics}')
    # selectionScore 越小，固定标定板在各样本间“漂移”越少。
    # 解包最优候选；下划线接收后续不需要再使用的最小分数。
    _, selected_name, selected_transform = min(candidates, key=lambda item: item[0])
    # 返回选中的 gTc、方法名以及两种算法完整诊断。
    return selected_transform, selected_name, diagnostics


def build_pose3d_calibration(
    samples: list[HandEyeSample],
    fixed_camera_matrix: list[list[float]] | np.ndarray | None = None,
    fixed_dist_coeffs: list[float] | np.ndarray | None = None,
    fixed_image_size: list[int] | tuple[int, int] | None = None,
    fixed_calibration_rms_px: float | None = None,
    fixed_intrinsics_source: str | None = None,
) -> tuple[dict[str, Any], float]:
    """串联离线标定流程，并生成可直接保存的 pose3d 标定数据。

    流程：ChArUco calibrateCamera -> 板内 ArUco solvePnP
    -> calibrateHandEye Tsai/Park -> 保存 K、畸变和 gTc。
    """
    # 第一步：由多视角 ChArUco 角点求相机内参和畸变。
    if fixed_camera_matrix is None and fixed_dist_coeffs is None:
        camera_matrix, dist_coeffs, camera_rms_px, image_size = calibrate_camera_from_charuco(samples)
        intrinsics_source = 'charuco-calibrateCamera'
        pipeline = 'Charuco-calibrateCamera-Aruco-cornerSubPix-solvePnP-handeye'
    else:
        if fixed_camera_matrix is None or fixed_dist_coeffs is None:
            raise CalibrationError('固定内参必须同时配置 camera_matrix 和 dist_coeffs')
        camera_matrix = np.asarray(fixed_camera_matrix, dtype=np.float64)
        dist_coeffs = np.asarray(fixed_dist_coeffs, dtype=np.float64).reshape(-1)
        if camera_matrix.shape != (3, 3) or not np.all(np.isfinite(camera_matrix)):
            raise CalibrationError('固定 camera_matrix 必须是有限数值组成的 3x3 矩阵')
        if camera_matrix[0, 0] <= 0 or camera_matrix[1, 1] <= 0 or not np.isclose(camera_matrix[2, 2], 1.0):
            raise CalibrationError('固定 camera_matrix 的 fx、fy 必须大于 0，且 K[2,2] 必须为 1')
        if dist_coeffs.size < 4 or not np.all(np.isfinite(dist_coeffs)):
            raise CalibrationError('固定 dist_coeffs 至少需要 4 个有限数值')
        if fixed_image_size is None or len(fixed_image_size) != 2:
            raise CalibrationError('固定内参必须配置 image_size: [width, height]')
        image_size = (int(fixed_image_size[0]), int(fixed_image_size[1]))
        if image_size[0] <= 0 or image_size[1] <= 0:
            raise CalibrationError('固定内参 image_size 的宽和高必须大于 0')
        for sample in samples:
            meta = sample.meta or {}
            sample_size = (meta.get('image_width_px'), meta.get('image_height_px'))
            if sample_size != image_size:
                raise CalibrationError(
                    f'样本 {sample.sample_id} 图像尺寸 {sample_size} 与固定内参尺寸 {image_size} 不一致'
                )
        if fixed_calibration_rms_px is None:
            camera_rms_px = None
        else:
            camera_rms_px = float(fixed_calibration_rms_px)
            if not np.isfinite(camera_rms_px) or camera_rms_px < 0:
                raise CalibrationError('固定内参 calibration_rms_px 必须是非负有限数值')
        intrinsics_source = fixed_intrinsics_source or 'configured'
        pipeline = 'Fixed-intrinsics-Aruco-cornerSubPix-solvePnP-handeye'
    # 第二步：使用同一批图像求每一帧的 cTt。
    camera_from_target = solve_charuco_poses(samples, camera_matrix, dist_coeffs)
    # 第三步：把机器人 bTg 与视觉 cTt 配对，求相机相对末端的固定外参 gTc。
    gripper_from_camera, selected_method, diagnostics = calibrate_handeye_tsai_park(
        # 传入含六轴 bTg 数据的原始样本。
        samples,
        # 传入与样本顺序严格对应的 cTt。
        camera_from_target,
    )
    # 取中选方法的平移 RMS，作为外层接口已有的标定误差返回值。
    selected_rmse = float(diagnostics[selected_method]['translationRmseM'])
    # 组装能写入 angleCalibration.pose3d 的 JSON 兼容字典。
    payload = {
        # 标定数据结构版本，方便以后兼容升级。
        'version': 1,
        # 记录生成这份标定数据所采用的完整算法链。
        'pipeline': pipeline,
        # 标明内参来自配置还是本次 ChArUco 自动标定。
        'intrinsicsSource': intrinsics_source,
        # NumPy 相机矩阵转普通列表，确保 JSON 可以序列化。
        'cameraMatrix': camera_matrix.tolist(),
        # 畸变系数展平成一维普通列表，兼容 OpenCV 不同返回形状。
        'distCoeffs': np.asarray(dist_coeffs, dtype=np.float64).reshape(-1).tolist(),
        # 保存标定图像宽高，在线时可检查相机分辨率是否一致。
        'imageSize': [int(image_size[0]), int(image_size[1])],
        # 保存 calibrateCamera 的像素重投影 RMS。
        'cameraCalibrationRmsPx': camera_rms_px,
        # 保存在线链路最关键的 gripper_from_camera 齐次矩阵。
        'gTc': gripper_from_camera.tolist(),
        # 记录最终选中 Tsai 还是 Park。
        'handEyeMethod': selected_method,
        # 保存两种方法的成功状态和误差，便于现场追溯。
        'handEyeCandidates': diagnostics,
        # 明确记录机器人欧拉角转矩阵的约定和单位兼容规则。
        'robotEulerConvention': 'Rz*Ry*Rx; rad input',
    }
    # 返回可保存的 3D 标定数据和保持旧接口的误差数值。
    return payload, selected_rmse


def marker_object_points(marker_length_m: float) -> np.ndarray:
    """生成单个 ArUco 的四个三维角点，原点位于 marker 中心。

    角点顺序与 OpenCV ArUco 检测结果一致：左上、右上、右下、左下；
    marker 位于 z=0 平面，边长单位为米。
    """
    # 以 marker 中心为原点，所以角点坐标使用边长的一半。
    half = float(marker_length_m) / 2.0
    # 返回与 ArUco 检测角点顺序严格相同的四个三维物点。
    return np.array(
        # 左上、右上、右下、左下；全部位于 marker 自身的 z=0 平面。
        [[-half, half, 0.0], [half, half, 0.0], [half, -half, 0.0], [-half, -half, 0.0]],
        # solvePnP 使用 float32，并与图像点类型保持一致。
        dtype=np.float32,
    )


def select_pose_marker(reference: StationReference):
    """选择用于 PnP 的 marker；优先首选 ID，否则使用检测列表第一个。"""
    # 列表为空时无法构造任何二维/三维角点对应。
    if not reference.markers:
        # 使用在线检测异常，让接口返回清楚的 ArUco 错误。
        raise DetectorError('Aruco solvePnP 没有可用 marker 角点')
    # next 返回第一个符合首选 ID 的 marker，否则使用第二个参数的默认值。
    return next(
        # 按原检测顺序查找 preferred_origin_id。
        (marker for marker in reference.markers if marker.marker_id == reference.preferred_origin_id),
        # 没有匹配项时回退到第一个已检测 marker。
        reference.markers[0],
    )


def solve_aruco_pose_lm(
    reference: StationReference,
    camera_matrix: np.ndarray,
    dist_coeffs: np.ndarray,
) -> np.ndarray:
    """在线计算所选 ArUco 的 cTt。

    先用 solvePnP ITERATIVE 得到稳定初值，再用 solvePnPRefineLM
    继续最小化重投影误差。marker.corners 已由检测器做过 cornerSubPix。
    """
    # 按首选 ID 规则选出当前目标 marker。
    marker = select_pose_marker(reference)
    # 二维角点顺序必须与 marker_object_points 生成的四个三维角点严格对应。
    # 将四个亚像素角点整理成 4 x 2 float32 数组。
    image_points = np.asarray(marker.corners, dtype=np.float32).reshape(4, 2)
    # 根据实际边长生成 marker 坐标系中的四个三维角点。
    object_points = marker_object_points(reference.marker_length_m)
    # 初始 PnP 输出的是 target(marker) -> camera，即 cTt。
    ok, rvec, tvec = cv2.solvePnP(
        # marker 坐标系下的四个三维角点。
        object_points,
        # 当前图像中的四个亚像素角点。
        image_points,
        # 离线 ChArUco 标定得到的相机内参 K。
        camera_matrix,
        # 离线 ChArUco 标定得到的镜头畸变系数。
        dist_coeffs,
        # 使用 ITERATIVE 得到供 LM 优化的初始值。
        flags=cv2.SOLVEPNP_ITERATIVE,
    )
    # ok=False 表示初始 PnP 没有得到有效解。
    if not ok:
        # 报出 marker ID，便于确认是哪块码失败。
        raise DetectorError(f'Aruco marker {marker.marker_id} solvePnP ITERATIVE 失败')
    # LM 可能因输入质量或数值问题抛出 cv2.error。
    try:
        # LM 在 ITERATIVE 的 rvec/tvec 初值上继续优化，而不是重新求一个方向未知的姿态。
        rvec, tvec = cv2.solvePnPRefineLM(
            # 与初始 PnP 相同的四个三维角点。
            object_points,
            # 与初始 PnP 相同的四个二维角点。
            image_points,
            # 相机内参保持不变。
            camera_matrix,
            # 镜头畸变保持不变。
            dist_coeffs,
            # ITERATIVE 返回的旋转向量作为 LM 初值。
            rvec,
            # ITERATIVE 返回的平移向量作为 LM 初值。
            tvec,
        )
    # 只捕获 OpenCV 求解异常，其他编程错误仍会暴露。
    except cv2.error as exc:
        # 转成项目在线检测异常，同时保留 OpenCV 原因。
        raise DetectorError(f'Aruco marker {marker.marker_id} solvePnPRefineLM 失败: {exc}') from exc
    # LM 输出仍是旋转向量，需要转换成 3x3 旋转矩阵。
    rotation, _ = cv2.Rodrigues(rvec)
    # 将优化后的旋转和平移组装成 cTt。
    return make_transform(rotation, tvec)


def solve_charuco_reference_pose_lm(
    reference: StationReference,
    camera_matrix: np.ndarray,
    dist_coeffs: np.ndarray,
) -> np.ndarray:
    """使用整块 ChArUco 的已识别交点在线计算 cTt。"""
    image_points = np.asarray(
        [[item['x'], item['y']] for item in reference.charuco_corners],
        dtype=np.float32,
    ).reshape(-1, 2)
    object_points = np.asarray(
        reference.charuco_object_points_m,
        dtype=np.float32,
    )
    if object_points.ndim != 2 or object_points.shape[1] not in (2, 3):
        raise DetectorError('ChArUco reference 物点格式无效')
    if object_points.shape[1] == 2:
        object_points = np.column_stack(
            [object_points, np.zeros(len(object_points), dtype=np.float32)]
        )
    if len(image_points) < 4 or len(image_points) != len(object_points):
        raise DetectorError('ChArUco reference 至少需要 4 组一一对应的角点')
    object_points = np.ascontiguousarray(object_points, dtype=np.float32)
    image_points = np.ascontiguousarray(image_points, dtype=np.float32)

    ok, rvec, tvec = cv2.solvePnP(
        object_points,
        image_points,
        camera_matrix,
        dist_coeffs,
        flags=cv2.SOLVEPNP_ITERATIVE,
    )
    if not ok:
        raise DetectorError('ChArUco reference solvePnP ITERATIVE 失败')
    try:
        rvec, tvec = cv2.solvePnPRefineLM(
            object_points,
            image_points,
            camera_matrix,
            dist_coeffs,
            rvec,
            tvec,
        )
    except cv2.error as exc:
        raise DetectorError(f'ChArUco reference solvePnPRefineLM 失败: {exc}') from exc
    rotation, _ = cv2.Rodrigues(rvec)
    return make_transform(rotation, tvec)


def yaw_deg(transform: np.ndarray) -> float:
    """从齐次变换中提取绕 Z 轴的偏航角，返回角度值。"""
    # 统一成 float64，再截取齐次矩阵左上角的 3x3 旋转部分。
    rotation = np.asarray(transform, dtype=np.float64)[:3, :3]
    # 对 Rz*Ry*Rx 欧拉角约定，yaw = atan2(R[1,0], R[0,0])。
    # atan2 返回弧度，degrees 将其转成补偿接口使用的角度。
    return math.degrees(math.atan2(rotation[1, 0], rotation[0, 0]))
