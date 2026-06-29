// API calls are RELATIVE so they hit the same CloudFront domain, which
// forwards /api/* to the ALB over HTTPS (no mixed-content, no CORS).
const BASE_URL = ''
// Short links are served directly by the ALB (HTTP). Opening them is a
// top-level navigation, which browsers allow from an HTTPS page.
export const SHORT_URL_BASE = 'http://linkpulse-alb-1966342716.us-east-1.elb.amazonaws.com'

// Fetch all users; the app uses the first one as the "current user".
export async function getUsers() {
  const res = await fetch(`${BASE_URL}/api/users`)
  if (!res.ok) throw new Error('Failed to load users')
  return res.json()
}

// Fetch all links for the table.
export async function getLinks() {
  const res = await fetch(`${BASE_URL}/api/links`)
  if (!res.ok) throw new Error('Failed to load links')
  return res.json()
}

// Create a short link. customSlug is optional.
export async function createLink(originalUrl, userId, customSlug) {
  const payload = { original_url: originalUrl, user_id: userId }
  if (customSlug && customSlug.trim()) {
    payload.custom_slug = customSlug.trim()
  }
  const res = await fetch(`${BASE_URL}/api/links`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    const detail = err.detail ? (typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail)) : 'Failed to create link'
    throw new Error(detail)
  }
  return res.json()
}

// Fetch analytics for one short code.
export async function getAnalytics(shortCode) {
  const res = await fetch(`${BASE_URL}/api/analytics/${shortCode}`)
  if (!res.ok) throw new Error('Could not load analytics for ' + shortCode)
  return res.json()
}
