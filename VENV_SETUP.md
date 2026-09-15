# pkg3_260522 venv 环境配置说明

这份文档只针对 `pkg3_260522` 在线版。

建议现场统一用 Python venv，避免不同项目的 OpenCV、FastAPI、numpy 版本互相影响。

## 1. 准备 Python

先确认电脑已经安装 Python 3.10 或更高版本：

```powershell
python --version
```

推荐版本：

```text
Python 3.10 / 3.11 / 3.12
```

如果电脑里有多个 Python，可以用：

```powershell
py -0
```

查看已安装版本。

## 2. 进入 pkg3_260522 目录

```powershell
cd D:\code\AGV\pkg3_260522
```

后面的命令都在这个目录下执行。

## 3. 创建 venv

```powershell
python -m venv .venv
```

创建完成后，目录里会多一个：

```text
.venv
```

这个目录就是 pkg3 自己的 Python 环境。

## 4. 激活 venv

PowerShell 里执行：

```powershell
.\.venv\Scripts\Activate.ps1
```

激活成功后，终端前面一般会出现：

```text
(.venv)
```

例如：

```text
(.venv) PS D:\code\AGV\pkg3_260522>
```

如果 PowerShell 提示禁止运行脚本，可以先执行：

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

然后重新激活：

```powershell
.\.venv\Scripts\Activate.ps1
```

## 5. 升级 pip

```powershell
python -m pip install --upgrade pip
```

## 6. 安装依赖

```powershell
pip install -r requirements.txt
```

当前 `requirements.txt` 里的主要依赖是：

```text
fastapi
uvicorn
pydantic
pyyaml
requests
opencv-contrib-python
numpy
pyorbbecsdk2
```

注意：`opencv-contrib-python` 里包含 ArUco/ChArUco 相关模块，所以这里不要换成普通的 `opencv-python`。

## 7. 奥比中光 Python SDK

在线版代码里使用的是：

```python
from pyorbbecsdk2 import Context, Pipeline, Config, OBSensorType, OBFormat
```

现场使用的 pip 包名是：

```powershell
pyorbbecsdk2
```

它已经写进 `requirements.txt`。正常情况下执行下面命令时会一起安装：

```powershell
pip install -r requirements.txt
```

如果要单独安装：

```powershell
python -m pip install pyorbbecsdk2
```

安装完成后检查包是否装进当前环境：

```powershell
python -m pip show pyorbbecsdk2
```

再检查能不能 import：

```powershell
python -c "import pyorbbecsdk2; print('pyorbbecsdk2 ok')"
```

正常输出：

```text
pyorbbecsdk2 ok
```

如果这里安装失败，通常不是项目代码问题，而是当前电脑的 Python 版本、系统架构或 pip 源里没有匹配的 `pyorbbecsdk2` 安装包。现场建议优先使用 Python 3.10 或 3.11。

如果 pip 源下载慢，可以尝试：

```powershell
python -m pip install pyorbbecsdk2 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

注意：`pyorbbecsdk2` 是 Python SDK 包；相机底层驱动、USB/网口连接、设备权限这些仍然要在电脑系统层面正常。

### 7.1 另一台电脑重点确认：pip 和 python 必须是同一个 venv

在另一台电脑上，先进入项目并激活 venv：

```powershell
cd D:\code\AGV\pkg3_260522
.\.venv\Scripts\Activate.ps1
```

然后确认当前 Python 路径：

```powershell
where python
python -c "import sys; print(sys.executable)"
```

正常应该看到类似：

```text
D:\code\AGV\pkg3_260522\.venv\Scripts\python.exe
```

再用同一个 Python 安装奥比中光包：

```powershell
python -m pip install pyorbbecsdk2
```

不要只写：

```powershell
pip install pyorbbecsdk2
```

因为另一台电脑上 `pip` 可能指向系统 Python，不一定指向当前 `.venv`。

安装后检查：

```powershell
python -m pip show pyorbbecsdk2
python -c "from pyorbbecsdk2 import Context, Pipeline; print('orbbec sdk ok')"
```

如果 `pip show` 能看到包，但 `python -c` 仍然导入失败，说明可能是 Python 版本不匹配、系统缺 DLL，或者奥比中光 SDK 运行库没有装好。

## 8. 检查关键依赖

执行：

```powershell
python -c "import cv2; print(cv2.__version__); print(hasattr(cv2, 'aruco'))"
```

正常应该输出类似：

```text
4.10.0
True
```

如果第二行是 `False`，说明 OpenCV 装错了，需要重新安装 `opencv-contrib-python`。

再检查奥比中光 SDK：

```powershell
python -c "from pyorbbecsdk2 import Context, Pipeline; print('orbbec sdk ok')"
```

## 9. 编译检查

```powershell
python -m compileall agv_vision
```

如果没有报错，说明 Python 代码至少语法上是正常的。

## 10. 启动在线服务

在线版启动命令：

```powershell
python -m agv_vision.main --config agv_vision/config/settings_online.yaml serve
```

默认服务地址：

```text
http://127.0.0.1:8088
```

健康检查接口：

```text
GET http://127.0.0.1:8088/api/v1/health
```

## 11. 启动前重点检查配置

配置文件：

```text
agv_vision/config/settings_online.yaml
```

重点检查：

```yaml
camera:
  width: 1280
  height: 800
  fps: 15
  timeout_ms: 2000
  ip_address: 192.168.1.101
  control_port: 8090

charuco:
  square_length_m: 0.030
  marker_length_m: 0.021

aruco:
  marker_length_m: 0.150
```

单位：

- `width / height`：像素，单位 `px`。
- `fps`：帧率，单位 `frame/s`。
- `timeout_ms`：超时时间，单位 `ms`。
- `charuco.square_length_m`：ChArUco 格子边长，单位 `m`。
- `charuco.marker_length_m`：ChArUco 内部 marker 边长，单位 `m`。
- `aruco.marker_length_m`：跨机台/二次补偿用 ArUco 板真实有效边长，单位 `m`。15cm 就填 `0.150`。

## 12. 奥比中光相机说明

`requirements.txt` 里已经包含奥比中光在线相机 Python 包：

```powershell
pyorbbecsdk2
```

如果在线模式使用奥比中光相机，还需要电脑本身的相机驱动/连接正常，并且项目能正常 import `pyorbbecsdk2`。

如果启动时报相机 SDK 相关错误，优先检查：

- 相机驱动是否安装。
- 相机是否被其他程序占用。
- IP、端口、分辨率、帧率配置是否和现场相机一致。
- `Log/OrbbecSDK.log.txt` 里有没有 SDK 级别报错。

## 13. 每次重新打开终端怎么运行

重新打开 PowerShell 后，不需要重新创建 venv，只需要：

```powershell
cd D:\code\AGV\pkg3_260522
.\.venv\Scripts\Activate.ps1
python -m agv_vision.main --config agv_vision/config/settings_online.yaml serve
```

## 14. 退出 venv

```powershell
deactivate
```

## 15. 常见问题

### 15.1 找不到 agv_vision

现象：

```text
ModuleNotFoundError: No module named 'agv_vision'
```

原因通常是没有在 `pkg3_260522` 目录下启动。

请先执行：

```powershell
cd D:\code\AGV\pkg3_260522
```

再启动。

### 15.2 没有 cv2.aruco

现象：

```text
AttributeError: module 'cv2' has no attribute 'aruco'
```

处理：

```powershell
pip uninstall opencv-python opencv-contrib-python -y
pip install "opencv-contrib-python>=4.10,<5"
```

### 15.3 未安装 pyorbbecsdk2

现象：

```text
未安装或无法导入 pyorbbecsdk2，在线模式不可用
```

处理：

```powershell
python -m pip install pyorbbecsdk2
```

然后检查：

```powershell
python -m pip show pyorbbecsdk2
python -c "import pyorbbecsdk2; print('pyorbbecsdk2 ok')"
```

### 15.4 端口被占用

现象：

```text
Address already in use
```

说明 `8088` 端口已经有服务在运行。

可以先关闭旧服务，或者修改：

```text
agv_vision/config/settings_online.yaml
```

里的服务端口。

### 15.5 依赖安装很慢

可以使用国内镜像：

```powershell
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```
