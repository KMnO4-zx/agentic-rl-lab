import { defineConfig } from 'vitepress'
import { slug } from 'github-slugger'
import { chapters, groups, repoUrl, chapterLink } from '../chapters.mjs'

export default defineConfig({
  title: 'Agentic RL Lab',
  description: '从论文到代码，从训练到评测。用真实实验理解 LLM 与 Agent 强化学习。',
  lang: 'zh-CN',
  base: '/agentic-rl-lab/',
  srcDir: './content',
  cleanUrls: false,
  lastUpdated: false,
  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/agentic-rl-lab/favicon.svg' }],
    ['meta', { name: 'theme-color', content: '#f8f9f5' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:locale', content: 'zh_CN' }],
  ],
  sitemap: { hostname: 'https://kmno4-zx.github.io/agentic-rl-lab/' },
  markdown: {
    math: true,
    image: { lazyLoading: true },
    anchor: { slugify: slug },
    theme: { light: 'github-light', dark: 'github-dark' },
    config(md) {
      // Public-directory assets in raw HTML need the repository base on GitHub Pages.
      const block = md.renderer.rules.html_block!
      const inline = md.renderer.rules.html_inline!
      for (const [type, renderer] of [['html_block', block], ['html_inline', inline]] as const) {
        md.renderer.rules[type] = (tokens, idx, options, env, self) => renderer(tokens, idx, options, env, self)
          .replace(/\bsrc="(\/media\/[^\"]+)"/g, (_, url) => `:src="'${'/agentic-rl-lab' + url}'"`)
      }
    },
  },
  themeConfig: {
    logo: '/favicon.svg',
    siteTitle: 'Agentic RL Lab',
    nav: [
      { text: '首页', link: '/' },
      { text: '实验手册', link: '/experiments/', activeMatch: '/experiments/' },
      { text: '学习路线', link: '/guide/learning-path' },
      { text: '关于这个 Lab', link: '/guide/introduction' },
    ],
    socialLinks: [{ icon: 'github', link: repoUrl, ariaLabel: '查看 GitHub 仓库' }],
    search: {
      provider: 'local',
      options: {
        _render(src, env, md) {
          const html = md.render(src, env)
          if (env.frontmatter?.search === false) return ''
          // Chapter titles are rendered by PageIntro; include them in the search index too.
          return env.frontmatter?.chapter
            ? `<h1 id="article-title">${md.utils.escapeHtml(env.frontmatter.title)}<a href="#article-title" class="header-anchor">#</a></h1><p>${md.utils.escapeHtml(env.frontmatter.description)}</p>${html}`
            : html
        },
        miniSearch: {
          options: {
            tokenize: (text) => Array.from(new Intl.Segmenter('zh', { granularity: 'word' }).segment(text), (part) => part.segment).filter((word) => /[\p{L}\p{N}]/u.test(word)),
          },
        },
        locales: { root: { translations: {
          button: { buttonText: '搜索实验与笔记', buttonAriaLabel: '搜索实验与笔记' },
          modal: {
            displayDetails: '显示详情', resetButtonTitle: '清空搜索', backButtonTitle: '关闭搜索',
            noResultsText: '没有找到相关内容',
            footer: { selectText: '选择', selectKeyAriaLabel: '回车', navigateText: '切换', navigateUpKeyAriaLabel: '向上', navigateDownKeyAriaLabel: '向下', closeText: '关闭', closeKeyAriaLabel: 'Esc' },
          },
        } } },
      },
    },
    sidebar: [
      { text: '从这里开始', items: [
        { text: '关于这个 Lab', link: '/guide/introduction' },
        { text: '学习路线', link: '/guide/learning-path' },
        { text: '环境准备', link: '/guide/quickstart' },
        { text: '全部实验', link: '/experiments/' },
      ] },
      ...groups.map(g => ({
        text: `${g.number} · ${g.label}`, collapsed: false,
        items: chapters.filter(c => c.group === g.id).map(c => ({
          text: `${c.number}  ${c.title}`, link: chapterLink(c),
          ...(c.start ? { collapsed: true, items: [{ text: '快速启动', link: `${chapterLink(c)}run` }] } : {}),
        })),
      })),
    ],
    outline: { label: '本页目录', level: [2, 3] },
    docFooter: { prev: '上一篇', next: '下一篇' },
    darkModeSwitchLabel: '外观',
    lightModeSwitchTitle: '切换至浅色', darkModeSwitchTitle: '切换至深色',
    sidebarMenuLabel: '章节目录', returnToTopLabel: '回到顶部',
    editLink: {
      pattern: ({ frontmatter, relativePath }) => frontmatter.source
        ? `https://github.com/KMnO4-zx/agentic-rl-lab/edit/main/${frontmatter.source}`
        : `https://github.com/KMnO4-zx/agentic-rl-lab/edit/doc/docs/content/${relativePath}`,
      text: '在 GitHub 上编辑此页',
    },
    notFound: { title: '这页笔记还没找到', quote: '换一个入口，继续探索强化学习。', linkLabel: '返回首页', linkText: '返回首页' },
    footer: { message: '开放代码，记录实验，也记录边界。', copyright: 'Agentic RL Lab · Built with curiosity.' },
  },
})
