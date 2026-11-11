from __future__ import annotations

from dataclasses import replace

import numpy as np

from agv_vision.core.models import CompensationResult, StationReference
from agv_vision.vision.pose3d import (
    euler_xyz_to_rotation,
    make_transform,
    solve_aruco_pose_lm,
    solve_charuco_reference_pose_lm,
)


def normalize_angle_deg(angle: float) -> float:
    while angle > 180:
        angle -= 360
    while angle <= -180:
        angle += 360
    return float(angle)


def rotation_to_rpy_rad(rotation: np.ndarray) -> list[float]:
    """把 Rz*Ry*Rx 旋转矩阵转换为 [rx, ry, rz] 弧度。"""
    sy = float(-rotation[2, 0])
    ry = float(np.arcsin(np.clip(sy, -1.0, 1.0)))
    cy = float(np.cos(ry))
    if abs(cy) > 1e-9:
        rx = float(np.arctan2(rotation[2, 1], rotation[2, 2]))
        rz = float(np.arctan2(rotation[1, 0], rotation[0, 0]))
    else:
        rx = 0.0
        rz = float(np.arctan2(-rotation[0, 1], rotation[1, 1]))
    return [rx, ry, rz]

def compose_target_flange_pose(
    current_pose_m_rad: list[float],
    flange_delta: list[list[float]] | np.ndarray,
) -> dict:
    """
    计算：
        目标末端矩阵 = 当前末端矩阵 × robotCommand.deltaTransform

    current_pose_m_rad:
        [x_m, y_m, z_m, rx_rad, ry_rad, rz_rad]
    """
    pose = np.asarray(current_pose_m_rad, dtype=np.float64).reshape(-1)

    if pose.size != 6 or not np.all(np.isfinite(pose)):
        raise ValueError(
            "data.currentFlangePose 必须包含6个有限数值，"
            "XYZ单位m，RX/RY/RZ单位rad"
        )

    delta_matrix = np.asarray(flange_delta, dtype=np.float64)

    if delta_matrix.shape != (4, 4):
        raise ValueError("robotCommand.deltaTransform 必须是4x4矩阵")

    if not np.all(np.isfinite(delta_matrix)):
        raise ValueError("robotCommand.deltaTransform 包含非有限数值")

    current_rotation = euler_xyz_to_rotation(
        float(pose[3]),
        float(pose[4]),
        float(pose[5]),
    )

    current_matrix = make_transform(
        current_rotation,
        pose[:3],
    )

    # 关键计算
    target_matrix = current_matrix @ delta_matrix

    target_rpy_rad = rotation_to_rpy_rad(target_matrix[:3, :3])

    target_pose = {
        "x": float(target_matrix[0, 3]),
        "y": float(target_matrix[1, 3]),
        "z": float(target_matrix[2, 3]),
        "rx": float(target_rpy_rad[0]),
        "ry": float(target_rpy_rad[1]),
        "rz": float(target_rpy_rad[2]),
        "translationUnit": "m",
        "rotationUnit": "rad",
    }

    # 这是基坐标系下的XYZ变化量，可以加到示教器当前XYZ上
    base_translation_delta = (
        target_matrix[:3, 3] - current_matrix[:3, 3]
    )

    return {
        "currentFlangeMatrix": current_matrix.tolist(),
        "targetFlangeMatrix": target_matrix.tolist(),
        "targetFlangePose": target_pose,
        "baseTranslationDeltaM": [
            float(base_translation_delta[0]),
            float(base_translation_delta[1]),
            float(base_translation_delta[2]),
        ],
    }


class CompensationCalculator:
    """保留原 compute 接口，内部只执行在线 3D 位姿补偿。"""

    def __init__(self, pixels_per_m_fallback: float):
        del pixels_per_m_fallback

    def compute(
        self,
        reference: StationReference,
        current: StationReference,
        handeye_matrix_2x3: list[list[float]] | None = None,
        calibration_pixels_per_m: float | None = None,
        angle_calibration: dict | None = None,
    ) -> CompensationResult:
        # matrix2x3 和 calibrationPixelsPerM 只为保持现有 HTTP/服务接口形状。
        # 真正计算只使用随 angleCalibration 回传的完整 pose3d 数据。
        del handeye_matrix_2x3, calibration_pixels_per_m

        pose3d = (angle_calibration or {}).get('pose3d')
        if not isinstance(pose3d, dict):
            raise ValueError(
                'handeye.angleCalibration.pose3d 缺失；请先用完整 3D 流程重新标定'
            )
        try:
            camera_matrix = np.asarray(
                pose3d['cameraMatrix'], dtype=np.float64
            ).reshape(3, 3)
            dist_coeffs = np.asarray(
                pose3d['distCoeffs'], dtype=np.float64
            ).reshape(-1, 1)
            gripper_from_camera = np.asarray(
                pose3d['gTc'], dtype=np.float64
            ).reshape(4, 4)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                'pose3d 中 cameraMatrix/distCoeffs/gTc 格式无效'
            ) from exc
        if not (
            np.all(np.isfinite(camera_matrix))
            and np.all(np.isfinite(dist_coeffs))
            and np.all(np.isfinite(gripper_from_camera))
        ):
            raise ValueError('pose3d 相机参数或 gTc 包含非有限数值')

        if reference.reference_type != current.reference_type:
            raise ValueError('参考图与当前图的跨机台目标类型不一致')

        if reference.reference_type == 'charuco':
            if not reference.charuco_corners or not current.charuco_corners:
                raise ValueError('ChArUco reference 缺少 charucoCorners')
            selected_marker_id = reference.preferred_origin_id
            camera_from_reference_target = solve_charuco_reference_pose_lm(
                reference,
                camera_matrix,
                dist_coeffs,
            )
            camera_from_current_target = solve_charuco_reference_pose_lm(
                current,
                camera_matrix,
                dist_coeffs,
            )
        else:
            if not reference.markers:
                raise ValueError(
                    'reference.markers 缺失；请重新调用跨机台标定并让 Java 原样保存 markers'
                )

            # 参考图和当前图必须使用同一个 marker 坐标系，否则两个 cTt 不能相减。
            reference_ids = {marker.marker_id for marker in reference.markers}
            current_ids = {marker.marker_id for marker in current.markers}
            common_ids = reference_ids & current_ids
            if not common_ids:
                raise ValueError('参考图与当前图没有共同的 ArUco marker ID')
            selected_marker_id = (
                reference.preferred_origin_id
                if reference.preferred_origin_id in common_ids
                else min(common_ids)
            )
            reference_for_pose = replace(
                reference,
                preferred_origin_id=selected_marker_id,
            )
            current_for_pose = replace(
                current,
                preferred_origin_id=selected_marker_id,
            )
            camera_from_reference_target = solve_aruco_pose_lm(
                reference_for_pose,
                camera_matrix,
                dist_coeffs,
            )
            camera_from_current_target = solve_aruco_pose_lm(
                current_for_pose,
                camera_matrix,
                dist_coeffs,
            )
        gripper_from_reference_target = gripper_from_camera @ camera_from_reference_target
        gripper_from_current_target = gripper_from_camera @ camera_from_current_target

        # 目标末端位姿满足：
        # bTg_target = bTg_current @ gCurrentTtarget @ inv(gReferenceTtarget)
        # 机械臂端必须右乘此 4x4 变换，不能逐项累加欧拉角。
        flange_delta = (
            gripper_from_current_target
            @ np.linalg.inv(gripper_from_reference_target)
        )
        if not np.all(np.isfinite(flange_delta)):
            raise ValueError('计算得到的六自由度补偿矩阵包含非有限数值')
        delta_rpy_rad = rotation_to_rpy_rad(flange_delta[:3, :3])
        dx_robot = float(flange_delta[0, 3])
        dy_robot = float(flange_delta[1, 3])
        dz_robot = float(flange_delta[2, 3])
        dtheta_robot = normalize_angle_deg(np.degrees(delta_rpy_rad[2]))

        robot_command = {
            'schemaVersion': 1,
            'operation': 'right_multiply_current_flange_pose',
            'sourceFrame': 'flange_current',
            'targetFrame': 'flange_target',
            'translationUnit': 'm',
            'rotationUnit': 'rad',
            'deltaTransform': flange_delta.tolist(),
            'deltaTranslationM': [dx_robot, dy_robot, dz_robot],
            'deltaRpyRad': delta_rpy_rad,
            'selectedMarkerId': selected_marker_id,
        }

        return CompensationResult(
            dtheta_deg=dtheta_robot,
            dx_m_camera=float(
                camera_from_current_target[0, 3]
                - camera_from_reference_target[0, 3]
            ),
            dy_m_camera=float(
                camera_from_current_target[1, 3]
                - camera_from_reference_target[1, 3]
            ),
            dtheta_robot_deg=dtheta_robot,
            dx_m_robot=dx_robot,
            dy_m_robot=dy_robot,
            robot_command=robot_command,
        )
