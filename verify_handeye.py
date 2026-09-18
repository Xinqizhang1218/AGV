"""
通用手眼标定端到端验证脚本。

用法:
    python verify_handeye.py <request.json> [output_subdir]
    python verify_handeye.py                                # 默认跑 20260626 那组

脚本流程：
  1. 解析 t_pose_eye_hand_request.json 风格的请求（sn / timestamp / imagePointList）
  2. 自动定位每张图片（按 JSON 原路径，找不到则在常用目录按文件名搜索）
  3. 调用 CharucoBoardDetector 检测每张图
  4. 调用 PlanarHandEyeCalibrator.solve 解算 2D 仿射 + 角度标定
  5. 输出每张图检测、整体 RMSE、单点回算误差、角度模型回算
  6. 保存可视化图片与 handeye_result.json 到 data/<output_subdir>
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import cv2
import numpy as np

from agv_vision.config.settings import AppSettings
from agv_vision.core.image_io import read_image
from agv_vision.core.models import HandEyeSample, dataclass_to_dict
from agv_vision.utils.logging_utils import setup_logging
from agv_vision.vision.charuco_detector import CharucoBoardDetector
from agv_vision.vision.handeye_calibrator import PlanarHandEyeCalibrator


ROOT = Path(__file__).resolve().parent
EXAMPLE_DIR = ROOT / 'examples'
POSE_DIR = EXAMPLE_DIR / '拍照位姿'
DEFAULT_REQUEST = POSE_DIR / 't_pose_eye_hand_request.json'

# 找不到图片时按文件名在这些目录里搜
CANDIDATE_DIRS = [
    POSE_DIR / '20260626',
    POSE_DIR / '2026.626_test',
    EXAMPLE_DIR / 'offline_images' / 'handeye_batch',
    EXAMPLE_DIR / 'offline_images' / 'handeye11',
    EXAMPLE_DIR / 'offline_images' / 'handeye',
]


def locate_image(image_path: str) -> Path | None:
    p = Path(image_path)
    if p.exists():
        return p
    name = p.name
    for d in CANDIDATE_DIRS:
        candidate = d / name
        if candidate.exists():
            return candidate
    return None


def run(request_json: Path, out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(request_json, 'r', encoding='utf-8') as f:
        request = json.load(f)

    settings = AppSettings.from_yaml(ROOT / 'agv_vision' / 'config' / 'settings.yaml')
    setup_logging(str(ROOT / 'logs'))
    detector = CharucoBoardDetector(settings.handeye_charuco)
    calibrator = PlanarHandEyeCalibrator()

    image_point_list = request['imagePointList']
    print(f'请求: {request_json}')
    print(f'共 {len(image_point_list)} 组样本')
    print('=' * 92)

    samples: list[HandEyeSample] = []
    rows: list[dict] = []
    skipped: list[dict] = []

    for idx, item in enumerate(image_point_list, start=1):
        sample_id = str(item.get('sampleId') or item.get('sample_id') or f'p{idx:02d}')
        image_path = item.get('imagePath') or item.get('image_path')
        located = locate_image(image_path)
        if located is None:
            skipped.append({'sample_id': sample_id, 'image_path': image_path, 'reason': '图片未找到'})
            print(f'[{sample_id}] 跳过：图片未找到 {image_path}')
            continue

        image = read_image(located)
        if image is None:
            skipped.append({'sample_id': sample_id, 'image_path': str(located), 'reason': '图片读取失败'})
            continue

        try:
            obs = detector.detect(image)
        except Exception as exc:
            skipped.append({'sample_id': sample_id, 'image_path': str(located), 'reason': f'检测失败: {exc}'})
            print(f'[{sample_id}] 检测失败: {exc}  ({located.name})')
            continue

        vis = detector.draw(image, obs)
        vis_path = out_dir / f'{sample_id}_{located.stem}.jpg'
        cv2.imwrite(str(vis_path), vis)

        meta = {
            'z': float(item.get('z', 0.0)),
            'rx': float(item.get('rx', 0.0)),
            'ry': float(item.get('ry', 0.0)),
            'rz': float(item.get('rz', 0.0)),
            'raw_image_path': str(located),
        }
        sample = HandEyeSample(
            sample_id=sample_id,
            robot_x_m=float(item['x']),
            robot_y_m=float(item['y']),
            observation=obs,
            image_path=str(vis_path),
            meta=meta,
        )
        samples.append(sample)
        rows.append({
            'sample_id': sample_id,
            'image': located.name,
            'robot_x': float(item['x']),
            'robot_y': float(item['y']),
            'robot_rz': meta['rz'],
            'cx_px': obs.board_center_px[0],
            'cy_px': obs.board_center_px[1],
            'angle_deg': obs.board_angle_deg,
            'corners': obs.corner_count,
            'px_per_m': obs.pixel_scale_px_per_m,
        })

    print('=' * 92)
    print(f'成功检测 {len(samples)} / {len(image_point_list)} 组，跳过 {len(skipped)} 组')
    print('=' * 92)
    header = f"{'id':<5}{'image':<22}{'robot_x':>9}{'robot_y':>9}{'rz':>9}{'cx_px':>9}{'cy_px':>9}{'angle':>8}{'corners':>8}{'px/m':>8}"
    print(header)
    print('-' * len(header))
    for r in rows:
        print(f"{r['sample_id']:<5}{r['image']:<22}"
              f"{r['robot_x']:>9.2f}{r['robot_y']:>9.2f}{r['robot_rz']:>9.2f}"
              f"{r['cx_px']:>9.2f}{r['cy_px']:>9.2f}{r['angle_deg']:>8.2f}"
              f"{r['corners']:>8}{(r['px_per_m'] or 0):>8.3f}")

    if len(samples) < 3:
        print('有效样本不足 3 个，无法做二维仿射标定。')
        return 1

    print('=' * 92)
    print('调用 PlanarHandEyeCalibrator.solve ...')
    result = calibrator.solve(samples)
    M = np.array(result.matrix_2x3, dtype=np.float64)

    print(f'\n2x3 仿射矩阵 (image_px -> robot_m):')
    print(f'  [[{M[0,0]:>12.6f}, {M[0,1]:>12.6f}, {M[0,2]:>12.6f}],')
    print(f'   [{M[1,0]:>12.6f}, {M[1,1]:>12.6f}, {M[1,2]:>12.6f}]]')
    print(f'\nRMSE = {result.rmse_m:.4f} m   样本数 = {result.sample_count}')

    # 额外统计：X、Y 分量各自的 RMSE
    pred = PlanarHandEyeCalibrator.transform_points(
        np.array([s.observation.board_center_px for s in samples], dtype=np.float64), M
    )
    real = np.array([[s.robot_x_m, s.robot_y_m] for s in samples], dtype=np.float64)
    rmse_x = float(np.sqrt(np.mean((pred[:, 0] - real[:, 0]) ** 2)))
    rmse_y = float(np.sqrt(np.mean((pred[:, 1] - real[:, 1]) ** 2)))
    max_err = float(np.max(np.hypot(pred[:, 0] - real[:, 0], pred[:, 1] - real[:, 1])))
    print(f'RMSE_x = {rmse_x:.4f} m   RMSE_y = {rmse_y:.4f} m   max_err = {max_err:.4f} m')

    # 像素/米比例（从仿射矩阵列向量长度也可估算）
    scale_from_M = float(np.hypot(M[0, 0], M[1, 0]))  # x 列对应的 m/px 量级
    print(f'矩阵列向量模: |col0|={scale_from_M:.6f} m/px  |col1|={float(np.hypot(M[0,1], M[1,1])):.6f} m/px')

    print('\n单样本回算误差:')
    print(f"{'id':<5}{'pred_x':>10}{'pred_y':>10}{'real_x':>10}{'real_y':>10}{'err_m':>9}")
    print('-' * 54)
    for s in samples:
        px, py = PlanarHandEyeCalibrator.transform_point(s.observation.board_center_px, M)
        err = float(np.hypot(px - s.robot_x_m, py - s.robot_y_m))
        print(f"{s.sample_id:<5}{px:>10.2f}{py:>10.2f}"
              f"{s.robot_x_m:>10.2f}{s.robot_y_m:>10.2f}{err:>9.3f}")

    # 留一交叉验证（LOOCV）：每组样本轮流留出，用剩下的拟合，再预测留出的那个
    print('\n留一交叉验证 (LOOCV):')
    print(f"{'id':<5}{'pred_x':>10}{'pred_y':>10}{'real_x':>10}{'real_y':>10}{'err_m':>9}")
    print('-' * 54)
    loo_errors = []
    for i in range(len(samples)):
        train = [s for j, s in enumerate(samples) if j != i]
        res_loo = calibrator.solve(train)
        M_loo = np.array(res_loo.matrix_2x3, dtype=np.float64)
        s = samples[i]
        px, py = PlanarHandEyeCalibrator.transform_point(s.observation.board_center_px, M_loo)
        err = float(np.hypot(px - s.robot_x_m, py - s.robot_y_m))
        loo_errors.append(err)
        print(f"{s.sample_id:<5}{px:>10.2f}{py:>10.2f}"
              f"{s.robot_x_m:>10.2f}{s.robot_y_m:>10.2f}{err:>9.3f}")
    print(f'LOOCV 平均误差 = {float(np.mean(loo_errors)):.4f} m   '
          f'最大 = {float(np.max(loo_errors)):.4f} m')

    ac = result.angle_calibration
    if ac is None:
        print('\n角度标定: 样本 meta 中 rz 信息不足，未做角度标定')
    else:
        print('\n角度标定结果:')
        print(f"  model        : {ac['model']}")
        print(f"  direction    : {ac['direction']}")
        print(f"  offsetDeg    : {ac['offsetDeg']:.4f}")
        print(f"  rmseDeg      : {ac['rmseDeg']:.4f}")
        print(f"  sampleCount  : {ac['sampleCount']}")
        print(f"  reliable     : {ac['reliable']}  ({ac['reason']})")
        print(f"  visionAngles : {[round(v, 2) for v in ac['visionAnglesDeg']]}")
        print(f"  robotRz      : {[round(v, 2) for v in ac['robotRzDeg']]}")
        print(f"  residuals    : {[round(v, 3) for v in ac['residualsDeg']]}")

        print('\n角度模型回算:')
        print(f"{'id':<5}{'vision':>9}{'real_rz':>10}{'pred_rz':>10}{'resid':>9}")
        print('-' * 43)
        for s in samples:
            if s.meta.get('rz') is None:
                continue
            vision_angle = float(s.observation.board_angle_deg)
            pred_rz = ac['direction'] * vision_angle + ac['offsetDeg']
            pred_rz = PlanarHandEyeCalibrator.normalize_angle_deg(pred_rz)
            resid = PlanarHandEyeCalibrator.normalize_angle_deg(pred_rz - float(s.meta['rz']))
            print(f"{s.sample_id:<5}{vision_angle:>9.2f}{float(s.meta['rz']):>10.2f}"
                  f"{pred_rz:>10.2f}{resid:>9.3f}")

    out_payload = {
        'request_file': str(request_json),
        'request': request,
        'samples': rows,
        'skipped': skipped,
        'result': dataclass_to_dict(result),
        'loo_errors_m': loo_errors,
    }
    out_json = out_dir / 'handeye_result.json'
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(out_payload, f, ensure_ascii=False, indent=2)
    print(f'\n结果已保存: {out_json}')
    print(f'可视化图片目录: {out_dir}')
    return 0


def main(argv: list[str]) -> int:
    request_json = Path(argv[1]) if len(argv) > 1 else DEFAULT_REQUEST
    if not request_json.is_absolute():
        request_json = ROOT / request_json
    out_name = argv[2] if len(argv) > 2 else request_json.stem
    out_dir = ROOT / 'data' / out_name
    return run(request_json, out_dir)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
