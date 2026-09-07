import { useEffect, useState, useCallback } from 'react'
import { getUsuarios, createUsuario, updateUsuario, deleteUsuario } from '../api/usuarios'
import { useToast } from '../context/ToastContext'
import { useAuth } from '../context/AuthContext'

const ROLES = ['Admin', 'Cajero', 'Mesero']
const ROLE_BADGE = { Admin: 'badge-purple', Cajero: 'badge-blue', Mesero: 'badge-amber' }
const INIT = { nombreCompleto: '', email: '', telefono: '', password: '', rol: 'Mesero', isActive: true }

export default function Usuarios() {
  const { toast } = useToast()
  const { user: me } = useAuth()
  const [users,      setUsers]      = useState([])
  const [loading,    setLoading]    = useState(true)
  const [modal,      setModal]      = useState(null) // 'create' | 'edit'
  const [selected,   setSelected]   = useState(null)
  const [form,       setForm]       = useState(INIT)
  const [submitting, setSubmitting] = useState(false)
  const [showPwd,    setShowPwd]    = useState(false)
  const [showDel,    setShowDel]    = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await getUsuarios(1, 100)
      setUsers(data?.items || [])
    } catch { toast('Error al cargar usuarios', 'error') }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const openCreate = () => { setForm(INIT); setShowPwd(true); setModal('create') }
  const openEdit   = (u) => {
    setSelected(u)
    setForm({ nombreCompleto: u.nombreCompleto, email: u.email, telefono: u.telefono || '', password: '', rol: u.rol, isActive: u.isActive })
    setShowPwd(false)
    setModal('edit')
  }

  const handleSave = async () => {
    if (!form.nombreCompleto || !form.email) { toast('Nombre y correo son requeridos', 'error'); return }
    if (modal === 'create' && !form.password) { toast('La contraseña es requerida', 'error'); return }
    setSubmitting(true)
    try {
      const payload = { ...form }
      if (modal === 'edit' && !payload.password) delete payload.password
      if (modal === 'create') { await createUsuario(payload); toast('Usuario creado ✓', 'success') }
      else { await updateUsuario(selected.id, payload); toast('Usuario actualizado ✓', 'success') }
      setModal(null); load()
    } catch (e) { toast(e.response?.data?.message || 'Error al guardar', 'error') }
    finally { setSubmitting(false) }
  }

  const handleDelete = async (u) => {
    try {
      await deleteUsuario(u.id)
      toast('Usuario eliminado', 'info')
      setShowDel(null); load()
    } catch (e) { toast(e.response?.data?.message || 'No se puede eliminar este usuario', 'error') }
  }

  const initials = (name) => name?.split(' ').slice(0, 2).map(n => n[0]).join('').toUpperCase() || '?'

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h1>Usuarios</h1>
          <p>{users.length} usuarios registrados</p>
        </div>
        <button className="btn btn-primary" onClick={openCreate}>+ Nuevo Usuario</button>
      </div>

      <div className="card">
        <div className="table-wrapper">
          {loading ? (
            <div className="spinner-center"><div className="spinner spinner-lg" /></div>
          ) : users.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">👥</div>
              <h4>Sin usuarios</h4>
              <button className="btn btn-primary btn-sm" onClick={openCreate}>+ Nuevo Usuario</button>
            </div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Usuario</th>
                  <th>Correo</th>
                  <th>Rol</th>
                  <th>Estado</th>
                  <th>Teléfono</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.id}>
                    <td>
                      <div className="flex-gap">
                        <div style={{
                          width: 32, height: 32, borderRadius: '50%', flexShrink: 0,
                          background: 'linear-gradient(135deg, var(--green-dark), var(--cyan))',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: '0.72rem', fontWeight: 700, color: 'white'
                        }}>
                          {initials(u.nombreCompleto)}
                        </div>
                        <div>
                          <div style={{ fontWeight: 600 }}>{u.nombreCompleto}</div>
                          {u.id === me?.userId && <div style={{ fontSize: '0.68rem', color: 'var(--green)' }}>Tú</div>}
                        </div>
                      </div>
                    </td>
                    <td style={{ color: 'var(--text-secondary)' }}>{u.email}</td>
                    <td><span className={`badge ${ROLE_BADGE[u.rol] || 'badge-gray'}`}>{u.rol}</span></td>
                    <td><span className={`badge ${u.isActive ? 'badge-green' : 'badge-red'}`}>{u.isActive ? 'Activo' : 'Inactivo'}</span></td>
                    <td style={{ color: 'var(--text-muted)' }}>{u.telefono || '—'}</td>
                    <td>
                      <div className="flex-gap">
                        <button className="btn btn-ghost btn-sm" onClick={() => openEdit(u)}>✏️ Editar</button>
                        {u.id !== me?.userId && (
                          <button className="btn btn-danger btn-sm btn-icon" onClick={() => setShowDel(u)} title="Eliminar">✕</button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* ═══ MODAL: Create / Edit ══════════════════════════════ */}
      {(modal === 'create' || modal === 'edit') && (
        <div className="modal-backdrop" onClick={e => e.target === e.currentTarget && setModal(null)}>
          <div className="modal slide-up">
            <div className="modal-header">
              <h2>{modal === 'create' ? 'Nuevo Usuario' : 'Editar Usuario'}</h2>
              <button className="btn btn-ghost btn-icon" onClick={() => setModal(null)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="grid-2">
                <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                  <label className="form-label">Nombre Completo <span className="required">*</span></label>
                  <input className="form-input" placeholder="Ej: María González" value={form.nombreCompleto}
                    onChange={e => setForm(f => ({ ...f, nombreCompleto: e.target.value }))} />
                </div>
                <div className="form-group">
                  <label className="form-label">Correo Electrónico <span className="required">*</span></label>
                  <input type="email" className="form-input" placeholder="correo@finca.com"
                    value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} />
                </div>
                <div className="form-group">
                  <label className="form-label">Teléfono</label>
                  <input className="form-input" placeholder="+57 300 000 0000"
                    value={form.telefono} onChange={e => setForm(f => ({ ...f, telefono: e.target.value }))} />
                </div>
                <div className="form-group">
                  <label className="form-label">Rol <span className="required">*</span></label>
                  <select className="form-select" value={form.rol} onChange={e => setForm(f => ({ ...f, rol: e.target.value }))}>
                    {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">
                    {modal === 'create' ? 'Contraseña' : 'Nueva Contraseña'} {modal === 'create' && <span className="required">*</span>}
                  </label>
                  <div className="input-wrapper">
                    <input
                      type={showPwd ? 'text' : 'password'}
                      className="form-input"
                      placeholder={modal === 'edit' ? 'Dejar vacío para no cambiar' : 'Mínimo 8 caracteres'}
                      value={form.password}
                      onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                    />
                    <button type="button" className="input-action" onClick={() => setShowPwd(v => !v)} tabIndex={-1}>
                      {showPwd ? '🙈' : '👁'}
                    </button>
                  </div>
                </div>
              </div>
              {modal === 'edit' && (
                <div className="checkbox-item" onClick={() => setForm(f => ({ ...f, isActive: !f.isActive }))}>
                  <input type="checkbox" readOnly checked={form.isActive} />
                  <div className="checkbox-item-label">
                    <div className="checkbox-item-name">Usuario Activo</div>
                    <div className="checkbox-item-mandatory">Los usuarios inactivos no pueden iniciar sesión</div>
                  </div>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setModal(null)}>Cancelar</button>
              <button className="btn btn-primary" onClick={handleSave} disabled={submitting}>
                {submitting ? <><span className="spinner" style={{ width: 14, height: 14 }} /> Guardando…</> : '✓ Guardar'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ═══ MODAL: Delete Confirm ══════════════════════════════ */}
      {showDel && (
        <div className="modal-backdrop" onClick={e => e.target === e.currentTarget && setShowDel(null)}>
          <div className="modal slide-up">
            <div className="modal-header">
              <h2>Eliminar Usuario</h2>
              <button className="btn btn-ghost btn-icon" onClick={() => setShowDel(null)}>✕</button>
            </div>
            <div className="modal-body">
              <p>¿Eliminar a <strong style={{ color: 'var(--text-primary)' }}>{showDel.nombreCompleto}</strong>?</p>
              <p style={{ marginTop: 8, fontSize: '0.8rem', color: 'var(--red)' }}>⚠️ Esta acción es permanente.</p>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowDel(null)}>Cancelar</button>
              <button className="btn btn-danger" onClick={() => handleDelete(showDel)}>✕ Eliminar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
