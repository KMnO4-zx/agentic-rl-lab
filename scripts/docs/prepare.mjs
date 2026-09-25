import { readFile, writeFile, mkdir, copyFile, rm, stat } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import MarkdownIt from 'markdown-it'
import { chapters, groups, repoUrl, chapterLink, articleCovers } from '../../docs/chapters.mjs'

const root = fileURLToPath(new URL('../../', import.meta.url))
const content = path.join(root, 'docs/content')
const media = path.join(content, 'public/media')
const parser = new MarkdownIt({ html: true })
const routes = new Map(chapters.flatMap(c => [
  [c.source, chapterLink(c)], ...(c.start ? [[c.start, `${chapterLink(c)}run`]] : []),
]))
routes.set('README.md', '/guide/introduction')
const copied = new Set()

// Only these generated paths are cleaned; handwritten guides and source articles are untouched.
await rm(media, { recursive: true, force: true })
for (const c of chapters) await rm(path.join(content, 'experiments', c.id), { recursive: true, force: true })

async function resolveUrl(raw, source, image = false) {
  let url = raw.replace(/&amp;/g, '&')
  const githubPrefix = `${repoUrl}/blob/main/`
  if (url.startsWith(githubPrefix)) url = '/' + url.slice(githubPrefix.length)
  if (/^(?:[a-z]+:|\/\/|#)/i.test(url)) return raw
  const hashAt = url.indexOf('#')
  const hash = hashAt < 0 ? '' : url.slice(hashAt)
  const local = decodeURIComponent((hashAt < 0 ? url : url.slice(0, hashAt)).split('?')[0])
  const relative = path.posix.normalize(local.startsWith('/') ? local.slice(1) : path.posix.join(path.posix.dirname(source), local))
  if (relative.startsWith('../')) throw new Error(`Path escapes repository: ${source}: ${raw}`)
  if (routes.has(relative)) return routes.get(relative) + hash
  const absolute = path.join(root, relative)
  const info = await stat(absolute).catch(() => null)
  if (!info) throw new Error(`Missing local target: ${source}: ${raw} -> ${relative}`)
  if (image || /\.(png|jpe?g|gif|svg|webp|avif)$/i.test(relative)) {
    if (!copied.has(relative)) {
      await mkdir(path.dirname(path.join(media, relative)), { recursive: true })
      await copyFile(absolute, path.join(media, relative))
      copied.add(relative)
    }
    return '/media/' + relative.split('/').map(encodeURIComponent).join('/') + hash
  }
  return `${repoUrl}/${info.isDirectory() ? 'tree' : 'blob'}/main/${relative.split('/').map(encodeURIComponent).join('/')}${hash}`
}

async function transform(body, source) {
  // GitHub's fenced math and VitePress's display math express the same equations.
  body = body.replace(/```math\r?\n([\s\S]*?)```/g, (_, equation) => `$$\n${equation.trim()}\n$$`)
  // Badges depend on third-party requests and duplicate the page's source links.
  body = body.replace(/<div\b[^>]*>[\s\S]*?<\/div>/gi, block => /(?:shields\.io|visitor-badge|komarev\.com)/.test(block) ? '' : block)
  const destinations = new Map()
  function visit(tokens) {
    for (const token of tokens) {
      if (token.type === 'image') destinations.set(token.attrGet('src'), true)
      if (token.type === 'link_open') destinations.set(token.attrGet('href'), false)
      if (token.children) visit(token.children)
    }
  }
  visit(parser.parse(body, {}))
  for (const match of body.matchAll(/\b(src|href)=["']([^"']+)["']/g)) destinations.set(match[2], match[1] === 'src')
  for (const [url, isImage] of destinations) {
    const resolved = await resolveUrl(url, source, isImage)
    if (resolved === url) continue
    // markdown-it URL-encodes paths; source files sometimes use literal spaces/Chinese.
    for (const original of new Set([url, decodeURI(url)])) {
      body = body.split(`](${original})`).join(`](${resolved})`)
      body = body.split(`](<${original}>)`).join(`](${resolved})`)
      body = body.split(`src="${original}"`).join(`src="${resolved}"`)
      body = body.split(`href="${original}"`).join(`href="${resolved}"`)
      body = body.split(`src='${original}'`).join(`src='${resolved}'`)
      body = body.split(`href='${original}'`).join(`href='${resolved}'`)
    }
  }
  return body
}

let pages = 0
for (const chapter of chapters) {
  for (const isRun of [false, true]) {
    const source = isRun ? chapter.start : chapter.source
    if (!source) continue
    let body = await readFile(path.join(root, source), 'utf8')
    body = body.replace(/^# .+\r?\n/, '')
    const cover = !isRun && articleCovers[chapter.id]
    if (cover) {
      body = body.replace(/!\[[^\]]*\]\(([^)]+)\)/g, (match, url) => decodeURI(url) === cover ? '' : match)
      body = body.replace(/<div\b[^>]*>\s*<img\b[^>]*>\s*<\/div>/gi, (block) => block.includes(`src="${cover}"`) ? '' : block)
    }
    body = await transform(body, source)
    const frontmatter = {
      title: isRun ? `${chapter.title} · 快速启动` : `${chapter.title} · ${chapter.subtitle}`,
      description: chapter.description,
      chapter: chapter.id,
      source,
      isRun,
      readingTime: Math.max(1, Math.ceil(body.replace(/```[\s\S]*?```/g, '').length / 450)),
      group: groups.find(g => g.id === chapter.group).label,
    }
    const output = path.join(content, 'experiments', chapter.id, isRun ? 'run.md' : 'index.md')
    await mkdir(path.dirname(output), { recursive: true })
    await writeFile(output, `---\n${Object.entries(frontmatter).map(([key, value]) => `${key}: ${JSON.stringify(value)}`).join('\n')}\n---\n\n${body.trim()}\n`)
    pages++
  }
}
console.log(`Prepared ${pages} pages from ${chapters.length} chapters; copied ${copied.size} referenced images. Source articles unchanged.`)
