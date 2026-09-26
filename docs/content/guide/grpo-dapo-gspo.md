---
title: GRPO、DAPO 与 GSPO 有什么区别？从 Loss 到训练实现
description: 对照 GRPO、DAPO 和 GSPO 的优化单位、裁剪、动态采样与当前实验边界，找到对应公式、代码和快速启动入口。
---

# GRPO、DAPO 与 GSPO 有什么区别？

三个章节都从同一条主线出发：对一道题采样一组回答，计算可验证的 reward，用组内相对表现构造 advantage，再更新策略。理解差异时，可以依次看重要性比率、裁剪、样本筛选和 loss 的归一化方式。

本页整理这个仓库的阅读入口。各章使用的模型、数据与训练预算并未完全对齐，现有分数无法用于排列三个方法的优劣。

| 观察点 | GRPO 章节 | DAPO 章节 | GSPO 章节 |
| --- | --- | --- | --- |
| 首先理解什么 | 组采样、reward、advantage 与策略更新 | 四项训练改进如何连接起来 | sequence-level 重要性比率与裁剪 |
| 比率与裁剪 | 在实验中比较 importance sampling、PPO 与 CISPO | Clip-Higher 使用非对称裁剪范围 | 对一条回答的 token log-ratio 求均值再取指数，按序列裁剪 |
| 数据筛选 | 先走通基本训练循环 | Dynamic Sampling 过滤原始正确性全对或全错的 group，再补采 | 当前实现不叠加 Dynamic Sampling |
| 值得记录的成本 | loss 选择怎样改变训练行为 | 无效 completion 已经消耗生成时间，补采也有等待成本 | 序列长度、clip fraction 与原始 batch 的归一化口径 |
| 本仓库的边界 | GSM8K 上的实验与代码 | 当前同步训练循环中的收益和成本 | 核心 loss 与训练链路，未复现论文规模及 MoE 稳定性实验 |

## 先看 GRPO：一次更新是怎么发生的？

从 [GRPO 原理与代码实战](/experiments/grpo/) 阅读采样、奖励和更新的连接方式，再用[快速启动](/experiments/grpo/run)跑通代码。遇到 logprob、importance ratio 或 clipping 时，可以回到[损失函数直觉](/experiments/loss-functions/)。

实验中切换 loss 时，记录相同的模型、数据、采样预算与随机种子；否则观察到的变化可能来自其他条件。

## 再看 DAPO：有效样本从哪里来？

[DAPO 章节](/experiments/dapo/)分别讨论 Clip-Higher、Dynamic Sampling、Token-level Policy Gradient Loss 和 Soft Overlong Punishment。这里的动态采样依据是原始正确性，advantage 则使用加入长度惩罚后的 reward，两者需要区分。

本地实现限制补采轮数，并记录 rollout 的实际耗时。被过滤的回答虽然不进入最终 loss，但已消耗采样资源。运行入口见 [DAPO 快速启动](/experiments/dapo/run)。

## 最后看 GSPO：为什么按整条回答计算比率？

[GSPO 章节](/experiments/gspo/)将 token log-ratio 的均值取指数，得到长度归一化的 sequence ratio。整条回答共享一个裁剪判断；它与 token-level ratio 约束的量不同，裁剪阈值不能直接照搬。

当前章节记录了核心 loss、训练链路和 AIME25 评测，也明确缺少同条件 GRPO 对照。组内全对或全错的样本会退化为零 advantage；跳过这些序列的梯度计算时，仍要保持原始归一化口径。运行入口见 [GSPO 快速启动](/experiments/gspo/run)。

## 怎样做一组有意义的比较？

先固定基础模型、训练和评测数据、训练预算、采样设置与答案判定规则。再选择要比较的变量，并同时记录正确率、格式遵循率、输出长度、采样成本和总耗时。不同 checkpoint、不同指标对应的最佳结果可能不同。

这个仓库已经提供三条可检查的训练入口。完整公平比较仍需要补做对照实验，现有章节的数字应在各自设置下解读。
