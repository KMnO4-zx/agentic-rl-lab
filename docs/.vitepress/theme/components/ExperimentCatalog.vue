<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { withBase } from 'vitepress'
import { chapters, groups, chapterLink } from '../../../chapters.mjs'
import LabIcon from './LabIcon.vue'
const selected = ref('all')
const query = ref('')
const filtered = computed(() => chapters.filter(c => (selected.value === 'all' || c.group === selected.value) && `${c.title} ${c.subtitle} ${c.description} ${c.tags.join(' ')}`.toLowerCase().includes(query.value.toLowerCase().trim())))
function readTopic() { const topic = new URLSearchParams(location.search).get('topic'); selected.value = groups.some(g => g.id === topic) ? topic : 'all' }
function selectTopic(id) { selected.value = id; const url = new URL(location.href); id === 'all' ? url.searchParams.delete('topic') : url.searchParams.set('topic', id); history.replaceState(null, '', url) }
onMounted(() => { readTopic(); window.addEventListener('popstate', readTopic) })
onUnmounted(() => window.removeEventListener('popstate', readTopic))
</script>

<template>
  <main class="catalog lab-width">
    <header class="catalog-header"><p class="eyebrow">THE EXPERIMENT HANDBOOK</p><h1>把想法，放进实验里。</h1><p>{{ chapters.length }} 篇算法拆解与实践记录。从一个训练循环，走向会搜索、会行动、会看图的 Agent。</p></header>
    <div class="catalog-controls"><div class="filter-tabs" aria-label="按研究方向筛选"><button v-for="group in [{ id: 'all', label: '全部实验' }, ...groups]" :key="group.id" :aria-pressed="selected === group.id" :class="{ active: selected === group.id }" @click="selectTopic(group.id)">{{ group.label }}</button></div><label class="catalog-search"><LabIcon name="search" :size="17" /><input v-model="query" aria-label="筛选实验" placeholder="搜索算法、任务或关键词…"></label></div>
    <div class="catalog-count" aria-live="polite">{{ filtered.length }} 个实验 <span>每篇包含算法说明与实现边界</span></div>
    <div class="catalog-list">
      <a v-for="chapter in filtered" :key="chapter.id" :href="withBase(chapterLink(chapter))" class="catalog-row"><span class="catalog-number">{{ chapter.number }}</span><div class="catalog-name"><h2>{{ chapter.title }}</h2><p>{{ chapter.subtitle }}</p></div><p class="catalog-description">{{ chapter.description }}</p><span class="catalog-group">{{ groups.find(g => g.id === chapter.group).label }}</span><LabIcon name="diagonal" :size="20" /></a>
      <div v-if="!filtered.length" class="catalog-empty"><LabIcon name="search" :size="30" /><h2>还没有找到这个实验</h2><p>试试 GRPO、搜索、蒸馏，或重置筛选。</p><button class="lab-button secondary" @click="query = ''; selectTopic('all')">查看全部实验</button></div>
    </div>
    <p class="catalog-bottom">第一次来？从 <a :href="withBase('/guide/learning-path.html')">学习路线 →</a> 找到适合自己的起点。</p>
  </main>
</template>
