"""在 AIME25 上公平评测 base、GRPO 或 DAPO sampler weights。

Base：

    uv run python 06-dapo/eval.py --algorithm base

Checkpoint：

    uv run python 06-dapo/eval.py \
        --algorithm dapo \
        --checkpoint-step 100 \
        --model-path trio://<sampler-weights-path>
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
import re
from typing import Any

from datasets import Dataset, DatasetDict, load_from_disk
import pytrio as trio
from tqdm import tqdm

from rollout import build_prompt_tokens, stop_sequences


trio.configure(sampling_timeout=18000)

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET_PATH = (
    SCRIPT_DIR.parent / "04-opsd" / "datasets" / "aime_2025"
)
EXPECTED_ROWS = 30


def parse_args() -> argparse.Namespace:
    """解析 AIME25 评测参数，并避免错标 base/checkpoint。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--algorithm",
        choices=["base", "grpo", "dapo"],
        default="base",
    )
    parser.add_argument("--checkpoint-step", type=int, default=0)
    parser.add_argument(
        "--dataset-path",
        type=Path,
        default=DEFAULT_DATASET_PATH,
    )
    parser.add_argument("--base-model", default="Qwen/Qwen3.5-4B")
    parser.add_argument(
        "--model-path",
        default=None,
        help="save_weights_for_sampler 返回的 trio:// 路径",
    )
    parser.add_argument("--val-n", type=int, default=12)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--concurrency", type=int, default=15)
    parser.add_argument("--max-prompt-tokens", type=int, default=4095)
    parser.add_argument("--max-tokens", type=int, default=12288)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--top-k", type=int, default=-1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    for name in (
        "val_n",
        "concurrency",
        "max_prompt_tokens",
        "max_tokens",
    ):
        if getattr(args, name) < 1:
            raise ValueError(f"--{name.replace('_', '-')} must be >= 1")
    if args.limit < 0 or args.checkpoint_step < 0:
        raise ValueError("--limit and --checkpoint-step must be >= 0")
    if args.temperature < 0 or not 0 < args.top_p <= 1:
        raise ValueError("invalid sampling temperature/top-p")
    if args.algorithm == "base":
        if args.model_path is not None or args.checkpoint_step != 0:
            raise ValueError("base evaluation must not set model path/checkpoint step")
        default_name = "aime25-base.jsonl"
    else:
        if not args.model_path:
            raise ValueError("GRPO/DAPO evaluation requires --model-path")
        if args.checkpoint_step < 1:
            raise ValueError("GRPO/DAPO evaluation requires --checkpoint-step >= 1")
        default_name = (
            f"aime25-{args.algorithm}-step{args.checkpoint_step}.jsonl"
        )
    args.output = args.output or SCRIPT_DIR / "eval-results" / default_name
    return args


def load_aime25(path: Path, limit: int) -> Dataset:
    """读取本地固定版本 AIME25，并验证 30 题结构。"""
    if not path.exists():
        raise FileNotFoundError(
            f"找不到 AIME25 数据：{path}\n"
            "请先运行：uv run python 04-opsd/00-datasets.py --only aime25"
        )
    loaded = load_from_disk(str(path))
    dataset = loaded["train"] if isinstance(loaded, DatasetDict) else loaded
    if not isinstance(dataset, Dataset):
        raise TypeError(f"期望 Dataset，实际得到 {type(dataset)!r}")
    missing = sorted({"problem", "answer"} - set(dataset.column_names))
    if missing:
        raise ValueError(f"AIME25 缺少字段 {missing}")
    if len(dataset) != EXPECTED_ROWS:
        raise ValueError(
            f"AIME25 应有 {EXPECTED_ROWS} 题，实际为 {len(dataset)} 题"
        )
    if limit > 0:
        dataset = dataset.select(range(min(limit, len(dataset))))
    return dataset


def extract_last_boxed(text: str) -> str | None:
    """提取最后一个完整 ``\\boxed{...}``，支持嵌套花括号。"""
    end = len(text)
    while True:
        start = text.rfind("\\boxed", 0, end)
        if start < 0:
            return None
        left = text.find("{", start)
        if left < 0:
            end = start
            continue
        depth = 0
        for index in range(left, len(text)):
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
                if depth == 0:
                    return text[left + 1 : index].strip()
        end = start


def normalize_aime_answer(answer: str | None) -> str | None:
    """把 AIME 答案规范为无前导零的整数字符串。"""
    if answer is None:
        return None
    cleaned = answer.strip().replace(",", "").replace("$", "")
    cleaned = re.sub(r"\\(?:text|mathrm)\s*\{([^{}]*)\}", r"\1", cleaned)
    match = re.fullmatch(r"\s*([+-]?\d+)\s*", cleaned)
    return str(int(match.group(1))) if match is not None else None


async def evaluate_problem(
    index: int,
    row: dict[str, Any],
    sampling_client: Any,
    tokenizer: Any,
    args: argparse.Namespace,
    semaphore: asyncio.Semaphore,
) -> dict[str, Any]:
    """并发采样一道题的 N 个答案。"""
    problem = str(row["problem"]).strip()
    ground_truth = normalize_aime_answer(str(row["answer"]))
    if ground_truth is None:
        raise ValueError(
            f"AIME25 第 {index} 题 ground truth 不是整数：{row['answer']!r}"
        )
    prompt_tokens = build_prompt_tokens(
        tokenizer,
        problem,
        max_prompt_tokens=args.max_prompt_tokens,
    )
    params = trio.SamplingParams(
        max_tokens=args.max_tokens,
        seed=args.seed + index,
        temperature=args.temperature,
        top_p=args.top_p,
        top_k=args.top_k,
        stop=stop_sequences(tokenizer),
    )
    async with semaphore:
        response = await sampling_client.sample_async(
            prompt=trio.ModelInput.from_ints(prompt_tokens),
            num_samples=args.val_n,
            sampling_params=params,
            return_text=True,
        )
    if len(response.sequences) != args.val_n:
        raise RuntimeError(
            f"AIME25 第 {index} 题请求 {args.val_n} 条 completion，"
            f"实际返回 {len(response.sequences)} 条"
        )

    generations: list[dict[str, Any]] = []
    for sequence in response.sequences:
        text = sequence.text
        if text is None:
            text = tokenizer.decode(
                sequence.tokens,
                skip_special_tokens=False,
            )
        boxed = extract_last_boxed(str(text))
        predicted = normalize_aime_answer(boxed)
        generations.append(
            {
                "predicted_answer": predicted,
                "boxed_answer": boxed,
                "correct": predicted == ground_truth,
                "formatted": boxed is not None,
                "completion_tokens": len(sequence.tokens),
                "stop_reason": str(getattr(sequence, "stop_reason", "")),
                "text": str(text),
            }
        )

    return {
        "type": "problem",
        "problem_id": int(row.get("id", index)),
        "problem": problem,
        "ground_truth": ground_truth,
        "val_n": args.val_n,
        "num_correct": sum(int(item["correct"]) for item in generations),
        "pass_at_n": any(item["correct"] for item in generations),
        "generations": generations,
    }


def summarize(
    results: list[dict[str, Any]],
    args: argparse.Namespace,
) -> dict[str, Any]:
    """聚合 Average@N、Pass@N、格式率与生成长度。"""
    generations = [
        generation
        for result in results
        for generation in result["generations"]
    ]
    total_generations = len(generations)
    total_correct = sum(result["num_correct"] for result in results)
    passed_problems = sum(int(result["pass_at_n"]) for result in results)
    return {
        "type": "summary",
        "dataset": "yentinglin/aime_2025",
        "algorithm": args.algorithm,
        "checkpoint_step": args.checkpoint_step,
        "base_model": args.base_model,
        "model_path": args.model_path,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "top_k": args.top_k,
        "max_tokens": args.max_tokens,
        "val_n": args.val_n,
        "problems": len(results),
        "generations": total_generations,
        "average_at_n": (
            total_correct / total_generations if total_generations else 0.0
        ),
        "pass_at_n": (
            passed_problems / len(results) if results else 0.0
        ),
        "format_rate": (
            sum(int(item["formatted"]) for item in generations)
            / total_generations
            if total_generations
            else 0.0
        ),
        "mean_completion_tokens": (
            sum(int(item["completion_tokens"]) for item in generations)
            / total_generations
            if total_generations
            else 0.0
        ),
        "correct_generations": total_correct,
        "passed_problems": passed_problems,
    }


async def evaluate(args: argparse.Namespace) -> None:
    """创建采样 client，完成 AIME25 评测并落盘。"""
    dataset = load_aime25(args.dataset_path, args.limit)
    service_client = trio.ServiceClient()
    sampling_client = await service_client.create_sampling_client_async(
        base_model=args.base_model,
        model_path=args.model_path,
    )
    tokenizer = sampling_client.get_tokenizer()
    semaphore = asyncio.Semaphore(args.concurrency)

    with tqdm(total=len(dataset), desc="AIME25", unit="problem") as progress:

        async def evaluate_and_track(
            index: int,
            row: dict[str, Any],
        ) -> dict[str, Any]:
            result = await evaluate_problem(
                index,
                row,
                sampling_client,
                tokenizer,
                args,
                semaphore,
            )
            progress.update(1)
            return result

        results = list(
            await asyncio.gather(
                *(
                    evaluate_and_track(index, row)
                    for index, row in enumerate(dataset)
                )
            )
        )

    summary = summarize(results, args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as file:
        for result in results:
            file.write(json.dumps(result, ensure_ascii=False) + "\n")
        file.write(json.dumps(summary, ensure_ascii=False) + "\n")

    print(
        f"AIME25 [{args.algorithm}] Average@{args.val_n}: "
        f"{summary['average_at_n']:.2%} | "
        f"Pass@{args.val_n}: {summary['pass_at_n']:.2%} | "
        f"Format: {summary['format_rate']:.2%}"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Results: {args.output}")


if __name__ == "__main__":
    asyncio.run(evaluate(parse_args()))
