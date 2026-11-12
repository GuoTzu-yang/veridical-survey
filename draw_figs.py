# -*- coding: utf-8 -*-
"""为大论文绘制 6 张图。所有数字来自本轮实测，不引用旧论文。"""
import pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 200
plt.rcParams["savefig.bbox"] = "tight"

OUT = pathlib.Path(r"C:\Users\21246\Documents\deepseek-harness\default-workspace\aidc2026\big\figs")
OUT.mkdir(parents=True, exist_ok=True)

# 出图前必须过 fig_lint：重叠、间距过小、出界、字号过小，任一不过就抛异常，
# 图不会生成。2026-11-12 用户把论文发到手机上看，发现 figA_layers 的图内文字
# 压住了 x 轴标签 —— 那条「图必须逐张打开看」的规矩写了两个月，没有任何东西
# 阻止一张排版坏掉的图被保存。这个包装就是那个东西。
import fig_lint


def save(fig, name):
    """检查后保存。检查不过直接抛，不生成文件。"""
    problems = fig_lint.check(fig, raise_on_error=False)
    if problems:
        raise fig_lint.FigLintError(
            "%s 排版检查未通过（%d 项）:\n  " % (name, len(problems))
            + "\n  ".join(problems[:8])
        )
    fig.savefig(OUT / name)
    print("  saved", name, "| lint OK")


# ---------- 图 A：三层成本占比（机器侧只占 0.82%） ----------
def fig_layers():
    labels = ["能力层", "验证与编译", "机器侧合计", "决策层（LLM）"]
    vals = [1.191, 7.966, 9.157, 1114.8]
    colors = ["#4C72B0", "#55A868", "#C44E52", "#DD8452"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.4, 3.3), gridspec_kw={"width_ratios": [1.25, 1]})

    y = np.arange(len(labels))
    bars = ax1.barh(y, vals, color=colors, height=0.6)
    ax1.set_yticks(y, labels)
    ax1.set_xscale("log")
    ax1.set_xlabel("耗时 / s（对数轴）")
    ax1.set_title("(a) 三层耗时对比", fontsize=10)
    for b, v in zip(bars, vals):
        ax1.text(v * 1.15, b.get_y() + b.get_height() / 2, f"{v:g} s", va="center", fontsize=8.5)
    ax1.invert_yaxis()
    ax1.grid(axis="x", ls=":", alpha=0.45)

    # 极端不均衡（0.82% vs 99.18%）用堆叠条比饼图可读。
    # 2026-11-12 修：原来「决策层 99.18%」放在 y=-0.42（数据坐标），
    # 与 xlabel 的 bbox 只差 5 px，缩到页宽后视觉上叠住；
    # 两个百分比标注也互相重叠 96%。fig_lint 把这两处都挡了下来。
    seg = [1.191, 7.966, 1114.8]
    seg_colors = ["#4C72B0", "#55A868", "#DD8452"]
    left = 0.0
    total = sum(seg)
    for v, c in zip(seg, seg_colors):
        w = v / total
        ax2.barh([0], [w], left=left, color=c, height=0.5, edgecolor="w", lw=1.5)
        left += w
    ax2.set_xlim(0, 1)
    ax2.set_yticks([])
    ax2.set_xlabel("占一篇论文墙钟（1124.8 s）的比例", labelpad=10)
    ax2.set_title("(b) 机器侧合计仅 0.82%（决策层为其 121.7 倍）", fontsize=10)
    # 大段文字放进条内，白字 —— 不再落在轴标签那一带
    ax2.text(0.55, 0, "决策层 99.18%", ha="center", va="center",
             fontsize=9.5, color="white", fontweight="bold")
    # 极窄的两段合并成一个标注：ax2 被 ax1 压窄之后，两行并排的标注会重叠 98%
    # （fig_lint 抓到）。合成一条引线，指向条的最左端。
    ax2.annotate("机器侧 0.82%\n（能力层 0.11 + 验证编译 0.71）",
                 xy=(0.004, 0.26), xytext=(0.16, 0.62),
                 fontsize=7.5, ha="left", va="bottom", linespacing=1.4,
                 arrowprops=dict(arrowstyle="->", lw=0.8, color="#444",
                                 connectionstyle="arc3,rad=-0.25"))
    ax2.set_ylim(-0.55, 1.0)
    ax2.grid(axis="x", ls=":", alpha=0.4)
    fig.tight_layout()
    save(fig, "figA_layers.png")
    plt.close(fig)


# ---------- 图 B：能力成本差 52 倍 ----------
def fig_capcost():
    names = ["排队论", "统计", "动态规划", "网络", "混合整数规划", "评价(TOPSIS)", "拟合"]
    eff = [398.4, 333.5, 238.9, 119.4, 113.8, 44.6, 7.6]
    cost = [0.040, 0.039, 0.113, 0.117, 0.114, 0.112, 0.656]
    selfs = [16, 13, 27, 14, 13, 5, 5]

    fig, ax = plt.subplots(figsize=(7.6, 3.4))
    x = np.arange(len(names))
    bars = ax.bar(x, eff, color="#4C72B0", width=0.62)
    bars[-1].set_color("#C44E52")
    ax.set_xticks(x, names, rotation=18, ha="right", fontsize=8.5)
    ax.set_ylabel("每秒自检数")
    ax.set_title("七项能力的验证效率（最高/最低 = %.0f 倍）" % (max(eff) / min(eff)), fontsize=10)
    for b, e, c, s in zip(bars, eff, cost, selfs):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 8,
                "%s\n%.3fs / %d项" % (f"{e:g}", c, s), ha="center", fontsize=7)
    ax.set_ylim(0, max(eff) * 1.28)
    ax.grid(axis="y", ls=":", alpha=0.45)
    fig.tight_layout()
    save(fig, "figB_capcost.png")
    plt.close(fig)


# ---------- 图 C：数字类别分布 ----------
def fig_genre():
    labels = ["计算值\n47.3%", "配置值\n27.1%", "结构性\n17.6%", "时间标签\n8.0%"]
    vals = [47.3, 27.1, 17.6, 8.0]
    colors = ["#C44E52", "#4C72B0", "#55A868", "#8172B2"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.2, 3.2), gridspec_kw={"width_ratios": [1, 1.1]})

    wedges, _ = ax1.pie(vals, colors=colors, startangle=90,
                        wedgeprops={"edgecolor": "w", "linewidth": 1.4})
    ax1.legend(wedges, labels, loc="center left", bbox_to_anchor=(0.95, 0.5), fontsize=8, frameon=False)
    ax1.set_title("(a) 9 337 个数字的类别构成", fontsize=10)

    # 可被知识源覆盖的只有后三类
    cat = ["必须来自计算", "可由配置/结构/时间解释"]
    v2 = [47.3, 52.7]
    bars = ax2.bar(cat, v2, color=["#C44E52", "#4C72B0"], width=0.5)
    ax2.set_ylabel("占比 / %")
    ax2.set_ylim(0, 100)
    for b, v in zip(bars, v2):
        ax2.text(b.get_x() + b.get_width() / 2, v + 2, f"{v}%", ha="center", fontsize=9)
    ax2.axhline(52.7, ls="--", lw=1, color="gray")
    ax2.text(0.5, 55, "知识源覆盖上界 52.7%", ha="center", fontsize=8, color="gray")
    ax2.set_title("(b) 若把后三类都当「该有出处」，半数是误报", fontsize=10)
    ax2.grid(axis="y", ls=":", alpha=0.4)
    fig.tight_layout()
    save(fig, "figC_genre.png")
    plt.close(fig)


# ---------- 图 D：门禁数量的演进 ----------
def fig_gategrowth():
    stages = ["史前", "R121", "R122", "R123", "R124 末"]
    total = [23, 23, 23, 33, 35]
    hard = [None, None, None, 12, 12]

    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    ax.plot(stages, total, "o-", color="#4C72B0", lw=2, ms=7, label="门禁总数")
    for i, (s, t) in enumerate(zip(stages, total)):
        ax.annotate(str(t), (i, t), textcoords="offset points", xytext=(0, 9),
                    ha="center", fontsize=9, color="#4C72B0")
    ax.axhline(12, ls="--", lw=1.2, color="#C44E52", label="硬门 12 项")
    ax.set_ylabel("检查项数")
    ax.set_ylim(0, 42)
    ax.set_title("门禁从 23 项扩到 35 项：每次扩张都由一个具体失败触发", fontsize=10)
    ax.legend(fontsize=8.5, frameon=False, loc="lower right")
    ax.grid(axis="y", ls=":", alpha=0.45)
    # 标注触发事件
    notes = {3: "题面落地\n显著性门", 4: "proof 门\niterlog 门"}
    for i, txt in notes.items():
        ax.annotate(txt, (i, total[i]), textcoords="offset points", xytext=(0, -30),
                    ha="center", fontsize=7, color="#555")
    fig.tight_layout()
    save(fig, "figD_gategrowth.png")
    plt.close(fig)


# ---------- 图 E：14 个缺陷的分级 ----------
def fig_defects():
    cats = ["协议级", "资源级", "数值级", "语法级"]
    cnt = [3, 3, 5, 3]
    colors = ["#C44E52", "#DD8452", "#4C72B0", "#55A868"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.0, 3.2), gridspec_kw={"width_ratios": [1, 1.25]})

    bars = ax1.bar(cats, cnt, color=colors, width=0.6)
    ax1.set_ylabel("缺陷数")
    ax1.set_ylim(0, 7)
    for b, c in zip(bars, cnt):
        ax1.text(b.get_x() + b.get_width() / 2, c + 0.15, str(c), ha="center", fontsize=10)
    ax1.set_title("(a) 14 个缺陷按危害分级", fontsize=10)
    ax1.grid(axis="y", ls=":", alpha=0.45)

    # 危害：整用例挂 vs 单值错
    types = ["整个用例失败\n（协议级+资源级）", "单点数值/语法错\n（数值级+语法级）"]
    v = [6, 8]
    bars2 = ax2.barh(types, v, color=["#C44E52", "#4C72B0"], height=0.5)
    for b, x in zip(bars2, v):
        ax2.text(x + 0.15, b.get_y() + b.get_height() / 2, f"{x} 个", va="center", fontsize=10)
    ax2.set_xlabel("缺陷数")
    ax2.set_xlim(0, 10)
    ax2.set_title("(b) 6 个属「整条用例直接失败」级", fontsize=10)
    ax2.grid(axis="x", ls=":", alpha=0.4)
    fig.tight_layout()
    save(fig, "figE_defects.png")
    plt.close(fig)


# ---------- 图 F：六环飞轮 ----------
def fig_flywheel():
    import matplotlib.patches as mpatches
    rings = ["① 做工作", "② 成果进论文", "③ 红队攻", "④ 分诊", "⑤ 修", "⑥ 台账"]
    n = len(rings)
    fig, ax = plt.subplots(figsize=(5.6, 5.6))
    ax.set_aspect("equal")
    ax.axis("off")

    R = 1.0
    for i, name in enumerate(rings):
        a0 = 90 - i * (360 / n)
        a1 = 90 - (i + 1) * (360 / n)
        th = np.linspace(np.radians(a1), np.radians(a0), 60)
        # 扇形
        xs = np.concatenate([[0], R * np.cos(th)])
        ys = np.concatenate([[0], R * np.sin(th)])
        color = plt.cm.tab20(i / n)
        ax.fill(xs, ys, color=color, alpha=0.55, edgecolor="w", lw=2)
        # 标签
        am = np.radians((a0 + a1) / 2)
        ax.text(0.62 * R * np.cos(am), 0.62 * R * np.sin(am), name,
                ha="center", va="center", fontsize=10, fontweight="bold")
    # 中心
    ax.add_patch(mpatches.Circle((0, 0), 0.26, color="white", ec="#333", lw=1.4, zorder=5))
    ax.text(0, 0.04, "仪表", ha="center", va="center", fontsize=11, fontweight="bold", zorder=6)
    ax.text(0, -0.12, "每环可测", ha="center", va="center", fontsize=8, zorder=6)
    # 外圈箭头示意
    ax.annotate("", xy=(0, R * 1.14), xytext=(0, R * 1.02),
                arrowprops=dict(arrowstyle="-|>", color="#333", lw=1.4))
    ax.set_xlim(-1.22, 1.22)
    ax.set_ylim(-1.22, 1.28)
    ax.set_title("生态飞轮：六环，只有每环可测整圈才不空转", fontsize=10, pad=4)
    fig.tight_layout()
    save(fig, "figF_flywheel.png")
    plt.close(fig)


for fn in (fig_layers, fig_capcost, fig_genre, fig_gategrowth, fig_defects, fig_flywheel):
    fn()
    print("OK", fn.__name__)

print()
for p in sorted(OUT.glob("*.png")):
    print("  %-24s %6.1f KB" % (p.name, p.stat().st_size / 1024))
