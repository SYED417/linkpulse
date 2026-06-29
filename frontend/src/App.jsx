import { useEffect, useState } from 'react'
import { getUsers, getLinks } from './api'
import CreateLinkForm from './components/CreateLinkForm'
import LinksTable from './components/LinksTable'
import Analytics from './components/Analytics'

export default function App() {
  const [user, setUser] = useState(null)
  const [links, setLinks] = useState([])
  const [selectedCode, setSelectedCode] = useState(null)
  const [error, setError] = useState('')

  // Reload the links list from the backend.
  async function refreshLinks() {
    try {
      setLinks(await getLinks())
    } catch (e) {
      setError(e.message)
    }
  }

  // On first render: load the current user and the links.
  useEffect(() => {
    getUsers()
      .then((users) => {
        if (users.length > 0) setUser(users[0])
        else setError('No users found. Seed a user in the database first.')
      })
      .catch((e) => setError(e.message))
    refreshLinks()
  }, [])

  return (
    <div className="container">
      <header>
        <h1>LinkPulse</h1>
        <p className="subtitle">URL shortener &amp; analytics</p>
        {user && (
          <p className="user">
            Signed in as <strong>{user.email}</strong>
          </p>
        )}
      </header>

      {error && <div className="error">{error}</div>}

      <CreateLinkForm user={user} onCreated={refreshLinks} />

      <LinksTable
        links={links}
        selectedCode={selectedCode}
        onSelect={setSelectedCode}
      />

      <Analytics shortCode={selectedCode} />
    </div>
  )
}
