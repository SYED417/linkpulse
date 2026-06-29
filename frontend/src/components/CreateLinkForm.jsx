import { useState } from 'react'
import { createLink } from '../api'

// Form to create a new short link. Calls onCreated() so the parent
// can refresh the table after a successful create.
export default function CreateLinkForm({ user, onCreated }) {
  const [url, setUrl] = useState('')
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState('')

  async function handleSubmit(e) {
    e.preventDefault() // stop the browser from reloading the page
    if (!user) {
      setMsg('No user loaded yet.')
      return
    }
    setBusy(true)
    setMsg('')
    try {
      const link = await createLink(url, user.id)
      setMsg(`Created /${link.short_code}`)
      setUrl('')
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
      <form onSubmit={handleSubmit} className="form-row">
        <input
          type="url"
          placeholder="https://example.com/some/long/url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          required
        />
        <button type="submit" disabled={busy || !user}>
          {busy ? 'Creating…' : 'Shorten'}
        </button>
      </form>
      {msg && <p className="msg">{msg}</p>}
    </section>
  )
}
