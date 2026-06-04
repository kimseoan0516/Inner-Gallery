import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('inner_gallery_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('inner_gallery_token')
      localStorage.removeItem('inner_gallery_user')
      window.dispatchEvent(new Event('auth:expired'))
    }
    return Promise.reject(err)
  }
)

// ── auth ───────────────────────────────────────────────────────────────────

export async function login({ username, password }) {
  const { data } = await api.post('/api/auth/login', { username, password })
  return data
}

export async function register({ username, email, password }) {
  const { data } = await api.post('/api/auth/register', { username, email, password })
  return data
}

export async function getMe() {
  const { data } = await api.get('/api/auth/me')
  return data
}

export async function deleteAccount() {
  const { data } = await api.delete('/api/auth/me')
  return data
}

export async function resetPassword(email, new_password) {
  const { data } = await api.post('/api/auth/reset-password', { email, new_password })
  return data
}

// ── analysis ───────────────────────────────────────────────────────────────

export async function analyzeImage({ file, mode, hintTitle = '', hintArtist = '', userIdentityProvided = false, artworkType = '자동', analysisFocus = '전체', artworkDescription = '' }) {
  const form = new FormData()
  form.append('image',               file)
  form.append('mode',                mode)
  form.append('hint_title',          hintTitle)
  form.append('hint_artist',         hintArtist)
  form.append('user_identity_provided', userIdentityProvided ? 'true' : 'false')
  form.append('artwork_type',        artworkType)
  form.append('analysis_focus',      analysisFocus)
  form.append('artwork_description', artworkDescription)
  const { data } = await api.post('/api/analyze', form)
  return data
}

export async function quickMatch(file) {
  const form = new FormData()
  form.append('image', file)
  const { data } = await api.post('/api/quick-match', form)
  return data
}

export async function quickQuality(file) {
  const form = new FormData()
  form.append('image', file)
  const { data } = await api.post('/api/quick-quality', form)
  return data
}

export async function getDailyArtwork() {
  const { data } = await api.get('/api/daily-artwork')
  return data
}

export async function getArtworkEra({ title, artist, year, identificationStatus, visualContext }) {
  const { data } = await api.post('/api/artwork-era', {
    title,
    artist,
    year,
    identification_status: identificationStatus,
    visual_context:        visualContext,
  })
  return data
}

export async function docentChat({ artwork_info, message }) {
  const { data } = await api.post('/api/docent-chat', { artwork_info, message })
  return data
}

export async function generateEssayText({ title, artist, year, mode = 'healing' }) {
  const { data } = await api.post('/api/essay-text', { title, artist, year, mode })
  return data
}

export async function sketchReflection({ sketchBase64, palette, keywords, guideQ, mode = 'short' }) {
  const { data } = await api.post('/api/sketch-reflection', {
    sketch_image: sketchBase64,
    palette,
    keywords,
    guide_q: guideQ,
    mode,
  })
  return data
}

// ── journal ────────────────────────────────────────────────────────────────

export async function getJournal() {
  const { data } = await api.get('/api/journal')
  return data
}

export async function saveJournal(entry) {
  const { data } = await api.post('/api/journal', entry)
  return data
}

export async function deleteJournal(date) {
  const { data } = await api.delete(`/api/journal/${encodeURIComponent(date)}`)
  return data
}

export async function updateJournalNote(date, note) {
  const { data } = await api.patch(`/api/journal/${encodeURIComponent(date)}/note`, { note })
  return data
}

export async function updateJournalSketch(date, sketchData) {
  const { data } = await api.patch(`/api/journal/${encodeURIComponent(date)}/sketch`, sketchData)
  return data
}
