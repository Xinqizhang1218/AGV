# Java_视觉角度接口对接说明

适用接口：

- `POST /api/v1/agv/eye_hand`（兼容 `POST /api/v1/avg/eye_hand`）
- `POST /api/v1/agv/cross_calibration`
- `POST /api/v1/agv/secondary_compensation`

---

## 1. 通用响应结构

所有业务接口返回：

```json
{
  "code": 0,
  "msg": "success",
  "data": {},
  "timestamp": 1770000000000
}
```

说明：

- `code=0` 成功
- `code=400` 业务失败（HTTP 状态通常仍为 200）

---

## 2. 手眼标定 `/api/v1/agv/eye_hand`

### 2.1 请求示例（当前已传）

```json
{
  "sn": "AGV-001",
  "timestamp": 1770000000000,
  "imagePointList": [
    {
      "sampleId": "p01",
      "imagePath": "D:/data/handeye/p01.jpg",
      "x": 0.180,
      "y": 0.250,
      "z": 0.31598,
      "rx": -179.96,
      "ry": 0.0,
      "rz": -10.0
    }
  ]
}
```

#### 本次新增字段（请求）

- 无（请求结构与原流程一致，仍为 `imagePointList`）

### 2.2 响应示例（当前已返）

```json
{
  "code": 0,
  "msg": "手眼标定完成",
  "data": {
    "matrix2x3": [[-0.000016, -0.000179, 0.2434], [-0.000179, 0.000017, 0.3428]],
    "calibrationType": "planar_affine",
    "calibrationPixelsPerM": 3200.0,
    "angleCalibration": {
      "direction": 1,
      "offsetDeg": -92.3
    }
  },
  "timestamp": 1770000000000
}
```

#### 本次新增字段（响应）

- `data.calibrationPixelsPerM`
- `data.angleCalibration.direction`
- `data.angleCalibration.offsetDeg`

### 2.3 字段说明

#### 请求字段

| 字段路径 | 含义 |
|---|---|
| `sn` | 设备编号 |
| `timestamp` | 时间戳（ms） |
| `imagePointList` | 标定样本数组 |
| `imagePointList[].sampleId` | 样本编号 |
| `imagePointList[].imagePath` | 样本图片路径 |
| `imagePointList[].x` | 机器人 X |
| `imagePointList[].y` | 机器人 Y |
| `imagePointList[].z` | 机器人 Z |
| `imagePointList[].rx` | 机器人 RX |
| `imagePointList[].ry` | 机器人 RY |
| `imagePointList[].rz` | 机器人 RZ（rad） |

#### 响应字段

| 字段路径 | 含义 |
|---|---|
| `code` | 业务状态码 |
| `msg` | 业务消息 |
| `timestamp` | 时间戳（ms） |
| `data.matrix2x3` | 2x3 手眼矩阵 |
| `data.calibrationType` | 标定类型 |
| `data.calibrationPixelsPerM` | 标定比例（px/m） |
| `data.angleCalibration.direction` | 角度方向系数 |
| `data.angleCalibration.offsetDeg` | 角度偏移 |

---

## 3. 跨机台标定 `/api/v1/agv/cross_calibration`

### 3.1 请求示例（当前已传）

```json
{
  "sn": "station_001",
  "timestamp": 1770000000000,
  "data": {
    "stationId": "station_001",
    "imagePath": "D:/data/cross/station_001_ref.jpg"
  }
}
```

#### 本次新增字段（请求）

- 无（请求仍为 `stationId` + `imagePath`）

### 3.2 响应示例（当前已返）

```json
{
  "code": 0,
  "msg": "跨机台标定完成",
  "data": {
    "stationId": "station_001",
    "imagePath": "D:/data/cross/station_001_ref.jpg",
    "boardCenterX": 675.0,
    "boardCenterY": 546.0,
    "boardAngleDeg": 92.63,
    "preferredOriginId": 0,
    "pixelsPerM": 2800.0
  },
  "timestamp": 1770000000000
}
```

#### 本次新增字段（响应）

- 无（响应按精简字段返回）


### 3.3 字段说明

#### 请求字段

| 字段路径 | 含义 |
|---|---|
| `sn` | 工位或设备编号 |
| `timestamp` | 时间戳（ms） |
| `data.stationId` | 工位编号 |
| `data.imagePath` | 基准图保存路径 |

#### 响应字段

| 字段路径 | 含义 |
|---|---|
| `code` | 业务状态码 |
| `msg` | 业务消息 |
| `timestamp` | 时间戳（ms） |
| `data.stationId` | 工位编号 |
| `data.imagePath` | 基准图路径 |
| `data.boardCenterX` | 基准中心 X（px） |
| `data.boardCenterY` | 基准中心 Y（px） |
| `data.boardAngleDeg` | 基准角度（deg） |
| `data.preferredOriginId` | 原点码 ID |
| `data.pixelsPerM` | 像素比例（px/m） |

---

## 4. 二次补偿 `/api/v1/agv/secondary_compensation`

### 4.1 请求示例（当前已传）

```json
{
  "sn": "station_001",
  "timestamp": 1770000000000,
  "data": {
    "stationId": "station_001",
    "cameraId": "cam_001",
    "taskId": "task_001",
    "imagePath": "D:/data/cross/current.jpg",
    "handeye": {
      "matrix2x3": [[-0.000016, -0.000179, 0.2434], [-0.000179, 0.000017, 0.3428]],
      "calibrationPixelsPerM": 3200.0,
      "angleCalibration": {
        "direction": 1,
        "offsetDeg": -92.3
      }
    },
    "reference": {
      "boardCenterX": 675.0,
      "boardCenterY": 546.0,
      "boardAngleDeg": 92.63,
      "pixelsPerM": 2800.0,
      "markerLengthM": 0.150,
      "preferredOriginId": 0
    }
  }
}
```

#### 本次新增字段（请求）

- `data.handeye.calibrationPixelsPerM`
- `data.handeye.angleCalibration.direction`
- `data.handeye.angleCalibration.offsetDeg`
- `data.reference.boardAngleDeg`

### 4.2 响应示例（当前已返）

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "dx": -0.02197,
    "dy": 0.02160,
    "dtheta": 0.027,
    "dthetaRobotDeg": 0.027,
    "stationId": "station_001",
    "cameraId": "cam_001",
    "taskId": "task_001",
    "imagePath": "D:/data/cross/current.jpg"
  },
  "timestamp": 1770000000000
}
```

#### 本次新增字段（响应）

- `data.dthetaRobotDeg`

### 4.3 字段说明

#### 请求字段

| 字段路径 | 含义 |
|---|---|
| `sn` | 设备或工位编号 |
| `timestamp` | 时间戳（ms） |
| `data.stationId` | 工位编号 |
| `data.cameraId` | 相机编号 |
| `data.taskId` | 任务编号 |
| `data.imagePath` | 当前图保存路径 |
| `data.handeye.matrix2x3` | 手眼矩阵 |
| `data.handeye.calibrationPixelsPerM` | 手眼标定比例 |
| `data.handeye.angleCalibration.direction` | 角度方向系数 |
| `data.handeye.angleCalibration.offsetDeg` | 角度偏移 |
| `data.reference.boardCenterX` | 基准中心 X |
| `data.reference.boardCenterY` | 基准中心 Y |
| `data.reference.boardAngleDeg` | 基准角度 |
| `data.reference.pixelsPerM` | 基准像素比例 |
| `data.reference.markerLengthM` | 码边长 |
| `data.reference.preferredOriginId` | 原点码 ID |

#### 响应字段

| 字段路径 | 含义 |
|---|---|
| `code` | 业务状态码 |
| `msg` | 业务消息 |
| `timestamp` | 时间戳（ms） |
| `data.dx` | X 补偿（m） |
| `data.dy` | Y 补偿（m） |
| `data.dtheta` | 视觉角差（deg） 视觉测出来的角度差（基准角 - 当前角）|
| `data.dthetaRobotDeg` | 机器人补偿角（deg）把视觉角差按手眼角度标定转换后得到 |
| `data.stationId` | 工位编号 |
| `data.cameraId` | 相机编号 |
| `data.taskId` | 任务编号 |
| `data.imagePath` | 当前图路径 |



