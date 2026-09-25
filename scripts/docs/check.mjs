import { readdir, readFile, stat } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { load } from 'cheerio'
import { chapters } from '../../docs/chapters.mjs'

const dist = fileURLToPath(new URL('../../docs/.vitepress/dist/', import.meta.url))
const base = '/agentic-rl-lab/'
const errors = new Set()
const documents = new Map()
async function walk(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const full = path.join(directory, entry.name)
    if (entry.isDirectory()) await walk(full)
    else if (entry.name.endsWith('.html')) documents.set(full, load(await readFile(full, 'utf8')))
  }
}
await walk(dist)
const chunks = path.join(dist, 'assets/chunks')
const searchFile = (await readdir(chunks)).find(name => name.startsWith('@localSearchIndexroot.') && name.endsWith('.js'))
if (!searchFile) throw new Error('Missing local search index')
const searchIndex = JSON.parse((await import(pathToFileURL(path.join(chunks, searchFile)).href)).default)
for (const [key, destination] of Object.entries(searchIndex.documentIds)) {
  const url = new URL(destination, 'https://docs.local')
  const file = path.join(dist, decodeURIComponent(url.pathname.slice(base.length)), url.pathname.endsWith('/') ? 'index.html' : '')
  const target = documents.get(file)
  if (!target) errors.add(`Search links to missing page: ${destination}`)
  else if (url.hash && !target('[id]').toArray().some(el => target(el).attr('id') === decodeURIComponent(url.hash.slice(1)))) errors.add(`Search links to missing anchor: ${destination}`)
  if (!searchIndex.storedFields[key]?.title) errors.add(`Search result lacks title: ${destination}`)
}
for (const chapter of chapters) {
  const file = path.join(dist, 'experiments', chapter.id, 'index.html')
  if (!documents.has(file)) errors.add(`Missing chapter: ${chapter.id}`)
  if (chapter.start && !documents.has(path.join(dist, 'experiments', chapter.id, 'run.html'))) errors.add(`Missing quickstart: ${chapter.id}`)
  if (!Object.values(searchIndex.documentIds).includes(`${base}experiments/${chapter.id}/#article-title`)) errors.add(`Chapter title missing from search: ${chapter.id}`)
}
let links = 0
for (const [file, $] of documents) {
  const relative = path.relative(dist, file)
  if (!$('title').text()) errors.add(`${relative}: no title`)
  if (relative !== '404.html' && $('h1').length !== 1) errors.add(`${relative}: expected one h1, got ${$('h1').length}`)
  if ($('mjx-merror, [data-mjx-error]').length) errors.add(`${relative}: invalid math`)
  const current = new URL(base + relative, 'https://docs.local')
  for (const element of $('a[href], img[src], script[src], link[href]').toArray()) {
    const raw = $(element).attr('href') || $(element).attr('src')
    if (!raw || /^(?:https?:|mailto:|tel:|data:|javascript:|\/\/)/i.test(raw)) continue
    const url = new URL(raw, current)
    if (!url.pathname.startsWith(base)) { errors.add(`${relative}: URL escapes Pages base: ${raw}`); continue }
    let target = path.join(dist, decodeURIComponent(url.pathname.slice(base.length)))
    if ((await stat(target).catch(() => null))?.isDirectory()) target = path.join(target, 'index.html')
    if (!await stat(target).catch(() => null)) { errors.add(`${relative}: missing target: ${raw}`); continue }
    if (url.hash && documents.has(target)) {
      const fragment = decodeURIComponent(url.hash.slice(1))
      const targetDocument = documents.get(target)
      if (fragment && !targetDocument('[id]').toArray().some(el => targetDocument(el).attr('id') === fragment)) errors.add(`${relative}: missing anchor: ${raw}`)
    }
    links++
  }
}
if (errors.size) {
  console.error([...errors].join('\n'))
  process.exitCode = 1
} else console.log(`Verified ${documents.size} HTML pages, ${links} internal links/assets and ${searchIndex.documentCount} search sections, including all ${chapters.length} chapters, headings and math.`)
