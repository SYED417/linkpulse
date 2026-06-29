import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getLinks, getAnalytics } from '../api'
import {
  ResponsiveContainer,
  LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip, Legend,
  PieChart, Pie, Cell,
  BarChart, Bar,
} from 'recharts'

const COLORS = ['#2563eb', '#16a34a', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

function DevicePie({ items }) {
  const data = items.map((d) => ({ name: d.device_type || 'unknown', value: d.count }))
  if (!data.length) return <p>No clicks yet.</p>
  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="name" outerRadius={80} label>
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  )
}

function CountryBar({ items }) {
  const data = items.map((d) => ({ name: d.country || 'unknown', value: d.count }))
  if (!data.length) return <p>No clicks yet.</p>
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis allowDecimals={false} />
        <Tooltip />
        <Bar dataKey="value" fill="#2563eb" />
      </BarChart>
    </ResponsiveContainer>
  )
}

// Page 3: analytics with charts for a selected short code.
export default function Analytics() {
  const { code } = useParams()
  const navigate = useNavigate()
  const [links, setLinks] = useState([])
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getLinks().then(setLinks).catch(() => {})
  }, [])

  useEffect(() => {
    if (!code) {
      setData(null)
      return
    }
    setError('')
    getAnalytics(code)
      .then(setData)
      .catch((e) => {
        setError(e.message)
        setData(null)
      })
  }, [code])

  return (
    <div>
      <section className="card">
        <h2>Analytics</h2>
        <label>
          Select a link:{' '}
          <select
            value={code || ''}
            onChange={(e) =>
              navigate(e.target.value ? `/analytics/${e.target.value}` : '/analytics')
            }
          >
            <option value="">— choose a link —</option>
            {links.map((l) => (
              <option key={l.id} value={l.short_code}>
                {l.short_code} → {l.original_url}
              </option>
            ))}
          </select>
        </label>
      </section>

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

          <section className="card">
            <h3>Clicks over time (last 7 days)</h3>
            {data.clicks_by_date.length === 0 ? (
              <p>No clicks yet.</p>
            ) : (
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={data.clicks_by_date}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Line type="monotone" dataKey="count" stroke="#2563eb" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </section>

          <div className="charts-row">
            <section className="card half">
              <h3>By device</h3>
              <DevicePie items={data.clicks_by_device} />
            </section>
            <section className="card half">
              <h3>By country</h3>
              <CountryBar items={data.clicks_by_country} />
            </section>
          </div>

          <section className="card">
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
          </section>
        </>
      )}
    </div>
  )
}
