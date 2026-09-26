<script setup>
import { computed } from 'vue'
import { useData, withBase } from 'vitepress'
import { chapterLink } from '../../../chapters.mjs'
import { useLocale } from '../composables.js'
const { frontmatter } = useData()
const { t, locale, chapters, path } = useLocale()
const current = computed(() => chapters.value.find(c => c.id === frontmatter.value.chapter))
const related = computed(() => current.value ? chapters.value.filter(c => c.group === current.value.group && c.id !== current.value.id) : [])
</script>
<template>
  <aside v-if="related.length" class="related-reading" :aria-label="t('继续阅读', 'Keep exploring')">
    <h2>{{ t('继续阅读', 'Keep exploring') }}</h2>
    <ul><li v-for="chapter in related" :key="chapter.id"><a :href="withBase(chapterLink(chapter, locale))">{{ chapter.title }} — {{ chapter.subtitle }}</a></li></ul>
    <p><a :href="withBase(path('/guide/learning-path.html'))">{{ t('查看完整学习路线', 'See the complete learning path') }} →</a></p>
    <p><a :href="withBase(path('/guide/pytrio.html'))">{{ t('PyTRIO 实战教程与运行入口', 'PyTRIO tutorials and running instructions') }} →</a></p>
  </aside>
</template>
