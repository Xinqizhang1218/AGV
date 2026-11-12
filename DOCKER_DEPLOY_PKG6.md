# 海康 + Nodka Linux Docker 部署

本仓库保留 pkg5 的业务代码，整合 pkg6 的 Docker 部署文件。在线服务名为
`agv-vision-pkg6-online`，Compose 项目名为 `agv-pkg6`，镜像名为
`agv-vision-pkg6:local`。目录不需要改名。

## 配置与行为

- 默认继续使用本仓库 `agv_vision/config/settings_online.yaml`，未覆盖为桌面版参数。
- 当前服务端口 8088，光源亮度 50，开灯等待 1000 ms。
- 手眼板方格/标记边长为 30/22 mm，工位板为 6/4 mm；必须与实物一致。
- 桌面包曾使用手眼板 12/8 mm、工位板 10/6.667 mm、亮度 100，这些不是通用默认值。
- 普通拍照流程为开灯、等待、取图、关灯；手动开灯保持期间，拍照校验灯状态并保留常亮。
- 光源接口为 POST `/api/v1/agv/light/control` 和 GET `/api/v1/agv/light/status`。
- 当前 `/health` 固定返回 `ok: true`，容器 healthy 只证明 HTTP 检查成功，不证明相机/光源可用。
- `restart: unless-stopped` 用于容器退出及重启恢复；unhealthy 本身不会触发自动重启。

## 首次配置

在 Linux 工控机项目根目录执行：

```bash
cp .env.example .env
```

编辑 `.env`，填入已验证的宿主机路径：

```dotenv
NODKA_SERIAL_DEVICE=/dev/ttyS2
MVS_RUNTIME_DIR=/opt/MVS/lib
```

这里的串口只是示例。SDK `light.port: 3` 不能直接换算成 `/dev/ttyS3`。
MVS 目录下须有 `64/libMvCameraControl.so` 及其依赖；仅有 `SDK/MvImport` 不够。
`.env` 不提交 Git；镜像外仍需携带 `.env`、Compose 文件、在线 YAML 和
`deploy/nkio_config.ini`，并在宿主机安装 MVS 运行库。

核对 YAML 的相机 IP、分辨率、曝光、板型，以及光源端口和通道。
默认使用 `deploy/nkio_config.ini` 挂载到容器内的
`/app/third_party/nodka/config/nkio_config.ini`。
不要用宿主机整个 `third_party/nodka/lib` 覆盖镜像内编译的库。

## 构建与离线搬运

镜像针对 Linux x86_64，使用 Python 3.10、Debian bookworm、headless OpenCV。
构建时需要下载基础镜像、系统依赖和 Python 包；不包含 Orbbec SDK。

```bash
docker compose -p agv-pkg6 -f docker-compose.online.yml config --quiet
docker compose -p agv-pkg6 -f docker-compose.online.yml build agv-vision-pkg6-online
docker save -o agv-vision-pkg6.tar agv-vision-pkg6:local
```

离线工控机导入镜像：

```bash
docker load -i agv-vision-pkg6.tar
docker image inspect agv-vision-pkg6:local
```

已有 tar 不会随源码修改自动更新。需要可复现的新版本时，重新构建并导出。

## 检查与启动

先执行不打开相机、不发光源指令的文件及动态库检查：

```bash
docker compose -p agv-pkg6 -f docker-compose.online.yml run --rm --no-deps --pull never agv-vision-pkg6-online python -m deploy.check_runtime
```

以下拍照命令会操作硬件。先停止实际占用相机、串口或 8088 端口的旧服务，
确认没有其他采集程序运行，再执行：

```bash
docker compose -p agv-pkg6 -f docker-compose.online.yml run --rm --no-deps --pull never agv-vision-pkg6-online python -m agv_vision.main --config agv_vision/config/settings_online.yaml capture
```

检查实际图片、灯亮灭和日志后，启动长期服务：

```bash
docker compose -p agv-pkg6 -f docker-compose.online.yml up -d --no-build --pull never agv-vision-pkg6-online
docker compose -p agv-pkg6 -f docker-compose.online.yml logs --tail=100 agv-vision-pkg6-online
```

`bash start_docker_online.sh build` 构建后启动；无参数时只使用已有镜像启动。
修改 Python、依赖或 Dockerfile 后需要重建/重新导入镜像并重建容器。
只改已挂载的 YAML 时可重启服务；改设备映射或 Compose 环境变量时需重新创建容器。
最后通过后端实际调用 `/api/v1/agv/photo` 验收，不能仅依据 `/health`。

`docker-compose.yml` 仍是离线入口，使用 `settings.yaml`，须自行提供离线图片。
本次本地静态检查不代表镜像构建、容器设备权限或现场拍照已经验证。
