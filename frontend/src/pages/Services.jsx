import { useEffect, useState, useCallback } from 'react'
import { getServices, createService, updateService, deleteService } from '../api/services'
import { useToast } from '../context/ToastContext'

const fmt = (n) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(n || 0)
const INIT = { nombre: '', descripcion: '', categoria: '', precioAdicional: '', isActive: true }
const CATS = ['Alojamiento', 'Alimentos y Bebidas', 'Spa y Bienestar', 'Transporte', 'Actividades', 'Otros']

export default function Services() {
  const { toast } = useToast()
  const [services, setServices]  = useState([])
  const [loading,  setLoading]   = useState(true)
  const [catFilter,setCatFilter] = useState('')
  const [modal,    setModal]     = useState(null) // 'create' | 'edit'
  const [selected, setSelected]  = useState(null)
  const [form,     setForm]      = useState(INIT)
  const [submitting, setSubmitting] = useState(false)
  const [showDel, setShowDel]    = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await getServices(1, 100, catFilter)
      setServices(data?.items || [])
    } catch { toast('Error al cargar servicios', 'error') }
    finally { setLoading(false) }
  }, [catFilter])

  useEffect(() => { load() }, [load])

  const openCreate = () => { setForm(INIT); setModal('create') }
  const openEdit   = (s) => { setSelected(s); setForm({ nombre: s.nombre, descripcion: s.descripcion || '', categoria: s.categoria || '', precioAdicional: s.precioAdicional, isActive: s.isActive }); setModal('edit') }

  const handleSave = async () => {
    if (!form.nombre || !form.precioAdicional) { toast('Nombre y precio son requeridos', 'error'); return }
    setSubmitting(true)
    try {
      const payload = { ...form, precioAdicional: parseFloat(form.precioAdicional) }
      if (modal === 'create') { await createService(payload); toast('Servicio creado ✓', 'success') }
      else { await updateService(selected.id, payload); toast('Servicio actualizado ✓', 'success') }
      setModal(null); load()
    } catch (e) { toast(e.response?.data?.message || 'Error al guardar', 'error') }
    finally { setSubmitting(false) }
  }

  const handleDelete = async (s) => {
    try {
      await deleteService(s.id)
      toast('Servicio eliminado', 'info')
      setShowDel(null); load()
    } catch (e) { toast(e.response?.data?.message || 'No se puede eliminar este servicio', 'error') }
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h1>Servicios</h1>
          <p>{services.length} servicios registrados</p>
        </div>
        <button className="btn btn-primary" onClick={openCreate}>+ Nuevo Servicio</button>
      </div>

      <div className="filter-bar">
        <select className="form-select" value={catFilter} onChange={e => setCatFilter(e.target.value)}>
          <option value="">Todas las categorías</option>
          {CATS.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        {catFilter && <button className="btn btn-ghost btn-sm" onClick={() => setCatFilter('')}>✕ Limpiar</button>}
      </div>

      <div className="card">
        <div className="table-wrapper">
          {loading ? (
            <div className="spinner-center"><div className="spinner spinner-lg" /></div>
          ) : services.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">✦</div>
              <h4>Sin servicios</h4>
              <p>Crea servicios adicionales para asignar a tus planes.</p>
              <button className="btn btn-primary btn-sm" onClick={openCreate}>+ Nuevo Servicio</button>
            </div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Categoría</th>
                  <th>Precio Adicional</th>
                  <th>Estado</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {services.map(s => (
                  <tr key={s.id}>
                    <td>
                      <div style={{ fontWeight: 600 }}>{s.nombre}</div>
                      {s.descripcion && <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2 }}>{s.descripcion}</div>}
                    </td>
                    <td>
                      {s.categoria
                        ? <span className="badge badge-gray">{s.categoria}</span>
                        : <span style={{ color: 'var(--text-muted)' }}>—</span>
                      }
                    </td>
                    <td><span style={{ color: 'var(--green)', fontWeight: 700 }} className="font-mono">{fmt(s.precioAdicional)}</span></td>
                    <td><span className={`badge ${s.isActive ? 'badge-green' : 'badge-gray'}`}>{s.isActive ? 'Activo' : 'Inactivo'}</span></td>
                    <td>
                      <div className="flex-gap">
                        <button className="btn btn-ghost btn-sm" onClick={() => openEdit(s)}>✏️ Editar</button>
                        <button className="btn btn-danger btn-sm btn-icon" onClick={() => setShowDel(s)} title="Eliminar">✕</button>
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
              <h2>{modal === 'create' ? 'Nuevo Servicio' : 'Editar Servicio'}</h2>
              <button className="btn btn-ghost btn-icon" onClick={() => setModal(null)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">Nombre <span className="required">*</span></label>
                <input className="form-input" placeholder="Ej: Masaje Relajante" value={form.nombre}
                  onChange={e => setForm(f => ({ ...f, nombre: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="form-label">Categoría</label>
                <select className="form-select" value={form.categoria}
                  onChange={e => setForm(f => ({ ...f, categoria: e.target.value }))}>
                  <option value="">Sin categoría</option>
                  {CATS.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Precio Adicional (COP) <span className="required">*</span></label>
                <input type="number" className="form-input" placeholder="0" min="0"
                  value={form.precioAdicional} onChange={e => setForm(f => ({ ...f, precioAdicional: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="form-label">Descripción</label>
                <textarea className="form-textarea" rows={3} placeholder="Descripción del servicio..."
                  value={form.descripcion} onChange={e => setForm(f => ({ ...f, descripcion: e.target.value }))} />
              </div>
              {modal === 'edit' && (
                <div className="checkbox-item" onClick={() => setForm(f => ({ ...f, isActive: !f.isActive }))}>
                  <input type="checkbox" readOnly checked={form.isActive} />
                  <div className="checkbox-item-label">
                    <div className="checkbox-item-name">Servicio Activo</div>
                    <div className="checkbox-item-mandatory">Los servicios inactivos no aparecen en nuevas órdenes</div>
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
              <h2>Eliminar Servicio</h2>
              <button className="btn btn-ghost btn-icon" onClick={() => setShowDel(null)}>✕</button>
            </div>
            <div className="modal-body">
              <p>¿Eliminar <strong style={{ color: 'var(--text-primary)' }}>{showDel.nombre}</strong>?</p>
              <p style={{ marginTop: 8, fontSize: '0.8rem', color: 'var(--amber)' }}>⚠️ No se puede eliminar si está asignado a un plan activo.</p>
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
