# -*- coding: utf-8 -*-
"""draw_advanced.py —— 四张「高级」图（第 125 轮）。

为什么需要：原来的 8 张图里 5 张是柱状图、2 张是整页截图。
用户评价「图太少了，还不高级」。这四张用现有实测数据画，
不新增任何未记录的数字。

数据来源全部在本文件里注明，便于核对：
  · 四类数字占比：out/数字类别分布.md（9 337 个 token）
  · A/B 五维分数：model1-arch/out/final/ablation_ab.json 的 scores
  · 五通道重叠：同一文件的 overlap_check
  · 门禁演进：main.tex 的 tab:phases（23 → 23 → 23 → 33 → 35 → 35）
"""
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, Rectangle

import fig_lint

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 200
plt.rcParams["savefig.bbox"] = "tight"

OUT = pathlib.Path(r"C:\Users\21246\Documents\deepseek-harness\default-workspace\aidc2026\big\figs")
OUT.mkdir(parents=True, exist_ok=True)


def save(fig, name):
    problems = fig_lint.check(fig, raise_on_error=False)
    if problems:
        raise fig_lint.FigLintError(
            "%s 排版检查未通过（%d 项）:\n  " % (name, len(problems))
            + "\n  ".join(problems[:8])
        )
    fig.savefig(OUT / name)
    plt.close(fig)
    print("  saved", name, "| lint OK")


# ─────────────────────────────────────────────
# 图 G：数字流向（9 337 → 四类 → 是否需要计算谱系）
# ─────────────────────────────────────────────
def fig_flow():
    total = 9337
    kinds = [
        ("计算值 computed", 47.3, "#C44E52", "必须来自一次实际计算"),
        ("配置值 config", 27.1, "#DD8452", "方法里声明一次的阈值/置信水平"),
        ("结构性 structural", 17.6, "#8172B2", "行/表/节编号、样本量 n"),
        ("时间标签 time", 8.0, "#64B5CD", "年份、时段，来自输入文件"),
    ]

    fig, ax = plt.subplots(figsize=(10.4, 4.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.2)
    ax.axis("off")

    # 左：总量
    ax.add_patch(FancyBboxPatch((0.15, 1.6), 1.5, 1.9,
                                boxstyle="round,pad=0.06",
                                fc="#2b2b2b", ec="none"))
    ax.text(0.9, 2.75, "9\\,337".replace("\\,", " "), ha="center", va="center",
            color="white", fontsize=15, fontweight="bold")
    ax.text(0.9, 2.15, "数值 token\n23 篇报告", ha="center", va="center",
            color="#d0d0d0", fontsize=8.5)

    # 中：四类
    y0 = 4.35
    gap = 1.02
    for i, (name, pct, color, note) in enumerate(kinds):
        y = y0 - i * gap
        h = 0.78
        w = 2.4 * (pct / 47.3) ** 0.55 + 0.9   # 视觉宽度压缩，避免 47% 独占
        ax.add_patch(Rectangle((3.0, y - h / 2), w, h, fc=color, ec="none", alpha=0.9))
        ax.text(3.15, y + 0.10, name, color="white", fontsize=9, fontweight="bold", va="center")
        ax.text(3.15, y - 0.20, "%.1f%%" % pct, color="white", fontsize=9, va="center")
        ax.text(3.0 + w + 0.18, y, note, fontsize=8, va="center", color="#333")
        # 左→中的流带（用半透明梯形近似）
        ax.plot([1.68, 3.0], [2.75, y], ls="-", lw=3.2, color=color, alpha=0.32,
                solid_capstyle="butt")

    # 右：判据
    ax.add_patch(FancyBboxPatch((7.55, 3.55), 2.2, 1.25,
                                boxstyle="round,pad=0.05",
                                fc="#EAF2EA", ec="#55A868", lw=1.2))
    ax.text(8.65, 4.45, "必须溯源", ha="center", fontsize=9, fontweight="bold", color="#2f6b3f")
    ax.text(8.65, 3.95, "冻结表 + 精度感知相等\n（得到 325/325）", ha="center",
            fontsize=7.8, color="#2f6b3f")

    ax.add_patch(FancyBboxPatch((7.55, 2.15), 2.2, 1.25,
                                boxstyle="round,pad=0.05",
                                fc="#FBF0E6", ec="#DD8452", lw=1.2))
    ax.text(8.65, 3.05, "声明一次即可", ha="center", fontsize=9, fontweight="bold", color="#8a4b1e")
    ax.text(8.65, 2.55, "52.7% 由知识源\n与数据结构解释", ha="center",
            fontsize=7.8, color="#8a4b1e")

    ax.annotate("", xy=(7.5, 4.15), xytext=(5.9, 3.86),
                arrowprops=dict(arrowstyle="-|>", lw=2.2, color="#C44E52",
                                connectionstyle="arc3,rad=0.18"))
    for yy in (3.35, 2.55, 1.75):
        ax.annotate("", xy=(7.5, 2.75), xytext=(5.9, yy),
                    arrowprops=dict(arrowstyle="-|>", lw=1.5, color="#999",
                                    connectionstyle="arc3,rad=0.1"))

    ax.text(5.0, 0.35, "只有最上面一类会产生「看起来像结果、背后没有东西」的错误——"
                       "这是本文判据的作用域，也是它的边界",
            ha="center", fontsize=8.5, color="#555", style="italic")

    save(fig, "figG_flow.png")


# ─────────────────────────────────────────────
# 图 H：A/B 五维雷达
# ─────────────────────────────────────────────
def fig_radar():
    dims = ["数据与假设\n/10", "问题一\n/25", "问题二\n/30", "问题三\n/25", "学术规范\n/10"]
    mx = np.array([10, 25, 30, 25, 10], dtype=float)
    a = np.array([9, 24, 27, 25, 9], dtype=float) / mx
    b = np.array([10, 25, 29, 18, 8], dtype=float) / mx

    ang = np.linspace(0, 2 * np.pi, len(dims), endpoint=False).tolist()
    ang += ang[:1]
    a = np.r_[a, a[0]]
    b = np.r_[b, b[0]]

    fig = plt.figure(figsize=(6.4, 5.0))
    ax = plt.subplot(111, polar=True)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    ax.plot(ang, a, "o-", lw=2.0, color="#C44E52", ms=5, label="有鉴真层（94.0/100）")
    ax.fill(ang, a, color="#C44E52", alpha=0.16)
    ax.plot(ang, b, "s--", lw=2.0, color="#4C72B0", ms=5, label="无鉴真层（90.0/100）")
    ax.fill(ang, b, color="#4C72B0", alpha=0.10)

    ax.set_xticks(ang[:-1])
    ax.set_xticklabels(dims, fontsize=9)
    ax.set_ylim(0.6, 1.02)
    ax.set_yticks([0.7, 0.8, 0.9, 1.0])
    ax.set_yticklabels(["70%", "80%", "90%", "100%"], fontsize=7.5, color="#777")
    ax.set_title("五维得分率：优势在「问题二」与「问题三」之间反转",
                 fontsize=10, pad=30)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.16), ncol=2,
              fontsize=8.5, frameon=False)

    # 图内不再重复标注哪一维反转 —— caption 已经写全，而在 polar 坐标里无论把文字放哪个半径都会压到数据线上。
    # 图只负责形状，文字负责读数。

    save(fig, "figH_radar.png")


# ─────────────────────────────────────────────
# 图 I：门禁演进热力图（哪一期加了哪些门）
# ─────────────────────────────────────────────
def fig_heatmap():
    # 35 道门按加入的期分组（依据 tab:phases 与 AGENTS.md 的轮次记录）
    phases = ["史前", "R121", "R122", "R123", "R124", "R125"]
    groups = {
        "史前": ["compile", "pdf", "code", "numbers", "rules", "abstract", "abs_page",
                 "bare_pct", "refs", "domain", "leakage", "math", "rules_apmcm",
                 "rigor", "required", "innovation", "ai_taste", "claims", "causal",
                 "biblio", "analysis", "method_argument", "self_correction"],
        "R123": ["deployment", "cross", "figures", "falsify", "extrap",
                 "sensitivity", "significance", "prompt"],
        "R124": ["proof", "iterlog", "stamp"],
        "R121": [], "R122": [], "R125": [],
    }

    gates = []
    for p in phases:
        for g in groups.get(p, []):
            gates.append((g, p))

    n_ph = len(phases)
    n_g = len(gates)
    M = np.zeros((n_g, n_ph))
    for i, (g, p) in enumerate(gates):
        j0 = phases.index(p)
        for j in range(j0, n_ph):
            M[i, j] = 1

    fig, ax = plt.subplots(figsize=(7.2, 9.2))
    # 原来用 YlOrRd + vmin0/vmax1.45，二值矩阵渲染成「全红/全黄」两块，
    # 配色没有层次。换成 YlGnBu 并把 vmax 压到 1，让「已加入」「未加入」
    # 之间的边界靠白线分隔，而不是靠色带。
    ax.imshow(M, cmap="YlGnBu", aspect="auto", vmin=0, vmax=1.0)

    ax.set_xticks(range(n_ph))
    ax.set_xticklabels(phases, fontsize=9)
    ax.set_yticks(range(n_g))
    ax.set_yticklabels([g for g, _ in gates], fontsize=7.2, family="monospace")

    # 加计数标注（每期累计）
    counts = [23, 23, 23, 31, 35, 35]
    deltas = [None, 0, 0, 8, 4, 0]
    # 增量原来单独标在 y=-0.9（图顶之外），与 title 重叠 27%（fig_lint 抓到）。
    # 改成与累计数一起写在热力图底部：一行累计、一行增量。
    for j, (c, d) in enumerate(zip(counts, deltas)):
        ax.text(j, n_g + 0.30, "%d" % c, ha="center", va="top",
                fontsize=9.5, fontweight="bold", color="#C44E52")
        if d:
            ax.text(j, n_g + 1.55, "+%d" % d, ha="center", va="top",
                    fontsize=8.5, color="#2f6b3f")

    ax.set_title("35 道门禁的加入时点（底部为该期的累计门数）",
                 fontsize=10, pad=14)
    ax.set_xlabel("演进期", fontsize=9, labelpad=16)
    ax.set_ylabel("门禁（按加入期排列）", fontsize=9, labelpad=4)

    # 用白线把格子分开，二值矩阵才不会糊成两块
    ax.set_xticks(np.arange(-0.5, n_ph, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, n_g, 1), minor=True)
    ax.grid(which="minor", color="white", lw=0.6)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)

    save(fig, "figI_heatmap.png")


# ─────────────────────────────────────────────
# 图 J：A/B 五通道重叠（替代原来的整页截图）
# ─────────────────────────────────────────────
def fig_overlap():
    labels = ["solver 值\n（3313 vs 618）", "论文小数\n（119 vs 141）",
              "30 字符散文", "3 行代码", "同哈希数据文件"]
    vals = [43, 5, 0, 0, 0]
    informative = [0, 0, 0, 0, 0]

    fig, ax = plt.subplots(figsize=(8.6, 3.4))
    x = np.arange(len(labels))
    ax.bar(x, vals, width=0.52, color="#C44E52", alpha=0.85, label="重合项")

    for xi, v in zip(x, vals):
        ax.text(xi, v + 1.2, str(v), ha="center", fontsize=10, fontweight="bold")
    # 原来还画了一组「信息性重合」的绿柱，但五个通道的值全是 0，
    # 柱子高度为 0 完全看不见，图例却留着 → 读者以为漏了什么。
    # 改成在图上直接写出这个 0。

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8.4)
    ax.set_ylabel("重合项数", fontsize=9)
    ax.set_ylim(0, 52)
    ax.set_title("两臂在五个通道上的重合：43 是唯一不能报零的数，"
                 "但其中信息性重合为 0", fontsize=9.5, pad=12)
    ax.legend(fontsize=8.5, frameon=False, loc="upper right")
    ax.grid(axis="y", ls=":", alpha=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # 括号标注：43 个都是结构整数
    ax.annotate("全部是格点、柜数、\n时间步与公共比值",
                xy=(0, 43), xytext=(0.75, 34),
                fontsize=7.8, color="#8a4b1e",
                arrowprops=dict(arrowstyle="->", lw=0.9, color="#8a4b1e",
                                connectionstyle="arc3,rad=-0.2"))

    save(fig, "figJ_overlap.png")


for fn in (fig_flow, fig_radar, fig_heatmap, fig_overlap):
    fn()
    print("OK", fn.__name__)
