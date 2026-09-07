import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'

const TITLES = {
  '/':          { title: 'Dashboard',         desc: 'Resumen del sistema POS' },
  '/ordenes':   { title: 'Órdenes de Venta',  desc: 'Gestión de órdenes y facturación' },
  '/planes':    { title: 'Planes',             desc: 'Catálogo de planes disponibles' },
  '/servicios': { title: 'Servicios',          desc: 'Servicios adicionales' },
  '/usuarios':  { title: 'Usuarios',           desc: 'Administración de usuarios del sistema' },
}

export default function TopBar() {
  const { pathname } = useLocation()
  const page = TITLES[pathname] || { title: 'POS', desc: '' }
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(t)
  }, [])

  const fmt = time.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  const date = time.toLocaleDateString('es-CO', { weekday: 'long', day: 'numeric', month: 'long' })

  return (
    <header className="topbar">
      <div className="topbar-left">
        <h2>{page.title}</h2>
        <p>{page.desc}</p>
      </div>
      <div className="topbar-right">
        <span className="topbar-time" title={date}>🕐 {fmt}</span>
        <span className="topbar-env-badge">DEV</span>
      </div>
    </header>
  )
}
