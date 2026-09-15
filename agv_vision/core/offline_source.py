from __future__ import annotations  # 启用未来版本类型注解语法

from pathlib import Path  # 导入路径处理模块
import cv2  # 导入 OpenCV，用于读取图片

from agv_vision.core.frame_source import BaseFrameSource  # 导入图像源抽象基类
from agv_vision.core.models import FrameBundle  # 导入图像帧数据结构
from agv_vision.core.exceptions import SourceError  # 导入图像源异常类


# =====================================================
# 离线图片输入源
# 用本地文件夹图片模拟真实相机取图
# =====================================================
class OfflineImageSource(BaseFrameSource):

    # -------------------------------------------------
    # 初始化
    # -------------------------------------------------
    def __init__(
        self,
        image_dir: str,                        # 图片目录
        loop: bool = True,                    # 是否循环读取
        supported_suffixes: list[str] | None = None  # 支持格式
    ):

        self.image_dir = Path(image_dir)  # 转成路径对象

        self.loop = loop  # 是否循环

        # 默认支持图片格式
        self.supported_suffixes = supported_suffixes or [
            '.jpg',
            '.jpeg',
            '.png',
            '.bmp'
        ]

        self.files: list[Path] = []  # 图片列表

        self.index = 0  # 当前读取位置


    # -------------------------------------------------
    # 打开图片目录
    # -------------------------------------------------
    def open(self) -> None:

        # 判断目录是否存在
        if not self.image_dir.exists():
            raise SourceError(f'离线图片目录不存在: {self.image_dir}')

        # 获取所有支持格式的图片文件
        self.files = sorted(
            [
                p for p in self.image_dir.iterdir()
                if p.suffix.lower() in self.supported_suffixes
            ]
        )

        # 如果目录中没有图片
        if not self.files:
            raise SourceError(f'离线图片目录中没有可用图片: {self.image_dir}')

        # 从第一张开始读取
        self.index = 0


    # -------------------------------------------------
    # 获取一张图片（模拟相机取图）
    # -------------------------------------------------
    def grab(self) -> FrameBundle:

        # 如果未执行 open()
        if not self.files:
            raise SourceError('离线图片源尚未打开')

        # 如果读取到末尾
        if self.index >= len(self.files):

            # 如果允许循环
            if self.loop:
                self.index = 0

            # 不允许循环则报错
            else:
                raise SourceError('离线图片已读取完毕')

        # 当前图片路径
        path = self.files[self.index]

        # 索引 +1
        self.index += 1

        # 使用 OpenCV 读取图片
        from agv_vision.core.image_io import read_image
        image = read_image(path)

        # 图片读取失败
        if image is None:
            raise SourceError(f'读取图片失败: {path}')

        # 返回统一图像数据结构
        return FrameBundle(
            color=image,  # 彩图

            meta={
                'source': 'offline',          # 来源：离线图片
                'image_path': str(path),     # 文件路径
                'index': self.index - 1      # 当前序号
            }
        )


    # -------------------------------------------------
    # 关闭资源
    # -------------------------------------------------
    def close(self) -> None:
        """
        离线图片源无需释放资源
        保留该函数用于统一接口结构
        """
        pass
