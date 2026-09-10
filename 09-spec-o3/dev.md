# Spec-o3 / Qwen3.5-4B 实施方案

当前阶段：已实现 SFT 与工具交互评测的 6 个 Python 文件及模板，本地检查和单样本远程工具交互检查已通过；尚未启动 SFT 训练。`train_rl.py` 按原定顺序，在 SFT 和交互评测完成后再实现。

实施方案、文件职责、参数选择和后续讨论都记录在 `dev.md`。`README.md` 留到训练完成后写博客，当前不作为实施文档维护。

基本方向已确定：使用 `Qwen/Qwen3.5-4B`，以 Qwen3.5 官方 chat template 为底稿进行改造，先做 cold-start SFT，再接多轮工具 GRPO。论文原始基模为 Qwen2.5-VL-3B/7B-Instruct，因此本项目属于更换基模后的方法迁移。

代码定位是教程：读者应能沿着数据、图文输入、采样、loss 和参数更新直接读懂流程。

教程代码优先保证阅读顺序清楚：较长的函数调用、字典和列表推导展开书写；用空行分开数据读取、模型初始化、训练、验证和保存。中文注释解释监督权重、异步调用和两种权重保存的用途，不以减少行数为目标。此前的纯排版调整通过语法树对比确认执行逻辑一致；异步训练流程按下文单独验证。

`eval.py`、`protocol.py`、`rollout.py`、`tools.py` 和 `prepare_data.py` 已统一按执行步骤分段，展开参数、消息字段与统计结构，补充图文监督、工具观察和数据划分的中文注释。绘图画布大小的嵌套三元表达式改为 `if/elif`，各宽度阈值保持原值；评测入口顶部补充 Base / sampler 权重的运行示例。

**禁止写防御性代码。** 按已确定的数据格式直接读写，不堆叠字段类型检查、路径校验、重复 assert、广泛 try/except、自动重试、静默跳过、fallback、多版本兼容和通用 schema 验证。不增加基类、注册器、配置框架或只为转发函数而存在的模块。数据清理处理已经观察到的具体问题；模型在交互中产生非法动作时，按任务环境的正常规则处理。

## 文件规划

SFT 阶段已落地 **6 个 Python 文件 + 1 个 Jinja 模板**，包含训练后的工具交互评测。RL 阶段只新增 **1 个 Python 文件**。

```text
09-spec-o3/
├── dev.md
├── prepare_data.py
├── protocol.py
├── train_sft.py
├── tools.py
├── rollout.py
├── eval.py
├── train_rl.py                       # 计划文件，SFT 和评测完成后再实现
└── templates/
    └── qwen3_5_spec_o3.jinja
```

| 文件 | 职责 | 状态 |
|---|---|---|
| `prepare_data.py` | 下载数据、修复已确认的编码问题、转换 messages、保留图片对应关系、划分训练/验证数据并统计长度 | 已实现，分为 `sft` / `bench` 两个入口 |
| `protocol.py` | 工具 schema、模板渲染、图片 chunk、SFT Datum、工具调用与最终答案解析 | 已实现 |
| `templates/qwen3_5_spec_o3.jinja` | 在 Qwen3.5 原生模板上保留完整多轮 reasoning，并标记 assistant 监督范围 | 已实现 |
| `train_sft.py` | 读取整理后的轨迹，构造 Datum，运行 PyTRIO SFT、验证 loss、SwanLab 记录和 checkpoint 保存 | 已实现，未运行远程训练 |
| `tools.py` | 从 wavelength/flux 数组按指定波段重绘光谱，返回图片 | 已实现 |
| `rollout.py` | 一条样本的多轮“生成 → 调工具 → 回填图像 → 继续生成”循环，保存实际采样 token 和 logprob | 已实现 |
| `eval.py` | 用相同任务、模板、工具与预算评测 Base / SFT / RL checkpoint，保存轨迹与分类指标 | 已实现 |
| `train_rl.py` | 从 SFT 权重开始，组采样、奖励、advantage、PPO 更新、SwanLab 记录与保存 | 后续 RL 阶段 |

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

`train_sft.py` 采用 `pytrio-skill` 中异步 SFT 示例的提交方式，项目保持锁定 PyTRIO 0.2.8。主循环依次提交 `forward_backward_async(cross_entropy)` 和 `optim_step_async()`，拿到两个 Future 后立即用 `asyncio.create_task()` 启动后台结果记录，继续构造和提交下一批。每个训练客户端的任务仍按 FB → 更新 → 下一批 FB 的顺序执行；客户端不逐批等待计算完成。

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

从 `datasets/sft/` 读取 SFT train/val 的对象标识，在公开 train 中先排除这些对象，再按对象划出约 10% 固定开发集；其余 train 留给后续 RL。在 `datasets/rl/` 下输出 `bench_rl_train.jsonl`、`bench_dev.jsonl` 和原始 test 对应的 `bench_test.jsonl`。`bench_stats.json` 记录数量、开发集任务分布及 SFT 与 dev/test 的对象重叠情况。`eval.py` 默认读取 `datasets/rl/bench_dev.jsonl`。

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

`eval.py` 复用同一个 rollout，在固定数据和交互预算下比较 Base 与 SFT checkpoint。输出各任务的正类 precision、recall、F1、accuracy，以及已评测任务的平均 F1；完整五任务文件对应五任务平均。格式不合格的结果记为无有效预测，accuracy 记错，正类样本记入 FN；没有正类预测时 precision 定义为 0。

评测目录保存 `metrics.json`、`trajectories.jsonl` 和每轮工具图片。JSONL 包含可阅读文本、真实采样 token/logprob、动作 mask 与停止原因。先用这些结果判断 SFT 是否学会完整光谱审核流程，再进入 RL。

评测使用 `tqdm` 显示样本进度、已用时间、预计剩余时间和处理速度。进度条的总数为评测集样本数，每批 rollout 完成并写入轨迹后，按该批实际完成数量更新，尾批不足并发数时也按实际数量计数。

## 默认参数与运行顺序

以下是可从命令行修改的首轮实验默认值，还没有用训练结果调参。

| 参数 | 默认值 |
|---|---|
| 基模（`--base-model`） | `Qwen/Qwen3.5-4B` |
| 训练 tokenizer/processor 文件版本（`--model-revision`） | `main` |
| SDK | 项目锁定的 PyTRIO `0.2.8` |
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

作者的 per-device batch 不能直接与当前脚本的全局 batch 等同；8 卡数据并行时，前者对应全局 32。学习率调度和 warmup 尚未对齐，正式训练前应确定是否沿用作者设置。当前优化器其余参数使用 PyTRIO 0.2.8 默认值，作者 YAML 未显式指定这些字段，尚未逐项核对其训练依赖默认值。本次讨论只记录差异，没有更改训练参数。

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

## 后续 RL

只新增 `train_rl.py`，复用 `protocol.py`、`tools.py`、`rollout.py` 和 `eval.py`。

训练顺序：从选定 SFT checkpoint 的 `state_path` 加载训练权重 → 同题采样一组完整轨迹 → 按最终 YES/NO 和答案格式计算 reward → 计算组内 advantage → 构造仅 assistant 动作参与 loss 的 Datum → PPO 更新 → 保存和评测。

工具观察进入后续上下文，但不参与策略 loss。old logprob 使用实际 rollout 返回值。奖励沿用论文的结果正确性与格式约束，不额外奖励工具调用次数。GRPO 的组内标准化、PPO 裁剪和 loss 归一化在实现这个阶段时对照作者配置确定。

## 本次检查与后续步骤

前期草稿 `sft_data.py`、`verify_sft.py`、`tests/test_sft_data.py` 已移除，职责归入上述 6 个文件。没有增加通用配置层、重试、异常吞掉、assert 或类型/路径校验。检查代码和样例产物放在 `/private/tmp/spec-o3-implementation-check/`，不混入正式训练代码。

本地已完成：

- 五个文件的可读性调整检查：去除文档字符串后，评测、协议、rollout 和数据准备的语法树与修改前一致；绘图工具对比 9 种情况，覆盖画布阈值两侧、红移、可选标签、空窗口和单点窗口，工具返回值与 PNG 字节均一致。五个文件语法检查、数据准备 / 评测 / SFT 的 `--help` 检查通过。未添加防御性逻辑或启动远程任务。
- 数据目录调整：本机已有 SFT 的 4,706 个原始文件已复制到 `datasets/sft/`，包含 4,702 张 PNG；逐文件校验内容与固定版本元数据一致。942 条轨迹共引用 4,641 张图片，全部指向项目内的实际文件，848/94 的训练/验证划分和长度统计保持不变。全局旧缓存保留，原先位于 `datasets/` 根目录的整理文件备份在 `/private/tmp/spec-o3-before-directory-migration-my_0tqdn/`。
- RL 目录检查使用缓存中的 671 条真实 carbon 数据，在临时目录验证 Parquet 输入、`rl/images/` 图片、`rl/spectra/` 数组、JSONL 路径及从 `sft/` 读取对象排除列表。完整 RL 数据尚未下载到项目目录；运行 `prepare_data.py bench` 后按上述结构生成。
- 942 条轨迹的结构转换；逐条确认波段参数保持原值，当前单条工具链的渲染结果与固定版本 Qwen3.5 原生模板完全相同。
- 跨新 user 问题的历史 reasoning 保留，以及 assistant generation mask。
- 已缓存完整图片的 209 条真实轨迹，共 961 张图片，检查视觉 token 展开、右移与监督范围；这批长度最大为 4,581。该批次不代表全量长度统计。
- 一条 4 图、4 轮 assistant 的原始样本仍为 3,223 输入 token、1,278 监督 token。
- 671 条真实 carbon benchmark train 数据的整理，覆盖其中 87 条 `redshift=null` 的记录；本地检查只使用该 parquet，未准备完整五任务 benchmark。
- 用模拟 sampler 跑三轮交互，实际生成局部光谱图并回填；覆盖 stop token 返回/省略、空波段观察、轮数预算、采样前缀连续和观察 mask。
- 用模拟 trainer 检查 batch token 归一化、异步两次 await、参数更新、验证 loss 及 checkpoint 路径记录。
- 异步 SFT 调度检查：使用真实图文数据中的 3 条训练样本、3 条验证样本和实际 PyTRIO `APIFuture`，配合模拟训练客户端运行 2 个 epoch、4 次更新，覆盖不足整 batch 的尾批。验证下一批在上一批结果返回前已提交、乱序返回仍按 step 记录日志、batch 构造在线程中完成、轮末先等待更新再验证，以及每轮 state/sampler 两份保存完成后才继续。检查脚本 `/private/tmp/spec-o3-async-sft-check.py`，产物 `/private/tmp/spec-o3-async-sft-check-otrg38rs/`；其中 loss 和权重路径为模拟结果，没有发起远程训练。

远程接口检查：使用真实 PyTRIO `Qwen/Qwen3.5-4B` Base sampler，对一条 carbon 样本运行两轮。第一轮生成 676 token 并成功调用绘图工具；回填局部图片后，第二轮生成 239 token 并请求另一波段。两轮的 token/logprob 数量对应。该检查在预设的两轮预算处结束，没有最终分类答案；它验证了图文采样与工具回填链路，不能用来评价分类准确率。产物位于 `/private/tmp/spec-o3-implementation-check/live-eval/`。

后续顺序：完成全量数据准备与待审阅符号处理 → 运行 SFT → 在固定开发集比较 Base/SFT → 根据结果实现 `train_rl.py`。本地模拟检查不构成远程训练成功或论文指标复现。

## 参考资料

- [Spec-o3 论文](https://arxiv.org/html/2601.06498v1)
- [作者代码](https://github.com/Maxwell-Jia/spec-o3)
- [Cold-start 数据](https://huggingface.co/datasets/Maxwell-Jia/Spec-o3-ColdStartSFT)
- [SpecVI-Bench](https://huggingface.co/datasets/Maxwell-Jia/SpecVI-Bench)
- [本次改造采用的 Qwen3.5 官方模板](https://huggingface.co/Qwen/Qwen3.5-4B/blob/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a/chat_template.jinja)
- [PyTRIO 多模态文档](https://docs.pytrio.com/docs/guide/vision)
