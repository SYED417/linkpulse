import { NavLink, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Login from './pages/Login'
import Register from './pages/Register'
import CreateLink from './pages/CreateLink'
import MyLinks from './pages/MyLinks'
import Analytics from './pages/Analytics'

function RequireAuth({ children }) {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

export default function App() {
  const { isAuthenticated, logout } = useAuth()

  return (
    <div className="container">
      <header className="app-header">
        <div>
          <h1>LinkPulse</h1>
          <p className="subtitle">URL shortener &amp; analytics</p>
        </div>
        {isAuthenticated && (
          <button className="logout" onClick={logout}>
            Log out
          </button>
        )}
      </header>

      {isAuthenticated && (
        <nav className="nav">
          <NavLink to="/" end>Create</NavLink>
          <NavLink to="/links">My Links</NavLink>
          <NavLink to="/analytics">Analytics</NavLink>
        </nav>
      )}

      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/" element={<RequireAuth><CreateLink /></RequireAuth>} />
        <Route path="/links" element={<RequireAuth><MyLinks /></RequireAuth>} />
        <Route path="/analytics" element={<RequireAuth><Analytics /></RequireAuth>} />
        <Route path="/analytics/:code" element={<RequireAuth><Analytics /></RequireAuth>} />
      </Routes>
    </div>
  )
}
