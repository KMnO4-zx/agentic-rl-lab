<script setup>
import { withBase } from 'vitepress'
import { chapters, groups, repoUrl, chapterLink } from '../../../chapters.mjs'
import LabIcon from './LabIcon.vue'
import TrainingLoop from './TrainingLoop.vue'
const featured = ['grpo', 'search-r1', 'spec-o3'].map(id => chapters.find(c => c.id === id))
const labels = ['你的第一个 RL 实验', '让模型学会使用工具', '探索多模态 Agent']
const icons = ['layers', 'search', 'flask']
</script>

<template>
  <div class="lab-home">
    <section class="lab-hero lab-width">
      <div class="hero-copy">
        <p class="eyebrow"><span class="status-dot" /> AN OPEN RESEARCH NOTEBOOK</p>
        <h1>从一篇论文，<br>到一次<span class="hero-emphasis">真实的训练<span class="hero-period">。</span></span></h1>
        <p class="hero-description">一起拆解 LLM 与 Agent 强化学习。<br>读懂算法，跑通代码，在实验里找到答案。</p>
        <div class="hero-actions">
          <a class="lab-button primary" :href="withBase('/guide/quickstart.html')">开始第一个实验 <LabIcon name="arrow" :size="17" /></a>
          <a class="lab-button secondary" :href="withBase('/experiments/')">浏览实验手册 <LabIcon name="book" :size="17" /></a>
        </div>
        <div class="hero-note"><span>开源共学</span><b>·</b><span>可运行代码</span><b>·</b><span>真实实验记录</span></div>
      </div>
      <TrainingLoop />
    </section>

    <div class="lab-proof lab-width">
      <div class="proof-intro"><span class="small-label">PAPER → CODE → EXPERIMENT</span><p>每个方法，都亲手跑一遍。</p></div>
      <div class="proof-number"><strong>{{ chapters.length.toString().padStart(2, '0') }}</strong><span>篇实验笔记</span></div>
      <div class="proof-number"><strong>04</strong><span>个探索方向</span></div>
      <div class="proof-tools"><span class="small-label">BUILT WITH</span><div><a href="https://pytrio.com" target="_blank" rel="noreferrer">PyTRIO <span>↗</span></a><i /> <a href="https://swanlab.cn" target="_blank" rel="noreferrer">SwanLab <span>↗</span></a></div></div>
    </div>

    <section class="home-section lab-width">
      <div class="section-top"><div><p class="eyebrow">START EXPLORING</p><h2>选一个问题，开始动手。</h2></div><a class="text-link" :href="withBase('/experiments/')">全部 {{ chapters.length }} 篇实验 <LabIcon name="arrow" :size="17" /></a></div>
      <div class="featured-grid">
        <a v-for="(chapter, i) in featured" :key="chapter.id" :href="withBase(chapterLink(chapter))" class="experiment-card" :class="`card-${i}`">
          <div class="card-top"><span class="card-icon"><LabIcon :name="icons[i]" :size="23" /></span><span class="card-number">LAB {{ chapter.number }}</span></div>
          <p class="card-kicker">{{ labels[i] }}</p><h3>{{ chapter.title }}<LabIcon name="diagonal" :size="21" /></h3>
          <p class="card-description">{{ chapter.description }}</p>
          <div class="card-footer"><span v-for="tag in chapter.tags" :key="tag">{{ tag }}</span><span class="read-label">阅读实验 <LabIcon name="arrow" :size="14" /></span></div>
        </a>
      </div>
    </section>

    <section class="home-section tracks-section lab-width">
      <div class="track-intro"><p class="eyebrow">FIND YOUR PATH</p><h2>从基础出发，<br>走向开放的问题。</h2><p>沿着一条路线读下去，也可以直接进入你正在研究的方向。</p><a class="text-link" :href="withBase('/guide/learning-path.html')">查看学习路线 <LabIcon name="arrow" :size="17" /></a></div>
      <div class="track-list">
        <a v-for="group in groups" :key="group.id" :href="withBase(`/experiments/?topic=${group.id}`)" class="track-row"><span class="track-number">{{ group.number }}</span><div><h3>{{ group.label }}</h3><p>{{ chapters.filter(c => c.group === group.id).map(c => c.title).join(' / ') }}</p></div><LabIcon name="arrow" :size="18" /></a>
      </div>
    </section>

    <section class="lab-invitation lab-width"><div class="invitation-mark"><LabIcon name="code" :size="29" /></div><div><p class="eyebrow">LEARN IN THE OPEN</p><h2>实验会有边界，好奇心可以更远。</h2><p>这里记录实现、结果和没跑通的地方。欢迎带着问题、复现记录和新想法一起加入。</p></div><a class="lab-button secondary" :href="repoUrl" target="_blank" rel="noreferrer">在 GitHub 交流 <LabIcon name="diagonal" :size="16" /></a></section>
  </div>
</template>
