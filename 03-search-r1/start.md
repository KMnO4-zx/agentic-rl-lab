# Search-R1 快速启动

以下命令均从仓库根目录运行。项目要求 Python `>=3.13`。

```bash
uv sync
trio login
swanlab login
```

## 1. 下载数据

```bash
uv run python 03-search-r1/prepare_data.py
```

使用 DeepSeek Search 时，登录一次即可：

```bash
uv run deepseek-search login
```

使用知乎搜索时，在 `03-search-r1/.env` 中填写 `ZHIHU_SEARCH_KEYS`。配置模板位于 `03-search-r1/.env.example`。

## 2. 启动训练

DeepSeek Search 后端：

```bash
uv run python 03-search-r1/train.py \
    --max-steps 20 \
    --questions-per-batch 8 \
    --group-size 8 \
    --save-every 5 \
    --base-model Qwen/Qwen3.5-4B \
    --search-backend deepseek \
    --run-name search-r1-qwen35-4b-deepseek \
    --swanlab-mode online
```

知乎搜索后端：

```bash
uv run python 03-search-r1/train.py \
    --max-steps 20 \
    --questions-per-batch 8 \
    --group-size 8 \
    --save-every 5 \
    --base-model Qwen/Qwen3.5-4B \
    --search-backend zhihu \
    --run-name search-r1-qwen35-4b-zhihu \
    --swanlab-mode online
```

正式训练可把 `--max-steps` 改为 `100`，并把 `--save-every` 改为 `50`。

## 3. 运行评测

下面以 DeepSeek Search 为例。先评测 Base Model：

```bash
uv run python 03-search-r1/eval.py \
    --batch-size 16 \
    --base-model Qwen/Qwen3.5-4B \
    --search-backend deepseek \
    --search-model deepseek-v4-flash \
    --search-concurrency 16 \
    --search-timeout 60 \
    --output 03-search-r1/eval_result/eval_results_base_deepseek_search.jsonl
```

再评测训练得到的 sampler weights：

```bash
uv run python 03-search-r1/eval.py \
    --batch-size 16 \
    --model-path 'trio://RUN_ID/sampler_weights/STEP_20_WEIGHTS_NAME' \
    --search-backend deepseek \
    --search-model deepseek-v4-flash \
    --search-concurrency 16 \
    --search-timeout 60 \
    --output 03-search-r1/eval_result/eval_results_rl_step_20_deepseek_search.jsonl
```

评测知乎后端时，两条命令都改为 `--search-backend zhihu`。Base 与 checkpoint 必须使用相同的后端和搜索配置。
