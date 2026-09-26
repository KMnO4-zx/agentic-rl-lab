# ReTool Quick Start

Run all commands from the repository root. The project requires Python `>=3.13`.

```bash
uv sync
trio login
swanlab login
```

## 1. Download the data

Prepare the training set and AIME25 evaluation set:

```bash
uv run python 05-retool/prepare_data.py
uv run python 04-opsd/00-datasets.py --only aime25
```

## 2. Start training

Begin with a 20-step validation run:

```bash
uv run python 05-retool/train.py \
    --max-steps 20 \
    --save-every 5 \
    --run-name retool-qwen35-4b-step20
```

For the full experiment, set `--max-steps` to `200` and `--save-every` to `50`.

## 3. Run evaluation

First evaluate the base model:

```bash
uv run python 05-retool/eval.py \
    --mode retool \
    --val-n 12 \
    --temperature 1.0 \
    --top-p 0.7 \
    --output 05-retool/eval-results/aime25-retool-base.jsonl
```

Then evaluate the trained sampler weights:

```bash
uv run python 05-retool/eval.py \
    --mode retool \
    --val-n 12 \
    --temperature 1.0 \
    --top-p 0.7 \
    --model-path 'trio://RUN_ID/sampler_weights/RETOOL_WEIGHTS_NAME' \
    --output 05-retool/eval-results/aime25-retool-step200.jsonl
```
