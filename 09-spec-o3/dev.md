# Spec-o3 / Qwen3.5-4B 实施方案


## result

| 模型 | Macro F1 | Accuracy | Format | 答对题数 |
|---|---:|---:|---:|---:|
| Base | 53.99% | 38.67% | 0.39% | 99 / 256 |
| SFT | 63.05% | 53.91% | 85.94% | 138 / 256 |
| RL | 71.68% | 67.97% | 96.09% | 174 / 256 |

在 `09-spec-o3/` 中执行 `uv run python analysis.py`，生成 [PNG](images/results_comparison.png) 和 [矢量 PDF](images/results_comparison.pdf)。图为 1×2 布局，沿用 AgentOPSD 参考图的风格：总标题与副标题、Times 衬线字体、完整坐标边框、点划网格、加粗数值标注。左侧按模型分组，每组左侧为蓝色斜纹 Accuracy 柱，右侧为红色实心 Macro F1 柱；右侧以橙色方点实线表示严格 Format 合规率，以灰蓝色圆点虚线表示答对题数，分别对应左右纵轴。右图标注 RL 相比 Base 的数值变化，图注注明双轴及生成预算差异。脚本直接使用上述固定结果，无需模型或评测产物；保留 Base 额外格式提醒的说明。PNG 为 300 DPI，图中文字采用英文。

## 最新开发集结果：Base → SFT → RL epoch 1

已完成 RL 第 1 个 epoch 的 sampler 评测。以下结果来自本地 `outputs/base-dev/metrics-reparsed.json`、`outputs/sft-dev/metrics-reparsed.json` 和 `outputs/sft-rl/metrics.json`，三组轨迹的 256 个样本 ID、任务和参考标签一致。分类均采用新规则：取最后一轮最后一个 `</think>` 后的最后一个完整 answer 块；严格格式合规率独立统计。耗时来自各次终端进度条。

| 指标 / 配置 | Base | SFT epoch 2 | SFT → RL epoch 1 |
|---|---:|---:|---:|
| 开发集样本数 | 256 | 256 | 256 |
| 单轮生成上限（token） | 6,132 | 2,048 | 6,144 |
| 总上下文上限（token） | 16,384 | 16,384 | 16,384 |
| Base 额外格式提醒 | 有 | 无 | 无 |
| 提取到答案的样本数 | 210 | 222 | 247 |
| 回答正确的样本数 | 99 | 138 | 174 |
| Macro F1 | 53.99% | 63.05% | **71.68%** |
| Accuracy | 38.67% | 53.91% | **67.97%** |
| 严格格式合规率 | 0.39% | 85.94% | **96.09%** |
| 平均生成轮数 | 1.7773 | 5.7461 | 5.3555 |
| 工具调用次数 | 199 | 1,215 | 1,115 |
| 工具调用成功次数 | 199 | 1,211 | 1,115 |
| 评测耗时 | 14 分 07 秒 | 11 分 57 秒 | 7 分 10 秒 |

相对同一答案提取规则下的 SFT 结果，RL epoch 1 的 Macro F1 增加 **8.63 个百分点**，accuracy 增加 **14.06 个百分点**，多答对 **36 道题**；严格格式合规率增加 **10.16 个百分点**。工具调用减少 100 次，本次 1,115 次调用全部成功。

RL epoch 1 各任务结果：

| 任务 | 样本数 | TP | FP | FN | Precision | Recall | F1 | Accuracy | 严格格式合规率 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| cc | 56 | 22 | 23 | 2 | 48.89% | 91.67% | 63.77% | 55.36% | 100.00% |
| cv | 50 | 13 | 3 | 10 | 81.25% | 56.52% | 66.67% | 74.00% | 98.00% |
| gm | 51 | 26 | 5 | 3 | 83.87% | 89.66% | 86.67% | 84.31% | 96.08% |
| ss | 50 | 20 | 6 | 3 | 76.92% | 86.96% | 81.63% | 82.00% | 100.00% |
| wd | 49 | 17 | 14 | 9 | 54.84% | 65.38% | 59.65% | 44.90% | 85.71% |

同规则比较下，五个任务的 F1 都提高：cc / cv / gm / ss / wd 分别增加 7.43 / 12.61 / 7.30 / 14.97 / 0.83 个百分点。ss 和 cv 的提升更大；wd 的 F1 变化较小，召回提高，但误报从 10 次增加到 14 次，precision 从 60.00% 降至 54.84%。

轨迹核对：246 条严格格式合格，另有 1 条格式不合格但能提取答案，9 条达到 8 轮工具交互上限。全部样本最后一轮均为 `stop_reason=stop`，本次没有最后一轮因 token 上限截断的记录。

**当前结果统一了样本和答案提取口径，但生成预算尚未统一。** SFT 的单轮上限为 2,048 token，RL 为 6,144 token，因此现有差值可能同时受模型训练与生成预算变化影响，尚不能全部归因于 RL。下一步可将 SFT 也设为 6,144 token 复测，保存到独立目录后再比较。两者的其余记录参数均为 `max_seq_len=16384`、`max_turns=8`、`concurrency=16`、`temperature=0.6`、`seed=42`。

本次 RL 评测命令（在 `09-spec-o3/` 中运行）：

```bash
uv run python eval.py \
    --model-path 'trio://run_nhpbcwj17fa7/sampler_weights/spec-o3-rl-epoch-1-sampler' \
    --output outputs/sft-rl \
    --max-tokens 6144 \
    --max-seq-len 16384
```

SFT 同预算复测命令（尚未运行）：

```bash
uv run python eval.py \
    --model-path 'trio://run_jjljxa4mc24x/sampler_weights/spec-o3-sft-epoch-2-sampler' \
    --output outputs/sft-dev-6144 \
    --max-tokens 6144 \
    --max-seq-len 16384
```

## 历史记录：Base 与 SFT 首轮严格评测

以下记录首轮实际运行的终端评测结果：基模为 `Qwen/Qwen3.5-4B`，SFT 使用第 2 个 epoch 保存的 sampler 权重，均评测固定开发集的 **256 条样本**，单轮生成上限为 2,048 token。后续 Base 的 4,096 / 6,132 token 复测单独记录在下方。比例指标以百分比展示，保留两位小数；平均轮数保留四位小数。

| 整体指标 | Base | SFT（epoch 2） |
|---|---:|---:|
| 样本数 | 256 | 256 |
| Macro F1 | 0.00% | 63.57% |
| Accuracy | 0.00% | 53.91% |
| 最终答案格式合规率（format_rate） | 0.00% | 85.94% |
| 平均生成轮数（mean_turns） | 1.5664 | 5.7461 |
| 工具调用次数（tool_calls） | 145 | 1,215 |
| 工具调用成功次数（tool_successes） | 145 | 1,211 |
| 评测耗时（进度条记录） | 15 分 34 秒 | 11 分 57 秒 |

| 任务 | 模型 | 样本数 | TP | FP | FN | Precision | Recall | F1 | Accuracy | 格式合规率 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| cc | Base | 56 | 0 | 0 | 24 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| cc | SFT | 56 | 20 | 27 | 4 | 42.55% | 83.33% | 56.34% | 41.07% | 92.86% |
| cv | Base | 50 | 0 | 0 | 23 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| cv | SFT | 50 | 10 | 4 | 13 | 71.43% | 43.48% | 54.05% | 56.00% | 88.00% |
| gm | Base | 51 | 0 | 0 | 29 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| gm | SFT | 51 | 25 | 9 | 4 | 73.53% | 86.21% | 79.37% | 72.55% | 94.12% |
| ss | Base | 50 | 0 | 0 | 23 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| ss | SFT | 50 | 16 | 8 | 7 | 66.67% | 69.57% | 68.09% | 62.00% | 84.00% |
| wd | Base | 49 | 0 | 0 | 26 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| wd | SFT | 49 | 15 | 9 | 11 | 62.50% | 57.69% | 60.00% | 38.78% | 69.39% |

Base 的最终答案格式合规率为 0%，说明当前严格解析协议下没有得到有效的最终答案，分类指标也因此为 0；仅凭这组结果无法判断基模本身的天文识别能力。SFT 后格式合规率达到 85.94%，Macro F1 达到 63.57%，平均交互轮数和工具调用次数均增加。

本次使用的命令（在 `09-spec-o3/` 中执行）：

```bash
uv run python eval.py --output outputs/base-dev

uv run python eval.py \
    --model-path 'trio://run_jjljxa4mc24x/sampler_weights/spec-o3-sft-epoch-2-sampler' \
    --output outputs/sft-dev
```

### Base 复测：单轮生成上限 4,096 token

本次使用 `--max-tokens 4096 --max-seq-len 16384`，其余记录参数为 `max_turns=8`、`concurrency=16`、`temperature=0.6`、`seed=42`。仍评测同一开发集的 256 道题，耗时 15 分 01 秒；Macro F1、accuracy 和 format rate 均为 0，平均轮数为 1.96484375，工具调用与成功次数均为 247。以下保留当时的轨迹排查结果；`outputs/base-dev/` 随后已被 6,132 token 复测覆盖。

逐条核对轨迹最后一轮的 `stop_reason`、生成 token 数和 `finish_reason`：

| 结束情况 | 样本数 | 占比 | 记录依据 |
|---|---:|---:|---|
| 生成正常停止，但动作格式不合格 | 206 | 80.47% | 最后一轮 `stop_reason=stop`，轨迹 `finish_reason=invalid_action` |
| 达到单轮 token 上限 | 44 | 17.19% | 最后一轮 `stop_reason=length`，均生成恰好 4,096 token |
| 达到最大交互轮数 | 6 | 2.34% | `finish_reason=max_turns`，均在第 8 轮继续请求工具 |

没有轨迹以 `max_seq_len` 结束。206 条正常停止但格式不合格的输出中，有 198 条在当前解析器截取的正文中包含 `\boxed{YES}` 或 `\boxed{NO}`；其中 16 条包含正确的 `<answer>\boxed{...}</answer>` 子串，但标签外仍有正文。这里统计的是输出结构，未据此重新计算分类准确率。

关键原因是 `protocol.py` 的 `parse_action()` 使用 `re.fullmatch()`：思考结束后的整个正文必须匹配 `<answer>\boxed{YES|NO}说明</answer>`，否则不会产生有效 prediction。实际例子来自 `trajectories.jsonl`：第 1 行正常停止，仅生成 1,317 token，末尾已输出 `\boxed{YES}`，但缺少 answer 标签；第 17 行正常停止，生成 3,421 token，末尾有 `<answer>\boxed{YES}</answer>`，但标签前还输出了分析正文。两条都被记为 `invalid_action`。

因此，本次全零主要反映严格动作协议不合格，截断影响其中 44 条；这些指标不能解读为模型对所有光谱都判断错误。继续增大 token 上限不能直接解决多数样本的格式问题。若后续单独衡量分类能力，应明确定义最终答案提取规则，并将答案正确性与严格格式合规率分开报告；本次排查保留原评测规则及原始指标。

本次调整按用户指定，仅在评测 Base 时追加最终答案格式提醒：没有传入 `--model-path` 时，`eval.py` 在原始 user 消息末尾追加一段文字，要求思考后的最终回答严格使用 `<answer>\boxed{YES}解释</answer>` 或对应的 NO 格式，所有解释放在 answer 标签内，标签外不输出正文。传入 SFT/RL sampler 路径时使用原始提示词。提醒只加入本次加载的消息，数据文件和动作解析规则保持原样；`metrics.json` 的 `config.base_format_reminder` 标记是否启用，完整提示词保存在轨迹的 `initial_messages` 中。上方两次 Base 结果均来自追加提醒之前；启用提醒后的结果记录如下。

### Base 复测：6,132 token，启用格式提醒

2026-09-11 核对 `outputs/base-dev/metrics.json` 和全部 256 条 `trajectories.jsonl`：`max_tokens=6132`、`max_seq_len=16384`、`max_turns=8`、`concurrency=16`、`temperature=0.6`、`seed=42`。配置中的 `base_format_reminder=true`，全部 256 条 `initial_messages` 都包含新增提醒。

本次耗时 14 分 07 秒；Macro F1 与 accuracy 均为 0，format rate 为 **1/256（0.39%）**，平均轮数为 1.77734375，工具调用与成功次数均为 199。

| 结束情况 | 样本数 | 占比 |
|---|---:|---:|
| 生成正常停止，但动作格式不合格 | 214 | 83.59% |
| 达到单轮 token 上限，均为 6,132 token | 32 | 12.50% |
| 达到最大交互轮数 | 9 | 3.52% |
| 严格格式合格，给出最终答案 | 1 | 0.39% |

唯一严格格式合格的是轨迹第 250 行（`train-wd-a33f960e-8fbd-4f05-ad92-81e2b2a58b3a`）：预测 YES，参考标签 NO。因此 format rate 已非零，但 accuracy 和 F1 仍为零。

主要失败原因仍是 answer 标签外出现分析正文。例如第 17 行最后一轮仅生成 420 token，正常停止，正文先写光谱分析，末尾给出 `<answer>\boxed{YES}</answer>`；参考标签也是 YES，但 `parse_action()` 要求整个正文匹配答案结构，所以 prediction 为 null。第 2 行还出现提前闭合 answer 标签、标签外解释及多余闭合标签的问题。增加 token 预算无法直接解决这些格式错误。

为确认格式错误与判断错误的区别，对现有轨迹做了一次离线统计：仅查看最后一轮 `stop_reason=stop` 且含 `</think>` 的输出，取最后一个 `</think>` 之后的正文；要求其中恰好出现一个完整的 `<answer>\boxed{YES|NO}...</answer>` 块，且整个正文仅有一个 boxed 标签。共有 **207 条**满足这一答案提取条件，其中 **97 条**与参考标签一致、110 条不一致；207 条中有 206 条被严格动作解析判为无效。这项统计允许答案标签外有文字或多余闭合标签，仅用于诊断，未覆盖原始 prediction、metrics 或训练奖励，也不能直接与上方 SFT 的严格指标比较。

本次排查后，用户确认将分类答案提取与严格 format rate 分开，具体规则和重算结果如下。

### 评测答案提取规则与现有轨迹重算

`eval.py` 的 `extract_answer()` 只读取最后一轮生成中、最后一个 `</think>` 之后的正文，在其中匹配完整的 `<answer>\boxed{YES|NO}解释</answer>`，取最后一个匹配结果。解释可以为空，也可以跨行；答案块前后允许有其他正文。没有 `</think>` 或没有匹配到完整答案块时，prediction 为 null。该规则不限制最后 100 个字符，也不从思考或裸 YES/NO 中提取答案。

Base、SFT、RL 评测共用这一规则。分类指标使用提取后的 prediction，`format_ok` / `format_rate` 仍记录 rollout 的严格动作格式。因此评测轨迹可能同时出现 `prediction=YES` 和 `finish_reason=invalid_action`：前者表示能提取出分类答案，后者表示生成时未满足严格动作协议。此次修改位于评测层，工具交互和 RL 的训练奖励仍按原规则执行。后续运行的 `metrics.json` 会记录 `config.answer_extraction=last_answer_after_last_think`。

已对现有 Base / SFT 各 256 条轨迹使用同一提取规则重算，结果分别保存到 `outputs/base-dev/metrics-reparsed.json` 和 `outputs/sft-dev/metrics-reparsed.json`，原始 `metrics.json` 与 `trajectories.jsonl` 保留。

| 指标 | Base（6,132 token，带格式提醒） | SFT epoch 2（2,048 token） |
|---|---:|---:|
| 提取到答案的样本数 | 210 / 256 | 222 / 256 |
| 回答正确的样本数 | 99 / 256 | 138 / 256 |
| Macro F1 | 53.99% | 63.05% |
| Accuracy | 38.67% | 53.91% |
| 严格格式合规率 | 0.39% | 85.94% |

SFT 的 Macro F1 从原来的 63.57% 降为 63.05%：新规则多提取出 2 条原先 prediction 为 null 的 YES 答案，两题参考标签都是 NO，因此增加了 2 次误报。正确数仍为 138，accuracy 保持 53.91%，严格格式合规率仍为 85.94%。这是相同轨迹在不同提取规则下的计分变化，无需重训 SFT。

这里统一了答案提取口径，两次生成的 token 预算和提示词设置仍有差异，不能视为预算一致的对照实验。提取规则仅要求正文中有完整答案块，没有额外按 `stop_reason` 筛选；Base 中有 3 条最后一轮达到 token 上限，但已生成完整答案块，也参与此次分类统计。这解释了此处 210 条可提取答案与上方仅检查正常停止输出的 207 条之间的差别。

验证覆盖思考内答案排除、多个 `</think>`、多个完整答案取最后一个、带解释及换行、答案标签不完整、未结束思考和空输出等 11 个用例；使用真实 512 条已有轨迹完成重算，严格格式合规率、工具次数和平均轮数保持原记录值，未发起远程生成或训练。

## 当前实施状态

当前阶段：已实现 SFT、GRPO、工具交互评测和结果绘图的 8 个 Python 文件及模板，已完成 Base、SFT 第 2 个 epoch 和 RL 第 1 个 epoch sampler 的固定开发集评测。最新 RL 结果为 Macro F1 71.68%、accuracy 67.97%、严格格式合规率 96.09%；同预算 SFT 对照及统一测试集评测待完成。

实施方案、文件职责、参数选择和后续讨论都记录在 `dev.md`。`README.md` 留到训练完成后写博客，当前不作为实施文档维护。

基本方向已确定：使用 `Qwen/Qwen3.5-4B`，以 Qwen3.5 官方 chat template 为底稿进行改造，先做 cold-start SFT，再接多轮工具 GRPO。论文原始基模为 Qwen2.5-VL-3B/7B-Instruct，因此本项目属于更换基模后的方法迁移。

代码定位是教程：读者应能沿着数据、图文输入、采样、loss 和参数更新直接读懂流程。

教程代码优先保证阅读顺序清楚：较长的函数调用、字典和列表推导展开书写；用空行分开数据读取、模型初始化、训练、验证和保存。中文注释解释监督权重、异步调用和两种权重保存的用途，不以减少行数为目标。此前的纯排版调整通过语法树对比确认执行逻辑一致；异步训练流程按下文单独验证。

`eval.py`、`protocol.py`、`rollout.py`、`tools.py` 和 `prepare_data.py` 已统一按执行步骤分段，展开参数、消息字段与统计结构，补充图文监督、工具观察和数据划分的中文注释。绘图画布大小的嵌套三元表达式改为 `if/elif`，各宽度阈值保持原值；评测入口顶部补充 Base / sampler 权重的运行示例。

**禁止写防御性代码。** 按已确定的数据格式直接读写，不堆叠字段类型检查、路径校验、重复 assert、广泛 try/except、自动重试、静默跳过、fallback、多版本兼容和通用 schema 验证。不增加基类、注册器、配置框架或只为转发函数而存在的模块。数据清理处理已经观察到的具体问题；模型在交互中产生非法动作时，按任务环境的正常规则处理。

## 文件规划

已落地 **8 个 Python 文件 + 1 个 Jinja 模板**。RL 阶段新增 `train_rl.py`，结果绘图使用 `analysis.py`；图文协议和工具交互继续复用原有文件。

```text
09-spec-o3/
├── dev.md
├── prepare_data.py
├── protocol.py
├── train_sft.py
├── tools.py
├── rollout.py
├── eval.py
├── train_rl.py
├── analysis.py
└── templates/
    └── qwen3_5_spec_o3.jinja
```

| 文件 | 职责 | 状态 |
|---|---|---|
| `prepare_data.py` | 下载数据、修复已确认的编码问题、转换 messages、保留图片对应关系、划分训练/验证数据并统计长度 | 已实现，分为 `sft` / `bench` 两个入口 |
| `protocol.py` | 工具 schema、模板渲染、图片 chunk、SFT / RL Datum、工具调用与最终答案解析 | 已实现 |
| `templates/qwen3_5_spec_o3.jinja` | 在 Qwen3.5 原生模板上保留完整多轮 reasoning，并标记 assistant 监督范围 | 已实现 |
| `train_sft.py` | 读取整理后的轨迹，构造 Datum，运行 PyTRIO SFT、验证 loss、SwanLab 记录和 checkpoint 保存 | 已完成训练，epoch 2 权重已评测 |
| `tools.py` | 从 wavelength/flux 数组按指定波段重绘光谱，返回图片 | 已实现 |
| `rollout.py` | 一条样本的多轮“生成 → 调工具 → 回填图像 → 继续生成”循环，保存实际采样 token 和 logprob | 已实现 |
| `eval.py` | 用相同任务、模板、工具与预算评测 Base / SFT / RL checkpoint，保存轨迹与分类指标 | 已实现 |
| `train_rl.py` | 从 SFT state 开始，组采样、奖励、advantage、PPO 更新、SwanLab 记录与两份权重保存 | 已完成 RL epoch 1，sampler 已评测 |
| `analysis.py` | 将固定开发集结果绘制成 1×2 柱状图与折线图，导出 PNG / PDF | 已生成并检查图表 |

不单独增加 `config.py`、`reward.py`、`loss.py`、`metrics.py`、`utils.py`。超参数放在对应入口脚本顶部或简单命令行参数里；简短的 reward/advantage 放在 `train_rl.py`，评测指标放在 `eval.py`。

## 数据准备与 SFT

`prepare_data.py sft` 处理公开 cold-start 数据。输出每条样本的结构化 messages、按出现顺序排列的图片路径，以及仅用于划分和统计的任务/光谱标识。参考标签等元数据不额外注入模型 prompt。原始对话、图片和整理结果统一保存在 `datasets/sft/`，JSONL 记录该目录下图片的绝对路径；换机器或移动项目后重新运行数据准备以更新路径。

SFT 与 RL 数据分目录保存。两个下载入口都通过 `snapshot_download(local_dir=...)` 直接写入项目目录；SFT 图片是实际文件，不链接到全局 HF cache。`--output` 指定数据根目录，脚本在其下创建 `sft/` 和 `rl/`。

```text
datasets/
├── sft/
│   ├── train_sharegpt.json         # 下载的原始对话
│   ├── images/                     # 下载的 SFT PNG 图片
│   ├── sft_train.jsonl
│   ├── sft_val.jsonl
│   ├── sft_cleaning.jsonl
│   └── sft_stats.json
└── rl/
    ├── data/                       # 下载的原始 Parquet
    ├── images/                     # 从 Parquet 提取的初始 PNG
    ├── spectra/                    # wavelength / flux / redshift 的 NPZ
    ├── bench_rl_train.jsonl
    ├── bench_dev.jsonl
    ├── bench_test.jsonl
    └── bench_stats.json
```

SDK 的下载进度元数据保存在各数据目录的 `.cache/huggingface/`，用于续下和重复运行。模型 tokenizer/image processor 仍使用 HF 模型缓存。

数据准备脚本在导入 Hugging Face 库前设置 `HF_ENDPOINT=https://huggingface.co` 和 `HF_HUB_DISABLE_XET=1`，通过官方普通 HTTP 通道下载 SFT 数据、SpecVI-Bench 以及 tokenizer/image processor 文件。禁用 Xet 使用 Hugging Face 官方提供的[环境变量](https://huggingface.co/docs/huggingface_hub/package_reference/environment_variables#hfhubdisablexet)。数据版本使用固定 revision，重新运行会复用已完成的文件。正在运行的旧进程需要先用 `Ctrl+C` 结束，再执行原命令，让新设置生效。

公开 SFT 仓库有 4,706 个文件，逐文件请求耗时会影响总体下载速度。默认并发为 8，使用 Hugging Face 原生的 [`max_workers`](https://huggingface.co/docs/huggingface_hub/package_reference/file_download#huggingface_hub.snapshot_download) 参数；命令行可通过 `--download-workers` 修改，SFT 与 bench 两个入口共用。启动时打印下载地址、HTTP 通道和并发数。没有增加自定义下载器或重试逻辑。

2026-09-10 排查发现：抽查图片的镜像请求实际重定向至 Hugging Face 官方地址和海外 CDN；原 32 并发进程的 Xet 日志记录了 65 次 HTTP 429，128 并发辅助进程记录了 257 次，辅助进程已停止。此前 32 张图片的小批测速未暴露全量下载的限流问题，不能据此继续提高并发。仅在镜像下禁用 Xet 时，本机 SDK 还出现响应缺少 commit 元数据的错误，因此当前采用已验证可直连的官方地址。

官方 HTTP 通道使用独立临时缓存实测：8 并发下载 8 张真实光谱图，全部成功，用时 4.37 秒。本次验证了该通道可用，不承诺全量下载的固定速度。验证脚本为 `/private/tmp/spec-o3-official-http-check.py`。

数据转换包括：

- `system` 保留任务指令，工具说明由 Qwen3.5 模板统一生成。
- 初始 `human` 转为 `user`；其中 `<image>` 转成对应的结构化图片项。
- `gpt` 转为 `assistant`，将 `<think>...</think>` 提取到 `reasoning_content`。
- 作者 JSON 工具调用转为结构化 `tool_calls`，由 Qwen3.5 原生模板序列化为 XML；工具名称、波段参数和调用顺序保留。
- 原数据 `human` 中的 `<tool_response>` 转为 `role=tool`，保留返回文字和局部图片。

每条完整多轮轨迹作为一条 SFT 样本，所有 assistant 轮次共同监督。训练/验证按 `source_name` 对象分组，固定 seed 42，默认约 90% / 10%；同一对象的轨迹不会跨集合。`--val-fraction` 和 `--seed` 可修改这两个实验设置。

公开 JSON 的异常控制字符由 `repair_text()` 集中处理。已确认的模式包括 `H\x03b1 → Hα`、`\x00c5 → Å`、若干 C₂、Ångströms、标点及 ANSI 颜色转义。工具参数先用 `json.loads(..., strict=False)` 解析含控制字符的字符串，再清理可选 label；波段数值原样保留。

部分原文已经丢失信息，例如 `\x03b` 缺少最后一位，无法单独判断是 α、β 还是 γ。这些位置保留为 `[U+0003]` 等可见码位标记，并输出原文与转换结果。当前全部 942 条轨迹中仍有 273 条含此类待审阅标记，共 2,459 处。**正式 SFT 前需要审阅这些位置或取得作者的干净原文。** 当前代码保留全部轨迹，不把不确定符号猜成某个科学符号，也不自动丢弃这些样本。

数据准备在 `datasets/sft/` 下输出 `sft_train.jsonl`、`sft_val.jsonl`、`sft_cleaning.jsonl` 和 `sft_stats.json`；`train_sft.py` 的默认 `--data-dir` 同步为 `datasets/sft/`。清理记录是数据产物，训练脚本中没有重复校验、重试或静默跳过逻辑。

整理数据时统计各任务数量、assistant 轮数、图片数、文本 token、视觉 token、完整轨迹长度分位数以及超过 16,384 的数量。当前脚本保留完整轨迹，不截断或自动过滤。正式训练前依据全量统计确定长度策略。

`protocol.py` 承担模型输入这条核心链路：

```text
messages + 改造后的 Qwen3.5 模板
→ token ids + assistant mask
→ 按顺序将 image_pad 替换成 ImageChunk
→ 由对应 image processor 计算 expected_tokens
→ 图片位置扩展为零 target / 零 weight
→ target 与 weight 统一自回归右移
→ PyTRIO Datum
```

保留 Qwen3.5 原生角色和视觉标记。图片以原始字节构造 `ImageChunk`，文本构造 `EncodedTextChunk`；全部 chunk 按模型实际阅读顺序排列。

assistant 的 reasoning、工具调用、最终回答与结束 token 参与 loss；角色头、system、user、tool 返回和图片仅作为上下文。SFT 使用 `cross_entropy`。右移与 mask 是数据构造本身的计算逻辑，不在训练主线外增加一套通用校验流程。

模板保留 Qwen3.5 原生角色、视觉标记、XML 工具调用和 tool response 格式，增加 `{% generation %}` 监督区间，并始终保留所有 assistant 的 `reasoning_content`。Qwen3.5 原生模板本来就保留同一工具交互链的思考；这里也保留跨新 user 问题的早期 reasoning。模板精简为本任务实际使用的文本、图片和消息结构，去掉通用校验、视频分支和兼容解析。SFT 与评测共用该模板。

`train_sft.py` 采用 `pytrio-skill` 中异步 SFT 示例的提交方式，项目锁定 PyTRIO 0.2.9。主循环依次提交 `forward_backward_async(cross_entropy)` 和 `optim_step_async()`，拿到两个 Future 后立即用 `asyncio.create_task()` 启动后台结果记录，继续构造和提交下一批。每个训练客户端的任务仍按 FB → 更新 → 下一批 FB 的顺序执行；客户端不逐批等待计算完成。

`build_training_batch()` 通过 `asyncio.to_thread()` 构造图文 Datum，图片读取和编码期间事件循环可以继续处理完成的任务。PyTRIO 的 cross entropy 使用求和归约，因此每个新 batch 的 weights 除以该 batch 的 assistant token 总数。后台 `log_training_step()` 等待该批计算和更新完成，再按权重统计 loss；日志任务使用同一个 `asyncio.Lock` 按提交顺序收集结果，保证 SwanLab 的 step 递增，锁不阻塞主循环提交任务。

每个 epoch 末先 `await asyncio.gather(*log_tasks)`，确认本轮所有更新和日志完成，再执行验证。验证仍只调用 `forward_async()`，按原始监督 token 数加权平均，不做参数更新。没有增加自定义任务队列、重试或异常兜底逻辑。

训练入口通过 `--base-model` 选择基模，默认 `Qwen/Qwen3.5-4B`；tokenizer、image processor 和远程 training client 都使用该参数。`--model-revision` 默认 `main`，只指定所选 HF 仓库的 tokenizer/processor 文件版本；切换模型时不沿用 4B 仓库的提交 ID。模型名称和文件版本写入 SwanLab 配置。当前消息模板仍为 Qwen3.5 专用模板。

原 4B 数据准备和评测使用固定 revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`；训练时要沿用该文件版本，可显式传入 `--model-revision 851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`。训练按当前 tokenizer/processor 重新构造 Datum，不直接使用准备阶段记录的长度进行训练。当前 `eval.py` 仍使用 `protocol.py` 中的默认 4B 配置，更换训练基模后，评测配置也需要匹配。

每个 epoch 后必须分别在远程保存 **state 和 sampler 两份权重**：依次提交 `save_state_async()` 和 `save_weights_for_sampler_async()`，用 `asyncio.gather()` 等待两次保存完成后，在终端打印该轮的 `state_path`、`sampler_path` 和验证 loss，随后才进入下一轮训练。SFT 入口不提供 `--output` 参数，不创建 `outputs/sft/` 或写入本地 checkpoint 清单，也不维护 `checkpoints` / `best` 记录。SwanLab 记录训练 loss、监督 token 数、epoch 和验证 loss；根据验证 loss 选择后续评测或 RL 使用的权重。

`--project-name` 直接传给 SwanLab 的 `project`，默认 `agentic-rl-lab-spec-o3`；`--run-name` 直接传给 `experiment_name`，默认 `spec-o3-sft`，同时用作远程权重名称前缀，例如 `spec-o3-sft-epoch-1-state` 和 `spec-o3-sft-epoch-1-sampler`。

训练前后的长度、mask 和输出格式通过独立的一次性检查验证，正式训练脚本不加入 smoke/debug 分支，也不重复执行与训练计算无关的检查。

## SFT 后的工具交互评测

SFT 训练直接使用数据中已经保存的图片。评测时才由模型自主决定波段，并实际执行光谱绘图。

`prepare_data.py bench` 把 SpecVI-Bench 的 Parquet 直接下载到 `datasets/rl/data/`，保留初始图、问题、标签和原始 wavelength/flux 数组。使用 parquet 文件名统一 `cc/cv/ss/gm/wd` 任务标识；原数据的 `carbon` 等来源名称不直接当作任务编码。图片提取为 `datasets/rl/images/` 下的 PNG，数组保存为 `datasets/rl/spectra/` 下的 NPZ。数据中 `redshift=null` 表示不作红移校正，整理为 0。

从 `datasets/sft/` 读取 SFT train/val 的对象标识，只从公开 train 中未在 SFT 出现的对象里划出约 10% 固定开发集；公开 train 中开发集以外的全部对象用于 RL，允许包含 SFT 对象。在 `datasets/rl/` 下输出 `bench_rl_train.jsonl`、`bench_dev.jsonl` 和原始 test 对应的 `bench_test.jsonl`。`bench_stats.json` 记录数量、开发集任务分布及 SFT 与 dev/test 的对象重叠情况。`eval.py` 默认读取 `datasets/rl/bench_dev.jsonl`。

`tools.py` 暴露一个直接的绘图函数，先计算静止系波长 `wavelength / (1 + redshift)`，再选定波段重绘。沿用作者的蓝色曲线、80 DPI 和按窗口宽度选画布的思路，简化刻度设置。它使用真实光谱数组生成新图片，不裁剪已有图片。窗口内不足两个数据点时返回文字观察，模型可据此继续选择波段。

`rollout.py` 负责以下顺序：

```text
初始全谱图 + 类别判别指南
→ assistant 生成
→ 解析工具调用
→ tools.py 返回局部图
→ 作为 tool observation 回填
→ assistant 继续生成
→ 最终 YES/NO 或达到约定的交互预算
```

轨迹记录保留每轮实际采样 token、logprob、工具参数、图片及最终回答，供评测和后续 RL 共用。追加工具返回时，模板只用于提取并编码新 tool response 与下一轮 assistant 前缀；旧 assistant token 直接沿用采样结果。服务端若省略 stop token，补入的结束标记只属于上下文，不伪造对应 logprob。

工具动作使用 Qwen3.5 原生 XML，每轮一个调用。最终回答使用 `<answer>\boxed{YES} 解释</answer>` 或 NO。非法动作结束轨迹；达到轮数或上下文预算时也结束，不自动修复模型输出或追加答案。所有 tool observation 的动作 mask、训练 target 占位和 old logprob 占位为零。

`eval.py` 复用同一个 rollout，在固定数据和交互预算下比较 Base 与 SFT checkpoint。输出各任务的正类 precision、recall、F1、accuracy，以及已评测任务的平均 F1；完整五任务文件对应五任务平均。分类 prediction 取最后一轮最后一个 `</think>` 后的最后一个完整 answer 块，严格格式合规率独立统计。未提取到答案时 accuracy 记错，正类样本记入 FN；没有正类预测时 precision 定义为 0。

评测目录保存 `metrics.json`、`trajectories.jsonl` 和每轮工具图片。JSONL 包含可阅读文本、真实采样 token/logprob、动作 mask 与停止原因。先用这些结果判断 SFT 是否学会完整光谱审核流程，再进入 RL。

评测使用 `tqdm` 显示样本进度、已用时间、预计剩余时间和处理速度。进度条的总数为评测集样本数，每批 rollout 完成并写入轨迹后，按该批实际完成数量更新，尾批不足并发数时也按实际数量计数。

## 默认参数与运行顺序

以下是可从命令行修改的首轮实验默认值，还没有用训练结果调参。

| 参数 | 默认值 |
|---|---|
| 基模（`--base-model`） | `Qwen/Qwen3.5-4B` |
| 训练 tokenizer/processor 文件版本（`--model-revision`） | `main` |
| SDK | 项目锁定的 PyTRIO `0.2.9` |
| SFT epochs / batch size | 1 / 4 |
| LoRA rank / learning rate | 32 / `2e-5` |
| SFT 学习率调度 / warmup | 当前为恒定学习率 / 无 warmup |
| 数据划分与训练 seed | 42 |
| 评测 max turns / 单轮 max tokens | 8 / 2,048 |
| 评测总上下文预算 | 16,384，包含文字和视觉 token |
| 评测 temperature / top-p | 0.6 / 0.95 |
| 评测并发数 | 16 |

2026-09-10 实查当前服务：4B 的训练单序列上限为 16,384，batch 上限 32，每请求上限 131,072 token。当前采用 LoRA，和作者冻结视觉部分、更新语言模型全部参数的训练方式不同。

当前训练参数没有与作者逐项对齐。具体超参数以作者公开的 [`qwen2_5_sft_full.yaml`](https://github.com/Maxwell-Jia/spec-o3/blob/dd6eb9130d9d850cd67b2a6c55e651da08ab28cb/cold_start/examples/spec_o3/qwen2_5_sft_full.yaml) 为对照，不能把代码默认值全部当作论文参数。

| 项目 | 作者公开 SFT 配置 | 当前实现 |
|---|---|---|
| 基模 | 配置为 Qwen2.5-VL-7B-Instruct；论文也实验了 3B | Qwen3.5-4B |
| 更新参数 | 语言模型全参数，冻结视觉编码器与 projector | LoRA，rank 32 |
| Epoch | 5 | 1（可用 `--epochs` 修改） |
| 学习率数值 | `2e-5` | `2e-5` |
| 调度 | cosine，warmup ratio 0.05 | 恒定学习率，无 warmup |
| Batch | 每卡 4，梯度累积 1 | 每次参数更新共 4 条 |
| 长度 | cutoff 32,768 | 当前服务训练上限 16,384，数据准备保留完整轨迹 |
| 验证集 | YAML 的 `val_size` 被注释，未开启 | 按对象划出约 10% |

作者的 per-device batch 不能直接与当前脚本的全局 batch 等同；8 卡数据并行时，前者对应全局 32。学习率调度和 warmup 尚未对齐，正式训练前应确定是否沿用作者设置。当前优化器其余参数使用 PyTRIO 0.2.9 默认值，作者 YAML 未显式指定这些字段，尚未逐项核对其训练依赖默认值。本次讨论只记录差异，没有更改训练参数。

先从仓库根目录进入 `09-spec-o3/`，后续命令均在这个目录执行；训练前需要审阅数据清理记录与全量长度统计。

SFT 入口使用 CLI 保存的登录信息，不再调用 `load_dotenv()` 读取 `.env` 文件。首次运行前执行 `uv run trio login`；默认使用 SwanLab 云端记录，还需执行 `uv run swanlab login`。已登录可跳过对应命令。传入 `--swanlab-mode local` 或 `disabled` 时无需登录 SwanLab。训练参数由命令行传入。

```bash
cd 09-spec-o3
uv run trio login
uv run swanlab login
uv run python prepare_data.py sft
uv run python prepare_data.py bench
uv run python train_sft.py
uv run python eval.py --output outputs/base-dev
uv run python eval.py --model-path '<训练终端打印的 sampler_path>' --output outputs/sft-dev
```

显式选择训练模型并沿用当前 4B 数据准备的文件版本：

```bash
uv run python train_sft.py --base-model Qwen/Qwen3.5-4B --model-revision 851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a
```

已下载 cold-start 原始目录时，可用 `uv run python prepare_data.py sft --sft-source /path/to/dataset`，脚本会把原始文件复制到 `datasets/sft/` 后重新整理，JSONL 的图片路径指向项目内的新位置。该参数用于从外部目录导入；已经位于 `datasets/sft/` 的数据直接运行普通 `sft` 命令。最终统一 test 时给 `eval.py` 传入 `--data datasets/rl/bench_test.jsonl`。Base/SFT/RL 比较时使用同一数据文件和采样参数。

## GRPO 训练

本轮编写 RL 前，先将之前的可读性调整、评测进度条和用户设置的评测并发数提交为 `b71084e`。随后新增 `train_rl.py`，在 `protocol.py` 中加入 RL Datum 构造，在 `rollout.py` 中加入第一轮已采样结果的接入；未新增通用训练框架。

论文 §3.3 明确使用 GRPO，§4.2 给出每题 8 条 rollout。核对作者固定提交 `dd6eb9130d9d850cd67b2a6c55e651da08ab28cb` 的 [`spec_o3.yaml`](https://github.com/Maxwell-Jia/spec-o3/blob/dd6eb9130d9d850cd67b2a6c55e651da08ab28cb/reinforcement_learning/recipe/spec_o3/configs/spec_o3.yaml)：RL 为 3 个 epoch、学习率 `1e-6`，关闭 KL loss 和 KL reward；继承的 rollout 默认 temperature / top-p 为 1.0 / 1.0。

### 第一轮组采样与后续工具交互

每个训练 batch 先通过 `save_weights_and_get_sampling_client_async()` 创建当前权重的 sampler。同一道题的第一轮输入完全相同，`rollout_group()` 用一次 `sample_async(num_samples=group_size)` 取得多个开头，再把每个 sequence 交给独立的 `rollout(first_sequence=...)`。

后续每条轨迹分别维护消息、原始生成 token、工具返回图片和随机种子。调用工具后，各自使用 `num_samples=1` 请求下一轮，保持一题总共 `group_size` 条轨迹，不逐轮扩展分支数量。已结束的轨迹不再请求生成。不同题目和同题的不同轨迹均通过 `asyncio.gather()` 并发执行。

必须等当前 batch 的全部 group 完成后才更新参数；整批更新完成后，下一批重新导出 sampler。整个 group 的 old logprob 都来自同一版采样权重，历史 assistant token 直接保留。单条评测仍使用原有 `rollout()` 入口和默认采样参数。

### Reward、advantage 与 loss

`trajectory_reward()` 使用 `reward = correctness - 0.2 × format_error`：正确且格式合格为 1，正确但格式错误为 0.8，错误但格式合格为 0，错误且格式错误为 -0.2。没有额外工具调用奖励。

正确性和格式分别判断：格式复用现有动作协议；正确性只从最后一轮 `</think>` 后、回答开头提取 YES/NO，允许缺少 answer 或 boxed 标签的答案得到部分分数。这里使用一条明确的解析规则，不沿用作者 reward 文件中的多层 fallback，不扫描思考或工具参数猜答案。因而异常格式答案的提取范围比作者实现更严格。

对同一题的完整 group 计算 `(reward - mean) / (std + 1e-6)`，`std` 使用 `ddof=1`，与作者 VeRL 的 `torch.std()` 一致。同组 reward 全部相同则没有相对梯度信号，不进入更新，但仍进入 reward、accuracy、format 和退化 group 比例等统计。没有生成动作的轨迹也保留在组内 reward 统计中，不创建零动作训练样本。

`build_rl_datum()` 将完整图文输入的最后一个文本 token 移除，将 targets、old logprobs 和动作 mask 统一右移一位。只有实际采样的 assistant token 拥有非零 advantage；初始问题、图片、工具观察和补入的上下文分隔符全部为零。采样没有产生新 token 时不追加空文本 chunk，以便结束处仍可正确右移。

当前使用 PyTRIO 内置 `loss_fn="ppo"`，显式设置 ratio 裁剪区间 `[0.8, 1.2]`。advantage 按整个 batch 有效轨迹的 assistant token 总数缩放。同题 advantage 先在完整 group 内确定，然后将当前 batch 的全部有效轨迹一次传给 `forward_backward_async()`。项目锁定的 PyTRIO 0.2.9 自动拆分请求并累积梯度，因此不设置 `--mini-batch-size`，每批只调用一次 `optim_step_async()`。先提交 forward/backward 和 optimizer 请求，再等待两个 Future 完成；整批没有有效训练样本时跳过更新。

这是标准 clipped PPO 的 GRPO 实现。作者 VeRL 默认还包含 `clip_ratio_c=3.0` 的 dual-clip 分支，本教程未加入该分支；基模、LoRA、batch、上下文预算与保存频率也存在以下差异，不能声称训练配置完全复现。

| 项目 | 作者公开 RL 配置 | 当前默认 |
|---|---|---|
| Epoch / 学习率 | 3 / `1e-6` | 1 / `1e-6` |
| 每题 group size | 8 | 8 |
| rollout batch 的题目数 | 64 | 8 |
| 一次参数更新的数据 | 32 个 prompt，VeRL 按 rollout 数展开 | 当前 batch 的全部有效轨迹，最多 8 × 8 = 64 条；PyTRIO 自动累积梯度 |
| 每批 PPO 遍历次数 | 1 | 1 |
| temperature / top-p | 1.0 / 1.0 | 1.0 / 1.0 |
| 最大 assistant 轮数 | 8 | 8 |
| 长度预算 | prompt 2,048，response 32,768 | 单轮生成 2,048，总上下文 16,384 |
| KL / entropy 项 | 关闭 / 系数为 0 | 关闭 |
| 格式错误罚分 | 0.2 | 0.2 |
| 权重保存 | 每 10 个 trainer step | 默认每 100 个累计 rollout step，以及每个 epoch 结束时保存 state 和 sampler |

### 权重、日志与运行命令

`--state-path` 必填，可从 PyTrio 权重控制台获取，也可使用 SFT / RL 训练终端打印的 **state_path**。SDK 从 checkpoint 元数据恢复基模和 LoRA rank，本地 tokenizer / processor 同样使用恢复客户端的 `model_id`。`--model-revision` 默认 `main`，需与 SFT 使用的文件版本相同。SFT → RL 默认只恢复模型权重，为新目标初始化优化器；从 RL state 继续时，`--resume-optimizer` 同时恢复权重和优化器。该选项不恢复本地数据游标、epoch、随机数进度或 SwanLab step，新运行从指定数据和 seed 开始。

工具图片使用每个 batch 独立的临时目录，组内每条轨迹各有子目录。构造 Datum 后图片已包含在 `ImageChunk.data` 中，临时目录自动清理。训练没有 `--output` 参数，也不写本地 checkpoint 清单。

SwanLab 按 rollout batch 递增 step，记录 reward、答案正确率、格式合格率、退化 group 比例、可训练轨迹数、动作 token 数、工具调用数、生成长度、batch 耗时和累计更新次数；`trainer/*` 为 PyTRIO 聚合当前完整 batch 后返回的服务端指标。每个有效 batch 增加一次更新计数；整批没有有效相对信号时仍记录指标并推进进度条。

`--save-every` 控制周期保存间隔，默认 100：本次运行完成第 100、200、300……个 rollout batch 后，分别提交 state 和 sampler 保存，等待两份都完成并打印远程路径，再进行下一批采样。显式传入 `--save-every 50` 时改为每 50 个 step 保存。保存发生在当前 batch 的参数更新完成之后。step 与 SwanLab 的 step 一致，跨 epoch 连续计数；跳过参数更新的 batch 也计入 step，达到间隔时保存当前权重。重新启动训练时，step 从 0 开始计数。

周期保存的名称为 `<run-name>-step-100-state` / `<run-name>-step-100-sampler` 等。每个 epoch 结束时仍保存 `<run-name>-epoch-1-state` / `<run-name>-epoch-1-sampler`；若恰好与周期保存重合，两组名称都会保留。两类 checkpoint 都只保存在远程，使用 `tqdm.write()` 打印路径，配合两层进度条显示。

训练显示两层进度条：外层保留当前 epoch 的总轨迹进度，每个 step 处理完后推进；内层显示 `Step 当前序号/本轮总步数`，每条完整轨迹结束就推进一次。同一 step 的所有 group 共用内层进度条，轨迹通过 `asyncio.gather()` 保持返回顺序。内层同时显示“准备采样 / 采样中 / 更新参数 / 完成”；全部轨迹没有相对学习信号时显示跳过更新。下一 step 重置内层计数，不保留每步的旧进度条。

当前 RL 训练集为 3,108 道题。`batch-size=8`、`group-size=8` 时，每个 epoch 的总轨迹数为 `3,108 × 8 = 24,864`，共有 `ceil(3,108 / 8) = 389` 个 step。前 388 个 step 各采样 64 条轨迹，最后一个 step 使用剩余 4 道题，采样 32 条轨迹；进度条按尾批实际数量设置总数。这里的 step 是 rollout batch 数，全组同分时实际参数更新次数可能更少。

在 `09-spec-o3/` 中运行：

```bash
uv run python train_rl.py --state-path '<PyTrio 权重控制台获取或训练终端打印的 state_path>'

uv run python train_rl.py \
    --state-path '<PyTrio 权重控制台获取或训练终端打印的 state_path>' \
    --epochs 3 \
    --batch-size 2 \
    --group-size 8 \
    --learning-rate 1e-6 \
    --save-every 50

uv run python eval.py --model-path '<RL 打印的 sampler_path>' --output outputs/rl-dev
```

若 SFT 使用固定 HF 文件版本，给 RL 同样传入 `--model-revision 851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`。正式训练仍应先审阅 SFT 符号清理记录，在固定开发集确认工具交互效果；RL 的在线训练 reward 不等于开发集 F1。

## 本次检查与后续步骤

前期草稿 `sft_data.py`、`verify_sft.py`、`tests/test_sft_data.py` 已移除，职责归入上述 6 个文件。没有增加通用配置层、重试、异常吞掉、assert 或类型/路径校验。检查代码和样例产物放在 `/private/tmp/spec-o3-implementation-check/`，不混入正式训练代码。

本地已完成：

- 五个文件的可读性调整检查：去除文档字符串后，评测、协议、rollout 和数据准备的语法树与修改前一致；绘图工具对比 9 种情况，覆盖画布阈值两侧、红移、可选标签、空窗口和单点窗口，工具返回值与 PNG 字节均一致。五个文件语法检查、数据准备 / 评测 / SFT 的 `--help` 检查通过。未添加防御性逻辑或启动远程任务。
- 数据目录调整：本机已有 SFT 的 4,706 个原始文件已复制到 `datasets/sft/`，包含 4,702 张 PNG；逐文件校验内容与固定版本元数据一致。942 条轨迹共引用 4,641 张图片，全部指向项目内的实际文件，848/94 的训练/验证划分和长度统计保持不变。全局旧缓存保留，原先位于 `datasets/` 根目录的整理文件备份在 `/private/tmp/spec-o3-before-directory-migration-my_0tqdn/`。
- 早期 RL 目录检查使用缓存中的 671 条真实 carbon 数据，验证 Parquet 输入、`rl/images/` 图片、`rl/spectra/` 数组、JSONL 路径及开发集划分。当前项目目录已准备完整数据，`bench_stats.json` 记录 RL train / dev / test 为 3,108 / 256 / 6,754；SFT 与 dev 的对象交集为 0，与原始 test 的交集为 2。正式报告测试结果时需说明这两个重叠对象的处理方式。
- 942 条轨迹的结构转换；逐条确认波段参数保持原值，当前单条工具链的渲染结果与固定版本 Qwen3.5 原生模板完全相同。
- 跨新 user 问题的历史 reasoning 保留，以及 assistant generation mask。
- 已缓存完整图片的 209 条真实轨迹，共 961 张图片，检查视觉 token 展开、右移与监督范围；这批长度最大为 4,581。该批次不代表全量长度统计。
- 一条 4 图、4 轮 assistant 的原始样本仍为 3,223 输入 token、1,278 监督 token。
- 671 条真实 carbon benchmark train 数据的整理，覆盖其中 87 条 `redshift=null` 的记录；本地检查只使用该 parquet，未准备完整五任务 benchmark。
- 用模拟 sampler 跑三轮交互，实际生成局部光谱图并回填；覆盖 stop token 返回/省略、空波段观察、轮数预算、采样前缀连续和观察 mask。
- 用模拟 trainer 检查 batch token 归一化、异步两次 await、参数更新、验证 loss 及 checkpoint 路径记录。
- 异步 SFT 调度检查：使用真实图文数据中的 3 条训练样本、3 条验证样本和实际 PyTRIO `APIFuture`，配合模拟训练客户端运行 2 个 epoch、4 次更新，覆盖不足整 batch 的尾批。验证下一批在上一批结果返回前已提交、乱序返回仍按 step 记录日志、batch 构造在线程中完成、轮末先等待更新再验证，以及每轮 state/sampler 两份保存完成后才继续。检查脚本 `/private/tmp/spec-o3-async-sft-check.py`，产物 `/private/tmp/spec-o3-async-sft-check-otrg38rs/`；其中 loss 和权重路径为模拟结果，没有发起远程训练。

远程接口检查：使用真实 PyTRIO `Qwen/Qwen3.5-4B` Base sampler，对一条 carbon 样本运行两轮。第一轮生成 676 token 并成功调用绘图工具；回填局部图片后，第二轮生成 239 token 并请求另一波段。两轮的 token/logprob 数量对应。该检查在预设的两轮预算处结束，没有最终分类答案；它验证了图文采样与工具回填链路，不能用来评价分类准确率。产物位于 `/private/tmp/spec-o3-implementation-check/live-eval/`。

RL 本地检查使用真实 benchmark 的图片和光谱数组、缓存的 Qwen3.5 tokenizer / processor、实际 PyTRIO Datum / APIFuture，远程客户端用模拟实现替代。覆盖第一轮 `num_samples=4` 后只有需要工具的两条轨迹分别请求下一轮、独立图片和上下文、实际采样 token / logprob 保留、图文 mask 右移、四种 reward、样本标准差归一化、全组同分、尾批、空生成、评测行为保持、采样与更新的权重版本顺序、state 恢复的两种模式、每轮两份权重和临时图片清理。移除手动拆批后，完整模拟训练跑 2 个 epoch，每个 epoch 的完整批和尾批分别提交 8 条、4 条轨迹，总共更新 4 次；同时检查 advantage 使用整批的 token 分母。另测全组同分时零次更新，日志仍正常递增。检查脚本为 `/private/tmp/spec-o3-rl-full-batch-check.py`，产物在 `/private/tmp/spec-o3-rl-check-9di6hwxt/`；测试 reward、正确率与权重路径均为模拟值。

项目依赖、`uv.lock` 和本地虚拟环境已从 PyTRIO 0.2.8 升级到 0.2.9。核对新版的异步训练、自动梯度累积、state 恢复和两份权重保存接口后，重新通过上述整批 RL 检查，产物为 `/private/tmp/spec-o3-rl-check-x7gox7cy/`。本次升级验证没有发起远程训练。

两层进度条检查使用 `/private/tmp/spec-o3-rl-progress-check.py`，在模拟远程客户端的条件下确认每条轨迹结束立即推进、返回顺序保持、外层不重复计数、尾批重置总数、step 序号及更新/跳过阶段显示。检查通过，产物为 `/private/tmp/spec-o3-rl-check-sd54y7qp/`。

周期保存检查使用 `/private/tmp/spec-o3-step-checkpoint-check.py`，运行两个各含 3 个 rollout batch 的模拟 epoch。保存间隔为 2 时，验证 step 2 / 4 / 6 的周期保存、epoch 1 / 2 的轮末保存，以及跨 epoch 计数、尾批、跳过更新、更新完成后保存和两份异步保存都完成后再采样；间隔为 50 时验证不足间隔仍保留轮末保存。使用 PyTRIO 0.2.9 的真实 `APIFuture` 配合模拟客户端，两组检查及 `train_rl.py --help` 均通过，没有发起远程训练或保存。

已完成 SFT 训练、RL epoch 1，以及固定开发集上的 Base / SFT / RL 评测，结果见文档开头。后续顺序：补齐 SFT 的 6,144 token 同预算开发集对照 → 按统一设置评测测试集。数据中待审阅符号的处理情况仍需单独记录；当前开发集结果不等同于论文测试集指标复现。

## 服务器副本（2026-09-11）

项目已复制到 `szx@111.231.2.126:/data/home/szx/code/agentic-rl-lab`，包含当前未提交的代码、Git 目录、全部教程数据集和评测产物。迁移文件总大小约 12.5 GB；未复制 macOS 的 `.venv`、Python 字节码、`.DS_Store` 和本地 `.env` 凭据文件，`.env.example` 保留。

服务器使用现有 UV 0.11.29 和 Python 3.13.14，在项目内创建 `.venv`。依赖按照原始 `uv.lock` 安装，共 93 个包，其中 PyTRIO 为 0.2.9、torch 为 2.13.0+cpu。官方 PyPI 下载慢，安装时通过 `uv export --locked` 导出固定版本与哈希，再使用国内镜像及 PyTorch CPU 源执行 `uv pip sync`；项目的 `pyproject.toml` 和 `uv.lock` 保持与本机一致。随后原项目的离线 `uv sync --locked --python 3.13` 和 `uv pip check` 均通过。

Qwen3.5-4B 的 Hugging Face / ModelScope tokenizer、chat template 和图像处理器缓存已从本机复制。服务器已有 PyTRIO 登录配置，连接检查确认可访问 `Qwen/Qwen3.5-4B`；没有复制本机登录凭据，也没有代为启动训练。

服务器副本中，6 个包含本机项目绝对路径的 Spec-o3 JSONL 文件已统一替换为服务器项目路径：SFT train / val / cleaning 和 RL train / dev / test。本机数据文件保持原样。迁移检查确认：

- 93 个代码及配置文件 SHA-256 一致，11 个教程数据目录在路径替换前的文件数、总字节数一致。
- SFT train / val 为 848 / 94 条；RL train / dev / test 为 3,108 / 256 / 6,754 条。
- 整理后的数据引用的 24,877 个不同图片、光谱文件全部存在。
- 服务器离线构造实际 RL 初始图文输入（1,274 token）和 SFT Datum（2,630 token），并成功读取光谱 NPZ、生成局部光谱图；`train_rl.py --help` 正常。

在服务器上运行：

```bash
ssh szx@111.231.2.126
cd /data/home/szx/code/agentic-rl-lab/09-spec-o3
tmux new -s spec-o3-rl

uv run python train_rl.py \
    --state-path 'trio://run_jjljxa4mc24x/weights/spec-o3-sft-epoch-2-state' \
    --epochs 1 \
    --batch-size 8 \
    --group-size 8 \
    --learning-rate 1e-6 \
    --swanlab-mode disabled
```

`tmux` 中按 `Ctrl+B` 再按 `D` 可离开会话；重新登录后用 `tmux attach -t spec-o3-rl` 返回。服务器已经安装环境，进入 `09-spec-o3/` 后可直接使用 `uv run`。以后再次同步数据时，需要保留或重新执行服务器路径转换。

## 参考资料

- [Spec-o3 论文](https://arxiv.org/html/2601.06498v1)
- [作者代码](https://github.com/Maxwell-Jia/spec-o3)
- [Cold-start 数据](https://huggingface.co/datasets/Maxwell-Jia/Spec-o3-ColdStartSFT)
- [SpecVI-Bench](https://huggingface.co/datasets/Maxwell-Jia/SpecVI-Bench)
- [本次改造采用的 Qwen3.5 官方模板](https://huggingface.co/Qwen/Qwen3.5-4B/blob/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a/chat_template.jinja)
- [PyTRIO 多模态文档](https://docs.pytrio.com/docs/guide/vision)
