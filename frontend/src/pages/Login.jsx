import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const navigate  = useNavigate()

  const [form,    setForm]    = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState('')
  const [showPwd, setShowPwd] = useState(false)

  const handleChange = e => setForm(f => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async e => {
    e.preventDefault()
    if (!form.email || !form.password) { setError('Ingresa tu correo y contraseña.'); return }
    setLoading(true); setError('')
    try {
      await login(form.email, form.password)
      navigate('/')
    } catch (err) {
      const msg = err.response?.data?.error || err.response?.data?.message
        || 'Credenciales incorrectas. Verifica e intenta de nuevo.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      {/* Background orbs */}
      <div className="login-bg-orb login-bg-orb-1" />
      <div className="login-bg-orb login-bg-orb-2" />
      <div className="login-bg-orb login-bg-orb-3" />

      <div className="login-card slide-up">
        {/* Logo */}
        <div className="login-logo">
          <div className="login-logo-icon">🌿</div>
        </div>

        {/* Title */}
        <div className="login-title">
          <h1>Finca POS</h1>
          <p>Sistema de Punto de Venta</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Correo electrónico</label>
            <input
              type="email"
              name="email"
              className={`form-input ${error ? 'error' : ''}`}
              placeholder="admin@finca.com"
              value={form.email}
              onChange={handleChange}
              autoComplete="email"
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label">Contraseña</label>
            <div className="input-wrapper">
              <input
                type={showPwd ? 'text' : 'password'}
                name="password"
                className={`form-input ${error ? 'error' : ''}`}
                placeholder="••••••••"
                value={form.password}
                onChange={handleChange}
                autoComplete="current-password"
              />
              <button
                type="button"
                className="input-action"
                onClick={() => setShowPwd(v => !v)}
                tabIndex={-1}
              >
                {showPwd ? '🙈' : '👁'}
              </button>
            </div>
          </div>

          {error && (
            <div style={{
              background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
              borderRadius: 'var(--r)', padding: '10px 14px', marginBottom: '16px',
              fontSize: '0.82rem', color: 'var(--red)', display: 'flex', gap: '8px', alignItems: 'center'
            }}>
              ⚠️ {error}
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary login-btn"
            disabled={loading}
          >
            {loading ? <><span className="spinner" style={{width:16,height:16}} /> Iniciando sesión…</> : '→ Ingresar al Sistema'}
          </button>
        </form>

        <div className="login-footer">
          Proyecto Finca &amp; Hotel · v1.0.0 &nbsp;·&nbsp; © 2026
        </div>
      </div>
    </div>
  )
}
