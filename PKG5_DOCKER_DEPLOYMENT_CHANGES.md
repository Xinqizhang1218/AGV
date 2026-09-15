# PKG5 Docker 部署改动与交接说明

更新时间：2026-08-14

本文记录 PKG5 已验证可用的最终部署状态。后续上传、构建、启动和排查时，以本文中的名称和目录为准，避免与已停用的 PKG3 混淆。

## 1. 最终名称和目录

| 项目 | 最终值 | 说明 |
|---|---|---|
| 服务器 | `192.168.112.165` | SSH 用户：`root` |
| 上传压缩包 | `/home/projects/vision/pkg5_vision.zip` | Windows 原文件：`C:\Users\DELL\Desktop\pkg5_vision.zip` |
| 项目外层目录 | `/home/projects/vision/pkg5-vision` | 解压目标目录 |
| 实际工作目录 | `/home/projects/vision/pkg5-vision/pkg5_vision` | Compose 命令都在这里执行 |
| Compose 文件 | `docker-compose.online.yml` | 完整路径在实际工作目录下 |
| Compose 项目名 | `agv-pkg5` | 来自命令参数 `-p agv-pkg5` |
| Compose 服务名 | `agv-vision-pkg5-online` | `services` 下的名称 |
| 容器名 | `agv-vision-pkg5-online` | 来自 `container_name` |
| 镜像名 | `agv-pkg5-agv-vision-pkg5-online:latest` | Compose 自动生成，不是容器名 |
| Web 服务端口 | `8088` | 主机网络模式下直接监听服务器端口 |
| 相机地址 | `192.168.1.101:8090` | `8090` 是相机控制端口 |

名称关系：

```text
Compose 项目 agv-pkg5
└── 服务 agv-vision-pkg5-online
    ├── 容器 agv-vision-pkg5-online
    └── 镜像 agv-pkg5-agv-vision-pkg5-online:latest
```

## 2. 必须保留的 Compose 改动

本地 `docker-compose.online.yml` 已保存以下关键配置：

```yaml
services:
  agv-vision-pkg5-online:
    build:
      context: .
      dockerfile: Dockerfile

    container_name: agv-vision-pkg5-online
    restart: unless-stopped
    network_mode: host

    environment:
      TZ: Asia/Shanghai
      PYTHONUNBUFFERED: "1"

    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./outputs:/app/outputs
      - /home/projects:/home/projects:z
      - ./agv_vision/config/settings_online.yaml:/app/agv_vision/config/settings_online.yaml:ro

    command: >
      python -m agv_vision.main
      --config agv_vision/config/settings_online.yaml
      serve
```

关键规则：

- 必须保留 `network_mode: host`，否则 G335Le 网络相机不能稳定创建。
- 使用主机网络时不要再添加 `ports: - "8088:8088"`。
- `extra_hosts: host.docker.internal:host-gateway` 当前可以保留，但主机网络模式通常不需要它。
- `restart: unless-stopped` 配合已启用的 Docker 服务实现服务器重启后自动启动。

## 3. 挂载和图片保存

| 服务器目录 | 容器目录 | 用途 |
|---|---|---|
| `./data` | `/app/data` | 业务数据 |
| `./logs` | `/app/logs` | 服务日志 |
| `./outputs` | `/app/outputs` | 程序默认输出 |
| `/home/projects` | `/home/projects` | Java 与视觉服务共享绝对路径 |

Java 请求传入的路径为：

```text
/home/projects/images/photo/文件名.jpg
```

因为 `/home/projects:/home/projects:z` 是同路径读写挂载，容器保存后，文件会直接出现在服务器相同位置：

```text
/home/projects/images/photo/文件名.jpg
```

`:z` 用于兼容启用了 SELinux 的服务器。该挂载包含整个 `/home/projects` 且可写，因此接口必须限制可接受的保存路径，避免不可信请求写入任意位置。

前端通信配置：

```text
服务地址：http://192.168.112.165:8088
基础路径：/home/projects
```

“图片地址”若用于浏览器访问图片，应填写真正提供静态文件的 Nginx 或 Java 地址；磁盘路径本身不是 HTTP 地址，也不一定使用视觉服务的 `8088`。

## 4. 相机和 SDK 结论

已验证相机 `192.168.1.101:8090` 能 Ping 通且 TCP 端口开放。Docker 桥接网络曾报：

```text
G335Le device detected but not supported
```

PKG5 镜像切换为主机网络后成功识别：

```text
name= Orbbec Gemini 335Le
```

当前验证组合：

```text
pyorbbecsdk2 包版本：2.1.2
Orbbec SDK 运行库版本：2.9.3
```

PKG3 旧镜像为 `pyorbbecsdk2 2.1.1 / SDK 2.8.6`，当前测试相机时出现控制传输失败，因此不再作为 PKG5 运行镜像。

## 5. 已同步到本地源码的改动

为避免下次重新压缩上传后丢失服务器临时修改，本地项目已同步：

1. `requirements.docker.txt` 增加：

   ```text
   pyorbbecsdk2==2.1.2
   ```

2. `agv_vision/config/settings_online.yaml` 改为：

   ```yaml
   camera:
     intrinsics:
       enabled: false
   ```

3. `docker-compose.online.yml` 保留：

   ```yaml
   network_mode: host
   volumes:
     - ./outputs:/app/outputs
     - /home/projects:/home/projects:z
   ```

当前环境曾同时装有 `opencv-python` 和 `opencv-contrib-python`，二者可能覆盖相同模块。后续整理依赖时建议只保留项目实际需要的一种，但不要在生产运行正常时临时更换。

## 6. 首次上传和部署

Windows PowerShell：

```powershell
scp "C:\Users\DELL\Desktop\pkg5_vision.zip" root@192.168.112.165:/home/projects/vision/
```

服务器：

```bash
cd /home/projects/vision
unzip pkg5_vision.zip -d pkg5-vision
cd /home/projects/vision/pkg5-vision/pkg5_vision

docker compose -p agv-pkg5 \
  -f docker-compose.online.yml \
  config

docker compose -p agv-pkg5 \
  -f docker-compose.online.yml \
  build

docker compose -p agv-pkg5 \
  -f docker-compose.online.yml \
  up -d
```

若解压层级变化，先定位文件：

```bash
find /home/projects/vision/pkg5-vision -maxdepth 3 \
  \( -name Dockerfile -o -name docker-compose.online.yml \)
```

## 7. 日常操作

先进入工作目录：

```bash
cd /home/projects/vision/pkg5-vision/pkg5_vision
```

状态和日志：

```bash
docker compose -p agv-pkg5 -f docker-compose.online.yml ps -a
docker compose -p agv-pkg5 -f docker-compose.online.yml logs -f --tail=200
```

停止但不删除容器、再次启动、重启：

```bash
docker compose -p agv-pkg5 -f docker-compose.online.yml stop
docker compose -p agv-pkg5 -f docker-compose.online.yml start
docker compose -p agv-pkg5 -f docker-compose.online.yml restart
```

停止并删除容器，但保留镜像和挂载目录中的文件：

```bash
docker compose -p agv-pkg5 -f docker-compose.online.yml down
```

`down` 删除的是容器，不是镜像。容器只是镜像的运行实例。只要挂载正确，服务器上的 `data`、`logs`、`outputs` 和 `/home/projects/images` 不会被删除。

仅修改 Compose 挂载、环境变量或启动命令后，不需要重建镜像：

```bash
docker compose -p agv-pkg5 \
  -f docker-compose.online.yml \
  up -d --no-build
```

修改 Python 源码、Dockerfile 或依赖后：

```bash
docker compose -p agv-pkg5 -f docker-compose.online.yml down

docker compose -p agv-pkg5 \
  -f docker-compose.online.yml \
  build

docker compose -p agv-pkg5 \
  -f docker-compose.online.yml \
  up -d
```

## 8. 验证命令

```bash
cd /home/projects/vision/pkg5-vision/pkg5_vision

docker compose -p agv-pkg5 -f docker-compose.online.yml ps -a

docker inspect agv-vision-pkg5-online \
  --format '{{.HostConfig.NetworkMode}}'

docker inspect agv-vision-pkg5-online \
  --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}'

curl -v http://127.0.0.1:8088/
```

网络模式正确时应输出：

```text
host
```

日志出现以下内容表示服务已正常启动：

```text
AGV Vision Service started
Application startup complete
Uvicorn running on http://0.0.0.0:8088
```

拍照后检查最近生成文件：

```bash
find /home/projects/images -type f -mmin -5 -ls
```

## 9. 开机自启

当前条件已经满足：

```yaml
restart: unless-stopped
```

```text
systemctl is-enabled docker  -> enabled
systemctl is-active docker   -> active
```

服务器重启后，现有容器会随 Docker 自动启动。如果手工执行 `docker compose down`，容器已经被删除，不存在可自启对象，需要再次执行 `up -d`。

## 10. 更新前检查清单

- 当前目录必须是 `/home/projects/vision/pkg5-vision/pkg5_vision`。
- Compose 命令始终带 `-p agv-pkg5 -f docker-compose.online.yml`。
- 保留 `network_mode: host`，不要恢复 `ports: "8088:8088"`。
- 保留 `/home/projects:/home/projects:z` 和 `./outputs:/app/outputs`。
- `requirements.docker.txt` 包含 `pyorbbecsdk2==2.1.2`。
- `settings_online.yaml` 中 `camera.intrinsics.enabled` 为 `false`。
- 重建前确认服务器磁盘空间足够，并预留依赖下载时间。
- 生产图片必须写入挂载目录，不要只保存在容器内部。
