# Docker 部署与开机启动

## 1. 手动一键启动

在项目根目录双击：

`start_docker.bat`

它会执行：

`docker compose up -d --build`

服务启动后地址（默认离线配置）：

`http://127.0.0.1:8010`

Linux 在线模式一键启动脚本：

```bash
chmod +x ./start_docker_online.sh
./start_docker_online.sh
```

在线模式地址：

`http://127.0.0.1:8088`

## 2. 开机自动启动（一次安装）

以管理员 PowerShell 执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\install_startup_task.ps1
```

安装后会创建计划任务 `AGVVisionDockerAutoStart`，每次 Windows 开机自动运行 `start_docker.bat`。

## 3. 取消开机自动启动

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall_startup_task.ps1
```

## 4. 常用运维命令

启动/更新：

```powershell
docker compose up -d --build
```

在线模式启动/更新：

```bash
docker compose -f docker-compose.online.yml up -d --build
```

在线模式停止：

```bash
docker compose -f docker-compose.online.yml down
```

停止：

```powershell
docker compose down
```

查看日志：

```powershell
docker compose logs -f
```

## 5. 目录挂载

`docker-compose.yml` 默认挂载（离线模式）：

- `./data -> /app/data`
- `./logs -> /app/logs`
- `./agv_vision/config/settings.yaml -> /app/agv_vision/config/settings.yaml`

如需改成在线模式（真实相机），需要你确认 Linux 容器中可用 `pyorbbecsdk2` 后，再把 compose 的配置文件切到 `settings_online.yaml`。

你也可以直接使用新增的 `docker-compose.online.yml`，它已经切到 `settings_online.yaml` 并映射 `8088` 端口。
