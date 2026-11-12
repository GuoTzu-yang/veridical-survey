# -*- coding: utf-8 -*-
"""把旧论文的关键页渲染为 PNG，供大论文以「证据截图」形式引用。"""
import pathlib
import pypdfium2 as pdfium

SRC = pathlib.Path(r"C:\Users\21246\Documents\xwechat_files\wxid_zs66slwasysu22_590d\msg\file\2026-11")
OUT = pathlib.Path(r"C:\Users\21246\Documents\deepseek-harness\default-workspace\aidc2026\big\figs")
OUT.mkdir(parents=True, exist_ok=True)

# (源文件, 页码(1-based), 输出名, 缩放)
PICKS = [
    ("③ 工具论文-含AB实验一节.pdf", 3,  "ev_t1_anatomy.png", 2.2),
    ("③ 工具论文-含AB实验一节.pdf", 8,  "ev_t5_gates33.png", 2.2),
    ("③ 工具论文-含AB实验一节.pdf", 16, "ev_t10_ablation.png", 2.2),
    ("③ 工具论文-含AB实验一节.pdf", 23, "ev_t13_seeded.png", 2.2),
    ("③ 工具论文-含AB实验一节.pdf", 25, "ev_fig21_ab.png", 2.2),
    ("插件构建-最终论文-23页.pdf", 6,   "ev_arch3layer.png", 2.2),
    ("插件构建-最终论文-23页.pdf", 22,  "ev_not_supported.png", 2.2),
    ("Plugin-Agent-Architecture(1).pdf", 3, "ev_capcost_table.png", 2.5),
    ("Plugin-Agent-Architecture(1).pdf", 7, "ev_topsis.png", 2.5),
    ("数模论文-最终版-27页.pdf", 8,     "ev_pinfine.png", 2.2),
    ("数模论文-最终版-27页.pdf", 10,    "ev_corr.png", 2.2),
]

for fn, page_no, out_name, scale in PICKS:
    p = SRC / fn
    if not p.exists():
        print("缺失", fn)
        continue
    doc = pdfium.PdfDocument(str(p))
    if page_no > len(doc):
        print("页码越界", fn, page_no)
        continue
    page = doc[page_no - 1]
    bmp = page.render(scale=scale)
    img = bmp.to_pil()
    dst = OUT / out_name
    img.save(dst)
    print("  %-26s <- %s p%d  (%dx%d)" % (out_name, fn[:18], page_no, *img.size))
