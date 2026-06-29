import { useEffect, useState } from 'react'
import { getAnalytics } from '../api'

// Shows analytics for the selected short code. Re-fetches whenever
// the selected shortCode changes.
export default function Analytics({ shortCode }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!shortCode) {
      setData(null)
      return
    }
    setError('')
    getAnalytics(shortCode)
      .then(setData)
      .catch((e) => {
        setError(e.message)
        setData(null)
      })
  }, [shortCode])

  if (!shortCode) {
    return (
      <section className="card">
        <h2>Analytics</h2>
        <p>Click a link's “Analytics” button to see its stats.</p>
      </section>
    )
  }

  return (
    <section className="card">
      <h2>Analytics — {shortCode}</h2>
      {error && <div className="error">{error}</div>}
      {data && (
        <>
          <div className="stats">
            <div className="stat">
              <span className="num">{data.total_clicks}</span>
              <span>Total clicks</span>
            </div>
            <div className="stat">
              <span className="num">{data.clicks_today}</span>
              <span>Today</span>
            </div>
          </div>

          <h3>Top referrers</h3>
          {data.top_referrers.length === 0 ? (
            <p>No clicks yet.</p>
          ) : (
            <ul>
              {data.top_referrers.map((r, i) => (
                <li key={i}>
                  {r.referrer || '(direct / none)'} — <strong>{r.count}</strong>
                </li>
              ))}
            </ul>
          )}

          <h3>Clicks by date (last 7 days)</h3>
          {data.clicks_by_date.length === 0 ? (
            <p>No clicks yet.</p>
          ) : (
            <ul>
              {data.clicks_by_date.map((d, i) => (
                <li key={i}>
                  {d.date} — <strong>{d.count}</strong>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </section>
  )
}
