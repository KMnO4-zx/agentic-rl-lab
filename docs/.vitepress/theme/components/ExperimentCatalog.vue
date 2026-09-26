<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { withBase } from 'vitepress'
import { chapterLink } from '../../../chapters.mjs'
import LabIcon from './LabIcon.vue'
import { useLocale } from '../composables.js'
const { t, locale, chapters, groups, path } = useLocale()
const selected = ref('all')
const query = ref('')
const filtered = computed(() => chapters.value.filter(c => (selected.value === 'all' || c.group === selected.value) && `${c.title} ${c.subtitle} ${c.description} ${c.tags.join(' ')}`.toLowerCase().includes(query.value.toLowerCase().trim())))
function readTopic() { const topic = new URLSearchParams(location.search).get('topic'); selected.value = groups.value.some(g => g.id === topic) ? topic : 'all' }
function selectTopic(id) { selected.value = id; const url = new URL(location.href); id === 'all' ? url.searchParams.delete('topic') : url.searchParams.set('topic', id); history.replaceState(null, '', url) }
onMounted(() => { readTopic(); window.addEventListener('popstate', readTopic) })
onUnmounted(() => window.removeEventListener('popstate', readTopic))
</script>

<template>
  <main class="catalog lab-width">
    <header class="catalog-header"><p class="eyebrow">THE EXPERIMENT HANDBOOK</p><h1>{{ t('把想法，放进实验里。', 'Put an idea to the test.') }}</h1><p>{{ chapters.length }} {{ t('篇算法拆解与实践记录。从一个训练循环，走向会搜索、会行动、会看图的 Agent。', 'algorithm walkthroughs and experiment notes. From a training loop to agents that search, act and interpret images.') }}</p></header>
    <div class="catalog-controls"><div class="filter-tabs" :aria-label="t('按研究方向筛选', 'Filter by research track')"><button v-for="group in [{ id: 'all', label: t('全部实验', 'All experiments') }, ...groups]" :key="group.id" :aria-pressed="selected === group.id" :class="{ active: selected === group.id }" @click="selectTopic(group.id)">{{ group.label }}</button></div><label class="catalog-search"><LabIcon name="search" :size="17" /><input v-model="query" :aria-label="t('筛选实验', 'Filter experiments')" :placeholder="t('搜索算法、任务或关键词…', 'Search algorithms, tasks or keywords…')"></label></div>
    <div class="catalog-count" aria-live="polite">{{ filtered.length }} {{ t('个实验', 'experiments') }} <span>{{ t('每篇包含算法说明与实现边界', 'Each note explains the method and its implementation limits') }}</span></div>
    <div class="catalog-list">
      <a v-for="chapter in filtered" :key="chapter.id" :href="withBase(chapterLink(chapter, locale))" class="catalog-row"><span class="catalog-number">{{ chapter.number }}</span><div class="catalog-name"><h2>{{ chapter.title }}</h2><p>{{ chapter.subtitle }}</p></div><p class="catalog-description">{{ chapter.description }}</p><span class="catalog-group">{{ groups.find(g => g.id === chapter.group).label }}</span><LabIcon name="diagonal" :size="20" /></a>
      <div v-if="!filtered.length" class="catalog-empty"><LabIcon name="search" :size="30" /><h2>{{ t('还没有找到这个实验', 'No matching experiments') }}</h2><p>{{ t('试试 GRPO、搜索、蒸馏，或重置筛选。', 'Try GRPO, search or distillation, or reset the filters.') }}</p><button class="lab-button secondary" @click="query = ''; selectTopic('all')">{{ t('查看全部实验', 'Show all experiments') }}</button></div>
    </div>
    <p class="catalog-bottom">{{ t('第一次来？从', 'New here? Use the') }} <a :href="withBase(path('/guide/learning-path.html'))">{{ t('学习路线', 'learning path') }} →</a> {{ t('找到适合自己的起点。', 'to find your starting point.') }}</p>
  </main>
</template>
