---
title: GRPO vs DAPO vs GSPO from Loss Functions to Training Code
description: Compare optimization units, clipping, dynamic sampling and implementation boundaries in the GRPO, DAPO and GSPO chapters, with links to equations and code.
---

# GRPO vs DAPO vs GSPO

All three chapters begin with the same loop: sample a group of answers to a prompt, compute verifiable rewards, derive advantages from relative performance within the group, and update the policy. To understand the differences, examine importance ratios, clipping, sample selection and loss normalization in that order.

This page connects the repository’s learning resources. Models, data and training budgets differ across chapters, so their scores cannot establish a ranking of the three methods.

| What to examine | GRPO chapter | DAPO chapter | GSPO chapter |
| --- | --- | --- | --- |
| Starting point | Group sampling, rewards, advantages and a policy update | How four training changes fit together | Sequence-level importance ratios and clipping |
| Ratios and clipping | Experiments with importance sampling, PPO and CISPO | Clip-Higher uses asymmetric clipping bounds | Exponentiate the mean token log-ratio and clip at the sequence level |
| Sample selection | Complete the basic training loop first | Filter groups with all-correct or all-incorrect raw outcomes, then sample replacements | This implementation does not add dynamic sampling |
| Practical costs to record | How the loss choice changes training behavior | Discarded completions still cost generation time; refill rounds also cause waiting | Sequence length, clip fraction and normalization over the original batch |
| Scope of this repository | GSM8K experiments and code | Benefits and costs in the current synchronous loop | Core loss and training pipeline, without paper-scale or MoE stability experiments |

## Start with GRPO: what happens in one update?

Read the [GRPO walkthrough](/en/experiments/grpo/) to connect sampling, rewards and policy updates, then run the [quick start](/en/experiments/grpo/run). Return to [loss-function intuition](/en/experiments/loss-functions/) when you need to revisit log probabilities, importance ratios or clipping.

When switching losses, keep the model, data, sampling budget and random seed fixed. Otherwise an observed change may come from another condition.

## Continue with DAPO: where do informative samples come from?

The [DAPO chapter](/en/experiments/dapo/) covers Clip-Higher, Dynamic Sampling, Token-level Policy Gradient Loss and Soft Overlong Punishment. Dynamic sampling here filters by raw correctness, while advantages use a reward shaped by a length penalty. These are distinct signals.

The local implementation bounds refill rounds and records actual rollout time. Filtered answers consume sampling resources even though they do not enter the final loss. See the [DAPO quick start](/en/experiments/dapo/run).

## Then study GSPO: why use a sequence ratio?

The [GSPO chapter](/en/experiments/gspo/) exponentiates the mean token log-ratio to obtain a length-normalized sequence ratio. Every token in the answer shares one clipping decision. This constrains a different quantity from a token-level ratio, so clipping thresholds are not interchangeable.

The chapter documents the core loss, training pipeline and AIME25 evaluation, including the absence of a matched GRPO control. All-correct or all-incorrect groups have zero advantage. Skipping their gradient computation must still preserve the original normalization. See the [GSPO quick start](/en/experiments/gspo/run).

## How to design a meaningful comparison

Align the base model, training and evaluation data, training budget, sampling settings and answer-checking rules. Choose the variable to compare, then record accuracy, format compliance, output length, sampling cost and total time. The best checkpoint can differ across metrics.

The repository provides three inspectable training entry points. A fair comparison still requires additional controlled experiments; interpret existing numbers within their own settings.
