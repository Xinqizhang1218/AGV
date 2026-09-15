from __future__ import annotations  # 启用未来版本类型注解语法，支持 dict | None 写法

from pathlib import Path  # 导入 Path，用于文件夹和文件路径处理
import json  # 导入 json，用于保存和读取 JSON 文件


# -------------------- 模拟后端类 --------------------
class MockBackend:
    """
    本地模拟后端系统（离线测试使用）

    用文件代替真实数据库 / HTTP接口：
    - stations/      保存工位基准点
    - calibration/  保存手眼标定结果
    - tasks/        保存任务补偿结果
    """

    # -------------------- 初始化 --------------------
    def __init__(self, root: str = 'data/mock_backend'):

        # 设置根目录
        self.root = Path(root)

        # 创建 stations 文件夹（保存工位基准点）
        (self.root / 'stations').mkdir(
            parents=True,      # 自动创建上级目录
            exist_ok=True      # 已存在不报错
        )

        # 创建 tasks 文件夹（保存任务补偿结果）
        (self.root / 'tasks').mkdir(
            parents=True,
            exist_ok=True
        )

        # 创建 calibration 文件夹（保存手眼标定）
        (self.root / 'calibration').mkdir(
            parents=True,
            exist_ok=True
        )

    # -------------------- 保存工位基准点 --------------------
    def save_reference(self, station_id: str, payload: dict) -> dict:
        """
        保存某工位基准点数据
        """

        # 生成保存路径
        path = self.root / 'stations' / f'{station_id}.json'

        # 写入 JSON 文件
        path.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,  # 保留中文
                indent=2             # 缩进格式化
            ),
            encoding='utf-8'
        )

        # 返回结果
        return {
            'ok': True,
            'path': str(path)
        }

    # -------------------- 获取工位基准点 --------------------
    def get_reference(self, station_id: str) -> dict:
        """
        读取某工位基准点数据
        """

        # 文件路径
        path = self.root / 'stations' / f'{station_id}.json'

        # 如果文件不存在
        if not path.exists():
            raise FileNotFoundError(f'机台基准不存在: {station_id}')

        # 读取并返回 JSON 内容
        return json.loads(
            path.read_text(encoding='utf-8')
        )

    # -------------------- 保存手眼标定参数 --------------------
    def save_handeye(self, camera_id: str, payload: dict) -> dict:
        """
        保存相机手眼标定参数
        """

        # 文件路径
        path = self.root / 'calibration' / f'{camera_id}_handeye.json'

        # 写入文件
        path.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2
            ),
            encoding='utf-8'
        )

        return {
            'ok': True,
            'path': str(path)
        }

    # -------------------- 获取手眼标定参数 --------------------
    def get_handeye(self, camera_id: str) -> dict | None:
        """
        读取手眼标定参数
        若不存在返回 None
        """

        # 文件路径
        path = self.root / 'calibration' / f'{camera_id}_handeye.json'

        # 如果文件不存在
        if not path.exists():
            return None

        # 读取 JSON 内容
        return json.loads(
            path.read_text(encoding='utf-8')
        )

    # -------------------- 保存补偿结果 --------------------
    def report_compensation(self, task_id: str, payload: dict) -> dict:
        """
        保存某任务补偿结果
        """

        # 文件路径
        path = self.root / 'tasks' / f'{task_id}_compensation.json'

        # 写入 JSON 文件
        path.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2
            ),
            encoding='utf-8'
        )

        return {
            'ok': True,
            'path': str(path)
        }