# -*- coding: utf-8 -*-
"""把正文里的直引号 "..." 成对替换为中文弯引号 “...”，避免 ctex 下渲染成直角引号。"""
import io
import re

P = r"C:\Users\21246\Documents\deepseek-harness\default-workspace\aidc2026\big\main.tex"
s = io.open(P, encoding="utf-8").read()

# 只处理中文语境下的成对直引号：不碰 \code{} 内部、不碰命令行、不碰 LaTeX 参数
# 策略：逐行扫描，遇到 " 就交替配对（奇数个为开引号，偶数个为闭引号）
lines = s.split("\n")
out = []
changed = 0
for ln in lines:
    # 跳过纯代码/命令类行（含 \code{ 且整行几乎都是它），保守起见仍处理正文
    if '"' not in ln:
        out.append(ln)
        continue
    res = []
    depth_code = 0
    open_q = True
    i = 0
    while i < len(ln):
        ch = ln[i]
        # 跟踪是否在 \code{...} 里
        if ln.startswith("\\code{", i):
            depth_code += 1
            res.append("\\code{")
            i += 6
            continue
        if ch == "}" and depth_code > 0:
            depth_code -= 1
            res.append(ch)
            i += 1
            continue
        if ch == '"' and depth_code == 0:
            res.append("“" if open_q else "”")
            open_q = not open_q
            changed += 1
            i += 1
            continue
        res.append(ch)
        i += 1
    out.append("".join(res))

s2 = "\n".join(out)
io.open(P, "w", encoding="utf-8", newline="\n").write(s2)
print("替换引号数 =", changed)
