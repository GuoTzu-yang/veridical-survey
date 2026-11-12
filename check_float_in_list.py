# -*- coding: utf-8 -*-
"""检查每个 figure 环境是否落在 enumerate/itemize 内部（会被撕断列表）。"""
import io
import re

P = "main.tex"
s = io.open(P, encoding="utf-8").read()
lines = s.split("\n")

# 逐行跟踪 list 深度
depth = 0
list_stack = []
figs = []
for i, ln in enumerate(lines, 1):
    stripped = ln.strip()
    if re.match(r"\\begin\{enumerate\}|\\begin\{itemize\}", stripped):
        depth += 1
        list_stack.append((depth, i, stripped[:40]))
    elif re.match(r"\\end\{enumerate\}|\\end\{itemize\}", stripped):
        if list_stack:
            list_stack.pop()
        depth = max(0, depth - 1)
    if "\\begin{figure}" in stripped:
        figs.append((i, depth, stripped))

print("figure 总数 = %d" % len(figs))
bad = [(i, d) for i, d, _ in figs if d > 0]
print()
if bad:
    print("*** 落在列表内部的 figure（会导致列表被撕断）：")
    for i, d in bad:
        print("    行 %d  list 深度 %d" % (i, d))
        # 打印前后文
        for k in range(max(0, i - 4), min(len(lines), i + 8)):
            t = lines[k]
            if len(t) > 100:
                t = t[:100] + " ..."
            print("        %4d: %s" % (k + 1, t))
        print()
else:
    print("没有 figure 落在列表内部")

# 同时找出所有 table 是否在列表内
depth = 0
tabs = []
for i, ln in enumerate(lines, 1):
    stripped = ln.strip()
    if re.match(r"\\begin\{enumerate\}|\\begin\{itemize\}", stripped):
        depth += 1
    elif re.match(r"\\end\{enumerate\}|\\end\{itemize\}", stripped):
        depth = max(0, depth - 1)
    if "\\begin{table}" in stripped:
        tabs.append((i, depth))

tab_bad = [(i, d) for i, d in tabs if d > 0]
print()
print("table 总数 = %d，落在列表内 = %d" % (len(tabs), len(tab_bad)))
for i, d in tab_bad:
    print("    行 %d  list 深度 %d" % (i, d))
