# 夹爪角度补偿变更报告

变更日期：2026-06-25

分支：`gripper-angle-compensation`

## 1. 变更目标

在原有 `dx / dy` 二次补偿基础上，增加夹爪平面角度补偿能力。

原系统已经能识别 ArUco / ChArUco 板角度，并在二次补偿中返回 `dtheta`。本次变更把“视觉角度”与“机器人夹爪 RZ”建立显式关系：

```text
robot_rz_deg = direction * vision_angle_deg + offsetDeg
```

其中：

- `direction`：视觉角度正方向与机器人 RZ 正方向是否一致，通常为 `1` 或 `-1`
- `offsetDeg`：视觉角度零点到机器人 RZ 零点的固定偏移
- `rmseDeg`：角度拟合误差，单位 deg

## 2. 是否三个流程都需要改

需要，但职责不同：

| 流程 | 本次职责 | 是否改变 |
|------|----------|----------|
| 手眼标定 `/api/v1/agv/eye_hand` | 根据标定图片识别视觉角度，并结合机器人 `rz` 生成 `angleCalibration` | 是 |
| 跨机台标定 `/api/v1/agv/cross_calibration` | 返回基准板角度，作为后续角度补偿的基准 | 是 |
| 二次补偿 `/api/v1/agv/secondary_compensation` | 接收 `angleCalibration`，返回机器人夹爪补偿角 `dthetaRobotDeg` | 是 |

## 3. 手眼标定变更

### 请求要求

`imagePointList` 中原来已有 `rz` 字段，本次开始参与角度标定：

```json
{
  "sampleId": "p01",
  "imagePath": "D:/data/photo/handeye/p01.jpg",
  "x": 227.0,
  "y": 12.0,
  "z": 0.0,
  "rx": 0.0,
  "ry": 0.0,
  "rz": 0.0
}
```

### 采样建议

如果所有样本的 `rz` 都一样，系统仍可计算 `offsetDeg`，但 `direction` 需要现场验证。

建议至少加入几组不同夹爪角度：

```text
rz = -10deg, -5deg, 0deg, 5deg, 10deg
```

### 响应新增字段

```json
{
  "matrix2x3": [[...], [...]],
  "calibrationPixelsPerM": 3200.018,
  "angleCalibration": {
    "direction": 1,
    "offsetDeg": -92.3,
    "rmseDeg": 0.15,
    "sampleCount": 9,
    "reliable": true,
    "reason": "ok"
  }
}
```

Java 后端需要把 `angleCalibration` 和原来的 `matrix2x3`、`calibrationPixelsPerM` 一起保存。

## 4. 跨机台标定变更

跨机台标定原来已经返回：

```json
{
  "boardAngleDeg": 92.63
}
```

本次新增同义字段：

```json
{
  "angleReferenceDeg": 92.63
}
```

用途：明确告诉后端这是后续二次补偿使用的角度基准。Java 可以继续保存 `boardAngleDeg`，也可以保存新字段 `angleReferenceDeg`。

## 5. 二次补偿变更

### 请求新增

Java 在 `handeye` 中回传手眼标定结果时，需要一起带上 `angleCalibration`：

```json
{
  "data": {
    "handeye": {
      "matrix2x3": [[...], [...]],
      "calibrationPixelsPerM": 3200.018,
      "angleCalibration": {
        "direction": 1,
        "offsetDeg": -92.3,
        "rmseDeg": 0.15
      }
    },
    "reference": {
      "boardCenterX": 702.0,
      "boardCenterY": 399.5,
      "boardAngleDeg": 92.63,
      "pixelsPerM": 3210.0
    }
  }
}
```

### 响应新增

```json
{
  "dx": -21.97,
  "dy": 21.60,
  "dtheta": 0.027,
  "dthetaRobotDeg": 0.027,
  "unit": "m_robot"
}
```

字段说明：

- `dtheta`：视觉基准角度与当前角度的差值
- `dthetaRobotDeg`：按 `angleCalibration.direction` 转换后的机器人夹爪 RZ 补偿角

当前计算公式：

```text
dtheta = normalize(reference.boardAngleDeg - current.boardAngleDeg)
dthetaRobotDeg = normalize(direction * dtheta)
```

`offsetDeg` 用于描述视觉角度和机器人 RZ 的绝对零点关系；做差分补偿时固定偏移会抵消，所以二次补偿主要使用 `direction`。

## 6. 代码变更文件

- `agv_vision/core/models.py`
  - `HandEyeCalibrationResult` 新增 `angle_calibration`
  - `CompensationResult` 新增 `dtheta_robot_deg`、`angle_direction`、`angle_offset_deg`

- `agv_vision/vision/handeye_calibrator.py`
  - 新增角度标定求解
  - 自动尝试 `direction=1` 和 `direction=-1`
  - 返回 `offsetDeg`、`rmseDeg`、`reliable`

- `agv_vision/vision/compensator.py`
  - 接收 `angle_calibration`
  - 计算 `dtheta_robot_deg`

- `agv_vision/core/service.py`
  - 从手眼参数中传递 `angleCalibration`
  - debug JSON 和日志中记录角度补偿信息

- `agv_vision/api/app.py`
  - 手眼标定返回 `angleCalibration`
  - 跨机台标定返回 `angleReferenceDeg`
  - 二次补偿接收 `angleCalibration`，返回 `dthetaRobotDeg`

## 7. 验证结果

已执行语法编译检查：

```powershell
python -m compileall pkg3_260522\agv_vision
```

结果：通过。

## 8. 现场注意事项

1. 标定角度时，夹爪或夹爪治具上的识别板必须固定牢靠，不能相对夹爪打滑。
2. 建议标定样本中包含不同 `rz`，否则 `direction` 只能先按算法猜测，需现场用正负角补偿验证。
3. 如果发现 `dthetaRobotDeg` 补反了，把 `angleCalibration.direction` 从 `1` 改为 `-1`，或重新采集带不同 `rz` 的样本。
4. 当前仍是平面补偿方案，`rx / ry / z` 未参与求解；如果后续要做完整空间姿态，需要升级为 3D 手眼标定。
