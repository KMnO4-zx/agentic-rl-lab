"""汇总 GRPO/DAPO 训练曲线与 AIME25 评测结果。

    uv run python 06-dapo/analysis.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter


SCRIPT_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--grpo-metrics",
        type=Path,
        default=SCRIPT_DIR / "results" / "grpo-qwen35-4b.jsonl",
    )
    parser.add_argument(
        "--dapo-metrics",
        type=Path,
        default=SCRIPT_DIR / "results" / "dapo-qwen35-4b.jsonl",
    )
    parser.add_argument(
        "--eval-dir",
        type=Path,
        default=SCRIPT_DIR / "eval-results",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=SCRIPT_DIR / "images" / "grpo-dapo-comparison.png",
    )
    parser.add_argument("--dpi", type=int, default=200)
    parser.add_argument("--show", action="store_true")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """读取 JSONL，并给出带行号的解析错误。"""
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(f"无效 JSON：{path}:{line_number}") from error
    return records


def load_train_history(
    path: Path,
    algorithm: str,
) -> list[dict[str, Any]]:
    """读取并校验一个算法的 step 指标。"""
    if not path.is_file():
        return []
    history = [
        record
        for record in read_jsonl(path)
        if record.get("type") == "train_step"
    ]
    if any(record.get("algorithm") != algorithm for record in history):
        raise ValueError(f"{path} 包含非 {algorithm} 训练记录")
    return sorted(history, key=lambda record: int(record["step"]))


def load_eval_summaries(result_dir: Path) -> list[dict[str, Any]]:
    """从每个 AIME25 JSONL 中读取最后一条 summary。"""
    summaries: list[dict[str, Any]] = []
    if not result_dir.is_dir():
        return summaries
    for path in sorted(result_dir.glob("aime25-*.jsonl")):
        summary = next(
            (
                record
                for record in reversed(read_jsonl(path))
                if record.get("type") == "summary"
            ),
            None,
        )
        if summary is None:
            raise ValueError(f"{path} 缺少 type=summary 记录")
        summaries.append(summary)
    order = {"base": 0, "grpo": 1, "dapo": 2}
    return sorted(
        summaries,
        key=lambda item: (
            order.get(str(item.get("algorithm")), 99),
            int(item.get("checkpoint_step", 0)),
        ),
    )


def plot_training_metric(
    axis: plt.Axes,
    histories: dict[str, list[dict[str, Any]]],
    key: str,
    title: str,
    ylabel: str,
) -> None:
    """在同一坐标系绘制 GRPO/DAPO step 曲线。"""
    colors = {"GRPO": "#3977B8", "DAPO": "#D95555"}
    plotted = False
    for label, history in histories.items():
        points = [
            (int(record["step"]), float(record[key]))
            for record in history
            if key in record
        ]
        if not points:
            continue
        plotted = True
        axis.plot(
            [point[0] for point in points],
            [point[1] for point in points],
            label=label,
            color=colors[label],
            linewidth=2,
        )
    axis.set_title(title)
    axis.set_xlabel("Training step")
    axis.set_ylabel(ylabel)
    axis.grid(alpha=0.25)
    if plotted:
        axis.legend()
    else:
        axis.text(
            0.5,
            0.5,
            "No training metrics",
            transform=axis.transAxes,
            ha="center",
            va="center",
        )


def make_figure(
    grpo_history: list[dict[str, Any]],
    dapo_history: list[dict[str, Any]],
    eval_summaries: list[dict[str, Any]],
) -> plt.Figure:
    """生成训练成本/效果和 AIME25 的四面板对照图。"""
    histories = {"GRPO": grpo_history, "DAPO": dapo_history}
    figure, axes = plt.subplots(2, 2, figsize=(13, 9))
    plot_training_metric(
        axes[0, 0],
        histories,
        "reward/shaped_mean",
        "Training shaped reward",
        "Reward",
    )
    plot_training_metric(
        axes[0, 1],
        histories,
        "reward/accuracy",
        "Training accuracy",
        "Accuracy",
    )
    axes[0, 1].yaxis.set_major_formatter(PercentFormatter(1.0))
    plot_training_metric(
        axes[1, 0],
        histories,
        "rollout/completion_tokens",
        "Rollout token cost",
        "Completion tokens / step",
    )

    eval_axis = axes[1, 1]
    if eval_summaries:
        labels = [
            (
                "Base"
                if item["algorithm"] == "base"
                else f"{str(item['algorithm']).upper()} "
                f"{int(item['checkpoint_step'])}"
            )
            for item in eval_summaries
        ]
        x = list(range(len(labels)))
        width = 0.36
        eval_axis.bar(
            [value - width / 2 for value in x],
            [float(item["average_at_n"]) for item in eval_summaries],
            width,
            label="Average@N",
            color="#5B8FF9",
        )
        eval_axis.bar(
            [value + width / 2 for value in x],
            [float(item["pass_at_n"]) for item in eval_summaries],
            width,
            label="Pass@N",
            color="#F6BD16",
        )
        eval_axis.set_xticks(x, labels, rotation=20, ha="right")
        eval_axis.yaxis.set_major_formatter(PercentFormatter(1.0))
        eval_axis.legend()
    else:
        eval_axis.text(
            0.5,
            0.5,
            "No AIME25 results",
            transform=eval_axis.transAxes,
            ha="center",
            va="center",
        )
    eval_axis.set_title("AIME25 evaluation")
    eval_axis.set_ylabel("Score")
    eval_axis.grid(axis="y", alpha=0.25)

    figure.suptitle("GRPO vs DAPO — PyTRIO reproduction", fontsize=16)
    figure.tight_layout()
    return figure


def main() -> None:
    args = parse_args()
    grpo_history = load_train_history(args.grpo_metrics, "grpo")
    dapo_history = load_train_history(args.dapo_metrics, "dapo")
    eval_summaries = load_eval_summaries(args.eval_dir)
    if not grpo_history and not dapo_history and not eval_summaries:
        raise FileNotFoundError("没有找到训练指标或 AIME25 评测结果")

    figure = make_figure(grpo_history, dapo_history, eval_summaries)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output, dpi=args.dpi, bbox_inches="tight")
    print(f"Saved figure: {args.output}")
    for summary in eval_summaries:
        print(
            f"{summary['algorithm']} step={summary['checkpoint_step']}: "
            f"Average@{summary['val_n']}={float(summary['average_at_n']):.2%}, "
            f"Pass@{summary['val_n']}={float(summary['pass_at_n']):.2%}"
        )
    if args.show:
        plt.show()
    else:
        plt.close(figure)


if __name__ == "__main__":
    main()
