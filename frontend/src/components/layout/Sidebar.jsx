import { NavLink, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

const NAV = [
  {
    label: 'Principal',
    items: [
      { to: '/',         icon: '⊞', label: 'Dashboard' },
      { to: '/ordenes',  icon: '📋', label: 'Órdenes de Venta' },
    ]
  },
  {
    label: 'Catálogo',
    adminOnly: true,
    items: [
      { to: '/planes',   icon: '🏨', label: 'Planes' },
      { to: '/servicios',icon: '✦',  label: 'Servicios' },
    ]
  },
  {
    label: 'Administración',
    adminOnly: true,
    items: [
      { to: '/usuarios', icon: '👥', label: 'Usuarios' },
    ]
  },
]

export default function Sidebar() {
  const { user, logout, isAdmin } = useAuth()

  const initials = user?.nombreCompleto
    ?.split(' ').slice(0, 2).map(n => n[0]).join('').toUpperCase() || '?'

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">🌿</div>
        <div className="sidebar-logo-text">
          <h3>Finca POS</h3>
          <span>Sistema de Ventas</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {NAV.map(section => {
          if (section.adminOnly && !isAdmin) return null
          return (
            <div key={section.label}>
              <div className="sidebar-section-label">{section.label}</div>
              {section.items.map(item => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                >
                  <span className="nav-icon">{item.icon}</span>
                  {item.label}
                </NavLink>
              ))}
            </div>
          )
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-user">
          <div className="sidebar-avatar">{initials}</div>
          <div className="sidebar-user-info">
            <div className="sidebar-user-name">{user?.nombreCompleto || user?.email}</div>
            <div className="sidebar-user-role">{user?.rol}</div>
          </div>
        </div>
        <button className="btn-logout" onClick={logout}>
          ↩ Cerrar Sesión
        </button>
      </div>
    </aside>
  )
}
