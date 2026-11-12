# -*- coding: utf-8 -*-
"""渲染 PDF 每页为 PNG，并做基础视觉体检：
  - 每页非空白像素占比（发现空白页/半空页）
  - 页内内容是否越过版心边距（Overfull 的视觉验证）
  - 图片是否真的嵌入（按页统计位图对象）
"""
import sys
import pathlib
import pypdfium2 as pdfium

PDF = sys.argv[1] if len(sys.argv) > 1 else r"main.pdf"
OUT = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "render")
SCALE = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0
OUT.mkdir(parents=True, exist_ok=True)

doc = pdfium.PdfDocument(PDF)
n = len(doc)
print("pages =", n)

# 版心（与 main.tex 的 geometry 一致）：left/right 2.6cm, top 2.6cm, bottom 2.4cm
PT = 72.0 / 2.54
MARGIN_CM = float(sys.argv[4]) if len(sys.argv) > 4 else 2.4
MARGIN_L = MARGIN_CM * PT
MARGIN_R = MARGIN_CM * PT
MARGIN_T = MARGIN_CM * PT
MARGIN_B = MARGIN_CM * PT
TOL = 5.0   # 容差 pt（≈1.8mm，肉眼不可辨的排版抖动）

report = []
for i in range(n):
    page = doc[i]
    w, h = page.get_size()
    bmp = page.render(scale=SCALE)
    pil = bmp.to_pil().convert("RGB")
    px_w, px_h = pil.size
    path = OUT / ("p%02d.png" % (i + 1))
    pil.save(path)

    # 非白像素统计 + 边界框
    gray = pil.convert("L")
    hist = gray.histogram()
    total = px_w * px_h
    nonwhite = total - hist[255]
    ratio = nonwhite / total if total else 0.0

    # 找内容边界（用于判断是否越界）：把亮度<250 视为有内容
    import numpy as np
    arr = np.asarray(gray)
    mask = arr < 250
    # 页脚区（页码）不算正文越界：LaTeX 页码字形顶部约在距底 64pt 处
    FOOT_PT = 64.0
    if mask.any():
        rows = np.where(mask.any(axis=1))[0]
        cols = np.where(mask.any(axis=0))[0]
        top_px, bot_px = int(rows[0]), int(rows[-1])
        left_px, right_px = int(cols[0]), int(cols[-1])
        # 只统计页脚区以上的内容，用来判断正文下边界
        body_limit_px = int((h - FOOT_PT) * SCALE)
        body_mask = mask[:max(1, body_limit_px), :]
        if body_mask.any():
            brows = np.where(body_mask.any(axis=1))[0]
            body_bot_px = int(brows[-1])
        else:
            body_bot_px = 0
        left_pt = left_px / SCALE
        right_pt = right_px / SCALE
        top_pt = top_px / SCALE
        bot_pt = bot_px / SCALE
        body_bot_pt = body_bot_px / SCALE
        over_left = left_pt < MARGIN_L - TOL
        over_right = right_pt > w - MARGIN_R + TOL
        over_top = top_pt < MARGIN_T - TOL - 20   # 页眉/页码在上边距内属正常
        over_bot = body_bot_pt > h - MARGIN_B + TOL
    else:
        left_pt = right_pt = top_pt = bot_pt = body_bot_pt = 0.0
        over_left = over_right = over_top = over_bot = False

    report.append(dict(page=i + 1, w=w, h=h, ratio=ratio,
                       left=left_pt, right=right_pt, top=top_pt, bot=bot_pt,
                       body_bot=body_bot_pt,
                       over_left=over_left, over_right=over_right,
                       over_top=over_top, over_bot=over_bot))

print("%-5s %-8s %-8s %-8s %-8s %-9s %s" % ("页", "内容占比", "左pt", "右pt", "上pt", "正文下pt", "异常"))
issues = 0
for r in report:
    flags = []
    if r["ratio"] < 0.02:
        flags.append("近空白页")
    if r["over_left"]:
        flags.append("越左边界")
    if r["over_right"]:
        flags.append("越右边界")
    if r["over_bot"]:
        flags.append("文越下边界")
    if flags:
        issues += 1
    print("%-5d %-8.3f %-8.1f %-8.1f %-8.1f %-9.1f %s"
          % (r["page"], r["ratio"], r["left"], r["right"], r["top"], r["body_bot"],
             ",".join(flags) if flags else "ok"))

print()
print("页面尺寸: %.1f x %.1f pt (A4 = 595.3 x 841.9)" % (report[0]["w"], report[0]["h"]))
print("版心: 左 %.1f / 右 %.1f 起" % (MARGIN_L, report[0]["w"] - MARGIN_R))
print("异常页数 =", issues)
print("图已写入", OUT.resolve())
