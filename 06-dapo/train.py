"""用一套 PyTRIO 训练入口对照 GRPO 与 DAPO。

快速接口试跑（短 completion 可能使整组退化并跳过更新）：

    uv run python 06-dapo/train.py \
        --algorithm dapo \
        --max-steps 1 \
        --groups-per-step 2 \
        --group-size 4 \
        --max-tokens 1024 \
        --overlong-cache 256 \
        --swanlab-mode disabled
"""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Callable
from dataclasses import asdict, dataclass, replace
from importlib.metadata import version as package_version
import json
from pathlib import Path
from time import perf_counter
from typing import Any, Literal

import numpy as np
import pytrio as trio
import swanlab
import torch
from tqdm import tqdm

from data import ExampleCursor, shuffled_examples
from rollout import (
    Algorithm,
    RolloutBatch,
    RolloutConfig,
    RolloutGroup,
    collect_rollout_batch,
)


trio.configure(timeout=600, sampling_timeout=18000)

Reduction = Literal["sample", "token"]


@dataclass(frozen=True)
class AlgorithmPreset:
    """GRPO/DAPO 公平对照中唯一允许变化的算法开关。"""

    name: Algorithm
    clip_low: float
    clip_high: float
    reduction: Reduction
    dynamic_sampling: bool
    soft_overlong: bool


PRESETS: dict[Algorithm, AlgorithmPreset] = {
    "grpo": AlgorithmPreset(
        name="grpo",
        clip_low=0.8,
        clip_high=1.2,
        reduction="sample",
        dynamic_sampling=False,
        soft_overlong=False,
    ),
    "dapo": AlgorithmPreset(
        name="dapo",
        clip_low=0.8,
        clip_high=1.28,
        reduction="token",
        dynamic_sampling=True,
        soft_overlong=True,
    ),
}


@dataclass(frozen=True)
class PPOTrainingDatum:
    """PyTRIO Datum 加上 custom PPO loss 的 completion mask。"""

    datum: trio.Datum
    completion_mask: np.ndarray
    completion_tokens: int

    def forward_datum(self) -> trio.Datum:
        """custom loss 首次 cross-entropy forward 只需要 target token。"""
        return trio.Datum(
            model_input=self.datum.model_input,
            loss_fn_inputs={
                "target_tokens": self.datum.loss_fn_inputs["target_tokens"],
            },
        )


def preset_for(algorithm: Algorithm) -> AlgorithmPreset:
    """返回算法 preset。"""
    return PRESETS[algorithm]


def build_ppo_datum(
    prompt_tokens: list[int],
    completion_tokens: list[int],
    old_logprobs: list[float],
    advantage: float,
) -> PPOTrainingDatum:
    """构造右移对齐的 prompt-masked PPO Datum。"""
    if len(prompt_tokens) < 1:
        raise ValueError("prompt_tokens must not be empty")
    if not completion_tokens:
        raise ValueError("completion_tokens must not be empty")
    if len(completion_tokens) != len(old_logprobs):
        raise ValueError("completion token/logprob lengths must match")

    observation_len = len(prompt_tokens) - 1
    input_tokens = prompt_tokens + completion_tokens[:-1]
    target_tokens = [0] * observation_len + completion_tokens
    padded_logprobs = [0.0] * observation_len + old_logprobs
    padded_advantages = [0.0] * observation_len + [
        advantage
    ] * len(completion_tokens)
    completion_mask = np.asarray(
        [False] * observation_len + [True] * len(completion_tokens),
        dtype=np.bool_,
    )
    if not (
        len(input_tokens)
        == len(target_tokens)
        == len(padded_logprobs)
        == len(padded_advantages)
        == len(completion_mask)
    ):
        raise ValueError("PPO datum fields must have the same token length")

    return PPOTrainingDatum(
        datum=trio.Datum(
            model_input=trio.ModelInput.from_ints(input_tokens),
            loss_fn_inputs={
                "target_tokens": np.asarray(target_tokens, dtype=np.int64),
                "logprobs": np.asarray(padded_logprobs, dtype=np.float32),
                "advantages": np.asarray(padded_advantages, dtype=np.float32),
            },
        ),
        completion_mask=completion_mask,
        completion_tokens=len(completion_tokens),
    )


def build_training_datums(groups: list[RolloutGroup]) -> list[PPOTrainingDatum]:
    """把所有有效 group 的 completion 转换为训练 Datum。"""
    return [
        build_ppo_datum(
            group.prompt_tokens,
            sample.tokens,
            sample.logprobs,
            sample.advantage,
        )
        for group in groups
        for sample in group.samples
    ]


def _tensor_values(datum: trio.Datum, key: str) -> list[float]:
    """从 PyTRIO TensorData 中读取 float 数组。"""
    return [float(value) for value in datum.loss_fn_inputs[key].data]


def make_ppo_loss_fn(
    training_datums: list[PPOTrainingDatum],
    preset: AlgorithmPreset,
) -> Callable[[list[trio.Datum], list[Any]], tuple[Any, dict[str, float]]]:
    """创建同时支持 GRPO sample mean 与 DAPO token mean 的 PPO loss。"""

    def ppo_loss_fn(
        data: list[trio.Datum],
        current_logprobs_list: list[Any],
    ) -> tuple[Any, dict[str, float]]:
        if not (
            len(data)
            == len(current_logprobs_list)
            == len(training_datums)
        ):
            raise ValueError("PPO loss got mismatched batch lengths")
        if not training_datums:
            raise ValueError("PPO loss requires at least one datum")

        sequence_losses: list[torch.Tensor] = []
        token_objectives: list[torch.Tensor] = []
        ratio_chunks: list[torch.Tensor] = []
        selected_clip_chunks: list[torch.Tensor] = []
        lower_clip_chunks: list[torch.Tensor] = []
        upper_clip_chunks: list[torch.Tensor] = []
        gradient_active_tokens = 0

        for item, current_values in zip(
            training_datums,
            current_logprobs_list,
            strict=True,
        ):
            current = current_values.float().reshape(-1)
            device = current.device
            old = torch.as_tensor(
                _tensor_values(item.datum, "logprobs"),
                dtype=torch.float32,
                device=device,
            )
            advantages = torch.as_tensor(
                _tensor_values(item.datum, "advantages"),
                dtype=torch.float32,
                device=device,
            )
            mask = torch.as_tensor(
                item.completion_mask,
                dtype=torch.bool,
                device=device,
            )
            if not (len(current) == len(old) == len(advantages) == len(mask)):
                raise ValueError("PPO datum/logprob fields must have equal lengths")

            current = current[mask]
            old = old[mask]
            advantages = advantages[mask]
            if current.numel() != item.completion_tokens:
                raise ValueError("completion mask does not match completion_tokens")

            ratio = torch.exp(current - old)
            clipped_ratio = torch.clamp(
                ratio,
                min=preset.clip_low,
                max=preset.clip_high,
            )
            unclipped_objective = ratio * advantages
            clipped_objective = clipped_ratio * advantages
            objective = torch.minimum(unclipped_objective, clipped_objective)

            token_objectives.append(objective)
            sequence_losses.append(-objective.mean())
            detached_ratio = ratio.detach()
            selected_clip = (
                clipped_objective.detach() < unclipped_objective.detach()
            )
            ratio_chunks.append(detached_ratio)
            selected_clip_chunks.append(selected_clip.float())
            lower_clip_chunks.append(
                ((detached_ratio < preset.clip_low) & (advantages < 0)).float()
            )
            upper_clip_chunks.append(
                ((detached_ratio > preset.clip_high) & (advantages > 0)).float()
            )
            gradient_active_tokens += int(
                ((advantages != 0) & ~selected_clip).sum().item()
            )

        if preset.reduction == "sample":
            ppo_loss = torch.stack(sequence_losses).mean()
        else:
            ppo_loss = -torch.cat(token_objectives).mean()

        # forward_backward_custom 会把 -dL/dlogprob 转成 CE weights；远端 CE
        # 再按非零 weights 的 token 数归一化。先乘回相同分母，远端归一化后
        # 才能恢复这里定义的 sample/token reduction，而不是被二次缩小。
        pytrio_gradient_scale = max(gradient_active_tokens, 1)
        loss_for_pytrio = ppo_loss * pytrio_gradient_scale

        ratios = torch.cat(ratio_chunks)
        selected_clips = torch.cat(selected_clip_chunks)
        lower_clips = torch.cat(lower_clip_chunks)
        upper_clips = torch.cat(upper_clip_chunks)
        metrics = {
            "ppo/loss": float(ppo_loss.detach().item()),
            "ppo/ratio_mean": float(ratios.mean().item()),
            "ppo/clip_fraction": float(selected_clips.mean().item()),
            "ppo/lower_clip_fraction": float(lower_clips.mean().item()),
            "ppo/upper_clip_fraction": float(upper_clips.mean().item()),
            "ppo/train_tokens": float(ratios.numel()),
            "ppo/gradient_active_tokens": float(gradient_active_tokens),
            "ppo/pytrio_gradient_scale": float(pytrio_gradient_scale),
            "ppo/sequences": float(len(training_datums)),
            "ppo/clip_low": preset.clip_low,
            "ppo/clip_high": preset.clip_high,
        }
        return loss_for_pytrio, metrics

    return ppo_loss_fn


def mean(values: list[float]) -> float:
    """空列表安全的均值。"""
    return sum(values) / len(values) if values else 0.0


def rollout_metrics(
    rollout_batch: RolloutBatch,
    training_datums: list[PPOTrainingDatum],
    *,
    data_cursor_consumed: int,
) -> dict[str, float]:
    """汇总 reward、采样成本、长度和多样性指标。"""
    samples = [
        sample
        for group in rollout_batch.candidate_groups
        for sample in group.samples
    ]
    train_samples = [
        sample for group in rollout_batch.train_groups for sample in group.samples
    ]
    completion_lengths = [
        float(sample.reward.completion_tokens) for sample in samples
    ]
    all_logprobs = [
        logprob for sample in samples for logprob in sample.logprobs
    ]
    unique_rates = [
        len({sample.text for sample in group.samples}) / max(len(group.samples), 1)
        for group in rollout_batch.candidate_groups
    ]
    max_tokens = max(completion_lengths, default=0.0)

    return {
        "reward/base_mean": mean(
            [sample.reward.base_reward for sample in samples]
        ),
        "reward/length_penalty_mean": mean(
            [sample.reward.length_penalty for sample in samples]
        ),
        "reward/shaped_mean": mean(
            [sample.reward.shaped_reward for sample in samples]
        ),
        "reward/accuracy": mean(
            [float(sample.reward.correct) for sample in samples]
        ),
        "reward/format_rate": mean(
            [float(sample.reward.valid_format) for sample in samples]
        ),
        "rollout/candidate_groups": float(len(rollout_batch.candidate_groups)),
        "rollout/effective_groups": float(len(rollout_batch.train_groups)),
        "rollout/effective_group_ratio": rollout_batch.effective_group_ratio,
        "rollout/oversample_ratio": rollout_batch.oversample_ratio,
        "rollout/completions": float(len(samples)),
        "rollout/train_completions": float(len(train_samples)),
        "rollout/completion_tokens": float(sum(completion_lengths)),
        "rollout/train_completion_tokens": float(
            sum(item.completion_tokens for item in training_datums)
        ),
        "rollout/mean_completion_tokens": mean(completion_lengths),
        "rollout/max_completion_tokens": max_tokens,
        "rollout/mean_sampled_token_surprisal": (
            -mean(all_logprobs) if all_logprobs else 0.0
        ),
        "rollout/unique_completion_rate": mean(unique_rates),
        "train/datums": float(len(training_datums)),
        "train/data_cursor_consumed": float(data_cursor_consumed),
    }


def merge_trainer_metrics(result: Any) -> dict[str, float]:
    """保留 custom PPO 指标，并为 PyTRIO 后端指标增加前缀。"""
    metrics: dict[str, float] = {}
    for key, value in dict(result.metrics).items():
        if not isinstance(value, (int, float, np.number)):
            continue
        output_key = key if key.startswith("ppo/") else f"trainer/{key}"
        metrics[output_key] = float(value)
    return metrics


def serializable_config(args: argparse.Namespace) -> dict[str, Any]:
    """将 Path 转成 SwanLab 可序列化配置。"""
    return {
        key: str(value) if isinstance(value, Path) else value
        for key, value in vars(args).items()
    }


def initialize_metrics_file(path: Path) -> None:
    """为本次运行创建空的本地 JSONL 指标文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


def append_metrics(path: Path, record: dict[str, Any]) -> None:
    """在远端 SwanLab 之外保留一份可供 analysis.py 使用的指标。"""
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def save_checkpoint(training_client: Any, name: str) -> dict[str, str]:
    """同时保存可续训 state 与可评测 sampler weights。"""
    state = training_client.save_state(name=f"{name}-state").result()
    weights = training_client.save_weights_for_sampler(
        name=f"{name}-sampler-weights"
    ).result()
    paths = {"state": state.path, "sampler_weights": weights.path}
    print(f"Saved state: {paths['state']}")
    print(f"Saved sampler weights: {paths['sampler_weights']}")
    return paths


def parse_args() -> argparse.Namespace:
    """解析并校验统一训练入口参数。"""
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--algorithm", choices=sorted(PRESETS), required=True)
    parser.add_argument("--max-steps", type=int, required=True)
    parser.add_argument(
        "--data",
        type=Path,
        default=script_dir / "datasets" / "train.jsonl",
    )
    parser.add_argument("--max-train-samples", type=int, default=0)
    parser.add_argument("--base-model", default="Qwen/Qwen3.5-4B")
    parser.add_argument("--lora-rank", type=int, default=32)
    parser.add_argument("--groups-per-step", type=int, default=16)
    parser.add_argument("--group-size", type=int, default=8)
    parser.add_argument("--max-candidate-multiplier", type=int, default=8)
    parser.add_argument("--max-prompt-tokens", type=int, default=4095)
    parser.add_argument("--max-tokens", type=int, default=12288)
    parser.add_argument("--overlong-cache", type=int, default=2048)
    parser.add_argument("--rollout-concurrency", type=int, default=16)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--top-k", type=int, default=-1)
    parser.add_argument("--learning-rate", type=float, default=4e-5)
    parser.add_argument("--beta1", type=float, default=0.9)
    parser.add_argument("--beta2", type=float, default=0.95)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--save-every", type=int, default=25)
    parser.add_argument("--run-name", default=None)
    parser.add_argument(
        "--metrics-output",
        type=Path,
        default=None,
        help="本地 step 指标 JSONL；默认写入 06-dapo/results/<run-name>.jsonl",
    )
    parser.add_argument(
        "--swanlab-project",
        default="llm-agent-rl-lab-dapo",
    )
    parser.add_argument("--swanlab-workspace", default=None)
    parser.add_argument(
        "--swanlab-mode",
        choices=["online", "local", "offline", "disabled"],
        default="online",
    )
    args = parser.parse_args()

    positive_names = (
        "max_steps",
        "lora_rank",
        "groups_per_step",
        "group_size",
        "max_candidate_multiplier",
        "max_prompt_tokens",
        "max_tokens",
        "overlong_cache",
        "rollout_concurrency",
    )
    for name in positive_names:
        if getattr(args, name) < 1:
            raise ValueError(f"--{name.replace('_', '-')} must be >= 1")
    if args.group_size < 2:
        raise ValueError("--group-size must be >= 2")
    if args.overlong_cache > args.max_tokens:
        raise ValueError("--overlong-cache must not exceed --max-tokens")
    if args.max_train_samples < 0 or args.save_every < 0:
        raise ValueError("--max-train-samples and --save-every must be >= 0")
    if args.temperature < 0 or not 0 < args.top_p <= 1:
        raise ValueError("invalid sampling temperature/top-p")

    args.run_name = args.run_name or f"{args.algorithm}-qwen35-4b"
    args.metrics_output = args.metrics_output or (
        script_dir / "results" / f"{args.run_name}.jsonl"
    )
    return args


def run_training(args: argparse.Namespace) -> None:
    """执行同步训练循环；每个 step 内部并发 rollout。"""
    preset = preset_for(args.algorithm)
    examples = shuffled_examples(args.data, args.seed)
    if args.max_train_samples > 0:
        examples = examples[: args.max_train_samples]
    cursor = ExampleCursor(examples)
    initialize_metrics_file(args.metrics_output)

    service_client = trio.ServiceClient()
    training_client = service_client.create_lora_training_client(
        base_model=args.base_model,
        rank=args.lora_rank,
        seed=args.seed,
    )
    tokenizer = training_client.get_tokenizer()
    rollout_config = RolloutConfig(
        group_size=args.group_size,
        max_prompt_tokens=args.max_prompt_tokens,
        max_tokens=args.max_tokens,
        overlong_cache=args.overlong_cache,
        temperature=args.temperature,
        top_p=args.top_p,
        top_k=args.top_k,
        concurrency=args.rollout_concurrency,
        seed=args.seed,
    )
    adam = trio.AdamParams(
        learning_rate=args.learning_rate,
        beta1=args.beta1,
        beta2=args.beta2,
    )
    run = swanlab.init(
        project=args.swanlab_project,
        workspace=args.swanlab_workspace,
        name=args.run_name,
        mode=args.swanlab_mode,
        config={
            **serializable_config(args),
            "preset": asdict(preset),
            "dataset_size": len(examples),
            "pytrio_version": package_version("pytrio"),
            "swanlab_version": package_version("swanlab"),
        },
        tags=["PyTRIO", args.algorithm.upper(), "DAPO-Math-17K"],
        log_dir=str(Path(__file__).resolve().parent / "swanlog"),
    )

    try:
        with tqdm(
            total=args.max_steps,
            desc=f"Training {args.algorithm.upper()}",
            unit="step",
        ) as progress:
            for step in range(args.max_steps):
                started = perf_counter()
                progress.set_postfix(phase="sampler", refresh=True)
                sampling_client = (
                    training_client.save_weights_and_get_sampling_client()
                )

                progress.set_postfix(phase="rollout", refresh=True)
                max_candidate_groups = (
                    args.groups_per_step * args.max_candidate_multiplier
                )
                step_rollout_config = replace(
                    rollout_config,
                    seed=args.seed + step * max_candidate_groups,
                )
                rollout_batch = asyncio.run(
                    collect_rollout_batch(
                        sampling_client,
                        tokenizer,
                        cursor.take,
                        algorithm=args.algorithm,
                        requested_groups=args.groups_per_step,
                        config=step_rollout_config,
                        max_candidate_groups=max_candidate_groups,
                    )
                )
                training_datums = build_training_datums(
                    rollout_batch.train_groups
                )

                trainer_result = None
                if training_datums:
                    progress.set_postfix(phase="backward", refresh=True)
                    forward_datums = [
                        item.forward_datum() for item in training_datums
                    ]
                    trainer_result = training_client.forward_backward_custom(
                        forward_datums,
                        make_ppo_loss_fn(training_datums, preset),
                    ).result()
                    progress.set_postfix(phase="optimizer", refresh=True)
                    training_client.optim_step(adam).result()

                metrics = rollout_metrics(
                    rollout_batch,
                    training_datums,
                    data_cursor_consumed=cursor.consumed,
                )
                if trainer_result is not None:
                    metrics.update(merge_trainer_metrics(trainer_result))
                metrics["train/update_skipped"] = float(not training_datums)
                metrics["train/learning_rate"] = args.learning_rate

                checkpoint_paths: dict[str, str] | None = None
                if args.save_every > 0 and (step + 1) % args.save_every == 0:
                    progress.set_postfix(phase="checkpoint", refresh=True)
                    checkpoint_paths = save_checkpoint(
                        training_client,
                        f"{args.run_name}-step-{step + 1}",
                    )

                metrics["time/step_seconds"] = perf_counter() - started
                swanlab.log(metrics, step=step)
                append_metrics(
                    args.metrics_output,
                    {
                        "type": "train_step",
                        "algorithm": args.algorithm,
                        "step": step + 1,
                        **metrics,
                        "checkpoint": checkpoint_paths,
                    },
                )

                progress.update(1)
                progress.set_postfix(
                    reward=f"{metrics['reward/shaped_mean']:.3f}",
                    effective=(
                        f"{int(metrics['rollout/effective_groups'])}/"
                        f"{int(metrics['rollout/candidate_groups'])}"
                    ),
                    step_s=f"{metrics['time/step_seconds']:.1f}",
                    refresh=True,
                )
                tqdm.write(
                    f"step={step + 1}/{args.max_steps} "
                    f"algorithm={args.algorithm} "
                    f"reward={metrics['reward/shaped_mean']:.3f} "
                    f"accuracy={metrics['reward/accuracy']:.3f} "
                    f"groups={int(metrics['rollout/effective_groups'])}/"
                    f"{int(metrics['rollout/candidate_groups'])} "
                    f"tokens={int(metrics['rollout/completion_tokens'])}"
                )

        final_paths = save_checkpoint(
            training_client,
            f"{args.run_name}-final",
        )
        swanlab.log(
            {
                "save/state_path": swanlab.Text(final_paths["state"]),
                "save/sampler_weights_path": swanlab.Text(
                    final_paths["sampler_weights"]
                ),
            },
            step=args.max_steps,
        )
    except Exception as error:
        run.finish(state="crashed", error=str(error))
        raise
    else:
        run.finish()


if __name__ == "__main__":
    run_training(parse_args())
