import { Link } from 'react-router-dom'
import { SHORT_URL_BASE } from '../api'

// Table of all links. Each short code is a clickable short URL, and the
// "Analytics" button routes to the Analytics page for that code.
export default function LinksTable({ links }) {
  return (
    <section className="card">
      <h2>Your links</h2>
      {links.length === 0 ? (
        <p>No links yet. Create one on the Create page.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Short code</th>
              <th>Original URL</th>
              <th>Active</th>
              <th>Created</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {links.map((link) => (
              <tr key={link.id}>
                <td>
                  <a
                    href={`${SHORT_URL_BASE}/${link.short_code}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {link.short_code}
                  </a>
                </td>
                <td className="url-cell">{link.original_url}</td>
                <td>{link.is_active ? '✓' : '✗'}</td>
                <td>{new Date(link.created_at).toLocaleString()}</td>
                <td>
                  <Link className="btn-link" to={`/analytics/${link.short_code}`}>
                    Analytics
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
