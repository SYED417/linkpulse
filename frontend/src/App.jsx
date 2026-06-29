import { NavLink, Routes, Route } from 'react-router-dom'
import CreateLink from './pages/CreateLink'
import MyLinks from './pages/MyLinks'
import Analytics from './pages/Analytics'

export default function App() {
  return (
    <div className="container">
      <header>
        <h1>LinkPulse</h1>
        <p className="subtitle">URL shortener &amp; analytics</p>
      </header>

      <nav className="nav">
        <NavLink to="/" end>Create</NavLink>
        <NavLink to="/links">My Links</NavLink>
        <NavLink to="/analytics">Analytics</NavLink>
      </nav>

      <Routes>
        <Route path="/" element={<CreateLink />} />
        <Route path="/links" element={<MyLinks />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/analytics/:code" element={<Analytics />} />
      </Routes>
    </div>
  )
}
