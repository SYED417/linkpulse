import { SHORT_URL_BASE } from '../api'

// Table of all links. Each row's short code is a clickable short URL,
// and an "Analytics" button selects that link for the analytics section.
export default function LinksTable({ links, selectedCode, onSelect }) {
  return (
    <section className="card">
      <h2>Your links</h2>
      {links.length === 0 ? (
        <p>No links yet. Create one above.</p>
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
              <tr
                key={link.id}
                className={link.short_code === selectedCode ? 'selected' : ''}
              >
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
                  <button onClick={() => onSelect(link.short_code)}>
                    Analytics
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
