# -*- coding: utf-8 -*-
"""列出四篇旧论文每页的首行，用于挑选值得截图引用的页。"""
import pathlib
import pypdfium2 as pdfium

SRC = pathlib.Path(r"C:\Users\21246\Documents\xwechat_files\wxid_zs66slwasysu22_590d\msg\file\2026-11")
FILES = [
    "③ 工具论文-含AB实验一节.pdf",
    "插件构建-最终论文-23页.pdf",
    "Plugin-Agent-Architecture(1).pdf",
    "数模论文-最终版-27页.pdf",
]

for name in FILES:
    p = SRC / name
    if not p.exists():
        print("缺失", name)
        continue
    doc = pdfium.PdfDocument(str(p))
    print("=" * 78)
    print("%s   共 %d 页" % (name, len(doc)))
    for i in range(len(doc)):
        t = doc[i].get_textpage().get_text_range()
        lines = [l.strip() for l in t.split("\n") if l.strip()]
        head = " / ".join(lines[:2])[:88] if lines else "（空页）"
        # 标记有图的页（文本很少但页面不小 -> 可能是图页）
        flag = ""
        if len(t.strip()) < 200:
            flag = "  << 少字（可能图页）"
        print("  p%-3d %s%s" % (i + 1, head, flag))
    print()
