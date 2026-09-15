from __future__ import annotations

import base64
import json
from html import escape
from pathlib import Path


FLIES_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FLIES_DIR.parent
OUTPUT_DIR = next(path for path in FLIES_DIR.glob("20260821*") if path.is_dir())
ARTIFACT_PATH = OUTPUT_DIR / "artifact.json"
SUMMARY_PATH = OUTPUT_DIR / "summary.json"
HTML_PATH = FLIES_DIR / "20260821精度测试汇总.html"
REFERENCE_IMAGE = (
    PROJECT_ROOT
    / "data"
    / "debug"
    / "20260821"
    / "20260821_100240_878987_station_ref_station_001"
    / "raw.jpg"
)


def format_number(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}"


def image_data_url(image_path: Path) -> str:
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def table_row(values: list[str], row_class: str = "") -> str:
    class_attribute = f' class="{row_class}"' if row_class else ""
    cells = "".join(f"<td>{escape(value)}</td>" for value in values)
    return f"<tr{class_attribute}>{cells}</tr>"


def build_html() -> str:
    artifact = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    datasets = artifact["snapshot"]["datasets"]
    measurements = datasets["measurements"]
    axis_summary = datasets["axis_summary"]
    worst_image_row = max(measurements, key=lambda row: row["corner_rms_px"])
    worst_image_path = PROJECT_ROOT / worst_image_row["image"]

    detail_rows = []
    for row in measurements:
        detail_rows.append(
            table_row(
                [
                    str(row["test"]),
                    row["time"],
                    str(row["common_corners"]),
                    format_number(row["center_dx_px"]),
                    format_number(row["center_dy_px"]),
                    format_number(row["corner_rms_px"]),
                    format_number(row["max_corner_px"]),
                    format_number(row["pnp_reproj_rmse_px"]),
                    format_number(row["x_mm"]),
                    format_number(row["y_mm"]),
                    format_number(row["z_mm"]),
                    format_number(row["translation_norm_mm"]),
                    format_number(row["rx_deg"]),
                    format_number(row["ry_deg"]),
                    format_number(row["rz_deg"]),
                    format_number(row["rotation_norm_deg"]),
                ],
                "worst" if row["test"] == worst_image_row["test"] else "",
            )
        )

    axis_rows = [
        table_row(
            [
                row["axis"],
                format_number(row["mean"], 4),
                format_number(row["sd"], 4),
                format_number(row["p2p"], 4),
            ]
        )
        for row in axis_summary
    ]

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>20260821 ChArUco 静止重复测量精度分析</title>
  <style>
    :root {{ color-scheme: light; --ink:#172033; --muted:#667085; --line:#d9e0ea; --blue:#2563eb; --soft:#f5f7fb; --good:#067647; --warn:#b54708; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:#eef2f7; color:var(--ink); font:15px/1.65 "Segoe UI","Microsoft YaHei",sans-serif; }}
    main {{ width:min(1500px, calc(100% - 32px)); margin:24px auto; background:white; border:1px solid var(--line); border-radius:16px; box-shadow:0 12px 40px #18223016; overflow:hidden; }}
    header {{ padding:34px 42px 26px; background:linear-gradient(135deg,#0f2e5f,#2563eb); color:white; }}
    header h1 {{ margin:0 0 8px; font-size:29px; }}
    header p {{ margin:0; opacity:.86; }}
    section {{ padding:26px 42px; border-top:1px solid var(--line); }}
    h2 {{ margin:0 0 14px; font-size:21px; }}
    .answer {{ font-size:17px; background:#f0fdf4; border-left:5px solid #12b76a; padding:18px 20px; border-radius:8px; }}
    .cards {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }}
    .card {{ background:var(--soft); border:1px solid var(--line); border-radius:10px; padding:15px; }}
    .card span {{ display:block; color:var(--muted); font-size:13px; }}
    .card strong {{ display:block; margin-top:4px; color:var(--blue); font-size:23px; }}
    .images {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
    figure {{ margin:0; border:1px solid var(--line); border-radius:10px; overflow:hidden; background:var(--soft); }}
    figure img {{ display:block; width:100%; }}
    figcaption {{ padding:10px 12px; color:var(--muted); }}
    .table-wrap {{ overflow:auto; border:1px solid var(--line); border-radius:10px; }}
    table {{ width:100%; border-collapse:collapse; white-space:nowrap; font-variant-numeric:tabular-nums; }}
    th {{ position:sticky; top:0; background:#eaf0fb; color:#344054; text-align:right; padding:9px 10px; border-bottom:1px solid var(--line); font-size:12px; }}
    th:nth-child(-n+3), td:nth-child(-n+3) {{ text-align:left; }}
    td {{ padding:8px 10px; text-align:right; border-bottom:1px solid #edf0f5; font-size:13px; }}
    tr:nth-child(even) td {{ background:#fafbfc; }}
    tr.worst td {{ background:#fff4e8; }}
    .note {{ color:var(--muted); font-size:13px; }}
    .callout {{ border-left:4px solid var(--warn); background:#fffaeb; padding:14px 16px; border-radius:7px; }}
    code {{ background:#f2f4f7; padding:2px 5px; border-radius:4px; }}
    @media(max-width:900px) {{ .cards,.images {{ grid-template-columns:1fr 1fr; }} section,header {{ padding-left:20px; padding-right:20px; }} }}
    @media print {{
      @page {{ size:A3 landscape; margin:10mm; }}
      * {{ -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
      body {{ background:white; font-size:12px; }}
      main {{ width:100%; margin:0; border:0; border-radius:0; box-shadow:none; }}
      header {{ padding:22px 28px 18px; }}
      section {{ padding:16px 28px; }}
      .cards {{ grid-template-columns:repeat(4,1fr); }}
      .images {{ grid-template-columns:1fr 1fr; }}
      .table-wrap {{ overflow:visible; }}
      table {{ width:100%; table-layout:auto; white-space:nowrap; }}
      th, td {{ padding:5px 4px; font-size:8px; }}
      h2 {{ break-after:avoid-page; }}
      h2:has(+ .images) {{ break-before:page; }}
      .images {{ break-before:avoid-page; break-inside:avoid; }}
      figure, .cards, .callout {{ break-inside:avoid; }}
    }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>2026-08-21 ChArUco 静止重复测量精度分析</h1>
    <p>基准图 10:02:40；17 次当前图 10:03:36–10:06:05；机械臂全程静止</p>
  </header>
  <section>
    <h2>结论</h2>
    <div class="answer"><strong>图片并没有差很多。</strong> 17 次都识别到同一组 16/16 角点；相对基准图的整板角点 RMS 仅 <strong>{summary['corner_rms_min_px']:.3f}–{summary['corner_rms_max_px']:.3f} px</strong>，最大单角点差 {summary['max_single_corner_px']:.3f} px，最大中心位移 {summary['max_center_shift_px']:.3f} px，肉眼基本不可见。接口返回的平移模长却为 {summary['translation_min_mm']:.3f}–{summary['translation_max_mm']:.3f} mm，旋转模长为 {summary['rotation_min_deg']:.3f}–{summary['rotation_max_deg']:.3f}°。因此较大的六轴波动不是因为标定板在图片里真的移动了那么多。</div>
  </section>
  <section>
    <h2>核心指标</h2>
    <div class="cards">
      <div class="card"><span>角点 RMS 最大值</span><strong>{summary['corner_rms_max_px']:.3f} px</strong></div>
      <div class="card"><span>单角点最大差</span><strong>{summary['max_single_corner_px']:.3f} px</strong></div>
      <div class="card"><span>返回平移最大值</span><strong>{summary['translation_max_mm']:.3f} mm</strong></div>
      <div class="card"><span>返回旋转最大值</span><strong>{summary['rotation_max_deg']:.3f}°</strong></div>
    </div>
    <p class="note">亮度相对基准最大只变化 {summary['brightness_delta_max_abs']:.3f} 个灰度级；拉普拉斯清晰度峰峰值 {summary['sharpness_range']:.3f}，曝光和清晰度也很稳定。</p>
  </section>
  <section>
    <h2>对应图片直观对比</h2>
    <div class="images">
      <figure><img src="{image_data_url(REFERENCE_IMAGE)}" alt="跨机台基准原图"><figcaption>跨机台基准图：10:02:40</figcaption></figure>
      <figure><img src="{image_data_url(worst_image_path)}" alt="角点 RMS 最大的当前原图"><figcaption>图片差异最大的一次：#{worst_image_row['test']}，{worst_image_row['time']}；角点 RMS {worst_image_row['corner_rms_px']:.3f} px</figcaption></figure>
    </div>
    <p class="note">上面右图已经是 17 次中“角点差最大”的一张，仍与基准图几乎一致。</p>
  </section>
  <section>
    <h2>图片变化与返回值的关系</h2>
    <div class="callout">角点 RMS 与返回平移模长的 Pearson 相关系数只有 <strong>{summary['corner_translation_corr']:.3f}</strong>；去除整板平移后的角点形变 RMS 与旋转模长相关系数为 <strong>{summary['nonrigid_rotation_corr']:.3f}</strong>，都接近 0。第 12 次角点 RMS 为 0.171 px，平移仅 0.099 mm；第 16 次角点 RMS 同样约 0.169 px，平移却达到 0.746 mm。</div>
    <p>这更符合“平面 PnP 对亚像素角点噪声的 Rx/Ry/深度解算敏感，再经 <code>gTc</code> 手眼变换产生平移耦合”的特征，而不是图像出现了真实的大幅移动。</p>
  </section>
  <section>
    <h2>17 次逐条汇总</h2>
    <div class="table-wrap"><table>
      <thead><tr><th>序号</th><th>时间</th><th>角点数</th><th>中心dx(px)</th><th>中心dy(px)</th><th>角点RMS(px)</th><th>最大角点差(px)</th><th>PnP重投影(px)</th><th>X(mm)</th><th>Y(mm)</th><th>Z(mm)</th><th>平移模长(mm)</th><th>Rx(°)</th><th>Ry(°)</th><th>Rz(°)</th><th>旋转模长(°)</th></tr></thead>
      <tbody>{''.join(detail_rows)}</tbody>
    </table></div>
    <p class="note">橙色行是按角点 RMS 判断的图片差异最大项。图片指标来自保存的 JPEG 调试原图重检；六轴值直接取日志中的 <code>data.targetFlangePose</code>。</p>
  </section>
  <section>
    <h2>六轴重复性统计</h2>
    <div class="table-wrap"><table><thead><tr><th>轴</th><th>均值</th><th>样本标准差</th><th>峰峰值</th></tr></thead><tbody>{''.join(axis_rows)}</tbody></table></div>
    <p>Y 均值为 {summary['y_mean_mm']:.3f} mm，说明存在稳定的负向偏置；X/Y 标准差约 {summary['x_sd_mm']:.3f}/{summary['y_sd_mm']:.3f} mm。Rz 最稳定；Rx/Ry 更容易受平面姿态解算影响。</p>
  </section>
  <section>
    <h2>口径与限制</h2>
    <ul>
      <li>基准图：<code>20260821_100240_878987_station_ref_station_001/raw.jpg</code>。</li>
      <li>当前图：日志对应的 17 个 <code>compensation_current/raw.jpg</code>。</li>
      <li>复算使用 <code>settings_online.yaml</code> 和项目同一 ChArUco 检测器，按角点 ID 一一配对。</li>
      <li>调试原图是 JPEG，压缩会带来轻微亚像素变化；所以这里只判断图像差异量级。</li>
      <li>这组数据评价的是静止重复性，不是机械臂绝对定位精度；后者需要激光跟踪仪、百分表等外部测量基准。</li>
    </ul>
  </section>
</main>
</body>
</html>"""


def main() -> None:
    HTML_PATH.write_text(build_html(), encoding="utf-8")
    print(HTML_PATH)


if __name__ == "__main__":
    main()
