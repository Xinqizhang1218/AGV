"""生成/完善《标定版拍照要求》Word 文档。"""
from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


SRC_DOCX = Path(r'C:\Users\Dell\Desktop\项目资料\01_AGV项目\标定版拍照要求.docx')
IMAGE1 = Path(r'd:\code\AGV\pkg3_260522\data\_docx_extract\image1.png')
IMAGE2 = Path(r'd:\code\AGV\pkg3_260522\data\_docx_extract\image2.png')
BACKUP = SRC_DOCX.with_name(SRC_DOCX.stem + '_备份.docx')


def set_doc_font(doc: Document) -> None:
    style = doc.styles['Normal']
    style.font.name = '宋体'
    style.font.size = Pt(11)
    style._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')


def add_title(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(18)
    run.font.name = '黑体'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')


def add_heading(doc: Document, text: str, level: int = 1) -> None:
    doc.add_heading(text, level=level)


def add_bullets(doc: Document, items: list[str]) -> None:
    for item in items:
        doc.add_paragraph(item, style='List Bullet')


def add_numbered(doc: Document, items: list[str]) -> None:
    for item in items:
        doc.add_paragraph(item, style='List Number')


def add_table(doc: Document, headers: list[str], rows: list[list[str]]) -> None:
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = 'Table Grid'
    hdr = table.rows[0].cells
    for i, header in enumerate(headers):
        hdr[i].text = header
        for p in hdr[i].paragraphs:
            for run in p.runs:
                run.bold = True
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            cells[i].text = value


def build_document() -> Document:
    doc = Document()
    set_doc_font(doc)

    add_title(doc, 'AGV 视觉标定版拍照要求')
    doc.add_paragraph(f'文档版本：V1.0    更新日期：{date.today():%Y-%m-%d}')
    doc.add_paragraph(
        '本文档用于指导现场进行手眼标定、跨机台基准采集和二次补偿时的标定板拍照。'
        '拍照质量直接影响标定精度和后续补偿结果。'
    )

    add_heading(doc, '一、标定板类型说明', 1)
    doc.add_paragraph('现场使用两类标定板，用途不同，不可混用：')
    add_table(
        doc,
        ['标定板', '用途', '视觉算法参数'],
        [
            ['ChArUco 棋盘标定板（手眼板）', '手眼标定，建立图像坐标与机器人坐标关系', 'DICT_4X4_50，5×5 格，方格 30 m，码块 18 m'],
            ['ArUco 单码板（工位板）', '跨机台基准采集、二次补偿定位', 'DICT_5X5_50，ID=0，有效边长 150 m（15 cm）'],
        ],
    )

    add_heading(doc, '二、通用拍照要求', 1)
    add_bullets(
        doc,
        [
            '机器人/AGV 到位后必须完全停稳，再触发拍照，避免运动模糊。',
            '拍照高度、相机焦距、曝光参数在整个标定和补偿流程中保持一致，不得中途调整。',
            '标定板表面平整，无折痕、污渍、反光遮挡；板面与相机光轴尽量垂直。',
            '标定板完整出现在画面内，四周至少留 10% 以上边距，不要被机械结构遮挡。',
            '光照均匀，避免强逆光、局部过曝或大面积阴影；金属台面反光时建议加柔光或调整角度。',
            '一次只拍一张，拍完后由 Java 后端记录对应机器人位姿（x/y/z/rx/ry/rz）。',
            '相机分辨率按现场配置：1280×800，格式 MJPG。',
        ],
    )

    add_heading(doc, '三、手眼标定板（ChArUco）拍照要求', 1)
    doc.add_paragraph('现场手眼标定板规格：约 20 cm × 20 cm（5×5 格，单格边长约 30 m）。')
    if IMAGE1.exists():
        doc.add_paragraph('参考示意图（手眼标定板）：')
        doc.add_picture(str(IMAGE1), width=Cm(12))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    add_heading(doc, '3.1 拍摄数量与位姿分布', 2)
    add_bullets(
        doc,
        [
            '至少采集 9 组样本：每组 = 1 张图片 + 1 组机器人坐标。',
            '机器人位姿应覆盖工作区域：X/Y 方向有分布，不要 9 个点挤在一起。',
            '建议包含多个不同的 rz（绕 Z 轴转角），用于角度标定；仅 rz=0 时角度补偿精度会下降。',
            '每次拍照前确认标定板在视野中，且识别角点数不少于 5 个（现场正常应达到 16 个角点）。',
        ],
    )

    add_heading(doc, '3.2 合格照片标准', 2)
    add_bullets(
        doc,
        [
            '整块 ChArUco 板清晰可见，黑白格对比明显。',
            '板面尽量正对相机，允许轻微倾斜，但不要大角度侧拍导致角点畸变严重。',
            '无手指、工具、线缆遮挡标定板。',
            '图像不糊、不过曝、不过暗；debug 目录中 detected.jpg 应能画出完整角点。',
        ],
    )

    add_heading(doc, '3.3 不合格示例（需重拍）', 2)
    add_bullets(
        doc,
        [
            '标定板只露出部分，角点数量不足。',
            '强反光导致黑码发白、白格发灰，算法无法稳定识别。',
            '机器人未停稳导致拖影。',
            '拍照高度与标定时不一致。',
        ],
    )

    add_heading(doc, '四、工位标定板（ArUco）拍照要求', 1)
    doc.add_paragraph('工位板用于跨机台基准采集和二次补偿，有效边长 150 m（15 cm），字典 DICT_5X5_50，ID=0。')
    if IMAGE2.exists():
        doc.add_paragraph('参考示意图（工位 ArUco 板）：')
        doc.add_picture(str(IMAGE2), width=Cm(12))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    add_bullets(
        doc,
        [
            '单块 ArUco 码完整出现在画面中央，四边留有足够静区（白边）。',
            '码面平整贴牢，边长方向与机台基准方向一致，后续每次到同一工位保持相同摆放。',
            '拍照高度与手眼标定时一致；高度变化会导致 pixelsPerM 变化，影响补偿精度。',
            '基准采集（cross_calibration）和二次补偿（secondary_compensation）时，工位板位置、光照条件尽量保持一致。',
        ],
    )

    add_heading(doc, '五、现场操作流程', 1)
    add_numbered(
        doc,
        [
            '手眼标定：机器人移动到标定点 → 停稳 → 调用 /api/v1/agv/photo 拍照 → 记录机器人坐标；重复至少 9 次 → 调用 /api/v1/agv/eye_hand。',
            '跨机台基准：机器人到工位基准位 → 停稳 → 调用 /api/v1/agv/cross_calibration → 保存返回的 boardCenterX/Y、boardAngleDeg、pixelsPerM 等。',
            '二次补偿：机器人再次到工位 → 停稳 → 调用 /api/v1/agv/secondary_compensation → 使用返回的 dx/dy/dtheta 修正。',
        ],
    )

    add_heading(doc, '六、现场自检清单', 1)
    add_table(
        doc,
        ['检查项', '合格标准'],
        [
            ['网络', '服务器可 ping 通相机 IP，视觉服务日志无连接失败'],
            ['照片路径', 'Java 指定的 imagePath 目录已挂载，宿主机可直接看到 jpg'],
            ['手眼角点', 'data/debug 下 detected.jpg 角点标注完整，corner_count ≥ 5'],
            ['工位识别', 'cross_calibration 返回 markerCount=1，pixelsPerM 合理（约 2~4 px/m）'],
            ['日志', 'logs/日期/agv_vision.log 中对应接口返回 code=0'],
        ],
    )

    add_heading(doc, '七、常见问题', 1)
    add_table(
        doc,
        ['现象', '可能原因', '处理办法'],
        [
            ['接口成功但找不到照片', 'Docker 未挂载 imagePath 目录', '挂载 /home/projects/images 后重启容器'],
            ['手眼标定失败', '角点不足、位姿分布不够、rz 单一', '重拍并增加位姿分布和 rz 变化'],
            ['补偿偏差大', '拍照高度变化、工位板移动、光照变化', '固定高度和板位置，重新采基准'],
            ['识别不稳定', '反光、过曝、板面脏污', '改善光照，清洁标定板，避免金属反光'],
        ],
    )

    doc.add_paragraph()
    doc.add_paragraph('备注：视觉服务只负责按 Java 指定路径存图和识别；机器人运动、停稳判断、路径规划由 Java/PLC 负责。')
    return doc


def main() -> None:
    if not SRC_DOCX.parent.exists():
        raise SystemExit(f'目标目录不存在: {SRC_DOCX.parent}')
    if SRC_DOCX.exists():
        shutil.copy2(SRC_DOCX, BACKUP)
        print(f'已备份原文件: {BACKUP}')
    if not IMAGE1.exists() or not IMAGE2.exists():
        raise SystemExit('缺少原始示意图，请先保留 image1.png / image2.png')

    doc = build_document()
    doc.save(SRC_DOCX)
    print(f'已更新文档: {SRC_DOCX}')


if __name__ == '__main__':
    main()
