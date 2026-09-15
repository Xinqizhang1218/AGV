from __future__ import annotations  # 启用未来版本类型注解语法

import cv2  # 导入 OpenCV


def get_aruco_dictionary(name: str):  # 根据名称获取 OpenCV 内置 ArUco 字典
    if not hasattr(cv2, 'aruco'):  # 如果当前 OpenCV 没有 aruco 模块
        raise RuntimeError('当前 OpenCV 未安装 aruco 模块，请安装 opencv-contrib-python')  # 报错提示安装扩展版 OpenCV

    aruco = cv2.aruco  # 获取 aruco 模块对象

    if not hasattr(aruco, name):  # 如果指定字典名称不存在
        raise ValueError(f'不支持的 aruco 字典: {name}')  # 报错提示字典不支持

    return aruco.getPredefinedDictionary(getattr(aruco, name))  
    # 返回预定义字典对象，例如 DICT_4X4_50
