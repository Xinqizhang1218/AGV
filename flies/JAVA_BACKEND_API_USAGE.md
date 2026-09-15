# Java 后端调用视觉 HTTP 接口说明

## 1. 启动视觉服务

```powershell
cd D:\code\AGV\agv_vision_pkg_v2
conda activate orbbec
python -m agv_vision.main --config agv_vision/config/settings_online.yaml serve
```

`settings_online.yaml` 已设置：

```yaml
mode: online
service:
  host: 0.0.0.0
  port: 8088
```

启动后，Java 使用：

```text
http://视觉工控机IP:8088
```

例如：

```text
http://192.168.1.100:8088
```

## 2. 健康检查

```http
GET /api/v1/health
```

返回：

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "ok": true,
    "mode": "online"
  },
  "timestamp": 1712000000000
}
```

## 3. 拍照接口

```http
POST /api/v1/agv/photo
```

请求：

```json
{
  "sn": "AMR150-20260001",
  "timestamp": 1712000000000,
  "data": {
    "imagePath": "data/photo/p01.jpg"
  }
}
```

说明：后端传入希望保存的图片路径，视觉在线调用相机拍照，并保存到该路径。

返回：

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "imagePath": "data/photo/p01.jpg"
  },
  "timestamp": 1712000000000
}
```

## 4. 手眼标定接口

接口文档写的是：

```http
POST /api/v1/avg/eye_hand
```

代码中同时兼容下面两个地址：

```http
POST /api/v1/avg/eye_hand
POST /api/v1/agv/eye_hand
```

推荐一次性传 9 张图片和 9 个机器人位姿：

```json
{
  "sn": "AMR150-20260001",
  "timestamp": 1712000000000,
  "imagePointList": [
    {
      "imagePath": "data/photo/p01.jpg",
      "x": 200.0,
      "y": 170.0,
      "z": 0.0,
      "rx": 0.0,
      "ry": 0.0,
      "rz": 0.0
    },
    {
      "imagePath": "data/photo/p02.jpg",
      "x": 200.0,
      "y": 150.0,
      "z": 0.0,
      "rx": 0.0,
      "ry": 0.0,
      "rz": 0.0
    }
  ]
}
```

说明：当前视觉算法是 2D 平面手眼标定，真正参与计算的是 `imagePath`、`x`、`y`。`z/rx/ry/rz` 会保存在扩展信息里，但不参与当前 2D 仿射矩阵求解。

返回：

```json
{
  "code": 0,
  "msg": "任务已接收",
  "data": {
    "x": 100.0,
    "y": 80.0,
    "z": 0.0,
    "rx": 0.0,
    "ry": 0.0,
    "rz": 0.0,
    "matrix2x3": [[0.1, 0.0, 100.0], [0.0, 0.1, 80.0]],
    "rmse_m": 0.0001,
    "sample_count": 9
  },
  "timestamp": 1712000000000
}
```

## 5. 跨机台标定接口

```http
POST /api/v1/agv/cross_calibration
```

请求：

```json
{
  "sn": "station_001",
  "timestamp": 1712000000000,
  "data": {
    "x": 0.0,
    "y": 0.0,
    "z": 0.0,
    "rx": 0.0,
    "ry": 0.0,
    "rz": 0.0
  }
}
```

说明：视觉会在线拍摄当前 ArUco 标记板，并将其保存为该 `sn` 对应的工位基准。

## 6. 二次补偿接口

```http
POST /api/v1/agv/secondary_compensation
```

请求：

```json
{
  "sn": "station_001",
  "timestamp": 1712000000000,
  "data": {
    "x": 0.0,
    "y": 0.0,
    "z": 0.0,
    "rx": 0.0,
    "ry": 0.0,
    "rz": 0.0
  }
}
```

返回：

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "dx": 1.57,
    "dy": 1.57,
    "dtheta": 0.5,
    "unit": "m_robot"
  },
  "timestamp": 1712000000000
}
```

## 7. Java 调用示例

```java
RestTemplate restTemplate = new RestTemplate();
String baseUrl = "http://192.168.1.100:8088";

Map<String, Object> req = new HashMap<>();
req.put("sn", "AMR150-20260001");
req.put("timestamp", System.currentTimeMillis());

Map<String, Object> data = new HashMap<>();
data.put("imagePath", "data/photo/p01.jpg");
req.put("data", data);

String resp = restTemplate.postForObject(
    baseUrl + "/api/v1/agv/photo",
    req,
    String.class
);
System.out.println(resp);
```
