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

export async function getJournalEntry(date) {
  const { data } = await api.get(`/api/journal/detail/${encodeURIComponent(date)}`)
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

export async function updateJournalExhibition(date, exhibition) {
  const { data } = await api.patch(`/api/journal/${encodeURIComponent(date)}/exhibition`, { exhibition })
  return data
}

export async function updateJournalSketch(date, sketchData) {
  const { data } = await api.patch(`/api/journal/${encodeURIComponent(date)}/sketch`, sketchData)
  return data
}

// ── exhibitions ────────────────────────────────────────────────────────────

export async function getExhibitions() {
  const { data } = await api.get('/api/exhibitions')
  return data
}

// ── daily artwork (AIC) — 브라우저에서 직접 호출 (CORS 허용) ───────────────

const _AIC_QUESTIONS = [
  "이 작품에서 가장 먼저 눈길이 가는 부분은 어디인가요?",
  "이 색감이 지금 내 기분과 어떻게 맞닿아 있나요?",
  "이 장면 속에 내가 있다면 어떤 감정을 느낄 것 같나요?",
  "작가는 무엇을 말하고 싶었을까요?",
  "이 작품이 떠올리게 하는 기억이나 장소가 있나요?",
  "빛과 그림자가 어디에서 시작되고 어디에서 끝나나요?",
  "이 작품을 한 단어로 표현한다면 무엇인가요?",
  "그림 속 인물 혹은 사물이 지금 어떤 소리를 내고 있을까요?",
  "오늘 하루와 이 작품 사이에 어떤 닮은 점이 있나요?",
  "만약 이 그림 속으로 들어갈 수 있다면, 어디에 서 있을 건가요?",
  "작가가 이 순간을 포착하기 위해 무엇을 내려놓았을까요?",
  "이 그림 앞에서 얼마나 오래 머물 수 있을 것 같나요?",
  "작품의 어느 부분이 가장 조용하게 느껴지나요?",
  "이 작품이 걸린 공간은 어떤 분위기일까요?",
  "그림 속 시간은 몇 시쯤일 것 같나요?",
  "이 작품을 보며 어떤 계절이 떠오르나요?",
  "구도에서 어떤 균형 또는 불균형이 느껴지나요?",
  "이 색 중 지금의 내 감정과 가장 가까운 색은 무엇인가요?",
  "이 장면이 끝나면 무슨 일이 일어날 것 같나요?",
  "작품이 나에게 조용히 건네는 말이 있다면 무엇일까요?",
  "붓터치 혹은 선 하나하나에서 어떤 감각이 느껴지나요?",
  "이 작품을 떠올릴 때 들릴 것 같은 음악이 있나요?",
  "작가는 이 작품을 그리면서 무엇을 느꼈을까요?",
  "지금 이 그림을 선물받는다면 어디에 걸고 싶나요?",
  "이 작품이 내 삶의 어떤 순간과 겹쳐 보이나요?",
  "가장 따뜻한 부분과 가장 차가운 부분은 어디인가요?",
  "이 그림을 처음 본 사람은 어떤 반응을 보였을까요?",
  "화면에서 눈에 보이지 않는 것은 무엇일까요?",
  "이 작품은 나에게 무엇을 허락해주는 것 같나요?",
  "오늘 하루를 이 그림의 제목으로 붙인다면?",
]

async function _fetchAICPainting(esFrom, questionIdx) {
  const attempts = [esFrom, (esFrom + 150) % 1780, (esFrom + 400) % 1780, Math.floor(Math.random() * 1780)]

  for (const offset of attempts) {
    try {
      const query = {
        query: { bool: { must: [
          { term: { is_public_domain: true } },
          { exists: { field: 'image_id' } },
          { term: { artwork_type_id: 1 } },
        ] } },
        from: offset,
        size: 20,
      }

      const url = `https://api.artic.edu/api/v1/artworks/search` +
        `?params=${encodeURIComponent(JSON.stringify(query))}` +
        `&fields=id,title,artist_display,date_display,medium_display,image_id,description`

      const res = await fetch(url, { headers: { 'AIC-User-Agent': 'inner-gallery (sakim9018@gmail.com)' } })
      if (!res.ok) continue

      const payload = await res.json()
      const artwork = (payload.data || []).find(a => a.image_id)
      if (!artwork) continue

      const iiifBase = payload.config?.iiif_url || 'https://www.artic.edu/iiif/2'
      const imgId = artwork.image_id

      return {
        fallback:      false,
        id:            artwork.id,
        title:         artwork.title || '',
        artist:        artwork.artist_display || '',
        date:          artwork.date_display || '',
        medium:        artwork.medium_display || '',
        description:   artwork.description || '',
        image_url:     `${iiifBase}/${imgId}/full/843,/0/default.jpg`,
        thumbnail_url: `${iiifBase}/${imgId}/full/400,/0/default.jpg`,
        artic_url:     `https://www.artic.edu/artworks/${artwork.id}`,
        question:      _AIC_QUESTIONS[questionIdx % _AIC_QUESTIONS.length],
      }
    } catch {}
  }

  throw new Error('Failed to fetch artwork')
}

export async function getDailyArtworkAIC() {
  const now = new Date()
  const todayStr = `${now.getFullYear()}-${now.getMonth()+1}-${now.getDate()}`
  
  const savedDate = localStorage.getItem('dailyArtworkDate')
  if (savedDate === todayStr) {
    const savedFrom = parseInt(localStorage.getItem('dailyArtworkFrom') || '0', 10)
    const savedQ = parseInt(localStorage.getItem('dailyArtworkQIdx') || '0', 10)
    return _fetchAICPainting(savedFrom, savedQ)
  }

  const ordinal = now.getFullYear() * 10000 + (now.getMonth() + 1) * 100 + now.getDate()
  const esFrom = ordinal % 1780
  
  localStorage.setItem('dailyArtworkDate', todayStr)
  localStorage.setItem('dailyArtworkFrom', esFrom.toString())
  localStorage.setItem('dailyArtworkQIdx', ordinal.toString())
  
  return _fetchAICPainting(esFrom, ordinal)
}

export async function getRandomArtworkAIC() {
  const esFrom = Math.floor(Math.random() * 1780)
  const qIdx   = Math.floor(Math.random() * _AIC_QUESTIONS.length)
  
  const now = new Date()
  const todayStr = `${now.getFullYear()}-${now.getMonth()+1}-${now.getDate()}`
  
  localStorage.setItem('dailyArtworkDate', todayStr)
  localStorage.setItem('dailyArtworkFrom', esFrom.toString())
  localStorage.setItem('dailyArtworkQIdx', qIdx.toString())
  
  return _fetchAICPainting(esFrom, qIdx)
}

export async function translateText(text) {
  const { data } = await api.post('/api/translate', { text })
  return data.translated || ''
}

// ── AIC 전시정보 — 브라우저 직접 호출 ─────────────────────────────────────────

function _fmtAICDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d)) return ''
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`
}

export async function getAICExhibitions() {
  // /exhibitions/search 로 status=Confirmed 필터 — 현재 진행 중인 전시만
  const query = { query: { term: { status: 'Confirmed' } }, size: 10 }
  const url = `https://api.artic.edu/api/v1/exhibitions/search` +
    `?params=${encodeURIComponent(JSON.stringify(query))}` +
    `&fields=id,title,image_id,aic_start_at,aic_end_at,gallery_title`

  const res = await fetch(url, {
    headers: { 'AIC-User-Agent': 'inner-gallery (sakim9018@gmail.com)' },
  })
  if (!res.ok) throw new Error('AIC exhibitions error')

  const payload = await res.json()
  const iiifBase = payload.config?.iiif_url || 'https://www.artic.edu/iiif/2'

  return (payload.data || [])
    .filter(ex => ex.title)
    .slice(0, 10)
    .map(ex => ({
      source:    'Art Institute of Chicago',
      title:     ex.title,
      place:     ex.gallery_title || 'Art Institute of Chicago',
      period:    (ex.aic_start_at || ex.aic_end_at)
        ? `${_fmtAICDate(ex.aic_start_at)} ~ ${_fmtAICDate(ex.aic_end_at)}`
        : '',
      fee:       '유료',
      thumbnail: ex.image_id ? `${iiifBase}/${ex.image_id}/full/400,/0/default.jpg` : '',
      url:       `https://www.artic.edu/exhibitions/${ex.id}`,
      author:    '',
    }))
}

export async function getArtistQuote() {
  const { data } = await api.get('/api/artist-quote')
  return data
}

export async function getDemoResult() {
  const { data } = await api.get('/api/demo-result')
  return data
}
