"""
使用 D:\\code\\AGV\\pkg3_260522\\examples\\拍照位姿 下的图片
对 PlanarHandEyeCalibrator 手眼标定代码进行端到端验证。

数据来源：
  - t_pose_eye_hand_request.json 中的 imagePointList
  - 20260626 文件夹中的 8 张图片 (1.6 / 1.8 / 2.0 / 2.2 / 2.5 / 2.8 / 3.0 / 3.14)
  - 2026.626_test 文件夹中的 5 张图片 (626test* rz/x/y 变化样本)

脚本会：
  1. 解析 JSON 请求
  2. 自动定位每张图片的真实路径（在 20260626 或 2026.626_test 中查找）
  3. 调用 CharucoBoardDetector 检测每张图
  4. 调用 PlanarHandEyeCalibrator.solve 解算 2D 仿射矩阵和角度标定
  5. 输出每张图的检测结果、整体 RMSE、角度标定结果、单点回算误差
  6. 保存可视化图片到 data/verify_handeye_20260626
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np

import logging

from agv_vision.config.settings import AppSettings
from agv_vision.core.image_io import read_image
from agv_vision.core.models import CharucoObservation, HandEyeSample
from agv_vision.utils.logging_utils import setup_logging
from agv_vision.vision.charuco_detector import CharucoBoardDetector
from agv_vision.vision.handeye_calibrator import PlanarHandEyeCalibrator


ROOT = Path(__file__).resolve().parent
EXAMPLE_DIR = ROOT / 'examples' / '拍照位姿'
REQUEST_JSON = EXAMPLE_DIR / 't_pose_eye_hand_request.json'
CANDIDATE_DIRS = [
    EXAMPLE_DIR / '20260626',
    EXAMPLE_DIR / '2026.626_test',
]
OUT_DIR = ROOT / 'data' / 'verify_handeye_20260626'
OUT_DIR.mkdir(parents=True, exist_ok=True)


def locate_image(image_path: str) -> Path | None:
    """先按 JSON 原路径找，找不到就在候选目录里按文件名搜。"""
    p = Path(image_path)
    if p.exists():
        return p
    name = p.name
    for d in CANDIDATE_DIRS:
        candidate = d / name
        if candidate.exists():
            return candidate
    return None


def main() -> int:
    with open(REQUEST_JSON, 'r', encoding='utf-8') as f:
        request = json.load(f)

    settings = AppSettings.from_yaml(ROOT / 'agv_vision' / 'config' / 'settings.yaml')
    logger = setup_logging(str(ROOT / 'logs'))
    logger = logging.getLogger('verify_handeye')
    detector = CharucoBoardDetector(settings.handeye_charuco)
    calibrator = PlanarHandEyeCalibrator()

    image_point_list = request['imagePointList']
    print(f'共 {len(image_point_list)} 组样本')
    print('=' * 92)

    samples: list[HandEyeSample] = []
    rows: list[dict] = []
    skipped: list[dict] = []

    for idx, item in enumerate(image_point_list, start=1):
        sample_id = str(item.get('sampleId') or f'p{idx:02d}')
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
        vis_path = OUT_DIR / f'{sample_id}_{located.stem}.jpg'
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

    print('\n单样本回算误差 (用仿射矩阵把图像中心点映射到机器人坐标，再与真实 robot_x/y 比较):')
    print(f"{'id':<5}{'pred_x':>10}{'pred_y':>10}{'real_x':>10}{'real_y':>10}{'err_m':>9}")
    print('-' * 54)
    for s, r in zip(samples, rows):
        pred_x, pred_y = PlanarHandEyeCalibrator.transform_point(s.observation.board_center_px, M)
        err = float(np.hypot(pred_x - s.robot_x_m, pred_y - s.robot_y_m))
        print(f"{s.sample_id:<5}{pred_x:>10.2f}{pred_y:>10.2f}"
              f"{s.robot_x_m:>10.2f}{s.robot_y_m:>10.2f}{err:>9.3f}")

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

    # 验证角度模型：把每个样本的 vision_angle 带入拟合公式，对比 robot_rz
    if ac is not None:
        print('\n角度模型回算:')
        print(f"{'id':<5}{'vision':>9}{'real_rz':>10}{'pred_rz':>10}{'resid':>9}")
        print('-' * 43)
        for s, r in zip(samples, rows):
            if s.meta.get('rz') is None:
                continue
            vision_angle = float(s.observation.board_angle_deg)
            pred_rz = ac['direction'] * vision_angle + ac['offsetDeg']
            pred_rz = PlanarHandEyeCalibrator.normalize_angle_deg(pred_rz)
            resid = PlanarHandEyeCalibrator.normalize_angle_deg(pred_rz - float(s.meta['rz']))
            print(f"{s.sample_id:<5}{vision_angle:>9.2f}{float(s.meta['rz']):>10.2f}"
                  f"{pred_rz:>10.2f}{resid:>9.3f}")

    # 保存结果 json
    from agv_vision.core.models import dataclass_to_dict
    out_payload = {
        'request': request,
        'samples': rows,
        'skipped': skipped,
        'result': dataclass_to_dict(result),
    }
    out_json = OUT_DIR / 'handeye_result.json'
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(out_payload, f, ensure_ascii=False, indent=2)
    print(f'\n结果已保存: {out_json}')
    print(f'可视化图片目录: {OUT_DIR}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
