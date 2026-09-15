# pkg2_260506 -> pkg3_260522 Java 字段变更说明

这份文档只写 Java/后端需要关心的字段。

pkg3 的原则是：**相对 pkg2 尽量小改动**。  
视觉内部 debug 字段只写日志和 `data/debug/.../center.json`，不返回给 Java。

## 1. 总结

Java 只需要新增两个必须保存/传回的字段：

```text
handeye.calibrationPixelsPerM
reference.pixelsPerM
```

建议额外保存一个排查字段：

```text
reference.markerPixelLengthPx
```

接口变化：

- `/api/v1/agv/photo`：不变。
- `/api/v1/agv/eye_hand`：返回新增 `calibrationPixelsPerM`。
- `/api/v1/agv/cross_calibration`：返回新增 `pixelsPerM`、`markerPixelLengthPx`。
- `/api/v1/agv/secondary_compensation`：请求需要传回 `calibrationPixelsPerM` 和 `pixelsPerM`；返回基本保持 pkg2 风格。

## 2. 拍照接口不变

接口：

```http
POST /api/v1/agv/photo
```

请求：

```json
{
  "timestamp": 1779420000000,
  "data": {
    "imagePath": "D:/data/20260522/photo/handeye/p01.jpg"
  }
}
```

返回：

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "imagePath": "D:\\data\\20260522\\photo\\handeye\\p01.jpg"
  },
  "timestamp": 1779420000000
}
```

Java 不需要改。

## 3. 手眼标定接口

接口：

```http
POST /api/v1/agv/eye_hand
```

### 3.1 Java 请求不变

```json
{
  "timestamp": 1779420000000,
  "imagePointList": [
    {
      "sampleId": "p01",
      "imagePath": "D:/data/20260522/photo/handeye/p01.jpg",
      "x": 200.0,
      "y": 170.0,
      "z": 0.0,
      "rx": 0.0,
      "ry": 0.0,
      "rz": 0.0
    }
  ]
}
```

### 3.2 pkg3 返回

比 pkg2 多一个字段：

```text
calibrationPixelsPerM
```

返回示例：

```json
{
  "code": 0,
  "msg": "手眼标定完成",
  "data": {
    "matrix2x3": [[...], [...]],
    "rmse_m": 0.00012,
    "sample_count": 9,
    "calibrationType": "planar_affine",
    "calibrationPixelsPerM": 3250.0
  },
  "timestamp": 1779420000000
}
```

### 3.3 Java 需要保存

保存：

```json
{
  "matrix2x3": [[...], [...]],
  "calibrationPixelsPerM": 3250.0,
  "calibrationType": "planar_affine",
  "rmse_m": 0.00012,
  "sample_count": 9
}
```

真正必须保存并传回视觉的是：

```text
matrix2x3
calibrationPixelsPerM
```

说明：

- `calibrationPixelsPerM` 单位是 `px/m`。
- 它表示手眼标定时，图像里 1mm 大约对应多少像素。
- 视觉内部还会计算 min/max，但只写日志和 debug JSON，不返回给 Java。

## 4. 跨机台基准接口

接口：

```http
POST /api/v1/agv/cross_calibration
```

### 4.1 Java 请求不变

```json
{
  "sn": "sn-001",
  "timestamp": 1779420000000,
  "data": {
    "stationId": "station_001",
    "imagePath": "D:/data/20260522/photo/cross/station_001_ref.jpg"
  }
}
```

### 4.2 pkg3 返回

比 pkg2 多两个字段：

```text
pixelsPerM
markerPixelLengthPx
```

返回示例：

```json
{
  "code": 0,
  "msg": "跨机台标定完成",
  "data": {
    "stationId": "station_001",
    "imagePath": "D:\\data\\20260522\\photo\\cross\\station_001_ref.jpg",
    "markerCount": 1,
    "boardCenterX": 675.0,
    "boardCenterY": 546.0,
    "boardAngleDeg": 180.0,
    "markerLengthM": 0.150,
    "preferredOriginId": 0,
    "pixelsPerM": 2800.0,
    "markerPixelLengthPx": 420.0
  },
  "timestamp": 1779420000000
}
```

### 4.3 Java 需要保存

保存：

```json
{
  "stationId": "station_001",
  "boardCenterX": 675.0,
  "boardCenterY": 546.0,
  "boardAngleDeg": 180.0,
  "markerLengthM": 0.150,
  "preferredOriginId": 0,
  "markerCount": 1,
  "pixelsPerM": 2800.0,
  "markerPixelLengthPx": 420.0,
  "imagePath": "D:/data/20260522/photo/cross/station_001_ref.jpg"
}
```

真正必须保存并传回视觉的是：

```text
boardCenterX
boardCenterY
boardAngleDeg
markerLengthM
pixelsPerM
```

`markerPixelLengthPx` 建议保存，方便排查，但不参与最终必需计算。

说明：

- `markerPixelLengthPx`：ArUco 在图像里的平均边长，单位 `px`。
- `pixelsPerM`：图像比例，单位 `px/m`。
- `pixelsPerM = markerPixelLengthPx / markerLengthM`

## 5. 二次补偿接口

接口：

```http
POST /api/v1/agv/secondary_compensation
```

### 5.1 Java 请求需要新增字段

相比 pkg2，新增：

```text
data.handeye.calibrationPixelsPerM
data.reference.pixelsPerM
```

建议同时传：

```text
data.reference.markerPixelLengthPx
```

请求示例：

```json
{
  "sn": "sn-001",
  "timestamp": 1779420000000,
  "data": {
    "stationId": "station_001",
    "cameraId": "cam_001",
    "taskId": "task_001",
    "imagePath": "D:/data/20260522/photo/cross/current.jpg",
    "handeye": {
      "matrix2x3": [[...], [...]],
      "calibrationPixelsPerM": 3250.0
    },
    "reference": {
      "boardCenterX": 675.0,
      "boardCenterY": 546.0,
      "boardAngleDeg": 180.0,
      "markerLengthM": 0.150,
      "preferredOriginId": 0,
      "markerCount": 1,
      "pixelsPerM": 2800.0,
      "markerPixelLengthPx": 420.0
    }
  }
}
```

### 5.2 pkg3 返回

返回保持接近 pkg2，只返回 Java 真正需要的补偿结果：

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "dx": -20.3,
    "dy": 0.4,
    "dtheta": 0.0,
    "unit": "m_robot",
    "stationId": "station_001",
    "cameraId": "cam_001",
    "taskId": "task_001",
    "imagePath": "D:\\data\\20260522\\photo\\cross\\current.jpg"
  },
  "timestamp": 1779420000000
}
```

Java 控制机器人只需要使用：

```text
dx
dy
dtheta
unit
```

## 6. 二次补偿不再返回给 Java 的调试字段

下面这些字段不放在 `/api/v1/agv/secondary_compensation` 的返回里，视觉自己写日志和 debug 文件：

```text
calibration_pixels_per_m
calibration_pixels_per_m_min
calibration_pixels_per_m_max
dxRaw
dyRaw
dxCameraDynamic
dyCameraDynamic
referencePixelsPerM
currentPixelsPerM
dynamicPixelsPerM
calibrationPixelsPerM
handeyeScaleCorrection
debugDir
debugRawImagePath
debugDetectedImagePath
debugCenterJsonPath
```

它们会保存在：

```text
logs/YYYYMMDD/agv_vision.log
data/debug/YYYYMMDD/时间戳_业务名/center.json
```

## 7. Java 最小改动清单

### 7.1 数据库/缓存新增字段

手眼结果新增：

```text
calibrationPixelsPerM  double
```

机台 reference 新增：

```text
pixelsPerM             double
markerPixelLengthPx     double，可选但建议保存
```

### 7.2 二次补偿请求新增字段

```text
handeye.calibrationPixelsPerM
reference.pixelsPerM
reference.markerPixelLengthPx  可选但建议传
```

## 8. 兼容字段名

pkg3 同时兼容驼峰和下划线。

推荐 Java 使用驼峰：

```text
calibrationPixelsPerM
pixelsPerM
markerPixelLengthPx
```

视觉也兼容：

```text
calibration_pixels_per_m
pixels_per_m
marker_pixel_length_px
```
