# Nodka 光源控制（NKIOSDK Linux V5.0.4）

已提供 Python 控制类、独立开灯命令，以及 AGVVisionService 拍照接入。
默认禁用；未填写设备参数时不会操作光源。硬件只在 `open()` 时连接。

## 接线与适用范围

- 面向 SDK 支持的 Nodka 光源控制器/内置光源接口，使用 NKLC 软件开关模式 0。
- 如果灯实际接在普通 DO 或外置控制器上，不适用本模块。
- 确认工控机/板卡型号、Linux 架构、实际串口、灯路，再选 SDK 配置文件。
- `channel_mask` 只允许单路：CH0=1、CH1=2、CH2=4、CH3=8。
- 亮度为 0～100；`settle_ms` 为毫秒，100 只是可调整的起始值。
- 手册写 COM3 在 Linux 映射 `/dev/ttyS2`、参数填 2；部分示例/INI 写 3。
  **必须在目标机器确认，不能照抄 2 或 3，也不能只按 Windows COM 编号填写。**

## Linux 准备与编译

SDK 原目录在开发机：
`D:\sdk\ndj\NKIOSDK_Linux_V5.0.4\NKIOSDK_Linux_V5.0.4\LinuxSDK`。
将 LinuxSDK 复制到目标 Linux，例如 `/opt/nodka/LinuxSDK`。
在项目根目录运行以下命令，SDK 路径和 GCC 目录按实际修改：

```bash
bash native/build_nodka_light.sh /opt/nodka/LinuxSDK GCC_9.4.0
mkdir -p third_party/nodka/config
# 从 ConfigFile 中挑选与实机型号相符的配置，替换下面的占位路径
cp /opt/nodka/LinuxSDK/ConfigFile/<平台>/<实际型号>/nkio_config.ini \
  third_party/nodka/config/nkio_config.ini
```

编译需要 g++ 和对应 SDK 库。脚本生成：

```text
third_party/nodka/lib/libNKLCLIB.so
third_party/nodka/lib/libagv_nodka_light.so
third_party/nodka/config/nkio_config.ini
```

桥接层用原厂 `NKLCLIB.h` 编译，在 C++ 内部接收按值传递的联合体回调，
Python 只读取固定布局结构体，避免依赖 ctypes 对联合体回调的 ABI 支持。
库采用同目录 `$ORIGIN` 搜索路径。检查脚本输出的 `ldd`，不能有 `not found`；
用 `file` 核对库和目标系统架构。GCC 目录名称不能替代实际 ABI/依赖验证。
SDK 二进制和实机 INI 被 Git 忽略，需单独部署。

厂商 Sample/ReadMe.txt 要求 root 权限。先在目标机按厂商要求验证，
服务账户的串口及其他资源权限需要现场确定。不要同时运行厂商测试工具与本程序。

## 独立 Python 开灯

下面仅举例：假设已经确认 Linux SDK 端口为 2，光源接 CH0。
在项目根目录、项目 Python 环境下运行：

```bash
python -m agv_vision.core.nodka_light \
  --library third_party/nodka/lib/libagv_nodka_light.so \
  --config third_party/nodka/config/nkio_config.ini \
  --port 2 --channel-mask 0x01 --brightness 50 --seconds 3
```

行为：初始化 → 连接 → 确认关灯 → 开灯并读回 → 保持 3 秒 → 关灯并释放。
正常退出、Python 异常和 Ctrl+C 会执行清理；断电、强杀进程、通信中断无法保证关灯，
需要现场处理。参数读回只证明控制器报告的状态，不证明灯实际发光。

也可在自己的 Python 代码里调用：

```python
import time
from agv_vision.core.nodka_light import NodkaLight

light = NodkaLight(
    library_path='third_party/nodka/lib/libagv_nodka_light.so',
    config_path='third_party/nodka/config/nkio_config.ini',
    port=2,             # 替换为实机确认值
    channel_mask=0x01, # 替换为实际接线通道
    brightness=50,
)
try:
    light.open()
    light.turn_on()
    time.sleep(0.1)
    # 在这里触发相机曝光并等待新图像返回
finally:
    light.close()      # 内含关灯、关闭串口、释放 SDK
```

模块固定使用模式 0，通过 on/off 控制亮灭。不是模式 3 的控制器定时脉冲；
CLI 的 `--seconds` 是 Python 计时，不修改控制器保持时间单位。

## 接入服务拍照

把 `config_examples/nodka_light.yaml` 的 `light` 块合并进实际启动使用的 YAML。
确认硬件后填写 `port`、`channel_mask`，将 `enabled` 改为 true。
同一 YAML 的相机配置要求：

```yaml
camera:
  vendor: hikvision
  auto_exposure: false
  exposure: 10000 # 示例：MVS 微秒；按现场图像调整
```

保留原有 camera 其他字段，只修改上述字段，不要用示例覆盖整个配置。
库/INI 相对路径以进程工作目录为准；systemd 可设置项目 WorkingDirectory，
或把路径改成 Linux 绝对路径。重启服务生效。

启用后所有通过 AGVVisionService 图像源拍照的路径使用同一事务锁：

1. 开灯，检查 SDK 返回值、执行回调及参数读回。
2. 等待 `settle_ms`。
3. 海康清理旧图像缓冲，发送 `TriggerSoftware`，等待图像返回。
4. 关灯并读回确认，再向调用方交付图像。

海康使用软件触发模式、固定曝光；关键设置或清缓冲不支持会报错，
不会悄悄回退连续取流。取图/光源控制失败会锁定此拍照源，
阻止继续曝光；检查设备后关闭并重新打开服务（通常重启）。
不会自动重试失败曝光或开灯指令。异常清理中的关灯失败会记录日志；
正常取图后的关灯失败会直接返回错误。

离线模式不连接光源；未启用 light 时保持原有连续取流行为。
Java API 字段、手眼变换和机台基准未改变。
独立 `tools/aubo_hik_capture*.py` 直接使用相机，未接此服务包装器；
如使用这些脚本，需调用上面的 NodkaLight 类并覆盖实际曝光区间。

## 部署与验证边界

- 必须同时部署 Python 修改、原厂库、编译后的桥接库、匹配型号的 INI、YAML 参数。
- MVS 的 Linux 运行库、Python MvImport 路径、软件触发和 ClearImageBuffer 支持需实机验证。
- 一台控制器只由一个服务进程持有，使用一个 API worker；不要并行启动独立测试命令。
- 如用 Docker，在容器兼容环境编译桥接库并检查依赖；映射实际串口设备、SDK/INI 路径及权限。
  当前 Compose 未自动新增这些映射，现有镜像也不因此自动具备完整 MVS/NKLC 环境。
- 使用非 Async 接口，执行时间受厂商 SDK 串口超时约束；Python 未声称可强制中断阻塞的 SDK 调用。
- `NKLC_SetPwmParams` 手册说明参数会保存到控制器；高频运行前向厂商确认保存介质/写入寿命。

离线验证命令：

```bash
python -m unittest discover -s tests -p test_nodka_light.py -v
```

测试覆盖模拟 SDK 错误/回调缺失/读回不一致、资源清理、互斥拍照、
取图失败关灯、故障后拒绝重拍、海康清缓冲与触发顺序、默认禁用及离线隔离。
这不替代 Linux 桥接库编译、原厂 SDK ABI、实际串口、灯亮灭和相机曝光的联调。
