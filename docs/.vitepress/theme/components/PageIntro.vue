<script setup>
import { computed } from 'vue'
import { useData, withBase } from 'vitepress'
import { chapters, chapterLink, repoUrl } from '../../../chapters.mjs'
import LabIcon from './LabIcon.vue'
const { frontmatter } = useData()
const chapter = computed(() => chapters.find(c => c.id === frontmatter.value.chapter))
</script>

<template>
  <header v-if="chapter" class="article-intro">
    <p class="eyebrow">LAB {{ chapter.number }} <span>/</span> {{ frontmatter.group }}</p>
    <h1 id="article-title">{{ chapter.title }}<span>{{ frontmatter.isRun ? '快速启动' : chapter.subtitle }}</span></h1>
    <p class="article-description">{{ chapter.description }}</p>
    <div class="article-meta"><span><LabIcon name="book" :size="15" /> 约 {{ frontmatter.readingTime }} 分钟</span><span v-for="tag in chapter.tags" :key="tag" class="article-tag">{{ tag }}</span></div>
    <div class="article-actions">
      <a v-if="chapter.start && !frontmatter.isRun" :href="withBase(`${chapterLink(chapter)}run.html`)"><LabIcon name="flask" :size="16" /> 快速启动 <span>→</span></a>
      <a v-if="frontmatter.isRun" :href="withBase(chapterLink(chapter))"><LabIcon name="book" :size="16" /> 阅读算法拆解 <span>→</span></a>
      <a :href="`${repoUrl}/tree/main/${chapter.source.slice(0, chapter.source.lastIndexOf('/'))}`" target="_blank" rel="noreferrer"><LabIcon name="code" :size="16" /> 查看代码 <span>↗</span></a>
    </div>
  </header>
</template>
