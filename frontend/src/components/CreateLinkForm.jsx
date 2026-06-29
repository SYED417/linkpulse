import { useState } from 'react'
import { createLink, SHORT_URL_BASE } from '../api'

// Form to create a new short link. Calls onCreated() so the parent
// can refresh the table after a successful create.
export default function CreateLinkForm({ user, onCreated }) {
  const [url, setUrl] = useState('')
  const [slug, setSlug] = useState('')
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState('')

  async function handleSubmit(e) {
    e.preventDefault() // stop the browser from reloading the page
    if (!user) {
      setMsg('No user loaded yet.')
      return
    }
    // Normalize: if the user didn't type a scheme, assume https://
    let normalized = url.trim()
    if (!normalized) {
      setMsg('Please enter a URL.')
      return
    }
    if (!/^https?:\/\//i.test(normalized)) {
      normalized = 'https://' + normalized
    }
    setBusy(true)
    setMsg('')
    try {
      const link = await createLink(normalized, user.id, slug)
      const code = link.custom_slug || link.short_code
      setMsg(`Created: ${SHORT_URL_BASE}/${code}`)
      setUrl('')
      setSlug('')
      onCreated()
    } catch (err) {
      setMsg(`Error: ${err.message}`)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="card">
      <h2>Create a short link</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <input
            type="text"
            placeholder="example.com/page  (https:// added automatically)"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
        </div>
        <div className="form-row" style={{ marginTop: '10px' }}>
          <input
            type="text"
            placeholder="custom slug (optional, e.g. my-link)"
            value={slug}
            onChange={(e) => setSlug(e.target.value)}
          />
          <button type="submit" disabled={busy || !user}>
            {busy ? 'Creating…' : 'Shorten'}
          </button>
        </div>
      </form>
      {msg && <p className="msg">{msg}</p>}
    </section>
  )
}
