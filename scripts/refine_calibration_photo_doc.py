"""在用户修订版基础上完善《标定版拍照要求》。"""
from __future__ import annotations

import shutil
import zipfile
from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


SRC_DOCX = Path(r'C:\Users\Dell\Desktop\项目资料\01_AGV项目\标定版拍照要求.docx')
OUT_DOCX = SRC_DOCX
BACKUP = SRC_DOCX.with_name(SRC_DOCX.stem + '_修订前备份.docx')
EXTRACT_DIR = Path(r'd:\code\AGV\pkg3_260522\data\_docx_extract')


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


def extract_images(src: Path) -> tuple[Path, Path]:
    image1 = EXTRACT_DIR / 'image1.png'
    image2 = EXTRACT_DIR / 'image2.png'
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(src) as zf:
        for name in ('word/media/image1.png', 'word/media/image2.png'):
            if name in zf.namelist():
                target = EXTRACT_DIR / Path(name).name
                target.write_bytes(zf.read(name))
    if not image1.exists() or not image2.exists():
        raise FileNotFoundError('文档中缺少示意图 image1.png / image2.png')
    return image1, image2


def build_document(image1: Path, image2: Path) -> Document:
    doc = Document()
    set_doc_font(doc)

    add_title(doc, 'AGV 视觉标定版拍照要求')
    doc.add_paragraph(f'文档版本：V1.1    更新日期：{date.today():%Y-%m-%d}')
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
            '相机分辨率按现场配置：1280×800，格式 MJPG。',
            '机器人/AGV 到位并完全停稳后再拍照，避免运动模糊。',
            '标定板完整出现在画面内，四周留出足够边距，不要被机械结构遮挡。',
            '光照均匀，避免强反光、局部过曝或大面积阴影。',
        ],
    )

    add_heading(doc, '三、手眼标定板（ChArUco）拍照要求', 1)
    doc.add_paragraph('现场手眼标定板规格：约 20 cm × 20 cm（5×5 格，单格边长约 30 m）。')
    p = doc.add_paragraph()
    run = p.add_run('拍照距离：相机镜头到标定板表面约 20 cm 左右。')
    run.bold = True
    doc.add_paragraph('该距离为现场基准高度，手眼标定、跨机台基准和二次补偿过程中须保持一致，不得随意调整。')

    add_bullets(
        doc,
        [
            '至少采集 9 组样本，每组包含 1 张图片和对应机器人坐标（x/y/z/rx/ry/rz）。',
            '整块 ChArUco 板清晰可见，黑白格对比明显。',
            '板面尽量正对相机，允许轻微倾斜，但不要大角度侧拍导致角点畸变严重。',
            '无手指、工具、线缆遮挡标定板。',
            '图像不糊、不过曝、不过暗；debug 目录中 detected.jpg 应能画出完整角点。',
        ],
    )

    doc.add_paragraph('参考示意图（手眼标定板）：')
    doc.add_picture(str(image1), width=Cm(12))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    add_heading(doc, '四、工位标定板（ArUco）拍照要求', 1)
    doc.add_paragraph('工位板用于跨机台基准采集和二次补偿，有效边长 150 m（15 cm），字典 DICT_5X5_50。')
    doc.add_paragraph('拍照距离与手眼标定时保持一致（约 20 cm），并保证每次到同一工位时高度相同。')

    add_bullets(
        doc,
        [
            '单块 ArUco 码完整出现在画面中央，四边留有足够静区（白边）。',
            '码面平整贴牢，边长方向与机台基准方向一致，后续每次到同一工位保持相同摆放。',
            '拍照高度与手眼标定时一致；高度变化会导致 pixelsPerM 变化，影响补偿精度。',
            '基准采集（cross_calibration）和二次补偿（secondary_compensation）时，工位板位置、光照条件尽量保持一致。',
        ],
    )

    doc.add_paragraph('参考示意图（工位 ArUco 板）：')
    doc.add_picture(str(image2), width=Cm(12))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    add_heading(doc, '五、现场快速自检', 1)
    add_bullets(
        doc,
        [
            '拍照后检查宿主机 imagePath 目录是否生成 jpg 文件。',
            '手眼标定后检查 debug 目录 detected.jpg 角点是否完整。',
            '若识别失败或角点不足，先检查距离、光照和板面是否被遮挡，再重拍。',
        ],
    )

    return doc


def main() -> None:
    if not SRC_DOCX.exists():
        raise SystemExit(f'找不到文件: {SRC_DOCX}')

    shutil.copy2(SRC_DOCX, BACKUP)
    image1, image2 = extract_images(SRC_DOCX)
    doc = build_document(image1, image2)

    try:
        doc.save(OUT_DOCX)
        print(f'已更新: {OUT_DOCX}')
    except PermissionError:
        alt = SRC_DOCX.with_name(SRC_DOCX.stem + '_完善.docx')
        doc.save(alt)
        print(f'原文件被占用，已保存为: {alt}')
    print(f'原文件备份: {BACKUP}')


if __name__ == '__main__':
    main()
