from __future__ import annotations  # 启用未来版本类型注解语法，支持 dict | None 等写法

from dataclasses import asdict  # 导入 dataclass 转字典工具，用于对象序列化
from pathlib import Path  # 导入 Path，用于路径拼接和文件管理
import json  # 导入 json，用于保存结果文件
import cv2  # 导入 OpenCV，用于图片保存和可视化处理

from agv_vision.config.settings import AppSettings  # 导入应用配置类
from agv_vision.core.models import (  # 导入数据模型
    HandEyeSample,  # 手眼标定样本
    HandEyeCalibrationResult,  # 手眼标定结果
    StationReference,  # 工位参考点对象
    dataclass_to_dict  # dataclass 转 dict 工具函数
)

from agv_vision.core.offline_source import OfflineImageSource  # 导入离线图片源
from agv_vision.core.orbbec_source import OrbbecColorSource  # 导入奥比中光在线相机源
from agv_vision.core.daheng_source import DahengColorSource
from agv_vision.core.hikvision_source import HikvisionColorSource
from agv_vision.vision.charuco_detector import CharucoBoardDetector  # Charuco 检测器
from agv_vision.vision.aruco_detector import ArucoReferenceDetector  # Aruco 检测器
from agv_vision.vision.handeye_calibrator import PlanarHandEyeCalibrator  # 手眼标定器
from agv_vision.vision.compensator import CompensationCalculator  # 偏移补偿器
from agv_vision.utils.time_utils import now_str, today_str  # 时间字符串生成工具，用于文件名

class AGVVisionService:  # 定义 AGV 视觉服务类
    def __init__(self, settings: AppSettings, logger):  # 初始化函数
        self.settings = settings  # 保存应用配置对象
        self.logger = logger  # 保存日志对象
        self.source = self._build_source()  # 根据模式构建图像源（在线或离线）
        self.handeye_charuco_detector = CharucoBoardDetector(settings.handeye_charuco)
        self.station_charuco_detector = CharucoBoardDetector(settings.station_charuco)  # 初始化 Charuco 检测器
        self.aruco_detector = ArucoReferenceDetector(settings.aruco)  # 初始化 Aruco 检测器
        intrinsics = settings.camera.intrinsics
        if intrinsics.enabled:
            self.handeye_calibrator = PlanarHandEyeCalibrator(
                camera_matrix=intrinsics.camera_matrix,
                dist_coeffs=intrinsics.dist_coeffs,
                image_size=intrinsics.image_size,
                calibration_rms_px=intrinsics.calibration_rms_px,
                intrinsics_source=intrinsics.source,
            )
            self.logger.info(
                '手眼标定使用固定相机内参 image_size=%s source=%s',
                intrinsics.image_size,
                intrinsics.source or 'configured',
            )
        else:
            self.handeye_calibrator = PlanarHandEyeCalibrator()
            self.logger.info('手眼标定未启用固定内参，将由本次 ChArUco 样本自动标定内参')
        self.compensator = CompensationCalculator(settings.aruco.pixels_per_m_fallback)  # 初始化补偿计算器
        self.debug_root_dir = Path(settings.debug.debug_dir)  # 调试输出根目录
        self.debug_dir = self._daily_debug_dir()  # 调试输出目录

    def _build_source(self):  # 根据模式创建图像源
        if self.settings.mode.lower() == 'online':  # 在线模式
            vendor = self.settings.camera.vendor.lower()
            profile = getattr(self.settings.camera, vendor)
            source_width = profile.width if profile.width is not None else self.settings.camera.width
            source_height = profile.height if profile.height is not None else self.settings.camera.height
            source_fps = profile.fps if profile.fps is not None else self.settings.camera.fps
            common = {
                "width": source_width,
                "height": source_height,
                "fps": source_fps,
                "timeout_ms": self.settings.camera.timeout_ms,
                "auto_exposure": self.settings.camera.auto_exposure,
                "exposure": self.settings.camera.exposure,
                "gain": self.settings.camera.gain,
                "auto_white_balance": self.settings.camera.auto_white_balance,
                "white_balance": self.settings.camera.white_balance,
            }
            if vendor == "daheng":
                return DahengColorSource(
                    **common,
                    serial_number=self.settings.camera.daheng.serial_number,
                    ip_address=self.settings.camera.daheng.ip_address,
                    sdk_installer=self.settings.camera.daheng.installer_path,
                    sdk_python_path=self.settings.camera.daheng.python_path,
                )
            if vendor == "hikvision":
                return HikvisionColorSource(
                    **common,
                    serial_number=self.settings.camera.hikvision.serial_number,
                    ip_address=self.settings.camera.hikvision.ip_address,
                    sdk_installer=self.settings.camera.hikvision.installer_path,
                    sdk_python_path=self.settings.camera.hikvision.python_path,
                )
            return OrbbecColorSource(  # 返回奥比中光相机源
                width=source_width,  # 使用 Orbbec 独立分辨率
                height=source_height,
                fps=source_fps,
                timeout_ms=self.settings.camera.timeout_ms,  # 设置超时
                enable_depth=self.settings.camera.enable_depth,  # 是否启用深度
                prefer_format=self.settings.camera.prefer_format,  # 图像格式
                ip_address=self.settings.camera.ip_address,  # 网络相机 IP
                control_port=self.settings.camera.control_port,  # 网络相机控制端口
                serial_number=self.settings.camera.serial_number,  # 指定序列号
            )
        return OfflineImageSource(  # 离线模式，返回图片源
            image_dir=self.settings.offline.image_dir,  # 图片目录
            loop=self.settings.offline.loop,  # 是否循环读取
            supported_suffixes=self.settings.offline.supported_suffixes,  # 支持的后缀
        )
    
    def batch_capture_handeye_samples(self, image_dir: str, poses_payload: list[dict], output_json: str) -> dict:
        """
        批量离线采集手眼样本。
        poses_payload 格式示例：
        [
          {"sample_id": "p01", "image_name": "handeye_01.png", "robot_x_m": 0.180, "robot_y_m": 0.250},
          ...
        ]
        """
        image_dir_path = Path(image_dir)
        if not image_dir_path.exists():
            raise FileNotFoundError(f'手眼图片目录不存在: {image_dir_path}')

        samples: list[dict] = []
        success_items: list[dict] = []
        failed_items: list[dict] = []

        for idx, item in enumerate(poses_payload):
            sample_id = item['sample_id']
            image_name = item['image_name']
            robot_x_m = float(item['robot_x_m'])
            robot_y_m = float(item['robot_y_m'])

            image_path = image_dir_path / image_name
            if not image_path.exists():
                failed_items.append({
                    'sample_id': sample_id,
                    'image_name': image_name,
                    'reason': f'图片不存在: {image_path}',
                })
                continue

            from agv_vision.core.image_io import read_image
            image = read_image(image_path)
            if image is None:
                failed_items.append({
                    'sample_id': sample_id,
                    'image_name': image_name,
                    'reason': f'图片读取失败: {image_path}',
                })
                continue

            try:
                obs = self.handeye_charuco_detector.detect(image)
                vis = self.handeye_charuco_detector.draw(image, obs)
                debug_image_path = self._save_image(f'handeye_{sample_id}', vis)

                sample = HandEyeSample(
                    sample_id=sample_id,
                    robot_x_m=robot_x_m,
                    robot_y_m=robot_y_m,
                    observation=obs,
                    image_path=debug_image_path,
                    meta={
                        'source': 'offline_batch',
                        'image_path': str(image_path),
                        'index': idx,
                    },
                )
                payload = dataclass_to_dict(sample)
                samples.append(payload)

                success_items.append({
                    'sample_id': sample_id,
                    'image_name': image_name,
                    'corner_count': obs.corner_count,
                })

                self.logger.info(
                    '批量采集手眼样本成功 sample_id=%s image=%s robot=(%.3f, %.3f) corners=%s',
                    sample_id, image_name, robot_x_m, robot_y_m, obs.corner_count
                )

            except Exception as e:
                failed_items.append({
                    'sample_id': sample_id,
                    'image_name': image_name,
                    'reason': str(e),
                })
                self.logger.exception('批量采集手眼样本失败 sample_id=%s image=%s', sample_id, image_name)

        output_path = Path(output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(samples, f, ensure_ascii=False, indent=2)

        return {
            'ok': len(failed_items) == 0,
            'sample_count': len(samples),
            'failed_count': len(failed_items),
            'output_json': str(output_path),
            'success_items': success_items,
            'failed_items': failed_items,
        }

    def set_offline_scenario(self, scenario: str) -> None:  # 切换离线场景
        if self.settings.mode.lower() != 'offline':  # 如果不是离线模式
            return  # 直接返回
        self.settings.offline.scenario = scenario  # 修改当前场景名称
        try:
            self.source.close()  # 尝试关闭当前图像源
        except Exception:
            pass  # 关闭失败忽略
        self.source = self._build_source()  # 重新构建图像源
        self.source.open()  # 打开新图像源
        self.logger.info('切换离线场景 scenario=%s image_dir=%s', scenario, self.settings.offline.image_dir)  # 打日志

    def open(self) -> None:  # 打开服务
        self.logger.info('打开图像源 mode=%s', self.settings.mode)  # 日志记录模式
        self.source.open()  # 打开图像源

    def close(self) -> None:  # 关闭服务
        self.logger.info('关闭图像源')  # 日志记录
        self.source.close()  # 关闭图像源

    def _daily_debug_dir(self) -> Path:
        path = self.debug_root_dir / today_str()
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _save_image(self, prefix: str, image) -> str:  # 保存图片
        self.debug_dir = self._daily_debug_dir()
        path = self.debug_dir / f'{prefix}_{now_str()}.jpg'  # 拼接文件名
        from agv_vision.core.image_io import write_image
        write_image(path, image)  # 写入图片
        return str(path)  # 返回路径

    def _resolve_output_path(self, image_path: str) -> Path:
        path = Path(image_path)
        if not path.is_absolute():
            path = Path.cwd() / path
        return path

    def _save_image_to_path(self, image_path: str, image) -> str:
        path = self._resolve_output_path(image_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        from agv_vision.core.image_io import write_image
        ok = write_image(path, image)
        if not ok:
            raise RuntimeError(f'图片保存失败: {path}')
        return str(path)

    def _save_json(self, prefix: str, payload: dict) -> str:  # 保存 JSON
        self.debug_dir = self._daily_debug_dir()
        path = self.debug_dir / f'{prefix}_{now_str()}.json'  # 拼接文件名
        with open(path, 'w', encoding='utf-8') as f:  # 打开文件
            json.dump(payload, f, ensure_ascii=False, indent=2)  # 写入 JSON
        return str(path)  # 返回路径

    def _safe_name(self, value: str) -> str:
        return ''.join(ch if ch.isalnum() or ch in ('-', '_') else '_' for ch in value)

    def _debug_case_dir(self, label: str) -> Path:
        self.debug_dir = self._daily_debug_dir()
        path = self.debug_dir / f'{now_str()}_{self._safe_name(label)}'
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _save_debug_case(self, label: str, raw_image, detected_image, center_payload: dict) -> dict:
        if not self.settings.debug.save_debug_images and not self.settings.debug.save_result_json:
            return {}

        case_dir = self._debug_case_dir(label)
        result = {'debug_dir': str(case_dir)}

        if self.settings.debug.save_debug_images:
            raw_path = case_dir / 'raw.jpg'
            detected_path = case_dir / 'detected.jpg'
            from agv_vision.core.image_io import write_image
            write_image(raw_path, raw_image)
            write_image(detected_path, detected_image)
            result['debug_raw_image_path'] = str(raw_path)
            result['debug_detected_image_path'] = str(detected_path)

        if self.settings.debug.save_result_json:
            json_path = case_dir / 'center.json'
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(center_payload, f, ensure_ascii=False, indent=2)
            result['debug_center_json_path'] = str(json_path)

        self.logger.info(
            '调试文件已保存 label=%s debug_dir=%s center=%s',
            label,
            result.get('debug_dir'),
            center_payload,
        )
        return result

    def capture_once(self) -> dict:  # 单次拍照
        frame = self.source.grab()  # 抓取一帧
        image_path = self._save_image('capture', frame.color)  # 保存彩色图像
        return {'ok': True, 'image_path': image_path, 'meta': frame.meta, 'shape': list(frame.color.shape)}  # 返回信息


    def capture_to_path(self, image_path: str) -> dict:
        """
        在线/离线抓取一帧，并保存到后端指定的 imagePath。
        后端接口 /api/v1/agv/photo 会调用这个方法。
        """
        frame = self.source.grab()
        saved_path = self._save_image_to_path(image_path, frame.color)
        self.logger.info('拍照完成 image_path=%s', saved_path)
        return {
            'ok': True,
            'image_path': saved_path,
            'meta': frame.meta,
            'shape': list(frame.color.shape),
        }

    def build_handeye_sample_from_image(
        self,
        sample_id: str,
        image_path: str,
        robot_x_m: float,
        robot_y_m: float,
        meta: dict | None = None,
    ) -> dict:
        """
        从后端传入的图片路径中读取图片，识别 ChArUco，并构造成手眼标定样本。
        对应接口文档里的 imagePointList.imagePath + x/y。
        """
        path = Path(image_path)
        if not path.is_absolute():
            path = Path.cwd() / path
        if not path.exists():
            raise FileNotFoundError(f'手眼标定图片不存在: {path}')

        from agv_vision.core.image_io import read_image
        image = read_image(path)
        if image is None:
            raise RuntimeError(f'图片读取失败: {path}')

        obs = self.handeye_charuco_detector.detect(image)
        vis = self.handeye_charuco_detector.draw(image, obs)
        debug_image_path = self._save_image(f'handeye_{sample_id}', vis)
        debug_case = self._save_debug_case(
            f'handeye_{sample_id}',
            image,
            vis,
            {
                'type': 'handeye_charuco',
                'sample_id': sample_id,
                'raw_image_path': str(path),
                'robot_x_m': robot_x_m,
                'robot_y_m': robot_y_m,
                'corner_count': obs.corner_count,
            },
        )
        sample = HandEyeSample(
            sample_id=sample_id,
            robot_x_m=robot_x_m,
            robot_y_m=robot_y_m,
            observation=obs,
            image_path=debug_image_path,
            meta={
                'source': 'http_eye_hand',
                'raw_image_path': str(path),
                'image_width_px': int(image.shape[1]),
                'image_height_px': int(image.shape[0]),
                **debug_case,
                **(meta or {}),
            },
        )
        payload = dataclass_to_dict(sample)
        self.logger.info(
            '从图片构造 3D 手眼样本 sample_id=%s image=%s robot=(%.3f, %.3f) corners=%s',
            sample_id, path, robot_x_m, robot_y_m, obs.corner_count
        )
        return payload

    def solve_handeye_from_image_pose_list(self, image_point_list: list[dict]) -> dict:
        """
        根据接口文档 imagePointList 一次性完成：读取图片 -> 识别 ChArUco -> 解算手眼矩阵。
        使用完整 3D 链；x/y/z 单位为米，rx/ry/rz 单位为弧度。
        """
        translations: list[float] = []
        for idx, item in enumerate(image_point_list, start=1):
            for field in ('x', 'y', 'z'):
                value = item.get(field)
                if value is None:
                    continue
                try:
                    translations.append(float(value))
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f'imagePointList[{idx}].{field} 必须是数值，单位为米'
                    ) from exc
        if translations and max(abs(value) for value in translations) > 10.0:
            raise ValueError(
                'imagePointList 的 x/y/z 必须使用米(m)；检测到绝对值大于 10 的坐标，'
                '疑似传入了毫米(mm)，请在 Java 侧除以 1000 后重试'
            )

        samples_payload: list[dict] = []
        for idx, item in enumerate(image_point_list, start=1):
            image_path = item.get('imagePath') or item.get('image_path')
            if not image_path:
                raise ValueError(f'imagePointList[{idx}] 缺少 imagePath')
            sample_id = str(item.get('sampleId') or item.get('sample_id') or f'p{idx:02d}')
            missing_pose_fields = [
                field for field in ('x', 'y', 'z', 'rx', 'ry', 'rz')
                if item.get(field) is None
            ]
            if missing_pose_fields:
                raise ValueError(
                    f'imagePointList[{idx}] 缺少姿态字段: {missing_pose_fields}'
                )
            sample_payload = self.build_handeye_sample_from_image(
                sample_id=sample_id,
                image_path=str(image_path),
                robot_x_m=float(item['x']),
                robot_y_m=float(item['y']),
                meta={
                    'z': float(item['z']),
                    'rx': float(item['rx']),
                    'ry': float(item['ry']),
                    'rz': float(item['rz']),
                },
            )
            samples_payload.append(sample_payload)
        return self.solve_handeye(samples_payload)

    def capture_handeye_sample(self, sample_id: str, robot_x_m: float, robot_y_m: float) -> dict:  # 采集手眼样本
        frame = self.source.grab()  # 获取一帧
        obs = self.handeye_charuco_detector.detect(frame.color)  # 检测 Charuco
        vis = self.handeye_charuco_detector.draw(frame.color, obs)  # 绘制可视化
        image_path = self._save_image(f'handeye_{sample_id}', vis)  # 保存可视化图片
        debug_case = self._save_debug_case(
            f'handeye_{sample_id}',
            frame.color,
            vis,
            {
                'type': 'handeye_charuco_live',
                'sample_id': sample_id,
                'robot_x_m': robot_x_m,
                'robot_y_m': robot_y_m,
                'corner_count': obs.corner_count,
            },
        )
        sample = HandEyeSample(  # 构建 HandEyeSample 对象
            sample_id=sample_id,
            robot_x_m=robot_x_m,
            robot_y_m=robot_y_m,
            observation=obs,
            image_path=image_path,
            meta={**frame.meta, **debug_case},
        )
        payload = dataclass_to_dict(sample)  # 转成 dict
        self.logger.info('采集手眼样本 sample_id=%s robot=(%.3f, %.3f)', sample_id, robot_x_m, robot_y_m)  # 日志
        return payload  # 返回字典

    def solve_handeye(self, samples_payload: list[dict]) -> dict:  # 求解手眼标定
        from agv_vision.core.models import CharucoObservation  # 导入 CharucoObservation
        samples: list[HandEyeSample] = []  # 初始化样本列表
        for item in samples_payload:  # 遍历传入 payload
            obs_data = item['observation']  # 取 observation
            obs = CharucoObservation(**obs_data)  # 转成对象
            samples.append(HandEyeSample(  # 构建 HandEyeSample
                sample_id=item['sample_id'],
                robot_x_m=float(item['robot_x_m']),
                robot_y_m=float(item['robot_y_m']),
                observation=obs,
                image_path=item.get('image_path'),
                meta=item.get('meta', {}),
            ))
        result = self.handeye_calibrator.solve(samples)  # 调用标定器求解
        if result.rmse_m > self.handeye_calibrator.RMSE_WARNING_M:
            self.logger.warning(
                '手眼标定 RMSE 偏大: %.3f mm，建议重新采集',
                result.rmse_m * 1000,
            )
        payload = dataclass_to_dict(result)  # 转 dict
        self.logger.info(
            '3D 手眼标定完成 sample_count=%s rmse_m=%.4f method=%s',
            result.sample_count,
            result.rmse_m,
            (result.angle_calibration or {}).get('pose3d', {}).get('handEyeMethod'),
        )  # 日志
        if self.settings.debug.save_result_json:  # 如果保存 json
            payload['local_json'] = self._save_json('handeye_result', payload)  # 保存
        return payload  # 返回结果

    def _detect_station_reference(self, image, station_id: str, reference_type: str):
        if reference_type == 'charuco':
            observation = self.station_charuco_detector.detect(image)
            corner_ids = observation.corner_ids or []
            corners = [
                {'id': int(corner_id), 'x': float(point[0]), 'y': float(point[1])}
                for corner_id, point in zip(corner_ids, observation.image_points)
            ]
            center_x = sum(float(item['x']) for item in corners) / len(corners)
            center_y = sum(float(item['y']) for item in corners) / len(corners)
            reference = StationReference(
                station_id=station_id,
                board_center_x=center_x,
                board_center_y=center_y,
                board_angle_deg=0.0,
                marker_count=len(observation.marker_ids or []),
                markers=[],
                marker_length_m=float(self.settings.station_charuco.marker_length_m),
                preferred_origin_id=int(self.settings.cross_calibration.charuco_marker_id),
                reference_type='charuco',
                charuco_corners=corners,
                charuco_object_points_m=observation.board_points_m,
            )
            return reference, self.station_charuco_detector.draw(image, observation)

        reference = self.aruco_detector.detect(image, station_id=station_id)
        return reference, self.aruco_detector.draw(image, reference)

    # def collect_station_reference(self, station_id: str) -> dict:  # 采集工位参考点
    def collect_station_reference(self, station_id: str, image_path: str | None = None) -> dict:
        frame = self.source.grab()  # 抓取一帧
        saved_image_path = self._save_image_to_path(image_path, frame.color) if image_path else None
        reference_type = self.settings.cross_calibration.target_type
        ref, vis = self._detect_station_reference(frame.color, station_id, reference_type)
        debug_case = self._save_debug_case(
            f'station_ref_{station_id}',
            frame.color,
            vis,
            {
                'type': f'station_reference_{reference_type}',
                'station_id': station_id,
                'image_path': saved_image_path,
                'board_center_x': ref.board_center_x,
                'board_center_y': ref.board_center_y,
                'board_angle_deg': ref.board_angle_deg,
                'marker_count': ref.marker_count,
                'marker_length_m': ref.marker_length_m,
                'marker_pixel_length_px': ref.marker_pixel_length_px,
                'pixels_per_m': ref.pixels_per_m,
                'preferred_origin_id': ref.preferred_origin_id,
            },
        )
        if image_path:
            debug_image_path = self._save_image(f'station_ref_{station_id}', vis)
        else:
            saved_image_path = self._save_image(f'station_ref_{station_id}', vis)  # 保存图片
            debug_image_path = saved_image_path
        payload = dataclass_to_dict(ref)  # 转 dict
        payload['image_path'] = saved_image_path  # 添加图片路径
        payload['debug_image_path'] = debug_image_path  # 添加可视化调试图路径
        payload.update(debug_case)
        payload['meta'] = {**frame.meta, **debug_case}  # 添加元信息
        self.logger.info(
            '机台参考采集完成 station_id=%s marker_count=%s image_path=%s marker_pixel_length_px=%s pixels_per_m=%s',
            station_id, ref.marker_count, saved_image_path, ref.marker_pixel_length_px, ref.pixels_per_m
        )  # 日志
        return payload  # 返回 payload

    # def compensate(self, reference_payload: dict, handeye_payload: dict | None = None) -> dict:  # 偏移补偿
    def compensate(self, reference_payload: dict, handeye_payload: dict | None = None, image_path: str | None = None) -> dict:
        frame = self.source.grab()  # 获取当前帧
        raw_debug_image_path = self._save_image('compensation_current_raw', frame.color)
        self.logger.info('二次补偿当前原始帧已保存 image_path=%s', raw_debug_image_path)
        saved_image_path = self._save_image_to_path(image_path, frame.color) if image_path else None
        reference_type = str(reference_payload.get('reference_type', 'aruco')).lower()
        current_ref, vis = self._detect_station_reference(
            frame.color,
            reference_payload.get('station_id', 'unknown'),
            reference_type,
        )
        current_center_payload = {
            'type': f'secondary_compensation_current_{reference_type}',
            'station_id': reference_payload.get('station_id', 'unknown'),
            'image_path': saved_image_path,
            'board_center_x': current_ref.board_center_x,
            'board_center_y': current_ref.board_center_y,
            'board_angle_deg': current_ref.board_angle_deg,
            'marker_count': current_ref.marker_count,
            'marker_length_m': current_ref.marker_length_m,
            'marker_pixel_length_px': current_ref.marker_pixel_length_px,
            'pixels_per_m': current_ref.pixels_per_m,
            'reference_board_center_x': reference_payload.get('board_center_x'),
            'reference_board_center_y': reference_payload.get('board_center_y'),
            'reference_board_angle_deg': reference_payload.get('board_angle_deg'),
            'reference_pixels_per_m': reference_payload.get('pixels_per_m'),
        }
        debug_case = self._save_debug_case(
            'compensation_current',
            frame.color,
            vis,
            current_center_payload,
        )
        if image_path:
            debug_image_path = self._save_image('compensation_current', vis)
        else:
            saved_image_path = self._save_image('compensation_current', vis)  # 保存可视化图片
            debug_image_path = saved_image_path
        from agv_vision.core.models import StationReference, ArucoMarkerPose2D  # 导入模型
        markers = [ArucoMarkerPose2D(**m) for m in reference_payload.get('markers', [])]
        charuco_corners = reference_payload.get('charuco_corners') or []
        charuco_object_points_m = (
            self.station_charuco_detector.board_points_for_corner_ids(
                [int(item['id']) for item in charuco_corners]
            )
            if reference_type == 'charuco'
            else []
        )
        reference = StationReference(  # 恢复 StationReference 对象
            station_id=reference_payload['station_id'],
            board_center_x=float(reference_payload['board_center_x']),
            board_center_y=float(reference_payload['board_center_y']),
            board_angle_deg=float(reference_payload['board_angle_deg']),
            marker_count=int(reference_payload['marker_count']),
            markers=markers,
            marker_length_m=float(reference_payload['marker_length_m']),
            preferred_origin_id=int(reference_payload['preferred_origin_id']),
            marker_pixel_length_px=(
                float(reference_payload['marker_pixel_length_px'])
                if reference_payload.get('marker_pixel_length_px') is not None
                else None
            ),
            pixels_per_m=(
                float(reference_payload['pixels_per_m'])
                if reference_payload.get('pixels_per_m') is not None
                else None
            ),
            reference_type=reference_type,
            charuco_corners=charuco_corners,
            charuco_object_points_m=charuco_object_points_m,
        )
        angle_calibration = (handeye_payload or {}).get('angle_calibration')
        current_center_payload['angle_calibration'] = angle_calibration
        result = self.compensator.compute(
            reference,
            current_ref,
            angle_calibration=angle_calibration,
        )
        current_center_payload['compensation'] = dataclass_to_dict(result)
        if debug_case.get('debug_center_json_path'):
            Path(debug_case['debug_center_json_path']).write_text(
                json.dumps(current_center_payload, ensure_ascii=False, indent=2),
                encoding='utf-8',
            )
        payload = {  # 构建返回 payload
            'reference': reference_payload,
            'current': dataclass_to_dict(current_ref),
            'compensation': dataclass_to_dict(result),
            'image_path': saved_image_path,
            'debug_image_path': debug_image_path,
            **debug_case,
            'meta': {**frame.meta, **debug_case},
        }
        self.logger.info(
            '3D 补偿完成 dx=%.6fm dy=%.6fm dtheta=%.3fdeg',
            result.dx_m_robot,
            result.dy_m_robot,
            result.dtheta_robot_deg,
        )  # 日志
        if self.settings.debug.save_result_json:  # 如果保存 json
            payload['local_json'] = self._save_json('compensation', payload)  # 保存
        return payload  # 返回 payload
