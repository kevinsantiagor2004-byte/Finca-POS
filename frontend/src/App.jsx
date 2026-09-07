import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { ToastProvider }         from './context/ToastContext'
import Layout    from './components/layout/Layout'
import Login     from './pages/Login'
import Dashboard from './pages/Dashboard'
import SalesOrders from './pages/SalesOrders'
import Planes    from './pages/Planes'
import Services  from './pages/Services'
import Usuarios  from './pages/Usuarios'

function PrivateRoute({ children, adminOnly = false }) {
  const { user, isAdmin } = useAuth()
  if (!user)            return <Navigate to="/login" replace />
  if (adminOnly && !isAdmin) return <Navigate to="/" replace />
  return <Layout>{children}</Layout>
}

function PublicRoute({ children }) {
  const { user } = useAuth()
  if (user) return <Navigate to="/" replace />
  return children
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
      <Route path="/"         element={<PrivateRoute><Dashboard /></PrivateRoute>} />
      <Route path="/ordenes"  element={<PrivateRoute><SalesOrders /></PrivateRoute>} />
      <Route path="/planes"   element={<PrivateRoute adminOnly><Planes /></PrivateRoute>} />
      <Route path="/servicios"element={<PrivateRoute adminOnly><Services /></PrivateRoute>} />
      <Route path="/usuarios" element={<PrivateRoute adminOnly><Usuarios /></PrivateRoute>} />
      <Route path="*"         element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <AppRoutes />
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
