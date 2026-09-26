import { openSync, readSync, closeSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
const sizes = new Map()
export function imageSize(src) {
  if (!src?.startsWith('/media/') || !src.toLowerCase().endsWith('.png')) return null
  if (sizes.has(src)) return sizes.get(src)
  const file = fileURLToPath(new URL('../content/public' + decodeURIComponent(src), import.meta.url))
  const fd = openSync(file, 'r')
  const header = Buffer.alloc(24)
  try { readSync(fd, header, 0, 24, 0) } finally { closeSync(fd) }
  const size = header.subarray(1, 4).toString() === 'PNG' ? { width: header.readUInt32BE(16), height: header.readUInt32BE(20) } : null
  sizes.set(src, size)
  return size
}
export function imageHints(html) {
  return html.replace(/<img\b[^>]*>/gi, tag => {
    const src = tag.match(/\bsrc=["']([^"']+)["']/)?.[1]
    const size = imageSize(src)
    let extra = ''
    if (!/\bloading=/.test(tag)) extra += ' loading="lazy"'
    if (!/\bdecoding=/.test(tag)) extra += ' decoding="async"'
    if (size && !/\b(?:width|height)=/.test(tag)) extra += ` width="${size.width}" height="${size.height}"`
    return tag.replace(/\s*\/?>$/, extra + '>')
  })
}
