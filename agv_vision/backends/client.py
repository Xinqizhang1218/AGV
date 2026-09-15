from __future__ import annotations  # 启用未来版本类型注解语法，支持 dict | None 写法

import requests  # 导入 requests，用于发送 HTTP 请求


# -------------------- 后端接口客户端 --------------------
class BackendClient:
    """
    用于和业务后端系统通信
    例如：
    - 保存工位基准点
    - 获取工位基准点
    - 保存手眼标定参数
    - 获取手眼标定参数
    - 回传补偿结果
    """

    # -------------------- 初始化 --------------------
    def __init__(self, base_url: str, timeout_sec: float = 5.0):
        self.base_url = base_url.rstrip('/')  # 去掉结尾的 /
        self.timeout_sec = timeout_sec        # 请求超时时间（秒）

    # -------------------- 保存工位基准点 --------------------
    def save_reference(self, station_id: str, payload: dict) -> dict:
        """
        向后端保存某工位的视觉基准点数据
        """

        # 发送 POST 请求
        r = requests.post(
            f'{self.base_url}/stations/{station_id}/reference',
            json=payload,
            timeout=self.timeout_sec
        )

        r.raise_for_status()  # 如果失败（如404/500）直接报错

        return r.json()  # 返回后端 JSON 数据

    # -------------------- 获取工位基准点 --------------------
    def get_reference(self, station_id: str) -> dict:
        """
        从后端读取某工位的视觉基准点数据
        """

        # 发送 GET 请求
        r = requests.get(
            f'{self.base_url}/stations/{station_id}/reference',
            timeout=self.timeout_sec
        )

        r.raise_for_status()  # 状态异常时报错

        return r.json()  # 返回 JSON 数据

    # -------------------- 保存手眼标定结果 --------------------
    def save_handeye(self, camera_id: str, payload: dict) -> dict:
        """
        保存某相机的手眼标定参数
        """

        # 发送 POST 请求
        r = requests.post(
            f'{self.base_url}/calibration/handeye/{camera_id}',
            json=payload,
            timeout=self.timeout_sec
        )

        r.raise_for_status()  # 请求失败时报错

        return r.json()

    # -------------------- 获取手眼标定结果 --------------------
    def get_handeye(self, camera_id: str) -> dict | None:
        """
        获取某相机的手眼标定参数
        若不存在则返回 None
        """

        # 发送 GET 请求
        r = requests.get(
            f'{self.base_url}/calibration/handeye/{camera_id}',
            timeout=self.timeout_sec
        )

        # 如果后端返回 404，表示没有数据
        if r.status_code == 404:
            return None

        r.raise_for_status()  # 其他异常状态直接报错

        return r.json()

    # -------------------- 回传补偿结果 --------------------
    def report_compensation(self, task_id: str, payload: dict) -> dict:
        """
        将补偿结果回传给任务系统
        """

        # 发送 POST 请求
        r = requests.post(
            f'{self.base_url}/tasks/{task_id}/compensation',
            json=payload,
            timeout=self.timeout_sec
        )

        r.raise_for_status()  # 请求失败时报错

        return r.json()  # 返回后端响应结果