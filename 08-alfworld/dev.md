# ALFWorld GiGPO 复现思路

首版先复现 text-only ALFWorld 上的 GiGPO 训练闭环，并用同样的 rollout 预算与 GRPO 对比；暂不追求论文分数的逐项复刻。

## 整体方案

- 模型只使用一个工具：`alfworld_step(action: str)`。ALFWorld 负责执行文本动作并返回 observation、reward、done 和 won，PyTRIO 负责模型采样与 LoRA 更新。
- 每次选择一个固定游戏，初始化 `K=8` 个相同初始状态的独立环境，采样一组完整轨迹。单条轨迹最多 50 步。
- 每一步保存执行动作前的 observation、assistant action tokens、rollout old logprobs 和环境即时 reward。首版使用精确 observation 作为 anchor state，不启用模糊匹配。
- 奖励采用论文配置：成功 `10`、失败 `0`、非法动作 `-0.1`；成功由 `won` 判断，达到步数上限属于截断失败。

## GiGPO Advantage

等同一任务的 `K` 条轨迹全部结束后统一计算：

```text
episode_return[i] = sum(reward[i])
episode_adv[i] = episode_return[i] - mean(group_episode_returns)

step_return[i][t] = reward[i][t] + gamma * step_return[i][t + 1]
step_adv[i][t] = step_return[i][t] - mean(same_anchor_state_returns)

final_adv[i][t] = episode_adv[i] + omega * step_adv[i][t]
```

首版使用论文参数 `gamma=0.95`、`omega=1`。只在相同 anchor state 内比较 step return；只有一个成员或回报完全相同的 step group，其 step advantage 为 0。

## PyTRIO 训练对齐

- 第 `t` 轮 assistant 生成的工具调用 token 使用 `final_adv[i][t]` 和采样时保存的 old logprobs。
- system、user 和 tool observation token 只进入后续上下文，`advantage=0`、`old_logprob=0`，不参与 loss。
- 完整轨迹统一右移后构造 `Datum`，使用 `loss_fn="importance_sampling"`；先在完整 group 上计算 advantage，再拆 micro-batch、累积 `forward_backward`，最后执行一次 `optim_step`。

## 环境与评测

- ALFWorld/TextWorld 放在独立 Python 3.12 worker 中运行，当前项目作为 PyTRIO 训练控制器，通过本地 IPC 或 HTTP 调用环境。
- 训练期间记录成功率、平均步数、非法动作率、step group 大小和全零 advantage group 比例。
- 使用相同 prompt、工具协议和最大步数，分别评测 `valid_seen` 与 `valid_unseen`，并比较 Base Model、GRPO 和 GiGPO 的任务成功率。
