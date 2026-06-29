// API calls are RELATIVE so they hit the same CloudFront domain, which
// forwards /api/* to the ALB over HTTPS (no mixed-content, no CORS).
const BASE_URL = ''
// Short links are served directly by the ALB (HTTP). Opening them is a
// top-level navigation, which browsers allow from an HTTPS page.
export const SHORT_URL_BASE = 'http://linkpulse-alb-1966342716.us-east-1.elb.amazonaws.com'

// ---- JWT token storage ----
const TOKEN_KEY = 'linkpulse_token'
export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}
export function setToken(t) {
  localStorage.setItem(TOKEN_KEY, t)
}
export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}
function authHeaders() {
  const t = getToken()
  return t ? { Authorization: `Bearer ${t}` } : {}
}

// ---- Auth ----
export async function register(email, password) {
  const res = await fetch(`${BASE_URL}/api/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) {
    const e = await res.json().catch(() => ({}))
    throw new Error(typeof e.detail === 'string' ? e.detail : 'Registration failed')
  }
  return res.json()
}

export async function login(email, password) {
  // OAuth2 password flow expects form-encoded username/password.
  const body = new URLSearchParams({ username: email, password })
  const res = await fetch(`${BASE_URL}/api/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  })
  if (!res.ok) throw new Error('Invalid email or password')
  const data = await res.json()
  setToken(data.access_token)
  return data
}

// ---- Links (require auth) ----
export async function getLinks() {
  const res = await fetch(`${BASE_URL}/api/links`, { headers: authHeaders() })
  if (!res.ok) throw new Error('Failed to load links')
  return res.json()
}

export async function createLink(originalUrl, customSlug) {
  const payload = { original_url: originalUrl }
  if (customSlug && customSlug.trim()) payload.custom_slug = customSlug.trim()
  const res = await fetch(`${BASE_URL}/api/links`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const e = await res.json().catch(() => ({}))
    const detail = e.detail
      ? typeof e.detail === 'string'
        ? e.detail
        : JSON.stringify(e.detail)
      : 'Failed to create link'
    throw new Error(detail)
  }
  return res.json()
}

// ---- Analytics (public) ----
export async function getAnalytics(shortCode) {
  const res = await fetch(`${BASE_URL}/api/analytics/${shortCode}`)
  if (!res.ok) throw new Error('Could not load analytics for ' + shortCode)
  return res.json()
}
