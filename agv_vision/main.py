from __future__ import annotations  # 启用未来版本类型注解语法，支持更灵活的类型提示写法

import argparse  # 导入命令行参数解析模块
import os  # 导入 os，用于向 FastAPI 服务传递配置文件路径
import json  # 导入 JSON 模块，用于读取和打印 JSON 数据
from pathlib import Path  # 导入 Path，用于处理文件路径
import uvicorn  # 导入 uvicorn，用于启动 FastAPI 服务

from agv_vision.config.settings import AppSettings  # 导入配置类
from agv_vision.core.service import AGVVisionService  # 导入 AGV 视觉主服务类
from agv_vision.utils.logging_utils import setup_logging  # 导入日志初始化函数
from agv_vision.backends.mock_backend import MockBackend  # 导入模拟后端，用于本地保存数据


def build_parser() -> argparse.ArgumentParser:  # 定义命令行参数解析器构建函数
    parser = argparse.ArgumentParser(description='AGV Vision Package')  # 创建参数解析器对象，并设置程序说明
    parser.add_argument('--config', default='agv_vision/config/settings.yaml', help='配置文件路径')  # 添加全局参数 --config，指定配置文件路径
    sub = parser.add_subparsers(dest='cmd', required=True)  # 创建子命令解析器，命令名保存到 cmd 字段，且子命令必填
    sub.add_parser('serve', help='启动 HTTP 服务')  # 添加 serve 子命令，用于启动 HTTP 服务
    sub.add_parser('capture', help='单次采图')  # 添加 capture 子命令，用于执行单次拍照

    handeye_sample = sub.add_parser('capture-handeye-sample', help='采集手眼样本')  # 添加采集手眼样本子命令
    handeye_sample.add_argument('--sample-id', required=True)  # 添加参数 --sample-id，样本编号，必填
    handeye_sample.add_argument('--robot-x-m', type=float, required=True)  # 添加参数 --robot-x-m，机器人 X 坐标，浮点数，必填
    handeye_sample.add_argument('--robot-y-m', type=float, required=True)  # 添加参数 --robot-y-m，机器人 Y 坐标，浮点数，必填
    handeye_sample.add_argument('--scenario', default=None)  # 添加参数 --scenario，可选，用于离线模式切换场景

    handeye_solve = sub.add_parser('solve-handeye', help='根据样本 JSON 列表求解手眼标定')  # 添加手眼标定求解子命令
    handeye_solve.add_argument('--camera-id', default='default_camera')  # 添加参数 --camera-id，相机编号，默认 default_camera
    handeye_solve.add_argument('--samples-json', required=True, help='样本列表 json 文件路径')  # 添加参数 --samples-json，样本 JSON 文件路径，必填
    handeye_batch = sub.add_parser('batch-capture-handeye', help='批量采集离线手眼样本')
    handeye_batch.add_argument('--image-dir', required=True, help='手眼图片目录')
    handeye_batch.add_argument('--poses-json', required=True, help='图片与机器人坐标对应表 JSON')
    handeye_batch.add_argument('--output-json', required=True, help='输出样本 JSON 文件')


    ref = sub.add_parser('collect-reference', help='采集机台基准')  # 添加机台基准采集子命令
    ref.add_argument('--station-id', required=True)  # 添加参数 --station-id，工位编号，必填
    ref.add_argument('--scenario', default=None)  # 添加参数 --scenario，可选，用于离线模式切换场景

    comp = sub.add_parser('compensate', help='做二次补偿')  # 添加补偿计算子命令
    comp.add_argument('--station-id', required=True)  # 添加参数 --station-id，工位编号，必填
    comp.add_argument('--camera-id', default='default_camera')  # 添加参数 --camera-id，相机编号，默认 default_camera
    comp.add_argument('--task-id', default='task_local')  # 添加参数 --task-id，任务编号，默认 task_local
    comp.add_argument('--scenario', default=None)  # 添加参数 --scenario，可选，用于离线模式切换场景

    return parser  # 返回构建好的参数解析器


def main() -> None:  # 定义主函数
    parser = build_parser()  # 构建命令行参数解析器
    args = parser.parse_args()  # 解析命令行参数
    settings = AppSettings.from_yaml(args.config)  # 从配置文件中读取配置
    logger = setup_logging(settings.debug.log_dir)  # 初始化日志系统

    if args.cmd == 'serve':  # 如果子命令是 serve
        # 关键修改：把命令行传入的 --config 传给 agv_vision.api.app。
        # 否则 FastAPI app 导入时会固定读取默认 settings.yaml，导致 settings_online.yaml 不生效。
        os.environ['AGV_VISION_CONFIG'] = str(Path(args.config).resolve())
        uvicorn.run('agv_vision.api.app:app', host=settings.service.host, port=settings.service.port, reload=False)  # 启动 FastAPI 服务
        return  # 启动服务后直接返回，不再执行后续逻辑

    service = AGVVisionService(settings, logger)  # 创建 AGV 视觉服务对象
    backend = MockBackend()  # 创建模拟后端对象
    try:  # 开始 try-finally，确保最后能关闭资源
        service.open()  # 打开图像源或初始化服务
        if args.cmd == 'capture':  # 如果子命令是 capture
            print(json.dumps(service.capture_once(), ensure_ascii=False, indent=2))  # 执行一次拍照并打印 JSON 结果
        elif args.cmd == 'capture-handeye-sample':  # 如果子命令是采集手眼样本
            if args.scenario:  # 如果传入了离线场景参数
                service.set_offline_scenario(args.scenario)  # 切换离线场景
            print(json.dumps(service.capture_handeye_sample(args.sample_id, args.robot_x_m, args.robot_y_m), ensure_ascii=False, indent=2))  # 采集手眼样本并打印结果
        elif args.cmd == 'batch-capture-handeye':
            poses = json.loads(Path(args.poses_json).read_text(encoding='utf-8'))
            payload = service.batch_capture_handeye_samples(
                image_dir=args.image_dir,
                poses_payload=poses,
                output_json=args.output_json,
            )
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        elif args.cmd == 'solve-handeye':  # 如果子命令是手眼标定求解
            samples = json.loads(Path(args.samples_json).read_text(encoding='utf-8'))  # 读取样本 JSON 文件并解析为 Python 对象
            payload = service.solve_handeye(samples)  # 调用服务求解手眼标定
            print(json.dumps(payload, ensure_ascii=False, indent=2))  # 打印手眼标定结果
            print(json.dumps(backend.save_handeye(args.camera_id, payload), ensure_ascii=False, indent=2))  # 把标定结果保存到模拟后端并打印保存结果
        elif args.cmd == 'collect-reference':  # 如果子命令是采集工位基准
            if args.scenario:  # 如果传入了离线场景参数
                service.set_offline_scenario(args.scenario)  # 切换离线场景
            payload = service.collect_station_reference(args.station_id)  # 采集工位基准
            print(json.dumps(payload, ensure_ascii=False, indent=2))  # 打印采集结果
            print(json.dumps(backend.save_reference(args.station_id, payload), ensure_ascii=False, indent=2))  # 把工位基准保存到模拟后端并打印保存结果
        elif args.cmd == 'compensate':  # 如果子命令是补偿计算
            if args.scenario:  # 如果传入了离线场景参数
                service.set_offline_scenario(args.scenario)  # 切换离线场景
            ref_payload = backend.get_reference(args.station_id)  # 从模拟后端读取该工位的参考基准数据
            handeye_payload = backend.get_handeye(args.camera_id)  # 从模拟后端读取该相机的手眼标定数据
            payload = service.compensate(ref_payload, handeye_payload)  # 根据参考数据和当前数据计算补偿结果
            print(json.dumps(payload, ensure_ascii=False, indent=2))  # 打印补偿结果
            print(json.dumps(backend.report_compensation(args.task_id, payload), ensure_ascii=False, indent=2))  # 把补偿结果保存到模拟后端并打印保存结果
    finally:  # 无论前面是否报错，最后都会执行
        service.close()  # 关闭图像源，释放资源


if __name__ == '__main__':  # 如果当前文件是直接运行，而不是被导入
    main()  # 执行主函数