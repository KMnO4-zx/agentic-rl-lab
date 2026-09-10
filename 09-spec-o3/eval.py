r"""用同一套工具与预算评测 Base、SFT 或后续 RL 的 sampler 权重。

在 09-spec-o3/ 目录下运行：

uv run python eval.py --output outputs/base-dev

uv run python eval.py \
    --model-path '<训练终端打印的 sampler_path>' \
    --output outputs/sft-dev

默认使用 datasets/rl/bench_dev.jsonl；输出分类指标、完整轨迹和工具图片。
进度条按已完成的样本数统计，每批评测结束后更新。
"""

import argparse
import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv
import pytrio as trio
from tqdm import tqdm
from transformers import AutoImageProcessor, AutoTokenizer

from protocol import BASE_MODEL, MODEL_REVISION
from rollout import rollout


def classification_metrics(results):
    """先计算各任务的二分类指标，再汇总整体表现与工具使用情况。"""
    metrics = {}

    for task in sorted({row["task"] for row in results}):
        rows = [row for row in results if row["task"] == task]
        tp = sum(
            row["label"] == "YES" and row["prediction"] == "YES"
            for row in rows
        )
        fp = sum(
            row["label"] == "NO" and row["prediction"] == "YES"
            for row in rows
        )
        # 未给出有效答案时，正类样本也计入漏检。
        fn = sum(
            row["label"] == "YES" and row["prediction"] != "YES"
            for row in rows
        )

        # 没有预测正类时 precision 记 0；这是分类指标的 zero-division 定义。
        metrics[task] = {
            "count": len(rows),
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": tp / (tp + fp) if tp + fp else 0.0,
            "recall": tp / (tp + fn) if tp + fn else 0.0,
            "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0,
            "accuracy": sum(row["label"] == row["prediction"] for row in rows) / len(rows),
            "format_rate": sum(row["format_ok"] for row in rows) / len(rows),
        }

    observations = [
        turn["observation"]
        for row in results
        for turn in row["turns"]
        if "observation" in turn
    ]

    return {
        "tasks": metrics,
        "macro_f1": sum(item["f1"] for item in metrics.values()) / len(metrics),
        "accuracy": sum(row["label"] == row["prediction"] for row in results) / len(results),
        "format_rate": sum(row["format_ok"] for row in results) / len(results),
        "mean_turns": sum(len(row["turns"]) for row in results) / len(results),
        "tool_calls": len(observations),
        "tool_successes": sum(obs["ok"] for obs in observations),
    }


async def main(args):
    load_dotenv()

    # 1. 读取评测集，创建与训练模板匹配的 tokenizer 和图像处理器。
    rows = [json.loads(line) for line in args.data.read_text().splitlines()]
    tokenizer = AutoTokenizer.from_pretrained(
        BASE_MODEL,
        revision=MODEL_REVISION,
    )
    processor = AutoImageProcessor.from_pretrained(
        BASE_MODEL,
        revision=MODEL_REVISION,
        backend="pil",
    )

    # 2. model_path 留空使用 Base；传入时加载对应 sampler 权重。
    service = trio.ServiceClient()
    sampler = service.create_sampling_client(
        base_model=BASE_MODEL,
        model_path=args.model_path,
    )
    args.output.mkdir(parents=True, exist_ok=True)
    results = []

    # 3. 按 concurrency 分批并发执行完整工具交互，逐批写入轨迹。
    with (
        (args.output / "trajectories.jsonl").open("w") as file,
        tqdm(total=len(rows), desc="Evaluating", unit="sample") as progress,
    ):
        for start in range(0, len(rows), args.concurrency):
            batch = rows[start : start + args.concurrency]
            trajectories = await asyncio.gather(
                *(
                    rollout(
                        row,
                        sampler,
                        tokenizer,
                        processor,
                        args.output / "images" / row["id"],
                        max_turns=args.max_turns,
                        max_tokens=args.max_tokens,
                        max_seq_len=args.max_seq_len,
                        temperature=args.temperature,
                        seed=args.seed + start + index,
                    )
                    for index, row in enumerate(batch)
                )
            )

            for result in trajectories:
                # PNG 单独保存；JSONL 保留逐轮文本、原始采样 token/logprob 和动作 mask。
                record = {
                    key: value
                    for key, value in result.items()
                    if key != "model_input"
                }
                file.write(json.dumps(record, ensure_ascii=False) + "\n")
                results.append({
                    key: record[key]
                    for key in ("task", "label", "prediction", "format_ok", "turns")
                })

            file.flush()
            progress.update(len(trajectories))

    # 4. 汇总各任务指标与整体指标，保存本次评测参数。
    metrics = classification_metrics(results)
    config = {
        **vars(args),
        "data": str(args.data),
        "output": str(args.output),
        "base_model": BASE_MODEL,
    }
    (args.output / "metrics.json").write_text(
        json.dumps({"config": config, **metrics}, ensure_ascii=False, indent=2)
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)

    # 数据、模型和评测产物。
    parser.add_argument(
        "--data",
        type=Path,
        default=Path(__file__).parent / "datasets/rl/bench_dev.jsonl",
    )
    parser.add_argument(
        "--model-path",
        help="留空评测 Base；SFT/RL 传入 sampler_path",
    )
    parser.add_argument("--output", type=Path, required=True)

    # 工具交互预算与采样参数。
    parser.add_argument("--concurrency", type=int, default=16)
    parser.add_argument("--max-turns", type=int, default=8)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--max-seq-len", type=int, default=16384)
    parser.add_argument("--temperature", type=float, default=0.6)
    parser.add_argument("--seed", type=int, default=42)

    asyncio.run(main(parser.parse_args()))
