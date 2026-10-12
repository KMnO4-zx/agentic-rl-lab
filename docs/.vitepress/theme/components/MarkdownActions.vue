<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useData, withBase } from 'vitepress'
import { useLocale } from '../composables.js'
const { page } = useData()
const { t } = useLocale()
const mdUrl = computed(() => withBase(`/${page.value.relativePath}`))
const absoluteMdUrl = computed(() => (typeof window === 'undefined' ? '' : window.location.origin) + mdUrl.value)
const kimiUrl = computed(() => `https://kimi.com/_prefill_chat?prefill_prompt=${encodeURIComponent(t(`阅读${absoluteMdUrl.value}，我想问你一些问题`, `Read ${absoluteMdUrl.value}, I have some questions`))}`)
const copied = ref(false)
const open = ref(false)
const root = ref(null)
async function copyMarkdown() {
  try {
    const text = await (await fetch(mdUrl.value)).text()
    await navigator.clipboard.writeText(text)
    copied.value = true
    setTimeout(() => (copied.value = false), 1800)
  } catch {}
}
const onOutsideClick = (event) => { if (!root.value?.contains(event.target)) open.value = false }
const onEscape = (event) => { if (event.key === 'Escape') open.value = false }
onMounted(() => { document.addEventListener('click', onOutsideClick); document.addEventListener('keydown', onEscape) })
onBeforeUnmount(() => { document.removeEventListener('click', onOutsideClick); document.removeEventListener('keydown', onEscape) })
</script>

<template>
  <div ref="root" class="md-actions">
    <button type="button" class="md-button" @click="copyMarkdown">
      <svg v-if="!copied" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="13" height="13" x="9" y="9" rx="2" ry="2" /><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" /></svg>
      <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 12 4 4L19 6" /></svg>
      {{ copied ? t('已复制', 'Copied') : t('复制 Markdown', 'Copy Markdown') }}
    </button>
    <div class="md-menu-wrap">
      <button type="button" class="md-button" :aria-expanded="open" @click.stop="open = !open">
        {{ t('打开', 'Open') }}
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" :style="{ transform: open ? 'rotate(180deg)' : 'none' }"><path d="m6 9 6 6 6-6" /></svg>
      </button>
      <div v-if="open" class="md-menu">
        <a :href="mdUrl" target="_blank" rel="noreferrer" @click="open = false"><svg class="md-item-icon" width="14" height="14" viewBox="0 0 1024 1024" fill="none" aria-hidden="true"><path d="M309.376 298.688a32 32 0 0 1 32-32H640a32 32 0 1 1 0 64H341.376a32 32 0 0 1-32-32zM341.376 437.312a32 32 0 0 0 0 64h128a32 32 0 1 0 0-64h-128z" fill="currentColor" /><path d="M546.816 53.312h-37.12c-83.52 0-149.248 0-200.64 6.528-52.608 6.656-94.976 20.608-128.512 52.16-33.856 31.872-49.024 72.512-56.256 122.88-6.912 48.704-6.912 110.976-6.912 189.248v267.392c0 35.2 0 63.168 1.472 85.888 1.536 23.232 4.736 43.2 12.16 62.08a208.32 208.32 0 0 0 125.696 118.592c35.84 12.608 79.36 12.608 149.12 12.608h43.392c109.504-0.128 175.296-1.6 229.632-20.672 94.528-33.152 169.856-103.616 205.568-193.856 11.776-29.632 17.088-61.76 19.712-101.248 2.56-39.04 2.56-87.296 2.56-149.504V393.6c0-63.744 0-114.432-4.736-154.688-4.864-41.536-15.104-75.904-38.4-105.088a208.512 208.512 0 0 0-43.072-40.576c-30.528-21.504-66.176-30.976-109.568-35.456-42.496-4.48-96.064-4.48-164.096-4.48z m38.848 849.92a173.44 173.44 0 0 0 36.544-106.816c0-7.872-0.32-16-0.64-23.552l-0.192-2.88c-0.256-6.72-0.576-12.992-0.704-19.2a130.56 130.56 0 0 1 2.88-35.584 39.104 39.104 0 0 1 27.648-27.648c9.344-2.56 20.992-3.2 35.52-2.88 6.272 0.128 12.608 0.384 19.264 0.704l2.88 0.128c7.552 0.384 15.68 0.704 23.616 0.704 40.704 0 78.208-13.952 107.904-37.44l-0.128 1.92c-2.368 36.352-7.04 61.056-15.36 81.92-28.544 72.064-89.28 129.664-167.232 157.056-20.032 7.04-42.368 11.136-72 13.568z m257.024-392.064V512c0 60.864-49.344 110.208-110.208 110.208-6.272 0-13.056-0.256-20.608-0.64l-2.816-0.128c-6.592-0.256-13.824-0.64-20.992-0.768a192 192 0 0 0-53.376 5.12c-35.584 9.472-63.36 37.248-72.96 72.832a192.064 192.064 0 0 0-5.056 53.44c0.128 7.168 0.512 14.336 0.832 20.992l0.128 2.752c0.32 7.616 0.64 14.336 0.64 20.608 0 60.16-48.128 108.992-107.968 110.208h-37.184c-79.488 0-110.976-0.384-135.168-8.96a144.384 144.384 0 0 1-87.424-81.792c-3.968-10.048-6.464-22.592-7.808-42.688a1389.44 1389.44 0 0 1-1.344-82.752V426.688c0-81.408 0-139.072 6.272-182.784 6.08-42.56 17.472-67.136 36.736-85.248 19.584-18.432 46.528-29.44 92.672-35.328 46.912-5.952 108.608-6.016 194.944-6.016h33.024c70.208 0 120.448 0.064 159.232 4.096 38.272 3.968 61.568 11.584 79.36 24.128 11.392 8 21.44 17.536 29.888 28.16 12.864 16.192 20.736 37.312 24.896 72.64 4.224 36.16 4.288 83.072 4.288 149.312v115.52z" fill="currentColor" /></svg>{{ t('查看 Markdown', 'View as Markdown') }} <span>↗</span></a>
        <a :href="kimiUrl" target="_blank" rel="noreferrer" @click="open = false"><svg class="md-item-icon" width="14" height="14" viewBox="0 0 1075 1024" fill="none" aria-hidden="true"><path d="M1049.6 0m0 186.1632l0 651.6736q0 186.1632-186.1632 186.1632l-651.6736 0q-186.1632 0-186.1632-186.1632l0-651.6736q0-186.1632 186.1632-186.1632l651.6736 0q186.1632 0 186.1632 186.1632Z" fill="#000" /><path d="M605.7984 459.9808c57.1392 1.28 104.1408 52.3264 104.1408 115.1488v232.5504a2.048 2.048 0 0 1-2.048 2.0992h-99.9936a2.048 2.048 0 0 1-2.048-2.048l-1.7408-294.0928c0-1.2288-2.2528-1.4848-2.6112-0.256-13.312 43.9296-52.736 56.32-99.84 56.32H329.984a2.048 2.048 0 0 0-2.048 2.048v235.9296a2.048 2.048 0 0 1-2.0992 2.0992H220.4672a2.048 2.048 0 0 1-2.048-2.048V241.5104a2.048 2.048 0 0 1 2.048-2.048h105.3696a2.048 2.048 0 0 1 2.048 2.048v216.32c0 1.1264 0.9728 2.048 2.0992 2.048h135.2192a2.048 2.048 0 0 0 1.8944-1.2288l96.9216-218.0096a2.048 2.048 0 0 1 1.8944-1.2288h116.7872c1.536 0 2.56 1.5872 1.8944 2.9696l-66.2528 142.2848c-19.7632 36.1984-34.304 61.8496-67.2768 72.8064-1.1776 0.3584-0.9216 2.4576 0.3584 2.4576h54.3744z" fill="#fff" /><path d="M752.9472 227.9936c-11.776 9.8304-19.456 25.9072-19.456 50.176 0 22.784 7.2704 40.448 18.1248 50.9952-5.632 9.3696-11.4176 15.9744-15.7696 19.456-0.7168 0.6144-0.2048 2.2528 0.7168 2.2016l64.512-4.6592c14.336-1.1264 26.624-6.5536 36.9664-15.7696 12.3904-10.496 19.456-28.5696 19.456-52.224 0-24.2688-7.0656-40.3456-19.456-50.176a64.7168 64.7168 0 0 0-43.008-14.7968c-16.384 0-30.3616 4.9664-42.0864 14.7968z" fill="#007AFF" /></svg>{{ t('在 Kimi 中打开', 'Open in Kimi') }} <span>↗</span></a>
      </div>
    </div>
  </div>
</template>
