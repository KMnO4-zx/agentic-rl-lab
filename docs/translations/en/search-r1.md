# Reproducing Ten RL Algorithms, Chapter 3: Search-R1 for the Price of a Drink

> Ready to run the code? See the [quick start](./start.md): prepare data → train → evaluate.

![Search-R1 experiment overview](./images/封面.png)

<div align="center">
  <a href="https://www.zhihu.com/people/feng-qi-xia-pian" target="_blank"><img alt="Zhihu" src="https://img.shields.io/badge/Zhihu-知乎-4362f6"></a>
  <a href="https://www.xiaohongshu.com/user/profile/63c2055e000000002502c58c" target="_blank"><img alt="Rednote" src="https://img.shields.io/badge/Rednote-小红书-e93c49"></a>
  <a href="https://github.com/KMnO4-zx/agentic-rl-lab"><img alt="visitors" src="https://komarev.com/ghpvc/?username=KMnO4-zx-agentic-rl-lab-search-r1&amp;label=visitors&amp;color=1283c3&amp;style=flat"></a>
</div>

> **Code and reproduction resources**
>
> - Complete code: [KMnO4-zx/agentic-rl-lab/03-search-r1](https://github.com/KMnO4-zx/agentic-rl-lab/tree/main/03-search-r1)
> - Paper: [Search-R1: Training LLMs to Reason and Leverage Search Engines with Reinforcement Learning](https://arxiv.org/abs/2503.09516)
> - Official implementation: [PeterGriffinJin/Search-R1](https://github.com/PeterGriffinJin/Search-R1)
> - DeepSeek Search tool: [KMnO4-zx/deepseek-search](https://github.com/KMnO4-zx/deepseek-search)
> - Wikipedia API: [Wikimedia Action API](https://www.mediawiki.org/wiki/API:Main_page)
> - Zhihu API keys: [Zhihu developer platform](https://developer.zhihu.com/)
> - PyTRIO: [https://pytrio.com/](https://pytrio.com/)
> - SwanLab, Zhihu experiment: [200-step training record](https://swanlab.cn/@kmno4/llm-agent-rl-lab-search-r1/runs/iy76hn51/chart)
> - SwanLab, DeepSeek Search experiment: [20-step training record](https://swanlab.cn/@kmno4/llm-agent-rl-lab-search-r1/runs/06e4gw6a)
> - SwanLab, Wikipedia experiment: [20-step training record](https://swanlab.cn/@kites/llm-agent-rl-lab-search-r1/runs/swi5nd46)
> - PyTRIO Skill：[SwanHubX/pytrio-skill](https://github.com/SwanHubX/pytrio-skill)

This is the third chapter in my series reproducing ten reinforcement learning algorithms.

The earlier chapters cover:

- [Chapter 0: RL loss functions](https://github.com/KMnO4-zx/agentic-rl-lab/blob/main/00-loss-function/readme.md)
- [Chapter 1: GRPO](https://github.com/KMnO4-zx/agentic-rl-lab/blob/main/01-grpo/readme.md)
- [Chapter 2: OPD](https://github.com/KMnO4-zx/agentic-rl-lab/blob/main/02-opd/readme.md)

This time I finally tried an Agentic RL problem I had wanted to explore: learning when to search, what query to write, whether to search again after reading results, and when to give a final answer.

> **Update: three search backends are supported.** Use `--search-backend deepseek` for higher-concurrency DeepSeek Search, `--search-backend wikipedia` for key-free English Wikipedia, or `--search-backend zhihu` for Zhihu search. All share the same rollout, reward, advantage and loss code.

The initial experiment was inexpensive: roughly the cost of a drink.

The screenshots show the original Zhihu-backed sessions, with evaluation first and training second. PyTRIO usage totaled `13.30` yuan, and Zhihu search added no API charge in that run. A HEYTEA drink in Beijing was about `17.5–20.5` yuan at the time, which is the comparison behind the title.

![](./images/pytrio-consume.png)

<p align="center">
  <img src="./images/喜茶-price.jpg" width="360" alt="Drink-price reference at the time of the experiment">
</p>

A learner also need not start with 100 or 200 steps to inspect behavior.

> With a stable search environment, **20 steps** were enough in this experiment to observe changes in format rate and answering behavior.

The checkpoint evaluation follows. A later section explains the full figure; first look at Steps 20 and 50:

![](./images/checkpoint_em_format.png)

The fixed 70-question evaluation shows early improvements within 50 steps:

```text
Base Model:  Macro EM 28.57% · Format 58.57%
RL Step 20:  Macro EM 31.43% · Format 87.14%
RL Step 50:  Macro EM 45.71% · Format 94.29%
```

**EM** means **Exact Match**. Evaluation extracts the final `Answer:`, lowercases it, removes punctuation and English articles, and normalizes whitespace before comparing against any reference answer. An exact match scores `1`; otherwise it scores `0`. Keyword overlap receives no partial credit.

**Macro EM** first calculates EM for each of 7 benchmarks, then averages them equally so a larger dataset cannot dominate. This fixed evaluation contains 10 questions per benchmark, so Macro EM also equals overall accuracy across the 70 questions.

I later evaluated Base and a 20-step checkpoint on the same 70 questions using DeepSeek Search. Both evaluations share search backend, concurrency, timeout and model settings:

![](./images/deepseek_checkpoint_em_format.png)

| DeepSeek Search | Macro EM | Format | Search success |
| --- | ---: | ---: | ---: |
| Base Model | 44.29% | 88.57% | 100% |
| RL Step 20 | 50.00% | 97.14% | 100% |
| **Change** | **+5.71 pp** | **+8.57 pp** | — |

Under the stable search conditions of this comparison, the checkpoint improves both correctness and format. This is one training run on 70 questions; the limitations are discussed below.

The goal is to make Search-R1's algorithm accessible to ordinary developers. Qwen3.5-4B, PyTRIO and switchable online search provide a runnable loop without first deploying the original retrieval and training infrastructure.

## Where does Search-R1 come from?

Search-R1 was introduced by Bowen Jin and colleagues in 2025, titled:

> Search-R1: Training LLMs to Reason and Leverage Search Engines with Reinforcement Learning

Its motivation is practical.

Traditional RAG commonly retrieves once before answering:

```text
问题 → 检索 → 把结果塞进 prompt → 模型回答
```

That works for simple factual questions, but multi-hop questions often need several searches. For example:

```text
《小王子》的作者出生在哪个国家？
```

The model may first search:

```text
The Little Prince author
```

After identifying Antoine de Saint-Exupéry as the author, it searches:

```text
Antoine de Saint-Exupéry birthplace country
```

It can then answer France.

A working search engine is only the beginning. The model must decide:

- Is the current evidence sufficient?
- What should the next query be?
- Which entity in the results is the next hop?
- Should it keep searching or stop and answer?

Prompt instructions can guide these choices at inference. Search-R1 instead uses reinforcement learning to train the pattern of alternating reasoning and search into model parameters.

The central change is:

> Search becomes an action the model can repeatedly choose throughout reasoning.

## Search-R1 in everyday terms

Imagine a student taking an open-book exam.

In ordinary RAG, the teacher retrieves a page of material first and then asks the student to answer.

Search-R1 gives the student a search box. The student can think, submit a query, read results, revise the query when information is insufficient, and answer when the evidence seems adequate.

At the end, grading checks the answer:

- Correct answers receive higher reward.
- Incorrect answers receive lower reward.
- Missing the required answer format incurs a small additional penalty.

Several trajectories for the same question are compared. Those above the group mean are encouraged; those below it are discouraged.

The complete process is:

![](<./images/Search-R1 · Paper Diagram.png>)

One distinction matters:

> Training updates the language model's LoRA weights. The search engine and embedding model remain fixed parts of the environment.

The model learns when to call search, how to form queries, how to use returned evidence and when to stop.

## How did we reproduce it?

Original Search-R1 builds on veRL. Its official quick start downloads a Wikipedia corpus and E5 index, then launches a local retrieval server.

I initially followed that route. The downloaded, extracted database was about 160 GB, and a smoothly running retrieval service required roughly 180 GB of memory in that setup. Those resources can be appropriate for a close paper reproduction, but they also distract a first-time learner from the algorithm.

Before reaching rewards, advantages and loss masks, learners can encounter infrastructure work such as:

```text
索引怎么下载？
为什么解压后磁盘不够？
Faiss 为什么启动失败？
retriever server 为什么 OOM？
训练卡和检索卡应该怎么分？
```

These are real engineering problems, separate from the core reward, advantage and masking mechanisms.

I replaced local retrieval with a switchable online search environment:

```text
原论文：本地 Wikipedia corpus + E5 retriever
本文：  DeepSeek Search Evidence 模式（默认）
        或 Wikipedia Action API
        或知乎全局搜索 API
```

The official code also supports replacing local retrieval with online search. The algorithm requires an interface of this form:

```text
search(query) → observations
```

The model still generates queries, reads observations, continues reasoning and receives final rewards, preserving the central training loop.

DeepSeek Search comes from my separate [`deepseek-search`](https://github.com/KMnO4-zx/deepseek-search) project. Training uses its constrained `Evidence` mode and receives numbered evidence after search, without consuming an answer summary generated by the search-side model. The agent must still judge sufficiency, choose further searches and produce its own answer.

![](./images/deepseek-search.png)

All three backends implement `search(query) → observations`:

| Backend | Returned content | Default concurrency | Default timeout | Cost and stability in this setup |
| --- | --- | ---: | ---: | --- |
| DeepSeek Search | Constrained, numbered evidence | 16 | 60 seconds | Usage-based API billing; more stable in this experiment |
| Wikipedia | Top 3 English article excerpts and URLs | 3 | 15 seconds | No key or search API charge; evidence limited to Wikipedia |
| Zhihu search | Top 3 titles, excerpts, sources and URLs | 1 | 15 seconds | Free quota at the time, with daily limits per key |

The Wikipedia client sends an identifiable User-Agent and bounds request starts to about 200 RPM, following the [published Wikimedia API limits](https://www.mediawiki.org/wiki/Wikimedia_APIs/Rate_limits) used for this implementation. One Action API request searches and obtains excerpts from the top 3 pages without separate page fetches.

The DeepSeek dashboard showed about `14.06` yuan of daily usage associated with the 20-step run. Actual cost depends on searches, input tokens and cache hits; this is a record of that experiment.

Our configuration is:

| Item | This implementation |
| --- | --- |
| Base Model | `Qwen/Qwen3.5-4B` |
| Trainable parameters | LoRA rank 32 |
| Training framework | PyTRIO |
| Search environment | DeepSeek Search / Wikipedia / Zhihu, selected by argument |
| Training data | NQ + HotpotQA |
| Questions per step | 8 |
| Trajectories per question | 8 |
| Maximum searches | 4 |
| Maximum assistant turns | 6 |
| Maximum trajectory length | 8,192 tokens |
| Reward | Exact Match + Format |
| Advantage | `reward - group_mean` |
| Loss | `importance_sampling` |

This is a **core-algorithm reproduction**. It retains questions, tools, interaction, group-relative advantages, retrieved-token masking and policy updates, while replacing the heavy local retriever. It does not reproduce every infrastructure detail or the paper's final scores.

For learning, Wikipedia offers a key-free path; DeepSeek Search offers general web coverage and higher concurrency; Zhihu remains another option. A closer benchmark reproduction could later restore the local Wikipedia retriever behind the same interface.

## Why use PyTRIO for Agentic RL?

I had tried frameworks such as veRL before. They are capable, but studying one algorithm can first require combined training/inference setup, weight synchronization, vLLM, distributed execution and multi-GPU scheduling.

Agentic RL adds work beyond model generation within a rollout:

```text
模型生成 → 工具调用 → 等待环境 → 模型继续生成 → 再调用工具 → ……
```

On a rented 8-GPU server, waiting for search APIs or long-tail rollouts may leave GPUs idle while wall-clock billing continues.

The billing unit matters. A rented machine typically charges for occupied time, including training and waits. Variable tool latency and trajectory length can therefore make idle time a real cost.

In the PyTRIO setup used here, training is charged by processed training tokens. Waiting for search, local tool execution or unfinished rollouts produces no additional training tokens. Sampling and other model work still cost resources, but the training-token bill does not continue simply because a local tool is taking time.

Responsibilities are divided as follows:

- Local Python: data, tools, rollout state, rewards, advantages and the experiment loop.
- PyTRIO: model sampling, forward/backward passes, LoRA optimization, checkpoints and sampler weights.

The local loop calls ordinary Python interfaces:

```python
sampling_client = training_client.save_weights_and_get_sampling_client()

training_client.forward_backward(
    datums,
    loss_fn="importance_sampling",
).result()

training_client.optim_step(adam_params).result()
```

See the complete loop in [`train.py`](https://github.com/KMnO4-zx/agentic-rl-lab/blob/main/03-search-r1/train.py).

This keeps rollout and training responsibilities clear while using remote compute. For a task with long generation and tool interaction but relatively short backward computation, that separation is useful.

For me, it makes the training service feel like compute accessed through an API, while local code describes the algorithm and experiment.

## Experimental results

Development evaluation fixes 70 questions: 10 from each of 7 benchmarks. First, the 200-step Zhihu-backed experiment:

![](./images/checkpoint_em_format.png)


| Model / checkpoint | Macro EM | Format | 2Wiki | Bamboogle | HotpotQA | MuSiQue | NQ | PopQA | TriviaQA |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen3.5-4B | 28.57% | 58.57% | 30% | 70% | 30% | 10% | 20% | 20% | 20% |
| RL Step 20 | 31.43% | 87.14% | 30% | 50% | 40% | 10% | 20% | 10% | 60% |
| **RL Step 50** | **45.71%** | **94.29%** | **60%** | **70%** | **50%** | **30%** | **30%** | 20% | **60%** |
| RL Step 100 | 35.71% | 100% | 40% | 70% | 30% | 0% | 20% | 30% | 60% |
| RL Step 150 | 38.57% | 100% | 40% | 70% | 30% | 20% | 20% | 30% | 60% |
| RL Step 200 | 40.00% | 100% | 40% | 70% | 40% | 10% | 30% | 30% | 60% |

### Zhihu: behavior already changes by 20 steps

A first algorithm check need not begin with 200 steps.

In the small 20-step trial:

```text
Macro EM: 28.57% → 31.43%
Format:   58.57% → 87.14%
```

Format changes particularly clearly. After multi-turn search, the model starts ending trajectories with the required form:

```text
Answer: <short answer>
```

This avoids further tool calls after the search budget is exhausted, or explanations without a scoreable final answer.

Step 20 comes from an earlier small run whose live search conditions differ from the main experiment. Its percentage gains are not a controlled paper-level result, but show that real rollouts, rewards, group advantages and updates changed behavior.

### Zhihu: Step 50 leads within the reliable window

Step 50 in the main run reaches `45.71%` Macro EM, or 32 correct answers out of 70, and `94.29%` Format.

Search success during that checkpoint evaluation is `96.41%`, making it a useful result to inspect.

One actual MuSiQue trajectory illustrates the change. Base remains at a tool call after 4 searches; Step 50 uses 3 searches, retains the `John Cabot → child` entity chain and answers `Sebastian Cabot`:

![](<./images/Real Trajectory · Base vs RL Checkpoints.png>)

One trajectory cannot replace aggregate evaluation, but illustrates the intended behavior: searching for relevant evidence and knowing when to stop.

### Zhihu: what happens after Step 50?

Reward alone might suggest later model regression:

![](./images/swanlab-reward.png)

Search diagnostics change that interpretation:

![](./images/swanlab-search.png)

The run used three Zhihu keys, which successively reached quota limits. Later searches returned many errors. We treat at least the first 50 steps as the reliable training window; subsequent correctness rewards are confounded by the external tool environment.

This helps explain the following pattern:

```text
reward/format 继续上升并稳定接近 1
reward/correct 和 reward/mean 在搜索环境恶化后下降
```

Format reward does not require successful retrieval. A correctly formed final `Answer:` line can be scored reliably even when search fails.

Correctness reward does depend on evidence. After an API failure, a reasonable query may yield nothing useful, so reward reflects both policy quality and service state.

Group-relative learning amplifies the issue:

- A reasonable trajectory can receive low reward because of an API error.
- Differences among group members may come from the service rather than the policy.
- If environment failures make all rewards identical, every advantage becomes 0 and the group contributes no gradient.

The late decline therefore cannot establish algorithm failure or an implementation bug. Early EM changes and format learning show an active training loop; the missing ingredient in the later portion is a consistently available search environment.

### DeepSeek Search: a 20-step experiment with stable retrieval

After observing the Zhihu quota issue, I ran another 20 steps with DeepSeek Search and evaluated Base and Step 20 on the same 70 questions under the same search settings.

Per-benchmark results are:

| Model / checkpoint | Macro EM | Format | 2Wiki | Bamboogle | HotpotQA | MuSiQue | NQ | PopQA | TriviaQA |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen3.5-4B | 44.29% | 88.57% | 50% | 70% | 60% | 20% | 40% | 20% | 50% |
| **RL Step 20** | **50.00%** | **97.14%** | **60%** | 70% | **70%** | **30%** | 40% | **30%** | 50% |

The 20 steps produce two directly checkable changes:

```text
Macro EM: 44.29% → 50.00%（+5.71 pp，70 题中净增 4 题）
Format:   88.57% → 97.14%（+8.57 pp）
```

Both evaluations have `search/success_rate=100%`, with `search/error_rate`, `search/429_rate` and `search/timeout_rate` all `0`. This comparison is therefore not confounded by observed search failures or exhausted quotas.

In the training plot, red is the DeepSeek 20-step run and green the original Zhihu experiment:

![](./images/deepseek-reward.png)

The red curve shows higher early correctness and format rewards. Because the live environments and training lengths differ, curve heights are descriptive. The matched Base / Step 20 evaluation above is the more controlled comparison.

The DeepSeek run also has more degenerate groups. That metric means all 8 trajectories for a question receive identical rewards; it combines all-correct and all-incorrect cases. Higher correctness suggests more all-correct groups, but current logs do not separate them. Increasing `group_size` can reduce degeneracy under mixed-success sampling, at roughly linear additional rollout and search cost.

This run shows an early optimization signal under stable search conditions. One run and 70 development questions still fall short of a large, multi-seed generalization study.

## The Search-R1 training loop in detail

The core idea is now established. Runnable code is in the [GitHub repository](https://github.com/KMnO4-zx/agentic-rl-lab).

The following sections follow an actual training step. The directory contains:

```text
03-search-r1/
├── prepare_data.py   # 下载并整理训练与评测数据
├── data.py           # 读取本地 JSONL
├── protocol.py       # search tool schema、prompt 和 tool-call 解析
├── search.py         # DeepSeek / Wikipedia / 知乎三种搜索后端
├── rollout.py        # 多轮工具调用状态机
├── reward.py         # EM + Format reward
├── train.py          # PyTRIO Search-R1 训练循环
├── eval.py           # Base / checkpoint 统一评测
└── analyse.py        # 绘制知乎与 DeepSeek checkpoint 结果图
```

## Step 1: prepare questions and answers

Data comes from the official [`PeterJinGo/nq_hotpotqa_train`](https://huggingface.co/datasets/PeterJinGo/nq_hotpotqa_train), downloaded at a fixed version through a ModelScope mirror.

The preparation script is [`prepare_data.py`](https://github.com/KMnO4-zx/agentic-rl-lab/blob/main/03-search-r1/prepare_data.py).

Training data contains:

| Source | Questions |
| --- | ---: |
| NQ | 79,168 |
| HotpotQA | 90,447 |
| Total | 169,615 |

Training requires four fields:

```json
{
  "id": "...",
  "question": "...",
  "answers": ["..."],
  "data_source": "nq"
}
```

There are no annotated search queries or expert reasoning trajectories. The model receives a question, then generates its own search process under the current policy.

The distinction is:

> We do not use SFT to imitate a fixed search path. Final outcomes provide rewards for exploring useful paths.

## Step 2: declare search as a model tool

The protocol is in [`protocol.py`](https://github.com/KMnO4-zx/agentic-rl-lab/blob/main/03-search-r1/protocol.py).

The search schema is short:

```python
SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search",
        "description": "Search the web for evidence. Use a concise English query.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "A concise English search query.",
                },
            },
            "required": ["query"],
        },
    },
}
```

Each turn injects tools through Qwen3.5's own chat template:

```python
prompt_tokens = tokenizer.apply_chat_template(
    messages,
    tools=[SEARCH_TOOL],
    tokenize=True,
    add_generation_prompt=True,
    enable_thinking=False,
)
```

The model emits structured `<tool_call>` output, which `protocol.py` parses into a query. After real search, the result returns in a `role="tool"` observation; no guessed stop word is needed to infer search intent.

Search backends are implemented in [`search.py`](https://github.com/KMnO4-zx/agentic-rl-lab/blob/main/03-search-r1/search.py). Training and evaluation use the same client factory:

```python
search_client = create_search_client(
    args.search_backend,
    Path(__file__).resolve().parent / ".env",
    model=args.search_model,
    timeout=args.search_timeout,
)
```

`DeepSeekSearchClient` uses `mode="evidence"` and converts numbered evidence into `SearchItem` records. `WikipediaSearchClient` obtains the top 3 English excerpts and URLs in one Action API call. `ZhihuSearchClient` rotates keys and retains the top 3 titles, excerpts, sources and URLs. All return the same `SearchResult`, so the multi-turn state machine is independent of the provider.

Each client logs success, errors, 429 responses and latency. DeepSeek also records requests, evidence counts, input tokens, cache-hit tokens and output tokens, connecting environment quality with API usage.

## Step 3: let trajectories diverge after search

This is an easily missed detail of multi-turn implementation.

The first 8 trajectories for a question share an identical prompt, so one request can sample them together:

```python
sample_async(
    prompt=shared_prompt,
    num_samples=8,
)
```

After that, they may produce 8 different queries and receive 8 different observations:

```text
query_i 不同
→ observation_i 不同
→ 下一轮 prompt_tokens_i 不同
```

One shared prompt with `num_samples=8` no longer represents those branches. Each trajectory must advance independently through concurrent `num_samples=1` requests.

![](<./images/Group Rollout · Shared Root and Diverged Contexts.png>)

The state machine is in [`rollout.py`](https://github.com/KMnO4-zx/agentic-rl-lab/blob/main/03-search-r1/rollout.py):

```text
第一轮：
每道题 1 个 shared prompt × num_samples=8

第一次搜索之后：
每条未结束轨迹 1 个独立 prompt × num_samples=1
多个 sample_async 用 asyncio.gather 并发
```

Within one trajectory, actions remain strictly sequential:

```text
assistant generation
→ search(query)
→ tool observation
→ next assistant generation
```

Concurrency applies across trajectories. This preserves causality without forcing all 64 trajectories to wait serially.

## Step 4: calculate reward from the final answer

Reward is implemented in [`reward.py`](https://github.com/KMnO4-zx/agentic-rl-lab/blob/main/03-search-r1/reward.py).

The model must leave exactly one nonempty final answer:

```text
Answer: <short answer>
```

Three reward values are used:

| Final result | Reward |
| --- | ---: |
| Valid format and correct answer | `1.0` |
| Valid format and incorrect answer | `0.0` |
| Invalid format or missing answer | `-0.1` |

The code is only a few lines:

```python
def score_answer(text: str, references: list[str]) -> RewardResult:
    answer = extract_answer(text)
    if answer is None:
        return RewardResult(-0.1, False, False, None)
    exact_match = any(
        normalize_answer(answer) == normalize_answer(reference)
        for reference in references
    )
    return RewardResult(float(exact_match), True, exact_match, answer)
```

There is no separate reward for search count or manually scored intermediate queries.

Such rewards could encourage endless searches or superficial keyword matching. This implementation uses final outcomes and lets the policy explore useful intermediate searches.

## Step 5: calculate advantages within each question

The 8 trajectories produce 8 final rewards. Calculate:

```math
A_i = r_i - \operatorname{mean}(r_1, r_2, \ldots, r_8)
```

See [`rollout.py`](https://github.com/KMnO4-zx/agentic-rl-lab/blob/main/03-search-r1/rollout.py):

```python
mean_reward = sum(item.reward for item in group) / len(group)
for item in group:
    item.advantage = item.reward - mean_reward
```

For example, a group may have these rewards:

```text
[1.0, 0.0, 0.0, -0.1, 1.0, 0.0, 0.0, -0.1]
```

Its mean is `0.225`, producing these three kinds of advantage:

```text
1.0  → +0.775
0.0  → -0.225
-0.1 → -0.325
```

Relatively better trajectories become more likely, and worse ones less likely, within the same question.

If all rewards match, every advantage is 0 and the code skips the update for that group. Search failures can therefore consume an expensive rollout without providing a useful relative gradient.

## Step 6: keep search results in context and mask their loss

This is a central difference from single-turn GRPO.

A multi-turn trajectory contains four kinds of token:

```text
system + user
assistant search(query)
tool observation
assistant final Answer
```

Assistant-generated tokens are actions to optimize. Search observations are environment state: they must remain visible but must not be trained as generated actions.

![](<./images/Reward Advantage Token Mask Artwork.png>)

No extra `mask` field is required here. Observation tokens receive zero advantage and zero old-logprob placeholders:

```text
system / user / tool observation: advantage = 0
assistant tool call / final answer: advantage = trajectory_advantage
```

See `build_datum()` in [`train.py`](https://github.com/KMnO4-zx/agentic-rl-lab/blob/main/03-search-r1/train.py).

The core logic is:

```python
full_tokens += delta_observation + turn.completion_tokens
old_logprobs_by_token += [0.0] * len(delta_observation) + turn.logprobs
advantages_by_token += (
    [0.0] * len(delta_observation)
    + [trajectory.advantage] * len(turn.completion_tokens)
)

input_tokens = full_tokens[:-1]
target_tokens = full_tokens[1:]
old_logprobs = old_logprobs_by_token[1:]
advantages = advantages_by_token[1:]
```

Then construct the PyTRIO `Datum`:

```python
datum = trio.Datum(
    model_input=trio.ModelInput.from_ints(input_tokens),
    loss_fn_inputs={
        "target_tokens": np.asarray(target_tokens, dtype=np.int64),
        "logprobs": np.asarray(old_logprobs, dtype=np.float32),
        "advantages": np.asarray(advantages, dtype=np.float32),
    },
)
```

`input_tokens`, `target_tokens`, `logprobs` and `advantages` must share consistent autoregressive alignment and equal lengths. Old log probabilities come from the rollout sampler and cannot be recomputed after a model update.

Search observations can then influence later decisions without incorrectly entering the policy loss as model actions.

## Step 7: compute full-group advantages before micro-batching

One training step contains:

```text
8 questions × 8 trajectories = 64 trajectories
```

With trajectories up to 8,192 tokens, this implementation packs the 64 trajectories into bounded remote training requests.

Advantages must first be calculated over all 8 trajectories for each question. Computing group means after arbitrary splitting would change the algorithm.

The order is therefore:

```text
完整 rollout group
→ reward
→ group-relative advantage
→ 每条完整轨迹构造 Datum
→ 按 padding 后的矩形大小拆 micro-batch
→ 累积 forward/backward
→ 整个逻辑 step 只做一次 optimizer step
```

The code bounds:

```text
单条 Datum ≤ 8,192 tokens
单个 micro-batch ≤ 32 Datums
micro-batch items × max_sequence_length ≤ 64,000
```

PyTRIO averages samples within each `forward_backward` call. Different-sized micro-batches therefore scale advantages by `n_k / N`, preserving the global mean of the logical batch under gradient accumulation.

See `pack_micro_batches()` and `weight_micro_batch_for_global_mean()` in [`train.py`](https://github.com/KMnO4-zx/agentic-rl-lab/blob/main/03-search-r1/train.py).

## Running a 20-step experiment

The following path runs the full Search-R1 pipeline with a small training budget, without a separate simplified algorithm branch.

### 1. Install and log in

```bash
git clone https://github.com/KMnO4-zx/agentic-rl-lab.git
cd agentic-rl-lab

uv sync
trio login
swanlab login
```

PyTRIO handles training and sampling remotely; the local host needs a CPU environment.

### 2. Download and prepare data

```bash
uv run python 03-search-r1/prepare_data.py
```

This generates:

```text
03-search-r1/datasets/
├── train.jsonl    # 169,615 道训练题
├── dev.jsonl      # 固定 70 道评测题
└── test.jsonl     # 完整评测池
```

### 3. Select and configure search

Copy the environment template:

```bash
cp 03-search-r1/.env.example 03-search-r1/.env
```

For the default DeepSeek Search backend, log in:

```bash
uv run deepseek-search login
```

Alternatively, place the API key in `03-search-r1/.env`:

```dotenv
DEEPSEEK_API_KEY=your_deepseek_api_key
```

For key-free public search, use `--search-backend wikipedia`. It searches English Wikipedia, defaults to concurrency `3` and timeout `15` seconds, and needs no `.env` change.

For Zhihu, request a search key from the personal center on the [developer platform](https://developer.zhihu.com/). At the time of the original note, the page advertised 1000 free calls per day; consult the platform for current quotas.

![](./images/zhihu-search.png)

Place it in the same `.env` file:

```dotenv
ZHIHU_SEARCH_KEYS=your_first_key,your_second_key,your_third_key
```

The Zhihu experiment used three keys with available quota. Whichever backend you choose, check `search/success_rate` before full training.

### 4. Run a small 20-step experiment

Enter the Search-R1 directory:

```bash
cd 03-search-r1
```

With DeepSeek Search:

```bash
uv run python train.py \
    --max-steps 20 \
    --questions-per-batch 8 \
    --group-size 8 \
    --save-every 5 \
    --base-model Qwen/Qwen3.5-4B \
    --search-backend deepseek \
    --run-name search-r1-qwen35-4b-deepseek \
    --swanlab-mode online
```

With Wikipedia:

```bash
uv run python train.py \
    --max-steps 20 \
    --questions-per-batch 8 \
    --group-size 8 \
    --save-every 5 \
    --base-model Qwen/Qwen3.5-4B \
    --search-backend wikipedia \
    --run-name search-r1-qwen35-4b-wikipedia \
    --swanlab-mode online
```

With Zhihu:

```bash
uv run python train.py \
    --max-steps 20 \
    --questions-per-batch 8 \
    --group-size 8 \
    --save-every 5 \
    --base-model Qwen/Qwen3.5-4B \
    --search-backend zhihu \
    --run-name search-r1-qwen35-4b-zhihu \
    --swanlab-mode online
```

Default search concurrency / timeout are `16` / `60` seconds for DeepSeek, `3` / `15` for Wikipedia and `1` / `15` for Zhihu. Override them with `--search-concurrency` and `--search-timeout`. For a longer run, set `--max-steps 100` and `--save-every 50`.

Each step uses 8 questions and 8 real multi-turn trajectories per question. Every 5 steps it saves:

```text
*-state    # 用于断点续训
*-weights  # 用于采样与评测
```

Over 20 steps, inspect:

- Whether `reward/format` rises.
- Whether final `Answer:` outputs become reliable.
- Early changes in `reward/correct`.
- Search counts and assistant turns.
- Stability of `search/success_rate`.
- The frequency of degenerate groups.

### 5. Evaluate Base and Step 20

Using DeepSeek Search as the example, evaluate Base first:

```bash
uv run python eval.py \
    --batch-size 16 \
    --base-model Qwen/Qwen3.5-4B \
    --search-backend deepseek \
    --search-model deepseek-v4-flash \
    --search-concurrency 16 \
    --search-timeout 60 \
    --output eval_result/eval_results_base_deepseek_search.jsonl
```

Training prints the Step 20 sampler weights path. Pass it to the evaluator:

```bash
uv run python eval.py \
    --batch-size 16 \
    --model-path 'trio://YOUR_STEP_20_SAMPLER_WEIGHTS' \
    --search-backend deepseek \
    --search-model deepseek-v4-flash \
    --search-concurrency 16 \
    --search-timeout 60 \
    --output eval_result/eval_results_rl_step_20_deepseek_search.jsonl
```

For Wikipedia, use `--search-backend wikipedia --search-concurrency 3 --search-timeout 15` in both evaluations. For Zhihu, use `--search-backend zhihu`. Give different backends different output filenames. Base and checkpoint must share the backend and search settings; absolute scores across backends are not directly comparable.

For an initial pipeline check, add `--limit 20` before running the fixed 70-question evaluation.

[`eval.py`](https://github.com/KMnO4-zx/agentic-rl-lab/blob/main/03-search-r1/eval.py) uses the same tokenizer, tool protocol, search environment, trajectory limits and EM rules for Base and checkpoint.

### 6. Plot evaluation results

Plot the original Zhihu Base and Step 20, 50, 100, 150 and 200 results:

```bash
uv run python analyse.py
```

Plot the DeepSeek Base / Step 20 comparison:

```bash
uv run python analyse.py --preset deepseek
```

[`analyse.py`](https://github.com/KMnO4-zx/agentic-rl-lab/blob/main/03-search-r1/analyse.py) reads each JSONL's final `summary.metrics`. Its DeepSeek preset also verifies 70 questions, matching backend and matching search settings before combining the results.

## Which training metrics matter?

One reward curve is insufficient for Search-R1.

| Metric | Question |
| --- | --- |
| `reward/mean` | How are complete trajectories performing on average? |
| `reward/correct` | Is final-answer accuracy changing? |
| `reward/format` | Does the model stop searching and answer in the required format? |
| `rollout/search_calls` | How often does each trajectory search? |
| `rollout/turns` | Are trajectories becoming longer or shorter? |
| `rollout/degenerate_group_rate` | How many questions lack relative learning signals? |
| `train/loss_tokens_per_rollout_batch` | How many assistant tokens enter the loss? |
| `search/success_rate` | Is the tool environment reliable? |
| `search/error_rate` | Might external errors contaminate rewards? |
| `search/latency` | Is search a rollout bottleneck? |
| `search/results` | How much evidence is returned per search? |
| `search/input_tokens` / `search/output_tokens` | What is DeepSeek Search API usage? |

If correctness falls while search errors rise, inspect the environment before attributing the change to the policy.

Unlike a typically deterministic mathematical verifier, a tool environment can time out, rate-limit, return nothing or change over time. Environment quality is itself an experimental variable.

## Reproduction boundaries

First, this reproduces the core Search-R1 algorithm, with different model, backend, framework and some settings. Its absolute scores cannot be directly compared with the paper.

Second, 70 fixed questions, 10 per benchmark, are useful for checking behavior and implementation. They do not replace larger multi-seed experiments.

Third, the Zhihu keys reached quotas during training. We treat at least the first 50 steps as the credible window. Later checkpoints document behavior, without proving overtraining or policy collapse.

Fourth, the DeepSeek Base / Step 20 evaluations share backend, model and search settings, with 100% search success in both. The `+5.71 pp` Macro EM and `+8.57 pp` Format changes are useful early signals, still insufficient for a stable generalization claim from one run.

Fifth, Zhihu and DeepSeek return different evidence. Their Base scores are not directly comparable; checkpoint comparisons stay within the same search environment.

Within those limits, the experiment provides a runnable way to understand Search-R1 with modest local storage and compute requirements.

## Summary

Search-R1's central loop can be expressed simply:

```text
1. 给模型一个问题和搜索工具。
2. 让当前策略生成多轮 search / observation / answer 轨迹。
3. 只根据最终答案计算 reward。
4. 在同一道题的多条轨迹之间计算相对 advantage。
5. 只训练模型生成的 assistant action token。
6. 用 PyTRIO importance_sampling 更新 LoRA。
7. 导出新 sampler，继续下一轮 rollout。
```

It trains the ability to actively obtain useful information from an environment.

The original retrieval setup's roughly 160 GB database and 180 GB memory requirement are relevant to a close reproduction. For learning the algorithm, switchable online search makes the entry point much lighter.

In these runs, 20 steps already revealed format and behavior changes. Wikipedia offers a key-free backend; DeepSeek offers broader web coverage and higher concurrency; Zhihu remains supported. Historical costs were `13.30` yuan for the Zhihu-backed PyTRIO training session and about `14.06` yuan in the DeepSeek search dashboard for its 20-step experiment. Wikipedia search itself incurred no API charge.

The appeal for me is spending time on rewards, rollouts, masks and experiment design instead of first maintaining a large training/inference cluster.

I expect model training to become more like using cloud storage or a database: ordinary Python describes the algorithm, while sampling, training and checkpoints are remote capabilities. That could make more experiments practical for individual researchers and small teams.

I had not yet chosen the next chapter when writing this note—perhaps GSPO, OPSD, or another Agentic RL idea.

## References

### Paper and official implementation

1. Bowen Jin et al. [Search-R1: Training LLMs to Reason and Leverage Search Engines with Reinforcement Learning](https://arxiv.org/abs/2503.09516), 2025.
2. Bowen Jin et al. [An Empirical Study on Reinforcement Learning for Reasoning-Search Interleaved LLM Agents](https://arxiv.org/abs/2505.15117), 2025.
3. [PeterGriffinJin/Search-R1](https://github.com/PeterGriffinJin/Search-R1)

### Data, model and search

1. [PeterJinGo/nq_hotpotqa_train](https://huggingface.co/datasets/PeterJinGo/nq_hotpotqa_train)
2. [Qwen/Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B)
3. [KMnO4-zx/deepseek-search](https://github.com/KMnO4-zx/deepseek-search)
4. [Zhihu global search API](https://developer.zhihu.com/docs?key=global_search)

### This implementation

1. [Complete Search-R1 PyTRIO code](https://github.com/KMnO4-zx/agentic-rl-lab/tree/main/03-search-r1)
2. [PyTRIO documentation](https://docs.pytrio.cn/)
3. [SwanLab documentation](https://docs.swanlab.cn/)
