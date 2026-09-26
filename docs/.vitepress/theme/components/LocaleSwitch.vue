<script setup>
import { computed } from 'vue'
import { useData, withBase } from 'vitepress'
import { useLocale } from '../composables.js'
import { routePath } from '../../../site.mjs'
const { page } = useData()
const { en } = useLocale()
const target = computed(() => {
  if (page.value.isNotFound || page.value.relativePath === '404.md') return withBase(en.value ? '/' : '/en/')
  return withBase('/' + routePath(en.value ? page.value.relativePath.replace(/^en\//, '') : 'en/' + page.value.relativePath))
})
</script>
<template><a class="locale-switch" :href="target" :lang="en ? 'zh-CN' : 'en'" :aria-label="en ? '阅读简体中文版' : 'Read in English'">{{ en ? '中文' : 'EN' }}</a></template>
