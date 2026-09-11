"""绘制 Base、SFT、RL 的开发集结果，输出论文风格的 1×2 图。

在 09-spec-o3/ 目录下运行：

uv run python analysis.py

数据固定为 dev.md 的 result 表，无需加载模型或重新评测。
左图比较 Macro F1 / Accuracy，右图以双轴展示 Format / 答对题数。
输出 images/results_comparison.png（300 DPI）和同名矢量 PDF。
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import PercentFormatter


# 本次记录：Base、SFT epoch 2、RL epoch 1；百分比与 dev.md 一致。
MODELS = ["Base", "SFT", "RL"]
METRICS = ["Macro F1", "Accuracy", "Format"]
SCORES = np.array([
    [53.99, 38.67, 0.39],
    [63.05, 53.91, 85.94],
    [71.68, 67.97, 96.09],
])
CORRECT_ANSWERS = [99, 138, 174]
TOTAL_QUESTIONS = 256
BAR_COLORS = ["#D94A4A", "#3388B8"]
FORMAT_COLOR = "#F28E2B"
COUNT_COLOR = "#596A7D"
OUTPUT_DIR = Path(__file__).parent / "images"


def main():
    # 1. 沿用 AgentOPSD 图的衬线字体、完整边框与点划网格。
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
        "font.size": 11,
        "axes.titlesize": 14,
        "axes.labelsize": 12,
        "axes.labelcolor": "#202020",
        "text.color": "#202020",
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "axes.edgecolor": "#202020",
        "axes.linewidth": 1.0,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "savefig.facecolor": "white",
    })
    fig, (bars_ax, format_ax) = plt.subplots(
        1,
        2,
        figsize=(13.2, 5.7),
        gridspec_kw={"wspace": 0.22},
    )
    fig.subplots_adjust(left=0.07, right=0.925, bottom=0.19, top=0.80)

    for ax in (bars_ax, format_ax):
        ax.set_axisbelow(True)
        ax.grid(
            axis="y",
            color="#C7C7C7",
            linestyle="-.",
            linewidth=0.8,
            alpha=0.75,
        )
        ax.tick_params(axis="x", direction="in", top=True)

    # 2. 左图：每个模型的 Accuracy 放左侧，Macro F1 放右侧。
    positions = np.arange(len(MODELS))
    bar_width = 0.34
    for position, metric_index in enumerate((1, 0)):
        values = SCORES[:, metric_index]
        bars = bars_ax.bar(
            positions + (position - 0.5) * bar_width,
            values,
            width=bar_width,
            color=BAR_COLORS[metric_index],
            edgecolor="#202020",
            linewidth=1.0,
            hatch=["", "///"][metric_index],
            alpha=0.95,
            label=METRICS[metric_index],
            zorder=3,
        )
        bars_ax.bar_label(
            bars,
            labels=[f"{value:.2f}%" for value in values],
            padding=4,
            fontsize=9,
            fontweight="bold",
        )

    bars_ax.set_xticks(positions, MODELS)
    bars_ax.set_ylim(0, 82)
    bars_ax.set_yticks(np.arange(0, 81, 10))
    bars_ax.yaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
    bars_ax.set_ylabel("Score")
    bars_ax.set_xlabel("Evaluated model", labelpad=10)
    bars_ax.set_title("(a) Classification Performance", pad=14)
    bars_ax.legend(loc="upper left", frameon=False, fontsize=10, handlelength=1.5)

    # 3. 右图：左轴表示格式合规率，右轴表示答对题数。
    format_line = format_ax.plot(
        positions,
        SCORES[:, 2],
        color=FORMAT_COLOR,
        marker="s",
        markersize=7,
        markerfacecolor="#F2B36B",
        markeredgecolor="#202020",
        markeredgewidth=0.9,
        linewidth=2.2,
        label="Strict format compliance",
        zorder=4,
    )[0]
    count_ax = format_ax.twinx()
    count_line = count_ax.plot(
        positions,
        CORRECT_ANSWERS,
        color=COUNT_COLOR,
        marker="o",
        markersize=7,
        markerfacecolor="#A7B4C2",
        markeredgecolor="#202020",
        markeredgewidth=0.9,
        linewidth=2.0,
        linestyle="--",
        label="Correct answers",
        zorder=4,
    )[0]
    for position, value in zip(positions, SCORES[:, 2]):
        format_ax.annotate(
            f"{value:.2f}%",
            xy=(position, value),
            xytext=(-6, 12) if position == 0 else (0, 10),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
            color=FORMAT_COLOR,
        )
    for position, correct in zip(positions, CORRECT_ANSWERS):
        count_ax.annotate(
            f"{correct} / {TOTAL_QUESTIONS}",
            xy=(position, correct),
            xytext=(0, -14),
            textcoords="offset points",
            ha="center",
            va="top",
            fontsize=9,
            fontweight="bold",
            color=COUNT_COLOR,
        )

    format_ax.set_xticks(positions, MODELS)
    format_ax.set_xlim(-0.15, 2.15)
    format_ax.set_ylim(-5, 115)
    format_ax.set_yticks(np.arange(0, 101, 20))
    format_ax.yaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
    format_ax.set_ylabel("Strict format compliance", color=FORMAT_COLOR)
    format_ax.tick_params(axis="y", colors=FORMAT_COLOR)
    format_ax.set_xlabel("Evaluated model", labelpad=10)
    format_ax.set_title("(b) Format Compliance & Correct Answers", pad=14)
    count_ax.set_ylim(0, TOTAL_QUESTIONS)
    count_ax.set_yticks([0, 64, 128, 192, 256])
    count_ax.set_ylabel("Correct answers (out of 256)", color=COUNT_COLOR)
    count_ax.tick_params(axis="y", colors=COUNT_COLOR)
    count_ax.spines["right"].set_color(COUNT_COLOR)
    format_ax.legend(
        [format_line, count_line],
        [format_line.get_label(), count_line.get_label()],
        loc="upper left",
        frameon=False,
        fontsize=9,
        handlelength=2.2,
    )

    format_gain = SCORES[-1, 2] - SCORES[0, 2]
    correct_gain = CORRECT_ANSWERS[-1] - CORRECT_ANSWERS[0]
    format_ax.text(
        0.5,
        0.06,
        f"RL vs Base: +{format_gain:.2f} pp format · +{correct_gain} correct answers",
        transform=format_ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=9.2,
        color="#303030",
        bbox={
            "boxstyle": "round,pad=0.38",
            "facecolor": "#FFF8EE",
            "edgecolor": "#E1B678",
            "linewidth": 0.8,
        },
    )

    # 4. 总标题、评测说明和脚注与参考图采用相同的排版层次。
    fig.suptitle("Spec-o3 · Qwen3.5-4B Evaluation", fontsize=17, fontweight="bold", y=0.98)
    fig.text(
        0.5,
        0.925,
        "Same 256 dev examples · Base / SFT (epoch 2) / RL (epoch 1) · shared answer extraction",
        ha="center",
        va="center",
        fontsize=10.5,
        color="#555555",
    )
    fig.text(
        0.5,
        0.035,
        "Generation caps: Base 6,132; SFT 2,048; RL 6,144 tokens per turn. Base alone uses an extra format reminder.\n"
        "Panel (a) starts at zero; panel (b) uses separate y-axes and connects only the evaluated models.",
        ha="center",
        va="center",
        fontsize=8.5,
        color="#666666",
        style="italic",
        linespacing=1.6,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for extension in ("png", "pdf"):
        path = OUTPUT_DIR / f"results_comparison.{extension}"
        fig.savefig(path, dpi=300, bbox_inches="tight", pad_inches=0.16)
        print(f"Saved: {path}")
    plt.close(fig)


if __name__ == "__main__":
    main()
