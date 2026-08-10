<div align="center">

<a href="https://github.com/KMnO4-zx/agentic-rl-lab">
  <img src="images/agentic-rl-lab.png" alt="Agentic-RL Lab" width=100% />
</a>

<br>

<p>
  <a href="./README.md">中文</a> | <strong>English</strong>
</p>

<p>
  Reproduce and dissect frontier LLM reinforcement learning algorithms — GRPO, OPD, OPSD, GSPO, DAPO, Search-R1, ReTool, ALFWorld, Slime and more — with simpler code and a lower GPU barrier.
</p>

<p>
  <a href="https://pytrio.cn/"><img alt="PyTRIO" src="https://img.shields.io/badge/PyTRIO-Remote%20Training-d94a45?style=flat" /></a>
  <a href="https://swanlab.cn/"><img alt="SwanLab" src="https://img.shields.io/badge/SwanLab-Experiment%20Tracking-258f4b?style=flat" /></a>
  <a href="https://swanlab.cn/@kmno4/llm-agent-rl-lab/overview"><img alt="SwanLab Experiments" src="https://img.shields.io/badge/Tracking_in-SwanLab-C4F042?style=flat&amp;labelColor=000000" /></a>
  <a href="https://www.zhihu.com/people/feng-qi-xia-pian"><img alt="Zhihu" src="https://img.shields.io/badge/Zhihu-知乎-4362f6?style=flat" /></a>
  <a href="https://www.xiaohongshu.com/user/profile/63c2055e000000002502c58c"><img alt="Rednote" src="https://img.shields.io/badge/Rednote-小红书-e93c49?style=flat" /></a>
  <a href="https://github.com/KMnO4-zx/agentic-rl-lab"><img alt="visitors" src="https://komarev.com/ghpvc/?username=KMnO4-zx-agentic-rl-lab&amp;label=visitors&amp;color=1283c3&amp;style=flat" /></a>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.13%2B-306998?style=flat" />
</p>

</div>

<p align="center">
  💬 <strong>WeChat Group:</strong>
  <a href="https://github.com/KMnO4-zx/agentic-rl-lab/issues/13">Click to view the group QR code</a>
</p>

## Introduction

This is a lab notebook and tutorial-style repository. I use [PyTRIO](https://pytrio.com) to reproduce a set of reinforcement learning algorithms related to LLM / Agent RL, with three goals in mind:

1. Explain each algorithm clearly first: which paper it comes from, what problem it solves, and what its core variables are.
2. Then reproduce it with runnable code: data, reward, loss, training loop, and SwanLab tracking are all in this repo.
3. Maybe build a friendlier and more lightweight Agent RL training framework in the future~
4. ***For the tenth article, I will reproduce and dissect Harness-RL.***

> *Why PyTRIO? I had long wanted to dig deep into Agentic-RL algorithms, but kept being held back by practical obstacles: no GPUs, the complexity of tightly coupled training-and-inference codebases, the highly coupled engineering of Verl, and so on. PyTRIO changed that — it lets me study Agentic-RL algorithms with much simpler code and a much lower barrier. I learned and reproduced everything in this repository in less than a month.*

> *I believe products like PyTRIO or Tinker are future-facing infrastructure for LLM post-training. Getting hands-on with them early is valuable for both algorithm engineers and researchers.*

## Table of Contents

| Chapter | Topic | Content |
| --- | --- | --- |
| [Ch. 0](./00-loss-function/readme.md) | Loss Function | An intuitive explanation of what `importance_sampling`, `ppo`, and `cispo` are each optimizing |
| [Ch. 1](./01-grpo/readme.md) | GRPO | Reproduce GRPO on GSM8K and compare the `importance_sampling` / `ppo` / `cispo` losses |
| [Ch. 2](./02-opd/general-opd/readme.md) | General OPD | A minimal closed loop on DeepMath-103K: Student sampling, Teacher scoring, and reverse KL |
| [Ch. 2](./02-opd/readme.md) | Medical OPD | Starting from Medical SFT, boost medical capability with SAR-OPD and IDT-OPD while preserving general ability |
| [Ch. 3](./03-search-r1/readme.md) | Search-R1 | Reproduce multi-turn search RL with Qwen3.5-4B, PyTRIO, and switchable online search backends |
| [Ch. 4](./04-opsd/readme.md) | OPSD | Distill the Student's self-sampled trajectories with a fixed step-0 Teacher |
| [Ch. 5](./05-retool/readme.md) | ReTool | Reproduce code-interleaved Agentic RL with Qwen3.5-4B, PyTRIO, and a local code sandbox |
| [Ch. 6](./06-dapo/readme.md) | DAPO | Dissect the four core improvements and measure the real time cost of Dynamic Sampling in training |
| [Ch. 7](./07-gspo/readme.md) | GSPO | Lift the importance ratio and clipping from the token level to the sequence level |
| [Ch. 8](./08-alfworld/readme.md) | ALFWorld | Train a household agent with 12K-token long trajectories, a real TextWorld environment, and group-relative advantage |

## Quick Start

If you want to clone this repository directly:

```bash
git clone https://github.com/KMnO4-zx/agentic-rl-lab.git
cd agentic-rl-lab
uv sync
```

To run Chapter 8 (ALFWorld), you also need the TextWorld environment dependencies:

```bash
uv sync --extra alfworld
```

If you only want to pull a single demo script into your own project, the current base dependencies are:

```bash
uv add \
  "datasets>=5.0.0" \
  "math-verify>=0.9.0" \
  "matplotlib>=3.11.0" \
  "modelscope>=1.38.1" \
  "numpy>=2.5.1" \
  "openai>=2.44.0" \
  "python-dotenv>=1.2.2" \
  "pytrio==0.2.7" \
  "swanlab==0.9.2" \
  "torch>=2.9.1" \
  "tqdm>=4.68.3"
```

The DeepSeek Search backend used by Search-R1 is pinned to a fixed source revision:

```bash
uv add "deepseek-search @ git+https://github.com/KMnO4-zx/deepseek-search.git@6215c8dbb7347f94e9dcea6e741df5918449d6c4"
```

The ALFWorld optional extra corresponds to:

```bash
uv add --optional alfworld "alfworld==0.4.2" "spacy==3.8.13"
```

## Star History

<div align="center">
  <img src="./images/star-history-202685.png" alt="GitHub Star History" width="700" />
</div>

## Contributor

<div align=center style="margin-top: 30px;">
  <a href="https://github.com/KMnO4-zx/agentic-rl-lab/graphs/contributors">
    <img src="https://contrib.rocks/image?repo=KMnO4-zx/agentic-rl-lab" />
  </a>
</div>

## License

See [LICENSE](./LICENSE).
