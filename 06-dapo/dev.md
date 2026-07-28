# 06-dapo 开发计划：用 PyTRIO 复现 DAPO

> 目标：在同一套 PyTRIO 训练代码中实现 GRPO 和 DAPO，完成可复现、可消融的公平对照。

本项目复现 DAPO 的算法与训练现象，不追求复刻论文的 Qwen2.5-32B / AIME24=50 结果。训练固定使用 DAPO-Math-17K，正式评测固定使用 AIME25；模型、数据、优化器和评测配置在 GRPO/DAPO 间保持一致，只切换算法差异。

## Results

| Model | Average@12 | Pass@12 | Format |
|---|---:|---:|---:|
| Base | 41.11% | 56.67% | 46.67% |

## 一、对照设计

`train.py` 使用统一入口：

```bash
uv run python 06-dapo/train.py --algorithm grpo
uv run python 06-dapo/train.py --algorithm dapo
```

| 配置 | GRPO | DAPO |
|---|---|---|
| PPO clip | `[0.8, 1.2]` | `[0.8, 1.28]` |
| Sampling | 固定问题 batch，跳过退化组 | Dynamic Sampling，候选最多为目标 batch 的 2 倍 |
| Loss reduction | 先做 sequence mean，再跨样本平均 | 全 batch completion token mean |
| Overlong | 关闭 | Soft Overlong Punishment |

共同设置：无 KL；基础正确性 reward 为 ±1；advantage 使用 `(R - mean) / (std + 1e-8)`。

GRPO 和 DAPO 都走同一个 `forward_backward_custom` PPO objective，通过 preset 改 clip、reduction、sampling 和 overlong 配置，避免比较时混入不同 loss 实现。

## 二、代码结构

保留清晰模块边界，不拆成过多小文件：

```text
06-dapo/
├── prepare_data.py   # 准备 DAPO-Math-17K 与 AIME25
├── data.py           # 数据加载和循环游标
├── reward.py         # boxed 正确性奖励和长度惩罚
├── rollout.py        # group rollout、Dynamic Sampling、advantage
├── train.py          # CLI、preset、Datum、custom loss、训练与保存
├── eval.py           # dev smoke test / AIME25 的 avg@N、pass@N
├── analysis.py       # GRPO/DAPO 结果对比
├── tests/
│   └── test_dapo.py
├── dev.md
└── readme.md
```

训练主循环保持同步；`rollout.py` 内使用 `sample_async` 并发采样，不再维护两套重复的 sync/async 训练脚本。

## 三、核心实现

每个训练 step：

1. 保存当前权重并取得 sampling client。
2. 对每道题采样 `group_size` 条 completion，计算基础 reward 和长度惩罚。
3. GRPO 使用固定问题 batch；DAPO 丢弃全对/全错组，并在目标 batch 的 2 倍候选预算内继续补采。
4. 在完整 group 内计算标准化 advantage。
5. 构造包含 `target_tokens`、old `logprobs`、`advantages` 的 PyTRIO Datum，prompt token 的训练信号置零。
6. DAPO 候选预算耗尽后只训练已收集到的有效组；若有效组为 0，则跳过本 step 的 `forward_backward_custom` 和 `optim_step`。
7. 记录 SwanLab 指标并按间隔保存 state 和 sampler weights。

DAPO loss：

```text
ratio = exp(current_logprob - old_logprob)
objective = min(ratio * A, clip(ratio, 0.8, 1.28) * A)
loss = -sum(objective) / completion_token_count
```

PyTRIO 0.2.4 会根据 custom loss 的 `dL/dlogprob` 构造线性代理目标，使远端参数梯度与客户端定义的损失梯度一致。因此 custom callback 直接返回上面的 sample/token reduction 结果，不再额外按有效 token 数缩放。

Soft Overlong Punishment 在 `reward.py` 中实现，先计算基础正确性 reward，再加长度惩罚：

```text
shaped_reward = base_reward + length_penalty

penalty_start = max_tokens - overlong_cache
completion_len <= penalty_start:
    length_penalty = 0
penalty_start < completion_len <= max_tokens:
    length_penalty = -(completion_len - penalty_start) / overlong_cache
completion_len > max_tokens:
    length_penalty = -1
```

长度使用 `len(sequence.tokens)`，即与训练 Datum 相同的实际生成 token；不能按字符数计算，也不能只在 `stop_reason` 表示截断时启用。当前 `max_tokens=8192`、`overlong_cache=2048`，所以 6144 token 前不惩罚，7168 token 为 `-0.5`，8192 token 为 `-1`。

advantage 使用 shaped reward；Dynamic Sampling 仍按原始 `correct` 判断 `0 < correct_count < group_size`。即使一组全部答错但因长度不同产生不同 shaped reward，也必须过滤。日志分别记录 `base_reward`、`length_penalty` 和 `shaped_reward`。

## 四、数据与默认配置

- 训练数据固定使用 `BytedTsinghua-SIA/DAPO-Math-17k` 的指定 revision，由本项目的 `prepare_data.py` 独立下载、去重和切分。当前实测从 1,791,700 行中得到 17,176 道无冲突唯一题目。
- 按标准化后的 question 分组切分 DAPO-Math-17K，避免同题同时进入 train/dev；dev 取 50 条，只用于 smoke test。
- 正式效果评测固定使用独立的 AIME25：`yentinglin/aime_2025`，共 30 题；AIME25 不参与训练或超参数选择。
- Reward 使用 `math_verify + 最后一个 \boxed{}` 规则。
- 模型：`Qwen/Qwen3.5-4B`，LoRA rank 32。
- Adam：lr `4e-5`，betas `0.9/0.95`。
- `group_size=8`；GRPO 每步固定采样 16 组；DAPO 目标为 16 个有效组，候选题组默认最多采样 32 个。
- 默认总上下文约 12288 token：prompt 最多 4095 token，completion 最多 8192 token；`overlong_cache=2048`。这些默认值都可以通过命令行覆盖。

## 五、验证与实验

`tests/test_dapo.py` 至少覆盖：

- 对称/非对称 clip 在正负 advantage 下的梯度。
- sample-level 与 token-level reduction 的权重差异。
- custom loss 经 PyTRIO 代理目标转换后保持原始梯度，无额外缩放。
- Soft Overlong Punishment 在 6144/7168/8192 等区间边界的值。
- Dynamic Sampling 对全对、全错、混合组，以及“全错但 shaped reward 不同”组的处理。

先分别执行 GRPO/DAPO 的 1-step smoke test，再运行正式对照。端到端 smoke 使用正式的 `max_tokens=8192`；`1024` 只适合检查接口连通性，可能在生成 `\boxed{}` 前截断并使整组退化。除相同训练 step 外，还要比较相同 rollout token 数和 wall time，避免 Dynamic Sampling 的额外采样成本被隐藏。

主要指标：

- base/shaped reward、length penalty、accuracy、有效组比例和目标 batch 填充率；
- candidate/effective groups、oversample ratio；
- rollout tokens、生成长度、wall time；
- loss、upper/lower clip fraction；
- sampled-token surprisal 和 completion 多样性；
- AIME25 avg@N / pass@N。

PyTRIO 目前不能提供完整词表分布，因此不复刻论文的精确 generation entropy，只记录上述代理指标。

## 六、实施顺序

1. 完成 `prepare_data.py`、`data.py`、`reward.py`。
2. 完成统一的 `rollout.py` 和 `train.py`。
3. 先通过本地 loss/gradient 单测，再做远端 1-step smoke test。
4. 完成 AIME25 `eval.py`，对 base model 或传入的 LoRA sampler weights 使用同一评测配置。
5. 启动 GRPO/DAPO 对照实验并用 `analysis.py` 汇总。
6. 实验完成后编写 `readme.md`，再更新根 README。
