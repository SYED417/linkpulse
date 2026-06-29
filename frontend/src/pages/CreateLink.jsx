import { useEffect, useState } from 'react'
import { getUsers } from '../api'
import CreateLinkForm from '../components/CreateLinkForm'

// Page 1: create a short link.
export default function CreateLink() {
  const [user, setUser] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getUsers()
      .then((users) => {
        if (users.length > 0) setUser(users[0])
        else setError('No users found. Seed a user in the database first.')
      })
      .catch((e) => setError(e.message))
  }, [])

  return (
    <div>
      {user && (
        <p className="user">
          Signed in as <strong>{user.email}</strong>
        </p>
      )}
      {error && <div className="error">{error}</div>}
      <CreateLinkForm user={user} onCreated={() => {}} />
    </div>
  )
}
