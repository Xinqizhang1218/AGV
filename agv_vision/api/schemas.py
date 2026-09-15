from __future__ import annotations  # 启用未来版本类型注解语法，支持 str | None 等写法

from pydantic import BaseModel, Field  # 导入 Pydantic 数据模型基类和字段定义工具


# -------------------- 工位基准点采集请求模型 --------------------
class ReferenceRequest(BaseModel):  # 定义请求数据结构，继承 BaseModel
    station_id: str  # 工位编号，例如 station_001


# -------------------- 手眼标定采样请求模型 --------------------
class HandEyeSampleCaptureRequest(BaseModel):
    sample_id: str          # 当前采样点编号，例如 sample_01
    robot_x_m: float       # 当前机器人 X 坐标（单位 m）
    robot_y_m: float       # 当前机器人 Y 坐标（单位 m）

    # 离线测试场景名称，可为空
    offline_scenario: str | None = None


# -------------------- 手眼标定求解请求模型 --------------------
class HandEyeSolveRequest(BaseModel):

    # 相机编号，默认使用 default_camera
    camera_id: str = 'default_camera'

    # 标定样本数据列表
    # 每一项通常包含机器人坐标 + 图像坐标
    samples: list[dict]


# -------------------- 偏移补偿请求模型 --------------------
class CompensateRequest(BaseModel):

    # 工位编号（用于读取基准点）
    station_id: str | None = None

    # 当前任务编号（用于结果回传）
    task_id: str | None = None

    # 前端直接传入的基准点数据（可选）
    reference_payload: dict | None = None

    # 前端直接传入的手眼标定参数（可选）
    handeye_payload: dict | None = None

    # 相机编号，默认值
    camera_id: str = 'default_camera'

    # 离线测试场景名称（可选）
    offline_scenario: str | None = None


# -------------------- 离线场景切换请求模型 --------------------
class ScenarioRequest(BaseModel):

    # 场景名称，例如 left_box / right_box / station_a
    scenario: str