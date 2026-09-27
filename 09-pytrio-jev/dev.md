# Intern-Decision（pytrio-jev）复现笔记

> 复现目标：InternLM Intern-Decision 式判别决策模型——共享 state + 多字段 typed questions（choice / score / noul），一次前向输出各字段的校准概率分布，不生成文本。
> 路线选择：走 Intern-Decision 公开路线（**marker 占位符 + 候选符号限定 softmax**），不走 AgentJev 的判别头路线（自定义打分组头 + 软标签，pytrio 表达不了）。
>
> 参考：[Intern-Decision 仓库](https://github.com/InternLM/Intern-Decision)、[Jev 架构逆向](https://archerhume.com/posts/jevs-architecture-unmasked)、[Datawhale AgentJev 教程](https://mp.weixin.qq.com/s/F7i83rn8oDzQ-sg13MKwWA)

## 训练思路

| 项目 | 方案 | 与原版的差异 |
|---|---|---|
| 任务形态 | masked SFT（非 RL）：assistant 输入是含占位符的 JSON 骨架，答案只进 labels | 无 |
| 基座 | `Qwen/Qwen3.5-4B`（TRIO 目录内，与 Intern-Decision-4B 同系） | 原版另有 0.8B / 2B / 9B，TRIO 只有 4B / 9B |
| 参数效率 | LoRA rank 32，`train_mlp/attn/unembed=True` | **原版是全参数微调**（XTuner FSDP，lr 2e-6，2 epoch），TRIO 仅支持 LoRA |
| marker | 不加 special token（TRIO 服务端词表不可扩展），用已有单 token `decision`（id 61781）做占位符 | 原版新增 `<decision>` special token |
| Datum 构造 | `loss_fn="cross_entropy"`；labels/weights 只落在 marker 位置（因果右移后 = marker 前一位置预测答案符号），其余全 0 | 无（机制一致） |
| 共享 state | 一条记录 = 一个序列，全部字段一次前向同时监督；答案不出现在输入，字段间无答案泄漏 | 无 |
| 推理 | `sample(max_tokens=1, topk_prompt_logprobs=K)` 在 marker 位读候选 logprob → 限定 softmax ÷ T → choice 取 argmax / noul 取 p(yes) / score 取期望分 | 无（机制一致） |
| 温度校准 | calibration 划分上对逆温度二分搜 NLL 最小，T ∈ [0.01, 100]，绑定 checkpoint | 一致 |
| 顺序敏感性 | 契约固定顺序 + 可选做字段/选项排列增强（label 随符号映射重排） | 原版只靠契约 + 评测测量，未做增强 |

## 数据集

### 训练（定稿：typed-decisions train + ToolACE 1200）

| 数据 | 规模 | 说明 |
|---|---|---|
| `LocalLLaMA/typed-decisions` train split | 1200 案例 × 5 题 = 6000 题 | **主训练集**；4 个 workflow，覆盖 choice/score/noul；gold 软分布取 argmax 当硬标签；锁定 revision |
| `Team-ACE/ToolACE` | 采 1200 条 | **先按 id 剔除 310 条 eval 行再采样**；按 eval 行的转换口径转 canonical record（`state = {request, tools}`，choice 题 = 选哪个工具），训练/评测口径必须一致 |
| 自留 dev / calibration | 案例级切分 | 从 typed-decisions train 按案例级哈希确定性切分（不打散题目，参考 240/30/30 per workflow），跨划分做 state 文本哈希查重；calibration 行带 `validation_role` |

注意：noul 题型的训练信号只来自 typed-decisions（ToolACE 是纯 choice）；若 Jevbench 上 noul 偏弱，优先怀疑这一点。

### 评估（定稿：Jevbench×3 + Typed Decision + ToolACE，全部纯文本）

| 基准 | 规模 | Intern-Decision-4B 参考值 | 说明 |
|---|---|---|---|
| Jevbench Easy | 48 | 100.00% | **无训练集，零样本评测** |
| Jevbench Original | 72 | 98.61% | 同上 |
| Jevbench Hard | 111 | 73.87% | 同上；10 条 gold_probs 可算 TVD |
| Typed Decision test | 400 案例 / 2000 题 | 80.55% | 与官方表直接可比；注意我们是 specialist 模式（train/test 同 workflow），Jev 是零样本 |
| ToolACE | 310 | 96.45% | 训练集已剔除这 310 行 |

指标：accuracy、ECE（10 等宽 bin）、Brier（多类别求和）；score 题另记期望分 MAE。

## 文件结构

```text
09-pytrio-jev/
├── 00-prepare-data.py  # 下载 typed-decisions（锁 revision）→ canonical JSONL + 案例级切分（train/dev/calibration）
├── templates/
│   └── qwen3_5_jev.jinja # 钉死的 chat template（空 think 块），训练/推理共用，已验证与内置模板逐字节一致
├── data.py             # record → messages →(apply qwen3_5_jev.jinja)→ tokens/weights；构造时记录 marker 索引（不扫 token id）
├── train.py            # 异步 LoRA SFT 主循环：cross_entropy + optim_step + SwanLab 记录
├── inference.py        # topk_prompt_logprobs 受限 softmax 推理（choice/noul/score 三种输出映射）
├── calibrate.py        # calibration 划分上拟合温度 T（NLL 二分搜索），输出 calibration.json
├── eval.py             # 五项基准评测（Jevbench×3 + Typed Decision + ToolACE；先选优/校准，最后才读 test）
├── analysis.py         # 汇总 SwanLab 与评测结果
├── start.md            # 启动命令
├── dev.md              # 本文件
└── readme.md           # 原理、结果与边界
```

## 防污染红线

- typed-decisions 的 train/test 官方独立生成（不同 seed、train id 带 `tr_` 前缀），可直接"train 训 / test 评"；ToolACE 的 310 条 eval 行、Jevbench 全部 231 条**一律不进训练**。
- 温度只在校准划分上拟合；测试集在所有决策（checkpoint 选优、T）冻结后才读。
