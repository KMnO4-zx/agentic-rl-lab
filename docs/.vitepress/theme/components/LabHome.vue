<script setup>
import { withBase } from 'vitepress'
import { repoUrl, chapterLink } from '../../../chapters.mjs'
import { computed } from 'vue'
import { useLocale } from '../composables.js'
import LabIcon from './LabIcon.vue'
import TrainingLoop from './TrainingLoop.vue'
const { t, locale, chapters, groups, path } = useLocale()
const featured = computed(() => ['grpo', 'search-r1', 'spec-o3'].map(id => chapters.value.find(c => c.id === id)))
const labels = computed(() => [t('你的第一个 RL 实验', 'Your first RL experiment'), t('让模型学会使用工具', 'Teach a model to use tools'), t('探索多模态 Agent', 'Explore multimodal agents')])
const icons = ['layers', 'search', 'flask']
</script>

<template>
  <main class="lab-home">
    <section class="lab-hero lab-width">
      <div class="hero-copy">
        <p class="eyebrow"><span class="status-dot" /> AN OPEN RESEARCH NOTEBOOK</p>
        <h1>{{ t('从一篇论文，', 'From a paper, ') }}<br>{{ t('到一次', 'to a real ') }}<span class="hero-emphasis">{{ t('真实的训练', 'training run') }}<span class="hero-period">{{ t('。', '.') }}</span></span></h1>
        <p class="hero-description">{{ t('用 PyTRIO 实践 LLM 与 Agent 强化学习。', 'Hands-on LLM and agent reinforcement learning with PyTRIO. ') }}<br>{{ t('读懂算法，跑通代码，在实验里找到答案。', 'Read the method, run the code, inspect the results.') }}</p>
        <div class="hero-actions">
          <a class="lab-button primary" :href="withBase(path('/guide/quickstart.html'))">{{ t('开始第一个实验', 'Run your first experiment') }} <LabIcon name="arrow" :size="17" /></a>
          <a class="lab-button secondary" :href="withBase(path('/experiments/'))">{{ t('浏览实验手册', 'Browse experiments') }} <LabIcon name="book" :size="17" /></a>
        </div>
        <div class="hero-note"><span>{{ t('开源共学', 'Learn in the open') }}</span><b>·</b><span>{{ t('可运行代码', 'Runnable code') }}</span><b>·</b><span>{{ t('真实实验记录', 'Real experiment notes') }}</span></div>
      </div>
      <TrainingLoop />
    </section>

    <div class="lab-proof lab-width">
      <div class="proof-intro"><span class="small-label">PAPER → CODE → EXPERIMENT</span><p>{{ t('每个方法，都亲手跑一遍。', 'Explore each method through experiments.') }}</p></div>
      <div class="proof-number"><strong>{{ chapters.length.toString().padStart(2, '0') }}</strong><span>{{ t('篇实验笔记', 'experiment notes') }}</span></div>
      <div class="proof-number"><strong>04</strong><span>{{ t('个探索方向', 'research tracks') }}</span></div>
      <div class="proof-tools"><span class="small-label">BUILT WITH</span><div><a href="https://pytrio.com" target="_blank" rel="noreferrer">PyTRIO <span>↗</span></a><i /> <a href="https://swanlab.cn" target="_blank" rel="noreferrer">SwanLab <span>↗</span></a></div></div>
    </div>

    <section class="home-section lab-width">
      <div class="section-top"><div><p class="eyebrow">START EXPLORING</p><h2>{{ t('选一个问题，开始动手。', 'Pick a question. Start experimenting.') }}</h2></div><a class="text-link" :href="withBase(path('/experiments/'))">{{ t('全部', 'All') }} {{ chapters.length }} {{ t('篇实验', 'experiments') }} <LabIcon name="arrow" :size="17" /></a></div>
      <div class="featured-grid">
        <a v-for="(chapter, i) in featured" :key="chapter.id" :href="withBase(chapterLink(chapter, locale))" class="experiment-card" :class="`card-${i}`">
          <div class="card-top"><span class="card-icon"><LabIcon :name="icons[i]" :size="23" /></span><span class="card-number">LAB {{ chapter.number }}</span></div>
          <p class="card-kicker">{{ labels[i] }}</p><h3>{{ chapter.title }}<LabIcon name="diagonal" :size="21" /></h3>
          <p class="card-description">{{ chapter.description }}</p>
          <div class="card-footer"><span v-for="tag in chapter.tags" :key="tag">{{ tag }}</span><span class="read-label">{{ t('阅读实验', 'Read experiment') }} <LabIcon name="arrow" :size="14" /></span></div>
        </a>
      </div>
    </section>

    <section class="home-section tracks-section lab-width">
      <div class="track-intro"><p class="eyebrow">FIND YOUR PATH</p><h2>{{ t('从基础出发，', 'Start with the foundations. ') }}<br>{{ t('走向开放的问题。', 'Follow an open question.') }}</h2><p>{{ t('沿着一条路线读下去，也可以直接进入你正在研究的方向。', 'Follow a learning path, or jump into the problem you are working on.') }}</p><a class="text-link" :href="withBase(path('/guide/learning-path.html'))">{{ t('查看学习路线', 'Find your learning path') }} <LabIcon name="arrow" :size="17" /></a></div>
      <div class="track-list">
        <a v-for="group in groups" :key="group.id" :href="withBase(path(`/experiments/?topic=${group.id}`))" class="track-row"><span class="track-number">{{ group.number }}</span><div><h3>{{ group.label }}</h3><p>{{ chapters.filter(c => c.group === group.id).map(c => c.title).join(' / ') }}</p></div><LabIcon name="arrow" :size="18" /></a>
      </div>
    </section>

    <section class="home-section lab-width">
      <div class="section-top"><div><p class="eyebrow">TRAINING PLATFORMS</p><h2>{{ t('从训练工具，走进实验。', 'From training tools to experiments.') }}</h2></div></div>
      <div class="platform-guides">
        <a class="platform-guide" :href="withBase(path('/guide/pytrio.html'))"><h3>{{ t('PyTRIO 实战教程', 'PyTRIO tutorials') }} <LabIcon name="arrow" :size="18" /></h3><p>{{ t('从安装与 GRPO 开始，找到工具调用、蒸馏和多模态训练的代码入口。', 'Start with setup and GRPO, then explore code for tool use, distillation and multimodal training.') }}</p></a>
        <a class="platform-guide" :href="withBase(path('/guide/tinker-pytrio.html'))"><h3>{{ t('Tinker 与 PyTRIO', 'Tinker and PyTRIO') }} <LabIcon name="arrow" :size="18" /></h3><p>{{ t('对照采样、奖励与策略更新，理解两个训练工作流以及迁移时要检查的细节。', 'Compare sampling, rewards and policy updates, with practical checks for adapting an experiment.') }}</p></a>
      </div>
    </section>

    <section class="lab-invitation lab-width"><div class="invitation-mark"><LabIcon name="code" :size="29" /></div><div><p class="eyebrow">LEARN IN THE OPEN</p><h2>{{ t('实验会有边界，好奇心可以更远。', 'Document the limits. Keep asking questions.') }}</h2><p>{{ t('这里记录实现、结果和没跑通的地方。欢迎带着问题、复现记录和新想法一起加入。', 'Implementations, results and things that did not work. Bring your questions, reproduction notes and ideas.') }}</p></div><a class="lab-button secondary" :href="repoUrl" target="_blank" rel="noreferrer">{{ t('在 GitHub 交流', 'Discuss on GitHub') }} <LabIcon name="diagonal" :size="16" /></a></section>
  </main>
</template>
