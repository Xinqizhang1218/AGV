from __future__ import annotations

import json
import math
import os
import time
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, HTTPException, Request, Response

from agv_vision.api.schemas import (
    ReferenceRequest,
    HandEyeSampleCaptureRequest,
    HandEyeSolveRequest,
    CompensateRequest,
    ScenarioRequest,
)
from agv_vision.backends.client import BackendClient
from agv_vision.backends.mock_backend import MockBackend
from agv_vision.config.settings import AppSettings
from agv_vision.core.service import AGVVisionService
from agv_vision.utils.logging_utils import setup_logging
from agv_vision.vision.compensator import compose_target_flange_pose


# =====================================================
# 配置加载
# =====================================================
# 注意：原代码写死读取 agv_vision/config/settings.yaml。
# 这样即使命令行传 --config settings_online.yaml，HTTP 服务仍可能没切到 online。
# 这里改成优先读取环境变量 AGV_VISION_CONFIG；main.py 启动 serve 时会自动写入该变量。
DEFAULT_SETTINGS_PATH = Path(__file__).resolve().parents[1] / 'config' / 'settings.yaml'
_settings_env = os.environ.get('AGV_VISION_CONFIG')
if _settings_env:
    SETTINGS_PATH = Path(_settings_env)
    if not SETTINGS_PATH.is_absolute():
        SETTINGS_PATH = Path.cwd() / SETTINGS_PATH
else:
    SETTINGS_PATH = DEFAULT_SETTINGS_PATH

settings = AppSettings.from_yaml(SETTINGS_PATH)
logger = setup_logging(settings.debug.log_dir)
service = AGVVisionService(settings, logger)
backend = BackendClient(settings.backend.base_url, settings.backend.timeout_sec) if settings.backend.enabled else MockBackend()

app = FastAPI(title='AGV Vision Service', version='0.3.0')


def _format_for_log(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, indent=2, default=str)
    except Exception:
        return repr(value)


def _decode_body_for_log(body: bytes) -> Any:
    if not body:
        return {}
    text = body.decode('utf-8', errors='replace')
    try:
        return json.loads(text)
    except Exception:
        return text


def _api_name(path: str) -> str:
    names = {
        '/api/v1/health': '健康检查',
        '/api/v1/agv/photo': '拍照保存',
        '/api/v1/agv/handeye_observation': '手眼标定单图检查',
        '/api/v1/agv/eye_hand': '手眼标定',
        '/api/v1/avg/eye_hand': '手眼标定(兼容 avg 拼写)',
        '/api/v1/agv/cross_calibration': '跨机台基准采集',
        '/api/v1/agv/secondary_compensation': '二次补偿',
        '/health': '本地健康检查',
        '/offline/scenario': '切换离线场景',
        '/capture': '本地单次拍照',
        '/calibration/handeye/sample': '本地采集手眼样本',
        '/calibration/handeye/solve': '本地求解手眼标定',
        '/reference/collect': '本地采集机台参考',
        '/compensate': '本地补偿',
    }
    return names.get(path, '未知接口')


def _nested_get(data: Any, *names: str) -> Any:
    if not isinstance(data, dict):
        return None
    for name in names:
        if name in data and data[name] not in (None, ''):
            return data[name]
    return None


def _request_summary(path: str, payload: Any) -> list[str]:
    data = payload.get('data') if isinstance(payload, dict) and isinstance(payload.get('data'), dict) else payload
    if not isinstance(data, dict):
        return ['请求体不是 JSON 对象，已按原始文本记录']

    lines: list[str] = []
    station_id = _nested_get(data, 'stationId', 'station_id') or _nested_get(payload, 'stationId', 'station_id', 'sn')
    camera_id = _nested_get(data, 'cameraId', 'camera_id') or _nested_get(payload, 'cameraId', 'camera_id')
    task_id = _nested_get(data, 'taskId', 'task_id')
    image_path = _nested_get(data, 'imagePath', 'image_path')

    if station_id is not None:
        lines.append(f'工位/机台 stationId={station_id}')
    if camera_id is not None:
        lines.append(f'相机 cameraId={camera_id}')
    if task_id is not None:
        lines.append(f'任务 taskId={task_id}')
    if image_path is not None:
        lines.append(f'后端指定图片保存路径 imagePath={image_path}')

    image_point_list = (
        _nested_get(payload, 'imagePointList', 'image_point_list')
        or _nested_get(data, 'imagePointList', 'image_point_list')
    )
    if isinstance(image_point_list, list):
        lines.append(f'手眼标定图片点位数量 imagePointList={len(image_point_list)} 组')
        first = image_point_list[0] if image_point_list else {}
        if isinstance(first, dict):
            lines.append(
                '第一组点位: '
                f'imagePath={first.get("imagePath") or first.get("image_path")}, '
                f'x={first.get("x")}m, y={first.get("y")}m, '
                f'z={first.get("z")}m, rx={first.get("rx")}rad, '
                f'ry={first.get("ry")}rad, rz={first.get("rz")}rad'
            )

    reference = _nested_get(data, 'reference', 'referencePayload', 'reference_payload')
    if isinstance(reference, dict):
        lines.append(
            '后端传回的跨机台基准: '
            f'center=({reference.get("board_center_x") or reference.get("boardCenterX")}, '
            f'{reference.get("board_center_y") or reference.get("boardCenterY")})px, '
            f'angle={reference.get("board_angle_deg") or reference.get("boardAngleDeg")}deg'
        )

    handeye = _nested_get(data, 'handeye', 'handEye', 'handeyePayload', 'handeye_payload')
    if isinstance(handeye, dict):
        pose3d = handeye.get('pose3d')
        if isinstance(pose3d, dict):
            lines.append(
                '后端传入精简3D手眼标定: '
                f'rmseM={handeye.get("rmseM")}, '
                f'sampleCount={handeye.get("sampleCount")}, '
                f'pose3d字段={list(pose3d.keys())}'
            )

    if not lines:
        lines.append('没有识别到业务关键字段，请看下方完整请求体')
    return lines


def _response_summary(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ['返回体不是 JSON 对象，已按原始文本记录']

    code = payload.get('code')
    msg = payload.get('msg')
    data = payload.get('data') if isinstance(payload.get('data'), dict) else {}
    ok_text = '成功' if code in (0, '0', None) else '失败'
    lines = [f'业务结果={ok_text}, code={code}, msg={msg}']

    for key in ('imagePath', 'stationId', 'cameraId', 'taskId', 'unit'):
        if key in data:
            lines.append(f'{key}={data.get(key)}')

    if 'boardCenterX' in data or 'boardCenterY' in data:
        lines.append(
            f'识别基准中心=({data.get("boardCenterX")}, {data.get("boardCenterY")})px, '
            f'角度={data.get("boardAngleDeg")}deg, 码数量={data.get("markerCount")}'
        )
    if 'pixelsPerM' in data or 'markerPixelLengthPx' in data:
        lines.append(
            f'动态比例 pixelsPerM={data.get("pixelsPerM")}px/m, '
            f'markerPixelLengthPx={data.get("markerPixelLengthPx")}px'
        )

    if 'pose3d' in data:
        lines.append(
            f'3D手眼标定 rmseM={data.get("rmseM")}, '
            f'sampleCount={data.get("sampleCount")}, '
            f'pose3d字段={list(data.get("pose3d", {}).keys())}'
        )

    if 'dx' in data or 'dy' in data or 'dtheta' in data:
        lines.append(
            f'补偿结果 dx={data.get("dx")}m, dy={data.get("dy")}m, '
            f'dtheta={data.get("dtheta")}deg, unit={data.get("unit")}'
        )
        lines.append(
            f'比例修正: raw=({data.get("dxRaw")}, {data.get("dyRaw")})m, '
            f'refScale={data.get("referencePixelsPerM")}, curScale={data.get("currentPixelsPerM")}, '
            f'dynamicScale={data.get("dynamicPixelsPerM")}, calScale={data.get("calibrationPixelsPerM")}, '
            f'correction={data.get("handeyeScaleCorrection")}'
        )

    return lines


def _troubleshooting_hint(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ''
    code = payload.get('code')
    msg = str(payload.get('msg') or '')
    if code in (0, '0', None):
        return ''
    if 'ArUco' in msg or '标记' in msg or '码' in msg:
        return '排查建议：确认 ArUco 字典是否匹配；检查反光/模糊/过曝；确认码完整入镜；确认 min_markers 配置没有高于实际识别数量。'
    if 'imagePath' in msg or '图片' in msg or '路径' in msg:
        return '排查建议：确认后端传了 data.imagePath；路径所在目录有写入权限；如果是相对路径，当前会按服务启动目录解析。'
    if 'handeye' in msg or 'pose3d' in msg or 'cameraMatrix' in msg or 'gTc' in msg:
        return '排查建议：二次补偿必须原样回传 eye_hand 响应 data，且包含 pose3d.cameraMatrix/distCoeffs/gTc。'
    if 'reference' in msg or 'markerId' in msg or 'corners' in msg:
        return '排查建议：二次补偿必须原样回传 cross_calibration 响应 data；ArUco corners 是四个二维点，ChArUco corners 是带 id/x/y 的角点对象。'
    return '排查建议：先看本条日志的完整请求体和完整返回体，确认字段名、层级 data、单位是否和 README 一致。'


def _join_log_lines(lines: list[str]) -> str:
    return '\n'.join(f'  - {line}' for line in lines)


@app.middleware('http')
async def log_http_request_response(request: Request, call_next):
    started = time.time()
    request_body = await request.body()

    async def receive():
        return {'type': 'http.request', 'body': request_body, 'more_body': False}

    request._receive = receive
    request_payload = _decode_body_for_log(request_body)
    query_params = dict(request.query_params)
    client = request.client.host if request.client else 'unknown'
    api_name = _api_name(request.url.path)

    logger.info(
        '\n========== 收到HTTP请求 ==========\n'
        '接口说明: %s\n'
        '请求方法: %s\n'
        '请求路径: %s\n'
        '客户端IP: %s\n'
        '查询参数: %s\n'
        '关键参数摘要:\n%s\n'
        '完整请求体:\n%s\n'
        '================================',
        api_name,
        request.method,
        request.url.path,
        client,
        _format_for_log(query_params),
        _join_log_lines(_request_summary(request.url.path, request_payload)),
        _format_for_log(request_payload),
    )

    try:
        response = await call_next(request)
    except Exception:
        elapsed_ms = (time.time() - started) * 1000
        logger.exception(
            '\n========== HTTP接口异常 ==========\n'
            '接口说明: %s\n'
            '请求方法: %s\n'
            '请求路径: %s\n'
            '耗时: %.2f ms\n'
            '说明: 接口代码抛出未捕获异常，详情见异常堆栈\n'
            '================================',
            api_name,
            request.method,
            request.url.path,
            elapsed_ms,
        )
        raise

    response_body = b''
    async for chunk in response.body_iterator:
        response_body += chunk

    response_payload = _decode_body_for_log(response_body)
    elapsed_ms = (time.time() - started) * 1000

    logger.info(
        '\n========== 返回HTTP响应 ==========\n'
        '接口说明: %s\n'
        '请求方法: %s\n'
        '请求路径: %s\n'
        'HTTP状态码: %s\n'
        '耗时: %.2f ms\n'
        '返回摘要:\n%s\n'
        '%s'
        '完整返回体:\n%s\n'
        '================================',
        api_name,
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
        _join_log_lines(_response_summary(response_payload)),
        (f'排查提示: {_troubleshooting_hint(response_payload)}\n' if _troubleshooting_hint(response_payload) else ''),
        _format_for_log(response_payload),
    )

    return Response(
        content=response_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
        background=response.background,
    )


def _now_ms() -> int:
    return int(time.time() * 1000)


def _resp_ok(data: dict | None = None, msg: str = 'success', timestamp: int | None = None) -> dict:
    return {
        'code': 0,
        'msg': msg,
        'data': data or {},
        'timestamp': timestamp or _now_ms(),
    }


def _resp_fail(msg: str, data: dict | None = None, timestamp: int | None = None) -> dict:
    # 按接口文档使用 JSON 内部 code=400；HTTP 状态仍返回 200，方便 Java 统一解析。
    return {
        'code': 400,
        'msg': msg,
        'data': data or {},
        'timestamp': timestamp or _now_ms(),
    }


def _get_timestamp(body: dict) -> int:
    try:
        return int(body.get('timestamp') or _now_ms())
    except Exception:
        return _now_ms()


def _get_data(body: dict) -> dict:
    data = body.get('data')
    if isinstance(data, dict):
        return data
    return body


def _get_sn(body: dict) -> str:
    data = _get_data(body)
    return str(body.get('sn') or data.get('sn') or 'default_station')


def _get_float(data: dict, name: str, default: float = 0.0) -> float:
    value = data.get(name, default)
    if value is None or value == '':
        return default
    return float(value)


def _get_nested(data: dict, *names: str) -> Any:
    """
    从 data 中按多个可能字段名取值。
    例如 handeye / handEye / handeyePayload 都兼容。
    """
    for name in names:
        if name in data and data[name] is not None:
            return data[name]
    return None


def _validate_numeric_matrix(value: Any, rows: int, cols: int, field_name: str) -> None:
    if not isinstance(value, list) or len(value) != rows:
        raise ValueError(
            f'data.handeye.pose3d.{field_name} 必须是 {rows}x{cols} 数组'
        )
    if any(not isinstance(row, list) or len(row) != cols for row in value):
        raise ValueError(
            f'data.handeye.pose3d.{field_name} 必须是 {rows}x{cols} 数组'
        )
    try:
        numbers = [float(item) for row in value for item in row]
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f'data.handeye.pose3d.{field_name} 格式无效'
        ) from exc
    if not all(math.isfinite(number) for number in numbers):
        raise ValueError(
            f'data.handeye.pose3d.{field_name} 包含非有限数值'
        )


def _normalize_handeye_payload(data: dict) -> dict:
    """提取 Java 原样回传的完整 3D 手眼标定结果。"""
    handeye = _get_nested(
        data,
        'handeye',
        'handEye',
        'handeyePayload',
        'handeye_payload',
        'handEyePayload',
    )

    if handeye is None:
        handeye = {}

    if not isinstance(handeye, dict):
        raise ValueError('data.handeye 必须是对象')

    pose3d = handeye.get('pose3d')
    if not isinstance(pose3d, dict):
        raise ValueError(
            '缺少 data.handeye.pose3d，请重新执行手眼标定'
        )

    _validate_numeric_matrix(pose3d.get('cameraMatrix'), 3, 3, 'cameraMatrix')
    _validate_numeric_matrix(pose3d.get('gTc'), 4, 4, 'gTc')
    dist_coeffs = pose3d.get('distCoeffs')
    if not isinstance(dist_coeffs, list) or len(dist_coeffs) < 4:
        raise ValueError('data.handeye.pose3d.distCoeffs 格式无效')
    try:
        dist_values = [float(value) for value in dist_coeffs]
    except (TypeError, ValueError) as exc:
        raise ValueError(
            'data.handeye.pose3d.distCoeffs 格式无效'
        ) from exc
    if not all(math.isfinite(value) for value in dist_values):
        raise ValueError(
            'data.handeye.pose3d.distCoeffs 包含非有限数值'
        )

    return {
        'calibration_type': 'charuco_calibrateCamera_pnp_handeye_tsai_park_3d',
        'rmse_m': handeye.get('rmseM'),
        'sample_count': handeye.get('sampleCount'),
        'angle_calibration': {'pose3d': pose3d},
    }


def _normalize_reference_marker(marker: Any) -> dict:
    path = 'data.reference'
    if not isinstance(marker, dict):
        raise ValueError(f'{path} 必须是对象')

    marker_id_value = marker.get('markerId')
    if marker_id_value is None:
        marker_id_value = marker.get('marker_id')
    if marker_id_value is None:
        raise ValueError(f'{path}.markerId 缺失')
    try:
        marker_id = int(marker_id_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'{path}.markerId 必须是整数') from exc

    corners_value = marker.get('corners')
    if not isinstance(corners_value, list) or len(corners_value) != 4:
        raise ValueError(f'{path}.corners 必须包含 4 个二维点')
    corners: list[list[float]] = []
    try:
        for corner in corners_value:
            if not isinstance(corner, list) or len(corner) != 2:
                raise ValueError
            point = [float(corner[0]), float(corner[1])]
            if not all(math.isfinite(value) for value in point):
                raise ValueError
            corners.append(point)
    except (TypeError, ValueError, IndexError) as exc:
        raise ValueError(f'{path}.corners 必须包含 4 个有限二维点') from exc

    center_x = sum(point[0] for point in corners) / 4.0
    center_y = sum(point[1] for point in corners) / 4.0
    angle_deg = math.degrees(
        math.atan2(
            corners[1][1] - corners[0][1],
            corners[1][0] - corners[0][0],
        )
    )
    edge_lengths = [
        math.hypot(
            corners[(edge + 1) % 4][0] - corners[edge][0],
            corners[(edge + 1) % 4][1] - corners[edge][1],
        )
        for edge in range(4)
    ]
    marker_pixel_length_px = sum(edge_lengths) / 4.0
    if marker_pixel_length_px <= 0:
        raise ValueError(f'{path}.corners 不能构成有效 ArUco 四边形')

    marker_length_m = float(settings.aruco.marker_length_m)
    if not math.isfinite(marker_length_m) or marker_length_m <= 0:
        raise ValueError('视觉配置 aruco.marker_length_m 必须大于 0')

    return {
        'marker_id': marker_id,
        'center_x': center_x,
        'center_y': center_y,
        'angle_deg': angle_deg,
        'corners': corners,
        'marker_pixel_length_px': marker_pixel_length_px,
        'pixels_per_m': marker_pixel_length_px / marker_length_m,
    }


def _normalize_charuco_corners(reference: dict) -> list[dict[str, float | int]] | None:
    field_name = 'charucoCorners'
    raw_corners = reference.get('charucoCorners')
    if raw_corners is None:
        raw_corners = reference.get('Corners')
        field_name = 'Corners'
    if raw_corners is None:
        compatible_corners = reference.get('corners')
        if (
            isinstance(compatible_corners, list)
            and compatible_corners
            and isinstance(compatible_corners[0], dict)
        ):
            raw_corners = compatible_corners
            field_name = 'corners'
    if raw_corners is None:
        return None
    if not isinstance(raw_corners, list) or len(raw_corners) < settings.station_charuco.min_corners:
        raise ValueError(
            f'data.reference.{field_name} 至少需要 {settings.station_charuco.min_corners} 个角点'
        )

    corners: list[dict[str, float | int]] = []
    ids: set[int] = set()
    for index, item in enumerate(raw_corners):
        if not isinstance(item, dict):
            raise ValueError(f'data.reference.{field_name}[{index}] 必须是对象')
        try:
            corner_id = int(item['id'])
            x = float(item['x'])
            y = float(item['y'])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f'data.reference.{field_name}[{index}] 必须包含有效的 id/x/y'
            ) from exc
        if corner_id < 0 or not math.isfinite(x) or not math.isfinite(y):
            raise ValueError(f'data.reference.{field_name}[{index}] 包含无效数值')
        if corner_id in ids:
            raise ValueError(f'data.reference.{field_name} 包含重复 id={corner_id}')
        ids.add(corner_id)
        corners.append({'id': corner_id, 'x': x, 'y': y})
    return corners


def _normalize_reference_payload(data: dict) -> dict:
    """把 Java 精简 reference 转为视觉内部 StationReference 形状。"""
    reference = _get_nested(
        data,
        'reference',
        'referencePayload',
        'reference_payload',
        'stationReference',
        'station_reference',
    )

    if reference is None:
        reference = {}

    if not isinstance(reference, dict):
        raise ValueError('data.reference 必须是对象')

    charuco_corners = _normalize_charuco_corners(reference)
    if charuco_corners is not None:
        try:
            marker_id = int(reference.get('markerId', settings.cross_calibration.charuco_marker_id))
        except (TypeError, ValueError) as exc:
            raise ValueError('data.reference.markerId 必须是整数') from exc
        center_x = sum(float(item['x']) for item in charuco_corners) / len(charuco_corners)
        center_y = sum(float(item['y']) for item in charuco_corners) / len(charuco_corners)
        return {
            'station_id': str(
                reference.get('stationId')
                or data.get('stationId')
                or _get_sn(data)
            ),
            'board_center_x': center_x,
            'board_center_y': center_y,
            'board_angle_deg': 0.0,
            'marker_count': 0,
            'marker_length_m': float(settings.station_charuco.marker_length_m),
            'preferred_origin_id': marker_id,
            'marker_pixel_length_px': None,
            'pixels_per_m': None,
            'image_path': reference.get('imagePath'),
            'markers': [],
            'reference_type': 'charuco',
            'charuco_corners': charuco_corners,
        }

    marker = _normalize_reference_marker(reference)
    markers = [marker]

    # 精简接口只有一个 marker，markerId 本身就是参考坐标系的选择结果。
    preferred_origin_id = marker['marker_id']

    marker_length_m = float(settings.aruco.marker_length_m)

    return {
        'station_id': str(
            reference.get('stationId')
            or data.get('stationId')
            or _get_sn(data)
        ),
        'board_center_x': marker['center_x'],
        'board_center_y': marker['center_y'],
        'board_angle_deg': marker['angle_deg'],
        'marker_count': 1,
        'marker_length_m': marker_length_m,
        'preferred_origin_id': preferred_origin_id,
        'marker_pixel_length_px': marker['marker_pixel_length_px'],
        'pixels_per_m': marker['pixels_per_m'],
        'image_path': reference.get('imagePath'),
        'markers': markers,
    }


def _marker_to_java_data(marker: dict) -> dict:
    return {
        'markerId': int(marker['marker_id']),
        'corners': marker['corners'],
    }


def _reference_to_java_data(ref: dict, station_id: str) -> dict:
    """
    跨机台标定结果只返回给 Java，不在视觉侧保存。
    """
    if ref.get('reference_type') == 'charuco':
        corners = ref.get('charuco_corners') or []
        if not corners:
            raise ValueError('跨机台 ChArUco 标定结果缺少 corners')
        return {
            'stationId': station_id,
            'imagePath': ref.get('image_path'),
            'markerId': int(ref.get('preferred_origin_id', settings.cross_calibration.charuco_marker_id)),
            'corners': corners,
        }

    markers = ref.get('markers') or []
    if not markers:
        raise ValueError('跨机台标定结果缺少 marker')
    preferred_origin_id = ref.get('preferred_origin_id')
    selected = next(
        (
            marker
            for marker in markers
            if marker.get('marker_id') == preferred_origin_id
        ),
        markers[0],
    )
    marker_data = _marker_to_java_data(selected)
    return {
        'stationId': station_id,
        'imagePath': ref.get('image_path'),
        'markerId': marker_data['markerId'],
        'corners': marker_data['corners'],
    }


def _handeye_result_to_java_data(result: dict) -> dict:
    """
    手眼标定返回给 Java 的精简结果。

    cameraMatrix/distCoeffs/gTc 直接封装在 pose3d 中，
    Java 必须原样保存并在在线补偿时传回。
    """
    angle_calibration = result.get('angle_calibration') or {}
    pose3d = angle_calibration.get('pose3d') or {}
    return {
        'rmseM': result.get('rmse_m'),
        'sampleCount': result.get('sample_count'),
        'pose3d': {
            'version': pose3d.get('version'),
            'cameraMatrix': pose3d.get('cameraMatrix'),
            'distCoeffs': pose3d.get('distCoeffs'),
            'gTc': pose3d.get('gTc'),
        },
    }
# =====================================================
# 生命周期
# =====================================================
@app.on_event('startup')
def on_startup() -> None:
    service.open()
    logger.info('AGV Vision Service started, config=%s, mode=%s', SETTINGS_PATH, settings.mode)


@app.on_event('shutdown')
def on_shutdown() -> None:
    service.close()
    logger.info('AGV Vision Service stopped')


# =====================================================
# 新增：按后端接口文档提供的 /api/v1 前缀接口
# =====================================================
@app.get('/api/v1/health')
def api_health() -> dict:
    return _resp_ok({
        'ok': True,
        'mode': settings.mode,
        'config': str(SETTINGS_PATH),
        'service_port': settings.service.port,
    })


@app.post('/api/v1/agv/photo')
def api_photo(body: dict = Body(...)) -> dict:
    """
    接口文档：/api/v1/agv/photo
    后端传 imagePath，视觉在线拍照并保存到该路径。
    """
    ts = _get_timestamp(body)
    try:
        data = _get_data(body)
        image_path = data.get('imagePath') or data.get('image_path')
        if not image_path:
            raise ValueError('缺少必填参数 data.imagePath')

        payload = service.capture_to_path(str(image_path))
        return _resp_ok({'imagePath': payload['image_path']}, timestamp=ts)
    except Exception as e:
        logger.exception('api photo failed')
        return _resp_fail(str(e), timestamp=ts)


@app.post('/api/v1/avg/eye_hand')
@app.post('/api/v1/agv/eye_hand')
def api_eye_hand(body: dict = Body(...)) -> dict:
    """
    手眼标定接口。

    Java 传至少 5 组标定图片和六轴末端位姿；
    视觉返回精简的 rmseM/sampleCount/pose3d，不保存。
    """
    ts = _get_timestamp(body)
    try:
        data = _get_data(body)

        image_point_list = (
            body.get('imagePointList')
            or data.get('imagePointList')
            or data.get('image_point_list')
        )

        if image_point_list is None:
            raise ValueError('缺少必填参数 imagePointList')

        if isinstance(image_point_list, dict):
            image_point_list = [image_point_list]

        if not isinstance(image_point_list, list):
            raise ValueError('imagePointList 必须是数组；如果只有一张图，也可以传一个对象')

        if len(image_point_list) < 5:
            raise ValueError('完整 3D 手眼标定至少需要 5 组点，建议采集 10 组以上多轴倾斜姿态')

        result = service.solve_handeye_from_image_pose_list(image_point_list)

        # 不再 backend.save_handeye()
        return _resp_ok(
            _handeye_result_to_java_data(result),
            msg='手眼标定完成',
            timestamp=ts,
        )

    except Exception as e:
        logger.exception('api eye hand failed')
        return _resp_fail(str(e), timestamp=ts)


@app.post('/api/v1/agv/handeye_observation')
def api_handeye_observation(body: dict = Body(...)) -> dict:
    """检查已经保存的单张 ChArUco 图片是否能用于完整3D手眼标定。"""
    ts = _get_timestamp(body)
    try:
        data = _get_data(body)
        image_path = data.get('imagePath') or data.get('image_path')
        if not image_path:
            raise ValueError('缺少必填参数 data.imagePath')
        sample_id = str(data.get('sampleId') or data.get('sample_id') or 'preview')
        sample = service.build_handeye_sample_from_image(
            sample_id=sample_id,
            image_path=str(image_path),
            robot_x_m=0.0,
            robot_y_m=0.0,
            meta={'z': 0.0, 'rx': 0.0, 'ry': 0.0, 'rz': 0.0, 'validation_only': True},
        )
        observation = sample['observation']
        return _resp_ok(
            {
                'sampleId': sample_id,
                'imagePath': str(image_path),
                'cornerCount': observation.get('corner_count'),
                'markerIds': observation.get('marker_ids') or [],
            },
            msg='ChArUco 单图检查通过',
            timestamp=ts,
        )
    except Exception as e:
        logger.exception('api handeye observation validation failed')
        return _resp_fail(str(e), timestamp=ts)

# @app.post('/api/v1/agv/cross_calibration')  #跨机台标定的基准图
# def api_cross_calibration(body: dict = Body(...)) -> dict:
#     """
#     接口文档：/api/v1/agv/cross_calibration
#     当前实现：视觉在线拍一张 ArUco 工位基准图，保存为 station reference。
#     station_id 默认使用 sn，也支持 data.stationId / data.station_id。
#     """
#     ts = _get_timestamp(body)
#     try:
#         data = _get_data(body)
#         sn = _get_sn(body)
#         station_id = str(data.get('stationId') or data.get('station_id') or sn)
#         image_path = data.get('imagePath') or data.get('image_path')

#         if not image_path:
#             raise ValueError('缺少必填参数 data.imagePath')

#         ref = service.collect_station_reference(station_id, image_path=str(image_path))
#         backend.save_reference(station_id, ref)

#         # return _resp_ok({
#         #     'x': ref.get('board_center_x'),
#         #     'y': ref.get('board_center_y'),
#         #     'z': _get_float(data, 'z', 0.0),
#         #     'rx': _get_float(data, 'rx', 0.0),
#         #     'ry': _get_float(data, 'ry', 0.0),
#         #     'rz': ref.get('board_angle_deg'),
#         #     'stationId': station_id,
#         #     'imagePath': ref.get('image_path'),
#         #     'markerCount': ref.get('marker_count'),
#         #     'reference': ref,
#         # }, msg='请求成功', timestamp=ts)
#         return _resp_ok({
#             'stationId': station_id,
#             'imagePath': ref.get('image_path'),
#             'markerCount': ref.get('marker_count'),
#             'boardCenterX': ref.get('board_center_x'),
#             'boardCenterY': ref.get('board_center_y'),
#             'boardAngleDeg': ref.get('board_angle_deg'),
#         }, msg='请求成功', timestamp=ts)
#     except Exception as e:
#         logger.exception('api cross calibration failed')
#         return _resp_fail(str(e), timestamp=ts)
@app.post('/api/v1/agv/cross_calibration')
def api_cross_calibration(body: dict = Body(...)) -> dict:
    """
    跨机台标定接口。

    Java 传 stationId 和 imagePath；
    视觉拍摄基准图并检测配置指定的 ArUco 或 ChArUco；
    返回扁平的 markerId/corners 给 Java，不保存。
    """
    ts = _get_timestamp(body)
    try:
        data = _get_data(body)
        sn = _get_sn(body)

        station_id = str(data.get('stationId') or data.get('station_id') or sn)

        image_path = data.get('imagePath') or data.get('image_path')
        if not image_path:
            raise ValueError('缺少必填参数 data.imagePath')

        # 如果你的 service.collect_station_reference 已经支持 image_path，就用这一句
        ref = service.collect_station_reference(station_id, image_path=str(image_path))

        # 不再 backend.save_reference()
        return _resp_ok(
            _reference_to_java_data(ref, station_id),
            msg='跨机台标定完成',
            timestamp=ts,
        )

    except Exception as e:
        logger.exception('api cross calibration failed')
        return _resp_fail(str(e), timestamp=ts)

# @app.post('/api/v1/agv/secondary_compensation')
# def api_secondary_compensation(body: dict = Body(...)) -> dict:
#     """
#     接口文档：/api/v1/agv/secondary_compensation
#     当前实现：在线拍当前 ArUco 图，与之前 cross_calibration 保存的基准图比较，返回 dx/dy。
#     station_id 默认使用 sn，也支持 data.stationId / data.station_id。
#     """
#     ts = _get_timestamp(body)
#     try:
#         data = _get_data(body)
#         sn = _get_sn(body)
#         station_id = str(data.get('stationId') or data.get('station_id') or sn)
#         camera_id = str(data.get('cameraId') or data.get('camera_id') or body.get('cameraId') or body.get('camera_id') or sn)
#         task_id = str(data.get('taskId') or data.get('task_id') or f'{station_id}_secondary_compensation')

#         reference_payload = backend.get_reference(station_id)
#         handeye_payload = backend.get_handeye(camera_id)
#         # payload = service.compensate(reference_payload, handeye_payload)
#         image_path = data.get('imagePath') or data.get('image_path')

#         if not image_path:
#             raise ValueError('缺少必填参数 data.imagePath')

#         payload = service.compensate(
#             reference_payload,
#             handeye_payload,
#             image_path=str(image_path)
#         )
        
#         backend.report_compensation(task_id, payload)

#         comp = payload['compensation']
#         dx = comp.get('dx_m_robot') if comp.get('dx_m_robot') is not None else comp.get('dx_m_camera')
#         dy = comp.get('dy_m_robot') if comp.get('dy_m_robot') is not None else comp.get('dy_m_camera')

#         return _resp_ok({
#             'dx': dx,
#             'dy': dy,
#             'dtheta': comp.get('dtheta_deg'),
#             'unit': 'm_robot' if comp.get('dx_m_robot') is not None else 'm_camera_fallback',
#             'stationId': station_id,
#             'cameraId': camera_id,
#             'taskId': task_id,
#             'imagePath': payload.get('image_path'),
#             'detail': payload,
#         }, timestamp=ts)
#     except Exception as e:
#         logger.exception('api secondary compensation failed')
#         return _resp_fail(str(e), timestamp=ts)

def _normalize_current_flange_pose(data: dict) -> list[float]:
    pose = (
        data.get("currentFlangePose")
        or data.get("current_flange_pose")
        or data.get("currentRobotPose")
        or data.get("current_robot_pose")
    )

    if not isinstance(pose, dict):
        raise ValueError(
            "缺少 data.currentFlangePose；"
            "必须传入当前示教器末端位姿，XYZ单位m，RX/RY/RZ单位rad"
        )

    translation_unit = str(
        pose.get("translationUnit", "m")
    ).lower()

    rotation_unit = str(
        pose.get("rotationUnit", "rad")
    ).lower()

    if translation_unit != "m":
        raise ValueError(
            "currentFlangePose.translationUnit 必须是 m"
        )

    if rotation_unit != "rad":
        raise ValueError(
            "currentFlangePose.rotationUnit 必须是 rad"
        )

    try:
        values = [
            float(pose["x"]),
            float(pose["y"]),
            float(pose["z"]),
            float(pose["rx"]),
            float(pose["ry"]),
            float(pose["rz"]),
        ]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "currentFlangePose 必须包含 x/y/z/rx/ry/rz"
        ) from exc

    if not all(math.isfinite(value) for value in values):
        raise ValueError(
            "currentFlangePose 包含非有限数值"
        )

    return values


def _validate_compensation_safety(target_result: dict, robot_command: dict) -> None:
    target_pose = target_result.get('targetFlangePose')
    if not isinstance(target_pose, dict):
        raise ValueError('二次补偿结果缺少 targetFlangePose')
    try:
        target_values = [
            float(target_pose[field])
            for field in ('x', 'y', 'z', 'rx', 'ry', 'rz')
        ]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError('targetFlangePose 必须包含有效的 x/y/z/rx/ry/rz') from exc
    if not all(math.isfinite(value) for value in target_values):
        raise ValueError('targetFlangePose 包含非有限数值')

    translation = target_result.get('baseTranslationDeltaM')
    if not isinstance(translation, list) or len(translation) != 3:
        raise ValueError('二次补偿结果缺少有效的 baseTranslationDeltaM')
    try:
        translation_norm = math.sqrt(sum(float(value) ** 2 for value in translation))
    except (TypeError, ValueError) as exc:
        raise ValueError('baseTranslationDeltaM 包含无效数值') from exc

    delta_transform = robot_command.get('deltaTransform')
    if not isinstance(delta_transform, list) or len(delta_transform) != 4:
        raise ValueError('二次补偿结果缺少有效的 robotCommand.deltaTransform')
    try:
        rotation_trace = sum(float(delta_transform[index][index]) for index in range(3))
    except (IndexError, TypeError, ValueError) as exc:
        raise ValueError('robotCommand.deltaTransform 必须是有效的4x4矩阵') from exc
    rotation_cos = max(-1.0, min(1.0, (rotation_trace - 1.0) / 2.0))
    rotation_angle = math.acos(rotation_cos)

    if translation_norm > settings.compensation.max_translation_m:
        raise ValueError(
            '补偿平移量超过安全阈值：'
            f'{translation_norm:.6f}m > {settings.compensation.max_translation_m:.6f}m'
        )
    if rotation_angle > settings.compensation.max_rotation_rad:
        raise ValueError(
            '补偿旋转量超过安全阈值：'
            f'{rotation_angle:.6f}rad > {settings.compensation.max_rotation_rad:.6f}rad'
        )


@app.post('/api/v1/agv/secondary_compensation')
def api_secondary_compensation(body: dict = Body(...)) -> dict:
    """
    二次补偿接口。

    Java 原样回传完整 3D handeye 和精简 reference。
    保持原字段名，targetFlangePose 返回应到位姿减去原目标位姿的六轴差值。
    """
    ts = _get_timestamp(body)
    try:
        data = _get_data(body)
        sn = _get_sn(body)
        current_flange_pose = _normalize_current_flange_pose(data)

        station_id = str(data.get('stationId') or data.get('station_id') or sn)
        task_id = str(data.get('taskId') or data.get('task_id') or f'{station_id}_secondary_compensation')

        image_path = data.get('imagePath') or data.get('image_path')
        if not image_path:
            raise ValueError('缺少必填参数 data.imagePath')

        # 关键改动：不再从 backend 取，而是直接用 Java 传来的数据
        reference_payload = _normalize_reference_payload(data)
        handeye_payload = _normalize_handeye_payload(data)

        # 如果你的 service.compensate 已经支持 image_path，就用这一句
        payload = service.compensate(
            reference_payload,
            handeye_payload,
            image_path=str(image_path),
        )

        # 不再 backend.report_compensation()
        comp = payload['compensation']

        robot_command = comp.get("robot_command")

        if not isinstance(robot_command, dict):
            raise ValueError("二次补偿结果缺少 robot_command")

        delta_transform = robot_command.get("deltaTransform")

        if delta_transform is None:
            raise ValueError(
                "二次补偿结果缺少 robotCommand.deltaTransform"
            )

        target_result = compose_target_flange_pose(
            current_pose_m_rad=current_flange_pose,
            flange_delta=delta_transform,
        )

        _validate_compensation_safety(target_result, robot_command)

        # target_pose = target_result['targetFlangePose']
        # pose_fields = ('x', 'y', 'z', 'rx', 'ry', 'rz')
        # target_pose_delta = {
        #     field: float(target_pose[field]) - current_flange_pose[index]
        #     for index, field in enumerate(pose_fields)
        # }
        # target_pose_delta['translationUnit'] = 'm'
        # target_pose_delta['rotationUnit'] = 'rad'

        target_pose = target_result['targetFlangePose']
        pose_fields = ('x', 'y', 'z', 'rx', 'ry', 'rz')
        target_pose_delta = {}

        for index, field in enumerate(pose_fields):
            delta = float(target_pose[field]) - current_flange_pose[index]

            # RX/RY/RZ 归一化到 [-π, π]
            if field in ('rx', 'ry', 'rz'):
                delta = math.atan2(math.sin(delta), math.cos(delta))

            target_pose_delta[field] = delta

        target_pose_delta['translationUnit'] = 'm'
        target_pose_delta['rotationUnit'] = 'rad'

        return _resp_ok(
            {
                'taskId': task_id,
                'targetFlangePose': target_pose_delta,
            },
            timestamp=ts,
        )

    except Exception as e:
        logger.exception('api secondary compensation failed')
        return _resp_fail(str(e), timestamp=ts)

# =====================================================
# 原有接口保留：方便你自己本地调试
# =====================================================
@app.get('/health')
def health() -> dict:
    return {
        'ok': True,
        'mode': settings.mode,
        'offline_image_dir': settings.offline.image_dir,
        'config': str(SETTINGS_PATH),
    }


@app.post('/offline/scenario')
def switch_scenario(req: ScenarioRequest) -> dict:
    try:
        service.set_offline_scenario(req.scenario)
        return {'ok': True, 'scenario': settings.offline.scenario, 'image_dir': settings.offline.image_dir}
    except Exception as e:
        logger.exception('switch scenario failed')
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/capture')
def capture() -> dict:
    try:
        return service.capture_once()
    except Exception as e:
        logger.exception('capture failed')
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/calibration/handeye/sample')
def capture_handeye_sample(req: HandEyeSampleCaptureRequest) -> dict:
    try:
        if req.offline_scenario:
            service.set_offline_scenario(req.offline_scenario)
        return service.capture_handeye_sample(req.sample_id, req.robot_x_m, req.robot_y_m)
    except Exception as e:
        logger.exception('capture handeye sample failed')
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/calibration/handeye/solve')
def solve_handeye(req: HandEyeSolveRequest) -> dict:
    try:
        payload = service.solve_handeye(req.samples)
        backend_ret = backend.save_handeye(req.camera_id, payload)
        return {'ok': True, 'payload': payload, 'backend': backend_ret}
    except Exception as e:
        logger.exception('solve handeye failed')
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/reference/collect')
def collect_reference(req: ReferenceRequest) -> dict:
    try:
        payload = service.collect_station_reference(req.station_id)
        backend_ret = backend.save_reference(req.station_id, payload)
        return {'ok': True, 'payload': payload, 'backend': backend_ret}
    except Exception as e:
        logger.exception('collect reference failed')
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/compensate')
def compensate(req: CompensateRequest) -> dict:
    try:
        if req.offline_scenario:
            service.set_offline_scenario(req.offline_scenario)

        if req.reference_payload is not None:
            reference_payload = req.reference_payload
        elif req.station_id:
            reference_payload = backend.get_reference(req.station_id)
        else:
            reference_payload = None

        if reference_payload is None:
            raise ValueError('reference_payload 和 station_id 至少提供一个')

        handeye_payload = req.handeye_payload or backend.get_handeye(req.camera_id)
        payload = service.compensate(reference_payload, handeye_payload)
        backend_ret = backend.report_compensation(req.task_id, payload) if req.task_id else {'ok': True, 'skipped': True}
        return {'ok': True, 'payload': payload, 'backend': backend_ret}
    except Exception as e:
        logger.exception('compensate failed')
        raise HTTPException(status_code=500, detail=str(e))
