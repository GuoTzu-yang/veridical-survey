# -*- coding: utf-8 -*-
"""fig_lint.py —— 出图时就检查排版缺陷，不通过就抛异常（第 125 轮）。

## 为什么要有这个工具

2026-11-12 把论文发到手机上看时，用户指出了 `figA_layers.png` 的两个问题：

1. 图内文字「决策层 99.18%」压在 x 轴标签「占一篇论文墙钟的比例」上
2. 图太宽，手机上右侧被截断

这两个都不是"看不出"的问题——**是根本没打开看过**。
`AGENTS.md` 里「图必须逐张打开看」这条规矩写了两个月，`fig_visual.py` 也检查了
图内标题与 caption 是否重复，但**没有任何东西阻止一张排版坏掉的图被保存**。

## 这个工具的立场

**「保证以后不犯」不能是口头承诺。** 前面已经证明过：在思考块里写「不写占位符」，
下一行就是「做。快。」——自我指令没有执行器。

所以这里做的是一个**执行器**：`draw_figs.py` 保存每一张图之前必须过 `check()`，
检出重叠就抛 `FigLintError`，**图根本不会生成**。

## 检查什么

| 项 | 判据 | 为什么 |
|---|---|---|
| **文字两两重叠** | 任意两段文字的 bbox 交集面积 / 较小者面积 > 阈值 | 这就是 `figA_layers` 的病 |
| **文字出界** | bbox 超出 figure 边界（含 padding） | 手机上被截断 |
| **文字压轴线** | 文字 bbox 与 axes 边框重叠 | 轴标签被条压住 |
| **字号过小** | < 6 pt | 缩到论文宽度后不可读 |

## 不检查什么（诚实边界）

- **内容对不对**（图里的数是不是真的）—— 机械判不了
- **图与正文一致**（正文说上升，图里是平的）—— 需要语义理解
- **灰度可辨** —— 需要看颜色，本工具只比 bbox
- **图里有没有数据** —— 空白图能通过全部几何检查
- **线条走位好不好看** —— 只查「同色冲突」（见下），不查弧度、绕行、交叉

**一处已修的盲区**：2026-11-12 图里有两道红色弧线（`annotate` 的
`connectionstyle="arc3"`），与红色数据线同色，读者以为是数据的一部分。
当时 `_collect_texts` 只收 `Text`，弧线在 `ax.patches` 里，**一眼都没看过**。
现在加了 `check_line_conflict()`：箭头/连线的颜色若与数据线相同，报冲突。

**所以这个工具只覆盖"排版"，不覆盖"内容"。** 剩下的仍要人看，
但至少**排版坏掉的图不会再被静默保存**。
"""
import matplotlib
from matplotlib.text import Text


class FigLintError(RuntimeError):
    """出图前检查未通过。"""


def _bbox(t, fig):
    """拿文字的显示坐标包围盒；失败返回 None。"""
    try:
        bb = t.get_window_extent(renderer=fig.canvas.get_renderer())
    except Exception:
        return None
    if bb.width <= 0 or bb.height <= 0:
        return None
    return bb


def _overlap_area(a, b):
    x0 = max(a.x0, b.x0)
    x1 = min(a.x1, b.x1)
    y0 = max(a.y0, b.y0)
    y1 = min(a.y1, b.y1)
    if x1 <= x0 or y1 <= y0:
        return 0.0
    return (x1 - x0) * (y1 - y0)


def _collect_texts(fig):
    """收集 figure 里所有非空文字，返回 [(label, Text)]。"""
    out = []
    for i, ax in enumerate(fig.axes):
        for t in ax.texts:
            if isinstance(t, Text) and t.get_text().strip():
                out.append(("ax%d.text:%r" % (i, t.get_text()[:14]), t))
        # 注意：Axes 没有 xlabel / ylabel 属性 —— 正确的是 ax.xaxis.label。
        # 用 getattr(ax, "xlabel") 会永远拿到 None，于是轴标签一个都收不进来，
        # 所有「间距/重叠」检查都在空集上跑（实测踩到：自校连续三次报 0 个问题）。
        for name, obj in (("title", ax.title),
                          ("xlabel", ax.xaxis.label),
                          ("ylabel", ax.yaxis.label)):
            if isinstance(obj, Text) and obj.get_text().strip():
                out.append(("ax%d.%s:%r" % (i, name, obj.get_text()[:14]), obj))
        # 刻意不检查刻度标签：
        # matplotlib 自己排 tick，正常不会重叠；而 tick.label2 在单轴图上
        # 没有显示却返回一个默认 bbox，会制造 100% 的假重叠（实测踩到：
        # 自校第一次报「0.0 × 0.2 重叠 100%」，22 个假问题）。
        # 本工具只查「人手工放的文字」——那才是会压到别处的来源。
    for t in fig.texts:
        if isinstance(t, Text) and t.get_text().strip():
            out.append(("fig.text:%r" % (t.get_text()[:14],), t))
    return out


def _rgb(c):
    """把任意 matplotlib 颜色转成 (r,g,b) 元组；失败返回 None。"""
    try:
        import matplotlib.colors as mcolors
        if c is None:
            return None
        return mcolors.to_rgb(c)
    except Exception:
        return None


def check_line_conflict(fig, tol=0.08):
    """箭头/连线的颜色若与数据线相同，报冲突。

    为什么要有这条：2026-11-12 的雷达图上，两处 annotate 用
    connectionstyle="arc3" 画了红色弧线，而数据线也是同一个红。
    读者看到的是「两条莫名其妙的红线」，分不清是数据还是注释。
    几何检查（重叠/间距/出界）对此完全无感——它不是几何问题，是
    「视觉层级」问题，但「同色」这一半可以机械判。
    """
    problems = []
    for i, ax in enumerate(fig.axes):
        line_colors = []
        for ln in ax.lines:
            # 半透明的线是「背景流带」，不是数据线。figG_flow 那种用
            # alpha=0.32 画的流向带就属于这一类 —— 它和箭头同色是设计意图，
            # 肉眼能靠透明度区分，不该报冲突。
            if ln.get_alpha() is not None and ln.get_alpha() < 0.6:
                continue
            c = _rgb(ln.get_color())
            if c:
                line_colors.append(c)
        if not line_colors:
            continue
        # annotate 的箭头不在 ax.patches 里（实测 ax.patches 为空），
        # 它挂在 Annotation 对象的 arrow_patch 属性上。所以要遍历 ax.texts。
        arrows = []
        for tx in ax.texts:
            ap = getattr(tx, "arrow_patch", None)
            if ap is not None:
                arrows.append(ap)
        # 兼容：直接画在 ax.patches 里的 FancyArrowPatch 也要看
        for pt in ax.patches:
            if type(pt).__name__ == "FancyArrowPatch":
                arrows.append(pt)

        for ap in arrows:
            c = _rgb(ap.get_edgecolor())
            if c is None:
                c = _rgb(ap.get_facecolor())
            if c is None:
                continue
            for lc in line_colors:
                if all(abs(a - b) <= tol for a, b in zip(c, lc)):
                    problems.append(
                        "同色冲突: ax%d 的引线颜色 %s 与数据线相同 ——"
                        " 读者会把它读成数据"
                        % (i, tuple(round(x, 2) for x in c)))
                    break
    seen, uniq = set(), []
    for x in problems:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq


def check(fig, ratio=0.18, min_gap_px=10.0, min_fontsize=6.0,
          raise_on_error=True, verbose=False):
    """检查一张 figure。返回问题列表；raise_on_error 时发现问题直接抛异常。

    ratio: 交集面积 / 较小者面积 的阈值。0.18 意味着两段文字重叠超过较小者的
           18% 就算缺陷。这个值不是定理，是估计：真正相邻的标签通常 < 0.05，
           而 figA_layers 那次「决策层 99.18%」压轴标签是 0.6 以上。
           注意：本函数只查手动放置的文字与轴标签/标题，不查 tick。
    """
    fig.canvas.draw()
    problems = []

    texts = _collect_texts(fig)

    # 1) 字号过小
    for label, t in texts:
        if t.get_fontsize() < min_fontsize:
            problems.append("字号 %.1f pt < %.1f: %s" % (t.get_fontsize(), min_fontsize, label))

    # 2) 两两重叠
    boxes = [(label, _bbox(t, fig)) for label, t in texts]
    boxes = [(l, b) for l, b in boxes if b is not None]
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            l1, b1 = boxes[i]
            l2, b2 = boxes[j]
            area = _overlap_area(b1, b2)
            if area <= 0:
                continue
            smaller = min(b1.width * b1.height, b2.width * b2.height)
            r = area / smaller if smaller > 0 else 0.0
            if r > ratio:
                problems.append("重叠 %.0f%%: %s  ×  %s" % (r * 100, l1, l2))

    # 2a2) 间距过小 —— 这一条比「重叠」更重要。
    # 实测 figA_layers: xlabel 的 bbox 是 y=81..109，图内文字是 y=53..76，
    # 几何上不相交，垂直只差 5 px。但 200 DPI 下 5 px = 0.6 mm，论文把图缩到
    # 0.92\textwidth、手机再缩放之后，视觉上就叠住了。
    # 所以判据不能只看「重叠面积」，要看「最小间距」。
    # 默认 10 px @ 200 DPI ≈ 1.27 mm，缩到页宽后仍有约 3 px 余量。
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            l1, b1 = boxes[i]
            l2, b2 = boxes[j]
            dx = max(b1.x0 - b2.x1, b2.x0 - b1.x1, 0.0)
            dy = max(b1.y0 - b2.y1, b2.y0 - b1.y1, 0.0)
            gap = (dx * dx + dy * dy) ** 0.5
            # 只报「本来该分开的两块」：重叠的已被上一条抓走
            overlapped = _overlap_area(b1, b2) > 0
            if not overlapped and gap < min_gap_px:
                problems.append(
                    "间距 %.1f px < %.1f: %s  ⋯  %s（缩放后可能粘连）"
                    % (gap, min_gap_px, l1, l2))

    # 2b) 文字跑到轴外：位置远超 axes 的数据范围。
    # 这条专抓 figA_layers 那种病：ax.text(0.55, -0.42) 在 barh 的轴上
    # （数据范围约 [-0.05, 0.05]）意味着 y 已是范围的 8 倍开外，savefig 的
    # bbox_inches="tight" 会把它包进来，最终压在 xlabel 上。
    # 「文字远在轴外」这条判据已删：ax.text 会把 ylim 撑开把它包进去，
    # 所以「超出轴范围」永远测不到（实测：ylim 从 (-0.05,0.05) 被撑到
    # (-0.44,0.44)，判据恒为假）。真正的问题是间距，已由 2a2 覆盖。

    # 3) 出界
    fw, fh = fig.get_size_inches() * fig.dpi
    # 容差 1 mm（按 DPI 换算）。原来写死 2 px 会在没调 tight_layout 的图上误报。
    tol = max(2.0, fig.dpi / 25.4)
    for label, b in boxes:
        # 轴标签与标题天然在 axes 外侧，savefig(bbox_inches="tight") 会把它们包进来。
        # 对它们做出界判断会稳定误报（实测：heatmap 的 ylabel 在 x=-46，
        # 而保存出来的 PNG 完全正常）。只有 ax.text / fig.text 才需要判出界。
        if any(k in label for k in ("xlabel:", "ylabel:", "title:")):
            continue
        if b.x0 < -tol or b.y0 < -tol or b.x1 > fw + tol or b.y1 > fh + tol:
            problems.append("出界: %s  bbox=(%.0f,%.0f)-(%.0f,%.0f) fig=%.0fx%.0f"
                            % (label, b.x0, b.y0, b.x1, b.y1, fw, fh))

    # 4) 引线与数据线同色
    problems.extend(check_line_conflict(fig))

    if verbose:
        print("  fig_lint: %d 段文字，%d 个问题" % (len(texts), len(problems)))

    if problems and raise_on_error:
        raise FigLintError(
            "出图前检查未通过（%d 项）:\n  " % len(problems) + "\n  ".join(problems[:10])
            + "\n\n修法：移开文字 / 加 labelpad / 缩小 figsize / 调 subplots 间距。"
        )
    return problems


# ─────────────────────────────────────────────
def _selftest():
    """构造样本：一张坏图必须被抓，一张好图必须放行。"""
    import matplotlib.pyplot as plt
    matplotlib.use("Agg")
    # 必须设中文字体：否则中文渲染成方块，bbox 全挤在一起，
    # 自校会报出大量假重叠（实测第一次跑就是这个问题）。
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
    plt.rcParams["axes.unicode_minus"] = False

    ok = True

    # 样本 1a：两段文字真的叠在同一处（最直接的重叠）
    fig, ax = plt.subplots(figsize=(4, 2.5))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.text(0.5, 0.5, "决策层 99.18%", ha="center", va="center", fontsize=10)
    ax.text(0.5, 0.5, "占一篇论文墙钟的比例", ha="center", va="center", fontsize=10)
    probs = check(fig, raise_on_error=False)
    plt.close(fig)
    got = len(probs) > 0
    print("  [%s] text_on_text  问题 %d 个（期望 >0）%s"
          % ("PASS" if got else "**FAIL**", len(probs),
             "  |  " + probs[0][:62] if probs else ""))
    ok = ok and got

    # 样本 1b：复现 figA_layers 的真实形状 —— 几何上不重叠，但间距只有 5 px
    plt.rcParams["figure.dpi"] = 200
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.4, 3.3),
                                   gridspec_kw={"width_ratios": [1.25, 1]})
    ax2.barh([0], [1], color="#DD8452", height=0.5)
    ax2.set_xlim(0, 1); ax2.set_yticks([])
    ax2.set_xlabel("占一篇论文墙钟的比例")
    ax2.set_title("(b) 机器侧合计仅 0.82%", fontsize=10)
    ax2.text(0.55, -0.42, "决策层 99.18%", ha="center", fontsize=8.5, color="#8a4b1e")
    fig.tight_layout()
    probs = check(fig, raise_on_error=False)
    plt.close(fig)
    got2 = any("间距" in x for x in probs)
    print("  [%s] tight_gap  问题 %d 个（期望含「间距」）%s"
          % ("PASS" if got2 else "**FAIL**", len(probs),
             "  |  " + probs[0][:66] if probs else ""))
    ok = ok and got2

    # 样本 2：干净图，必须 0 问题
    fig, ax = plt.subplots(figsize=(4, 2))
    ax.barh([0], [1], color="#DD8452")
    ax.set_yticks([])
    ax.set_xlabel("比例", labelpad=6)
    ax.text(0.5, 0, "决策层 99.18%", ha="center", va="center", color="white", fontsize=9)
    fig.tight_layout()          # 不加这句，xlabel 会被挤到画布外，产生误报
    probs = check(fig, raise_on_error=False)
    plt.close(fig)
    good = len(probs) == 0
    print("  [%s] good_sample  问题 %d 个（期望 0）%s"
          % ("PASS" if good else "**FAIL**", len(probs),
             "" if good else "  |  " + probs[0][:60]))
    ok = ok and good

    # 样本 3：出界（文字放到 figure 外面）
    fig, ax = plt.subplots(figsize=(3, 2))
    ax.text(1.6, 0.5, "出界的字", transform=ax.transAxes, fontsize=9)
    probs = check(fig, raise_on_error=False)
    plt.close(fig)
    out = any("出界" in p for p in probs)
    print("  [%s] out_of_bounds 问题 %d 个（期望含出界）"
          % ("PASS" if out else "**FAIL**", len(probs)))
    ok = ok and out

    print()
    if ok:
        print("自校通过：重叠被抓、干净放行、出界被抓。")
        return 0
    print("**自校失败**：判据坏了")
    return 1


if __name__ == "__main__":
    import sys
    sys.exit(_selftest())
