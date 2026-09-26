import { computed } from 'vue'
import { useData } from 'vitepress'
import { localizedChapters, localizedGroups } from '../../chapters.mjs'
export function useLocale() {
  const { lang } = useData()
  const en = computed(() => lang.value.startsWith('en'))
  const locale = computed(() => en.value ? 'en' : 'zh')
  const chapters = computed(() => localizedChapters(locale.value))
  const groups = computed(() => localizedGroups(locale.value))
  const path = (value) => (en.value ? '/en' : '') + value
  const t = (zh, english) => en.value ? english : zh
  return { en, locale, chapters, groups, path, t }
}
