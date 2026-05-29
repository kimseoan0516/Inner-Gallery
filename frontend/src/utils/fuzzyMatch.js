import { ARTWORK_DB } from '../data/artworks.js'

function norm(s) {
  if (!s) return ''
  return s.toLowerCase().replace(/[\s\-·,.''"'"()\[\]!?]/g, '')
}

function score(query, target) {
  const q = norm(query)
  const t = norm(target)
  if (!q || q.length < 1) return 0
  if (t === q) return 1.0
  if (t.startsWith(q) || q.startsWith(t)) return 0.9
  if (t.includes(q) || q.includes(t)) return 0.8
  // character overlap ratio
  let overlap = 0
  for (const c of q) if (t.includes(c)) overlap++
  const ratio = overlap / Math.max(q.length, t.length)
  return ratio > 0.55 ? ratio * 0.7 : 0
}

function bestScore(query, aliases) {
  if (!query) return 0
  return Math.max(0, ...aliases.map(a => score(query, a)))
}

function titleAliases(a) {
  return [a.title, a.titleKo || '', ...(a.titleAlias || [])]
}

function artistAliases(a) {
  return [a.artist, a.artistKo || '', ...(a.artistAlias || [])]
}

export function searchByTitle(query, maxResults = 10) {
  if (!query || query.length < 2) return []
  return ARTWORK_DB
    .map(a => ({ ...a, _s: bestScore(query, titleAliases(a)) }))
    .filter(a => a._s > 0.25)
    .sort((a, b) => b._s - a._s)
    .slice(0, maxResults)
}

export function searchByArtist(query, maxResults = 10) {
  if (!query || query.length < 2) return []
  const seen = new Set()
  return ARTWORK_DB
    .map(a => ({ ...a, _s: bestScore(query, artistAliases(a)) }))
    .filter(a => a._s > 0.25 && !seen.has(a.artist) && seen.add(a.artist))
    .sort((a, b) => b._s - a._s)
    .slice(0, maxResults)
}

export function findCandidates(titleQuery, artistQuery, maxResults = 3) {
  if (!titleQuery && !artistQuery) return []
  return ARTWORK_DB
    .map(a => {
      const ts = titleQuery  ? bestScore(titleQuery,  titleAliases(a))  : 0
      const as_ = artistQuery ? bestScore(artistQuery, artistAliases(a)) : 0
      const _s = titleQuery && artistQuery ? ts * 0.55 + as_ * 0.45
               : titleQuery ? ts : as_
      return { ...a, _s }
    })
    .filter(a => a._s > 0.35)
    .sort((a, b) => b._s - a._s)
    .slice(0, maxResults)
}

export function isExactMatch(titleQuery, artistQuery, artwork) {
  const tExact = !titleQuery || titleAliases(artwork).some(a => norm(a) === norm(titleQuery))
  const aExact = !artistQuery || artistAliases(artwork).some(a => norm(a) === norm(artistQuery))
  return tExact && aExact
}

export function findBestMatch(titleQuery, artistQuery) {
  const cands = findCandidates(titleQuery, artistQuery, 1)
  if (cands.length === 0) return null
  const best = cands[0]
  if (best._s < 0.55) return null
  return best
}
