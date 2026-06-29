import { useEffect, useState } from 'react'
import { getLinks } from '../api'
import LinksTable from '../components/LinksTable'

// Page 2: list all links.
export default function MyLinks() {
  const [links, setLinks] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    getLinks().then(setLinks).catch((e) => setError(e.message))
  }, [])

  return (
    <div>
      {error && <div className="error">{error}</div>}
      <LinksTable links={links} />
    </div>
  )
}
