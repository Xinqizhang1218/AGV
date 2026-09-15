# AGV Vision pkg5：完整 3D 手眼标定与在线补偿

当前版本只使用完整 3D 算法链。旧的二维仿射、动态像素比例和 RZ 杠杆臂算法已经不参与计算。Java 接口保持原 URL 和原有主要层级，删除 3D 算法不使用的兼容字段；Java 保存视觉返回的完整标定 `data`，最终只执行 `targetFlangePose`。

## 1. 当前算法

离线标定：

```text
ChArUco 多姿态图像
-> cornerSubPix
-> calibrateCamera（cameraMatrix、distCoeffs）
-> 板内 ArUco 对应点
-> solvePnP ITERATIVE（每帧 cTt）
-> 机器人六轴姿态（每帧 bTg）
-> calibrateHandEye Tsai / Park
-> 按固定标定板一致性选优
-> gTc
```

在线补偿：

```text
当前 ArUco 图像
-> ArUco 检测
-> cornerSubPix
-> solvePnP ITERATIVE
-> solvePnPRefineLM
-> cTt
-> gTt = gTc @ cTt
-> 当前末端位姿右乘六自由度补偿矩阵
-> targetFlangePose
```

坐标记号：

- `bTg`：末端/夹爪坐标系到机器人基座坐标系。
- `cTt`：目标坐标系到相机坐标系。
- `gTc`：相机坐标系到末端/夹爪坐标系。
- `gTt = gTc @ cTt`：目标在末端坐标系下的完整 3D 位姿。

## 2. 安装与启动

要求 Python 3.10 及以上。

```powershell
cd D:\code\AGV\pkg5_260728
python -m pip install -r requirements.txt
python -m agv_vision.main --config agv_vision/config/settings_online.yaml serve
python -m agv_vision.main --config agv_vision/config/settings.yaml serve
```

默认地址为 `http://127.0.0.1:8088`，健康检查：

```http
GET /api/v1/health
```

在线配置文件：

```text
agv_vision/config/settings_online.yaml
```

现场必须核对：

```yaml
camera:
  vendor: orbbec  # 可选：orbbec / daheng / hikvision
  orbbec:
    width: 1280
    height: 800
    fps: 15
  width: 1280
  height: 800
  fps: 15
  ip_address: 192.168.1.101
  control_port: 8090

charuco:
  dictionary_name: DICT_4X4_50
  squares_x: 5
  squares_y: 5
  square_length_m: 0.030
  marker_length_m: 0.021
  min_corners: 5
  use_subpix: true

aruco:
  dictionary_name: DICT_5X5_50
  marker_length_m: 0.150
  marker_ids: [0]
  preferred_origin_id: 0
  min_markers: 1

compensation:
  max_translation_m: 0.05
  max_rotation_rad: 0.174533
```

`charuco` 必须与实际标定板一致；`aruco` 必须与在线目标码一致。`aruco.marker_length_m` 是接口内外唯一使用的 ArUco 实际边长来源，Java 不保存也不回传 `markerLengthM`。长度和平移统一使用米 `m`，图像坐标使用像素 `px`，机器人欧拉角统一使用弧度 `rad`，旋转顺序固定为 `Rz * Ry * Rx`。

`compensation` 是视觉侧安全阈值。超过最大平移或旋转时，接口返回 `code=400`，不会返回可执行目标位姿。示例阈值必须根据现场机器人安全范围复核。

### 2.1 相机厂商切换

在线模式通过 `camera.vendor` 选择相机，修改配置后重启服务即可。大恒示例：

```yaml
camera:
  vendor: daheng
  daheng:
    installer_path: 'D:\sdk\Galaxy_Windows_CN_32bits-64bits_2.6.2607.9201\Galaxy_Windows_CN_32bits-64bits_2.6.2607.9201.exe'
    python_path: 'D:\sdk\大恒\GalaxySDK'
    serial_number: null
    ip_address: null
    width: 1280
    height: 800
    fps: 15
```

海康示例：

```yaml
camera:
  vendor: hikvision
  hikvision:
    installer_path: 'D:\sdk\Hikvision\MVS_SDK_V4_7_0_3_MVFG_V2_7_0_2_VC90_Runtime_STD_251113.exe'
    python_path: 'D:\sdk\hik\MvImport'
    serial_number: null
    ip_address: null
    width: 1280
    height: 800
    fps: 15
```

`installer_path` 是 SDK 安装程序位置，服务不会自动执行它。先安装对应 SDK；若安装后仍提示无法导入 Python 模块，再填写实际绑定目录：

- 大恒：包含 `gxipy` 包的目录。
- 海康：包含 `MvCameraControl_class.py` 的 `MvImport` 目录，常见位置为 `C:\Program Files (x86)\MVS\Development\Samples\Python\MvImport`。

`serial_number` 和 `ip_address` 都为空时选择枚举到的第一台对应厂商相机；多相机现场建议填写序列号。大恒/海康的选择配置与原有 Orbbec 的 `camera.serial_number`、`camera.ip_address` 相互独立。

三种相机的 `width`、`height`、`fps` 分别配置在各自厂商块中，切换 `vendor` 时会自动采用对应参数。顶层同名字段仅作为旧配置兜底。

## 3. Java 调用流程

### 3.1 拍摄标定图片

机器人每到一个标定姿态，Java 可先调用：

```http
POST /api/v1/agv/photo
Content-Type: application/json
```

```json
{
  "timestamp": 1785254400000,
  "data": {
    "imagePath": "D:/data/handeye/p01.jpg"
  }
}
```

`imagePath` 必须是视觉服务所在机器能够写入和读取的路径。Java 要保存图片对应的机器人六轴姿态。

### 3.2 完整 3D 手眼标定

```http
POST /api/v1/agv/eye_hand
Content-Type: application/json
```

兼容别名：`POST /api/v1/avg/eye_hand`。

```json
{
  "timestamp": 1785254400000,
  "imagePointList": [
    {
      "sampleId": "p01",
      "imagePath": "D:/data/handeye/p01.jpg",
      "x": 0.200,
      "y": 0.170,
      "z": 0.350,
      "rx": 0.000,
      "ry": 0.000,
      "rz": 0.000
    },
    {
      "sampleId": "p02",
      "imagePath": "D:/data/handeye/p02.jpg",
      "x": 0.220,
      "y": 0.170,
      "z": 0.360,
      "rx": 0.120,
      "ry": 0.000,
      "rz": 0.050
    },
    {
      "sampleId": "p03",
      "imagePath": "D:/data/handeye/p03.jpg",
      "x": 0.180,
      "y": 0.170,
      "z": 0.340,
      "rx": -0.120,
      "ry": 0.060,
      "rz": -0.040
    },
    {
      "sampleId": "p04",
      "imagePath": "D:/data/handeye/p04.jpg",
      "x": 0.200,
      "y": 0.190,
      "z": 0.350,
      "rx": 0.040,
      "ry": 0.140,
      "rz": 0.030
    },
    {
      "sampleId": "p05",
      "imagePath": "D:/data/handeye/p05.jpg",
      "x": 0.200,
      "y": 0.150,
      "z": 0.360,
      "rx": -0.050,
      "ry": -0.140,
      "rz": -0.030
    }
  ]
}
```

以上数字只展示字段格式，不能作为现场姿态。

采集要求：

- 最少 5 组，建议 10～20 组。
- ChArUco 板在机器人基座下必须固定不动。
- 所有图片分辨率必须相同。
- 每张图必须清楚看到足够的 ChArUco 角点和板内 marker。
- 机器人必须同时改变位置和姿态，尤其需要不同方向的 `rx/ry` 倾斜。
- 至少两次相对第一姿态大于 2° 的旋转，且旋转轴不能几乎平行。
- Java 必须把 `rx/ry/rz` 全部转换成弧度再发送；视觉不再自动判断度/弧度。

成功响应的核心结构：

```json
{
  "code": 0,
  "msg": "手眼标定完成",
  "data": {
    "rmse_m": 0.0004,
    "sample_count": 12,
    "calibrationType": "charuco_calibrateCamera_pnp_handeye_tsai_park_3d",
    "angleCalibration": {
      "pose3d": {
        "version": 1,
        "cameraMatrix": [
          [1000.0, 0.0, 640.0],
          [0.0, 1000.0, 400.0],
          [0.0, 0.0, 1.0]
        ],
        "distCoeffs": [0.01, -0.02, 0.0, 0.0, 0.0],
        "gTc": [
          [1.0, 0.0, 0.0, 0.05],
          [0.0, 1.0, 0.0, -0.02],
          [0.0, 0.0, 1.0, 0.10],
          [0.0, 0.0, 0.0, 1.0]
        ]
      }
    }
  }
}
```

矩阵数值仅展示结构，现场必须使用真实响应。Java 必须完整保存响应 `data`，尤其是：

```text
angleCalibration.pose3d.cameraMatrix
angleCalibration.pose3d.distCoeffs
angleCalibration.pose3d.gTc
```

Java 不再保存或回传 `matrix2x3`、`calibrationPixelsPerM` 和旧的 `direction/offsetDeg/rmseDeg`。完整相机标定质量、算法候选、旋转约定和 `imageSize` 继续保存在视觉侧 debug JSON，不进入 Java 精简接口。

### 3.3 跨机台基准采集

```http
POST /api/v1/agv/cross_calibration
Content-Type: application/json
```

```json
{
  "sn": "sn-001",
  "timestamp": 1785254400000,
  "data": {
    "stationId": "station_001",
    "imagePath": "D:/data/station/station_001_reference.jpg"
  }
}
```

跨机台目标类型由视觉配置选择，默认保持现有 ArUco：

```yaml
cross_calibration:
  target_type: charuco  # aruco / charuco
  charuco_marker_id: 2
```

ArUco 成功响应：

```json
{
  "code": 0,
  "msg": "跨机台标定完成",
  "data": {
    "stationId": "station_001",
    "imagePath": "D:/data/station/station_001_reference.jpg",
    "markerId": 0,
    "corners": [
      [600.0, 470.0],
      [750.0, 470.0],
      [750.0, 620.0],
      [600.0, 620.0]
    ]
  },
  "timestamp": 1785254400000
}
```

ChArUco 成功响应：

```json
{
  "code": 0,
  "msg": "跨机台标定完成",
  "data": {
    "stationId": "station_001",
    "imagePath": "D:/data/station/station_001_reference.jpg",
    "markerId": 2,
    "corners": [
      {"id": 0, "x": 620.3, "y": 481.7},
      {"id": 1, "x": 651.2, "y": 480.9},
      {"id": 2, "x": 682.4, "y": 480.1},
      {"id": 5, "x": 621.1, "y": 512.6},
      {"id": 6, "x": 652.0, "y": 511.8}
    ]
  },
  "timestamp": 1785254400000
}
```

`markerId=2` 是 ChArUco 跨机台板的逻辑 ID；`corners[].id` 是 OpenCV ChArUco 棋盘交点 ID，两者含义不同。Java 应按 `stationId` 保存完整响应 `data`，二次补偿时原样放入 `data.reference`。视觉根据 `corners` 的元素类型自动选择流程：对象元素是 ChArUco，二维数组元素是旧 ArUco。旧版 `charucoCorners` 输入仍然兼容。

### 3.4 二次补偿

```http
POST /api/v1/agv/secondary_compensation
Content-Type: application/json
```

最稳妥的做法：第 3.2 步响应的 `data` 整体作为 `handeye`，第 3.3 步响应的 `data` 整体作为 `reference`。

```json
{
  "sn": "sn-001",
  "timestamp": 1785254400000,
  "data": {
    "stationId": "station_001",
    "taskId": "task_001",
    "imagePath": "D:/data/station/station_001_current.jpg",
    "currentFlangePose": {
      "x": 0.200,
      "y": 0.170,
      "z": 0.350,
      "rx": 0.000,
      "ry": 0.000,
      "rz": 0.000
    },
    "handeye": {
      "rmse_m": 0.0004,
      "sample_count": 12,
      "calibrationType": "charuco_calibrateCamera_pnp_handeye_tsai_park_3d",
      "angleCalibration": {
        "pose3d": {
          "version": 1,
          "cameraMatrix": [
            [1000.0, 0.0, 640.0],
            [0.0, 1000.0, 400.0],
            [0.0, 0.0, 1.0]
          ],
          "distCoeffs": [0.01, -0.02, 0.0, 0.0, 0.0],
          "gTc": [
            [1.0, 0.0, 0.0, 0.05],
            [0.0, 1.0, 0.0, -0.02],
            [0.0, 0.0, 1.0, 0.10],
            [0.0, 0.0, 0.0, 1.0]
          ]
        }
      }
    },
    "reference": {
      "stationId": "station_001",
      "imagePath": "D:/data/station/station_001_reference.jpg",
      "markers": [
        {
          "markerId": 0,
          "corners": [
            [600.0, 470.0],
            [750.0, 470.0],
            [750.0, 620.0],
            [600.0, 620.0]
          ]
        }
      ]
    }
  }
}
```

示例矩阵不能用于现场，必须替换为真实标定响应。

响应：

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "taskId": "task_001",
    "targetFlangePose": {
      "x": 0.201,
      "y": 0.168,
      "z": 0.3501,
      "rx": 0.001,
      "ry": 0.002,
      "rz": 0.004,
      "translationUnit": "m",
      "rotationUnit": "rad"
    },
    "deltaTranslationM": [0.001, -0.002, 0.0001],
    "deltaRpyRad": [0.001, 0.002, 0.004]
  }
}
```

Java 可读取 `taskId`、`targetFlangePose`、`deltaTranslationM` 和 `deltaRpyRad`。后两个数组表示当前法兰局部坐标系下的补偿误差，仅用于展示和质量判断；机器人仍应执行 `targetFlangePose`，不得把误差数组再次叠加到当前位姿。视觉内部继续把完整补偿矩阵、marker 选择和质量信息写入 debug JSON。

## 4. 接口与升级规则

- URL、通用 `code/msg/data/timestamp` 外层和已有主要层级保持不变。
- 二次补偿不再要求 `matrix2x3`、`calibrationPixelsPerM`、二维中心、二维角度、`pixelsPerM`、`markerLengthM` 或 `imageSize`。
- `markerLengthM` 始终读取视觉配置 `settings.aruco.marker_length_m`。
- marker 新接口输出 `markerId`；Python 输入短期兼容旧 `marker_id`，Java 新 DTO 只能使用 `markerId`。
- 缺少 `handeye.angleCalibration.pose3d` 会直接报错，不回退旧二维算法。
- ArUco 或 ChArUco 缺少 `reference.markerId/corners`，都会要求重新采集跨机台基准。
- 缺少 `pose3d` 的旧手眼标定全部作废；缺少 marker 四角点的旧工位基准全部作废。
- 修改实际 ArUco 尺寸、相机分辨率、相机内参或相机安装关系后，必须重新采集相关标定数据。

## 5. 常见错误

### 缺少 `pose3d`

Java 没有完整保存 `angleCalibration.pose3d`。必须重新完成 3D 标定，并完整保存手眼响应 `data`。

### 缺少跨机台角点

Java 必须完整保存跨机台响应 `data` 并原样回传。ArUco 的 `corners` 是四个二维数组；ChArUco 的 `corners` 是至少 5 个带 `id/x/y` 的对象。

### 缺少六轴姿态

每条 `imagePointList` 必须包含：

```text
x, y, z, rx, ry, rz
```

2026-07-22 的旧样本只有 `x/y`，不能用于当前标定。

### 手眼标定退化

增加不同方向的 `rx/ry` 倾斜，不要只做 XY 平移或只绕 Z 轴旋转。

### PnP 失败或跳动

检查字典、marker ID、视觉配置中的实际边长、图像反光/模糊/遮挡，以及相机配置是否与标定时一致。

### 补偿超过安全阈值

视觉返回 `code=400` 且不返回可执行目标位姿。检查工位基准、当前图、marker 识别和 `compensation.max_translation_m/max_rotation_rad`；不得直接提高阈值绕过异常。

## 6. 日志、调试和测试

```text
logs/YYYYMMDD/agv_vision.log
data/debug/YYYYMMDD/<时间戳_业务名称>/
```

调试目录通常包含 `raw.jpg`、`detected.jpg` 和 `center.json`。

```powershell
python -m compileall agv_vision
python -m pytest -q test_api_contract.py
```

当前接口契约测试覆盖手眼响应过滤、marker 驼峰转换、配置中的 ArUco 尺寸、弧度约定、精简补偿响应和视觉安全限幅。完整相机端到端验证仍需在部署环境连接真实相机执行。

核心代码：

- `agv_vision/vision/pose3d.py`
- `agv_vision/vision/handeye_calibrator.py`
- `agv_vision/vision/compensator.py`
- `agv_vision/api/app.py`
