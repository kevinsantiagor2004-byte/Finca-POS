import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getSalesOrders } from '../api/salesOrders'
import { getPlanes } from '../api/planes'

const STATUS_MAP = {
  Pendiente:  { label: 'Pendiente',   cls: 'badge-amber'  },
  EnProceso:  { label: 'En Proceso',  cls: 'badge-blue'   },
  Completada: { label: 'Completada',  cls: 'badge-purple' },
  Facturada:  { label: 'Facturada',   cls: 'badge-green'  },
  Cancelada:  { label: 'Cancelada',   cls: 'badge-red'    },
}

const fmt = (n) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(n)
const fmtDate = (d) => new Date(d).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })

export default function Dashboard() {
  const { user, isAdmin } = useAuth()
  const navigate           = useNavigate()

  const [orders,  setOrders]  = useState([])
  const [planes,  setPlanes]  = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getSalesOrders({ pageSize: 10 }),
      getPlanes(),
    ]).then(([o, p]) => {
      // salesOrders devuelve {items:[...]}, planes devuelve array directo
      setOrders(o.data?.items || [])
      setPlanes(Array.isArray(p.data) ? p.data : (p.data?.items || []))
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  // ── Stats ──────────────────────────────────────
  const today  = new Date().toDateString()
  const todayOrders = orders.filter(o => new Date(o.fechaCreacion).toDateString() === today)
  const pending     = orders.filter(o => o.estado === 'Pendiente').length
  const inProcess   = orders.filter(o => o.estado === 'EnProceso').length
  const revenue     = todayOrders.reduce((sum, o) => sum + (o.total || 0), 0)

  const greeting = () => {
    const h = new Date().getHours()
    if (h < 12) return 'Buenos días'
    if (h < 18) return 'Buenas tardes'
    return 'Buenas noches'
  }

  const stats = [
    { label: 'Órdenes Hoy',     value: todayOrders.length, icon: '📋', color: 'var(--blue)',   glow: 'var(--blue-glow)',   change: 'Del día actual' },
    { label: 'Ingresos del Día',value: fmt(revenue),        icon: '💰', color: 'var(--green)',  glow: 'var(--green-glow)',  change: 'Órdenes facturadas' },
    { label: 'Pendientes',      value: pending,             icon: '⏳', color: 'var(--amber)',  glow: 'var(--amber-glow)',  change: `${inProcess} en proceso` },
    { label: 'Planes Activos',  value: planes.length,       icon: '🏨', color: 'var(--purple)', glow: 'var(--purple-glow)', change: 'Disponibles para venta' },
  ]

  return (
    <div>
      {/* Greeting */}
      <div className="page-header">
        <div className="page-header-left">
          <h1>{greeting()}, {user?.nombreCompleto?.split(' ')[0] || 'Usuario'} 👋</h1>
          <p>{new Date().toLocaleDateString('es-CO', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}</p>
        </div>
        <button className="btn btn-primary" onClick={() => navigate('/ordenes')}>
          + Nueva Orden
        </button>
      </div>

      {/* Stat Cards */}
      <div className="stats-grid">
        {stats.map(s => (
          <div key={s.label} className="stat-card" style={{ '--card-glow': s.glow }}>
            <div className="stat-icon" style={{ background: `${s.glow}`, color: s.color }}>
              {s.icon}
            </div>
            <div className="stat-card-body">
              <div className="stat-label">{s.label}</div>
              <div className="stat-value font-mono">
                {loading ? <span style={{ animation: 'pulse 1.5s infinite', color: 'var(--text-muted)' }}>—</span> : s.value}
              </div>
              <div className="stat-change neutral">{s.change}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Main grid */}
      <div className="dashboard-grid">
        {/* Recent Orders */}
        <div className="card">
          <div className="card-header">
            <h3>Últimas Órdenes</h3>
            <button className="btn btn-ghost btn-sm" onClick={() => navigate('/ordenes')}>Ver todas →</button>
          </div>
          <div className="table-wrapper">
            {loading ? (
              <div className="spinner-center"><div className="spinner spinner-lg" /></div>
            ) : orders.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">📭</div>
                <h4>Sin órdenes aún</h4>
                <p>Las órdenes creadas aparecerán aquí.</p>
              </div>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Cliente</th>
                    <th>Plan</th>
                    <th>Total</th>
                    <th>Estado</th>
                    <th>Fecha</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.slice(0, 8).map(o => {
                    const st = STATUS_MAP[o.estado] || { label: o.estado, cls: 'badge-gray' }
                    return (
                      <tr key={o.id} style={{ cursor: 'pointer' }} onClick={() => navigate('/ordenes')}>
                        <td><span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>#{o.id?.slice(0,8)}</span></td>
                        <td style={{ fontWeight: 600 }}>{o.clienteNombre || '—'}</td>
                        <td style={{ color: 'var(--text-secondary)' }}>{o.planNombre || '—'}</td>
                        <td style={{ color: 'var(--green)', fontWeight: 700 }} className="font-mono">{fmt(o.total)}</td>
                        <td><span className={`badge ${st.cls}`}>{st.label}</span></td>
                        <td style={{ color: 'var(--text-muted)' }}>{fmtDate(o.fechaCreacion)}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Right panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Quick actions */}
          <div className="card">
            <div className="card-header"><h3>Acciones Rápidas</h3></div>
            <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <button className="btn btn-primary w-full" onClick={() => navigate('/ordenes')}>
                📋 Nueva Orden de Venta
              </button>
              {isAdmin && (
                <>
                  <button className="btn btn-secondary w-full" onClick={() => navigate('/planes')}>
                    🏨 Gestionar Planes
                  </button>
                  <button className="btn btn-secondary w-full" onClick={() => navigate('/usuarios')}>
                    👥 Administrar Usuarios
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Status summary */}
          <div className="card">
            <div className="card-header"><h3>Estado de Órdenes</h3></div>
            <div className="card-body">
              {Object.entries(STATUS_MAP).map(([k, v]) => {
                const count = orders.filter(o => o.estado === k).length
                return (
                  <div key={k} className="flex-between" style={{ marginBottom: '10px' }}>
                    <span className={`badge ${v.cls}`}>{v.label}</span>
                    <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>{count}</span>
                  </div>
                )
              })}
              {loading && <div className="spinner-center" style={{ padding: 20 }}><div className="spinner" /></div>}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
