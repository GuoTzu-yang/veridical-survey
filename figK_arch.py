# -*- coding: utf-8 -*-
"""figK_arch.py —— 四层架构图（矢量重画，替代原来的整页截图）。

原来 §2.1 用的是一张「工具论文第 6 页」的截图（ev_arch3layer.png）：
它把 Figure 1、Figure 2、Gate composition 段、§6 Validation 开头一起截了进来，
而内嵌的 Figure 2 自己的标签就是重叠的（advise/hints/race… 下面的说明叠成一团）。
那张截图的信息只有最上面的一块，其余都是噪声。

这里重画成矢量图，并且把数字改成当前的：
  能力层 23 个子命令（schema.json 的 n_commands）
  门禁 35 项 = 硬门 12 + 软门 23
"""
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

import fig_lint

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 200
plt.rcParams["savefig.bbox"] = "tight"

OUT = pathlib.Path(r"C:\Users\21246\Documents\deepseek-harness\default-workspace\aidc2026\big\figs")


def fig_arch():
    fig, ax = plt.subplots(figsize=(9.0, 6.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7.2)
    ax.axis("off")

    layers = [
        # (y, 名称, 副标题, 右注, 填充, 边)
        (5.55, "LLM（作者）", "决定模型、写正文、作判断",
         "它不能被替代——\n判断不在护栏的范围内", "#EAF0F7", "#4C72B0"),
        (3.95, "能力层  mmkit.py", "23 个子命令，JSON 纯净输出",
         "只算不写：\n任何一步都不产生段落", "#FDF2E9", "#DD8452"),
        (2.35, "验证层  verify / falsify / lanes", "数字溯源、结论攻击、8 条通道",
         "独立于前两层：\n它可以否定作者的判断", "#EAF4EC", "#55A868"),
        (0.75, "门禁  35 项（硬 12 · 软 23）", "失败关闭：不通过就不出稿",
         "唯一一个\n可以整体说“不”的层", "#FBEAEA", "#C44E52"),
    ]

    for y, name, sub, note, fc, ec in layers:
        ax.add_patch(FancyBboxPatch((0.75, y), 5.55, 1.15,
                                    boxstyle="round,pad=0.06",
                                    fc=fc, ec=ec, lw=1.6))
        ax.text(1.02, y + 0.74, name, fontsize=11, fontweight="bold", color=ec, va="center")
        ax.text(1.02, y + 0.30, sub, fontsize=8.6, color="#444", va="center")
        ax.text(6.75, y + 0.55, note, fontsize=8.0, color="#666", va="center", linespacing=1.5)

    # 层间箭头与动作标签
    acts = [
        (5.05, "提议 proposes"),
        (3.45, "计算 + 自检 computes"),
        (1.85, "拒绝通过 refuses"),
    ]
    for y, label in acts:
        ax.add_patch(FancyArrowPatch((3.5, y + 0.42), (3.5, y + 0.02),
                                     arrowstyle="-|>", mutation_scale=15,
                                     lw=1.6, color="#555"))
        ax.text(3.75, y + 0.22, label, fontsize=8.2, color="#555", va="center")

    # 右侧竖排：每一层都能拒绝上一层
    ax.add_patch(FancyArrowPatch((6.10, 1.30), (6.10, 5.95),
                                 arrowstyle="-|>", mutation_scale=16,
                                 lw=1.4, color="#C44E52", ls="--",
                                 connectionstyle="arc3,rad=0.30"))
    ax.text(8.75, 3.65, "每一层都能拒绝上一层", fontsize=8.6,
            color="#C44E52", ha="center", va="center",
            rotation=90, fontweight="bold")

    # 顶部一句：这一节的主张
    ax.text(5.0, 7.02, "工具从不写论证，它让论证里的每个数可被核对",
            fontsize=9.6, ha="center", style="italic", color="#333")

    problems = fig_lint.check(fig, raise_on_error=False)
    if problems:
        raise fig_lint.FigLintError(
            "figK_arch.png 排版检查未通过（%d 项）:\n  " % len(problems)
            + "\n  ".join(problems[:8]))
    fig.savefig(OUT / "figK_arch.png")
    plt.close(fig)
    print("  saved figK_arch.png | lint OK")


if __name__ == "__main__":
    fig_arch()
