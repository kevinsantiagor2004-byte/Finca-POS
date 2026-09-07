import { useEffect, useState, useCallback } from 'react'
import { getPlanes, createPlan, updatePlan, deletePlan, assignService, removeService } from '../api/planes'
import { getServices } from '../api/services'
import { useToast } from '../context/ToastContext'

const fmt = (n) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(n || 0)

const INIT = { nombre: '', descripcion: '', precioBase: '' }

export default function Planes() {
  const { toast }  = useToast()
  const [planes,   setPlanes]   = useState([])
  const [services, setServices] = useState([])
  const [loading,  setLoading]  = useState(true)

  const [modal,       setModal]       = useState(null) // 'create' | 'edit' | 'services'
  const [selected,    setSelected]    = useState(null) // current plan
  const [form,        setForm]        = useState(INIT)
  const [submitting,  setSubmitting]  = useState(false)
  const [saveError,   setSaveError]   = useState('') // error visible inside modal
  const [loadError,   setLoadError]   = useState('') // error al cargar
  const [showDelConf, setShowDelConf] = useState(null)

  // Service assignment
  const [svcModal, setSvcModal] = useState(null) // plan object
  const [svcForm,  setSvcForm]  = useState({ serviceId: '', esObligatorio: false, precioEspecial: '' })

  const load = useCallback(async () => {
    setLoading(true)
    setLoadError('')
    try {
      const [p, s] = await Promise.all([getPlanes(), getServices(1, 100)])
      // Planes devuelve array directo; Services devuelve {items: [...]}
      setPlanes(Array.isArray(p.data) ? p.data : (p.data?.items || []))
      setServices(s.data?.items || [])
    } catch (e) {
      const msg = !e.response
        ? '❌ No se puede conectar con la API. Asegúrate de que el servidor esté corriendo en localhost:5000.'
        : `Error ${e.response.status}: ${e.response.data?.message || 'Error del servidor'}`
      setLoadError(msg)
      toast(msg, 'error')
    }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const openCreate = () => { setForm(INIT); setSaveError(''); setModal('create') }
  const openEdit   = (p)  => { setSelected(p); setForm({ nombre: p.nombre, descripcion: p.descripcion || '', precioBase: p.precioBase }); setSaveError(''); setModal('edit') }

  const handleSave = async () => {
    if (!form.nombre.trim()) { setSaveError('El nombre del plan es requerido.'); return }
    if (form.precioBase === '' || form.precioBase === null) { setSaveError('El precio base es requerido.'); return }
    setSaveError('')
    setSubmitting(true)
    try {
      if (modal === 'create') {
        await createPlan({ ...form, precioBase: parseFloat(form.precioBase) })
        toast('Plan creado exitosamente ✓', 'success')
      } else {
        await updatePlan(selected.id, { ...form, precioBase: parseFloat(form.precioBase) })
        toast('Plan actualizado ✓', 'success')
      }
      setModal(null)
      load()
    } catch (e) {
      const msg = !e.response
        ? 'No se puede conectar con la API. Verifica que el servidor esté corriendo (dotnet run en puerto 5000).'
        : e.response.data?.message || e.response.data?.errors
          ? Object.values(e.response.data.errors || {}).flat().join(' ') || e.response.data?.message
          : `Error ${e.response.status} del servidor. Revisa los logs de la API.`
      setSaveError(msg)
      toast(msg, 'error')
    }
    finally { setSubmitting(false) }
  }

  const handleDelete = async (plan) => {
    try {
      await deletePlan(plan.id)
      toast('Plan eliminado', 'info')
      setShowDelConf(null); load()
    } catch (e) { toast(e.response?.data?.message || 'No se puede eliminar este plan', 'error') }
  }

  const handleAssign = async () => {
    if (!svcForm.serviceId) { toast('Selecciona un servicio', 'error'); return }
    try {
      await assignService(svcModal.id, {
        serviceId: svcForm.serviceId,
        esObligatorio: svcForm.esObligatorio,
        precioEspecial: svcForm.precioEspecial ? parseFloat(svcForm.precioEspecial) : null,
      })
      toast('Servicio asignado ✓', 'success')
      setSvcForm({ serviceId: '', esObligatorio: false, precioEspecial: '' })
      load()
    } catch (e) { toast(e.response?.data?.message || 'Error al asignar', 'error') }
  }

  const handleRemoveSvc = async (planId, svcId) => {
    try {
      await removeService(planId, svcId)
      toast('Servicio removido', 'info'); load()
    } catch (e) { toast(e.response?.data?.message || 'Error al remover', 'error') }
  }

  // Servicios no asignados al plan actual
  const availableServices = (plan) => {
    const assigned = new Set(plan?.servicios?.map(s => s.serviceId) || [])
    return services.filter(s => !assigned.has(s.id) && s.isActive)
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h1>Planes</h1>
          <p>{planes.length} planes disponibles</p>
        </div>
        <button className="btn btn-primary" onClick={openCreate}>+ Nuevo Plan</button>
      </div>

      {/* Banner de error de conexión */}
      {loadError && (
        <div style={{
          background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.35)',
          borderRadius: 'var(--r)', padding: '14px 18px', marginBottom: '20px',
          color: 'var(--red)', fontSize: '0.875rem', display: 'flex', gap: '10px', alignItems: 'flex-start'
        }}>
          <span style={{ fontSize: '1.1rem', flexShrink: 0 }}>⚠️</span>
          <div>
            <strong>Error de conexión con la API</strong><br/>
            {loadError}<br/>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 4, display: 'block' }}>
              Ejecuta: <code style={{ background: 'rgba(0,0,0,0.3)', padding: '1px 6px', borderRadius: 4 }}>dotnet run</code> en la carpeta <code style={{ background: 'rgba(0,0,0,0.3)', padding: '1px 6px', borderRadius: 4 }}>src/ProyectoFinca.API</code>
            </span>
          </div>
          <button onClick={load} className="btn btn-secondary btn-sm" style={{ marginLeft: 'auto', flexShrink: 0 }}>↻ Reintentar</button>
        </div>
      )}

      {loading ? (
        <div className="spinner-center"><div className="spinner spinner-lg" /></div>
      ) : planes.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🏨</div>
          <h4>Sin planes aún</h4>
          <p>Crea tu primer plan de alojamiento o servicio.</p>
          <button className="btn btn-primary btn-sm" onClick={openCreate}>+ Nuevo Plan</button>
        </div>
      ) : (
        <div className="plans-grid">
          {planes.map(plan => (
            <div key={plan.id} className="plan-card">
              <div className="plan-card-header">
                <div>
                  <div className="plan-card-name">{plan.nombre}</div>
                  {plan.descripcion && <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 3 }}>{plan.descripcion}</div>}
                </div>
                <span className={`badge ${plan.isActive ? 'badge-green' : 'badge-gray'}`}>
                  {plan.isActive ? 'Activo' : 'Inactivo'}
                </span>
              </div>

              <div className="plan-card-price">
                {fmt(plan.precioBase)} <span>/ base</span>
              </div>
              {plan.precioMinimo > plan.precioBase && (
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2 }}>
                  Precio mínimo con servicios: {fmt(plan.precioMinimo)}
                </div>
              )}

              {/* Services — DTO fields: nombreServicio, esObligatorio, precioEfectivo, serviceId */}
              <div className="plan-services-list" style={{ marginTop: 12 }}>
                {plan.servicios?.length === 0 && <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Sin servicios asignados</span>}
                {plan.servicios?.map(s => (
                  <div key={s.serviceId} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <span className={`plan-service-chip ${s.esObligatorio ? 'mandatory' : ''}`}>
                      {s.nombreServicio}
                    </span>
                    <button
                      onClick={() => handleRemoveSvc(plan.id, s.serviceId)}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', fontSize: '0.7rem', padding: '0 2px', lineHeight: 1 }}
                      title="Quitar servicio"
                    >✕</button>
                  </div>
                ))}
              </div>

              <div className="plan-card-actions">
                <button className="btn btn-secondary btn-sm" style={{ flex: 1 }} onClick={() => { setSvcModal(plan); setSvcForm({ serviceId: '', esObligatorio: false, precioEspecial: '' }) }}>
                  + Servicio
                </button>
                <button className="btn btn-ghost btn-sm" onClick={() => openEdit(plan)}>✏️ Editar</button>
                <button className="btn btn-danger btn-sm btn-icon" onClick={() => setShowDelConf(plan)} title="Eliminar">✕</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ═══ MODAL: Create / Edit Plan ══════════════════════════ */}
      {(modal === 'create' || modal === 'edit') && (
        <div className="modal-backdrop" onClick={e => e.target === e.currentTarget && setModal(null)}>
          <div className="modal slide-up">
            <div className="modal-header">
              <h2>{modal === 'create' ? 'Nuevo Plan' : 'Editar Plan'}</h2>
              <button className="btn btn-ghost btn-icon" onClick={() => setModal(null)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">Nombre <span className="required">*</span></label>
                <input className="form-input" placeholder="Ej: Plan Eco-Turismo" value={form.nombre}
                  onChange={e => setForm(f => ({ ...f, nombre: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="form-label">Descripción</label>
                <textarea className="form-textarea" rows={3} placeholder="Descripción del plan..."
                  value={form.descripcion} onChange={e => setForm(f => ({ ...f, descripcion: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="form-label">Precio Base (COP) <span className="required">*</span></label>
                <input type="number" className="form-input" placeholder="0" min="0"
                  value={form.precioBase} onChange={e => setForm(f => ({ ...f, precioBase: e.target.value }))} />
              </div>
              {/* Error visible dentro del modal */}
              {saveError && (
                <div style={{
                  background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.35)',
                  borderRadius: 'var(--r)', padding: '12px 14px', marginTop: '8px',
                  color: 'var(--red)', fontSize: '0.82rem', display: 'flex', gap: '8px', alignItems: 'flex-start'
                }}>
                  <span>⚠️</span>
                  <span>{saveError}</span>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setModal(null)}>Cancelar</button>
              <button className="btn btn-primary" onClick={handleSave} disabled={submitting}>
                {submitting ? <><span className="spinner" style={{ width: 14, height: 14 }} /> Guardando…</> : '✓ Guardar Plan'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ═══ MODAL: Assign Service ══════════════════════════════ */}
      {svcModal && (
        <div className="modal-backdrop" onClick={e => e.target === e.currentTarget && setSvcModal(null)}>
          <div className="modal slide-up">
            <div className="modal-header">
              <h2>Asignar Servicio a "{svcModal.nombre}"</h2>
              <button className="btn btn-ghost btn-icon" onClick={() => setSvcModal(null)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">Servicio</label>
                <select className="form-select" value={svcForm.serviceId}
                  onChange={e => setSvcForm(f => ({ ...f, serviceId: e.target.value }))}>
                  <option value="">Selecciona un servicio...</option>
                  {availableServices(svcModal).map(s => (
                    <option key={s.id} value={s.id}>{s.nombre} — {fmt(s.precioAdicional)}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Precio Especial en Plan (opcional)</label>
                <input type="number" className="form-input" placeholder={`Precio estándar del servicio`} min="0"
                  value={svcForm.precioEspecial}
                  onChange={e => setSvcForm(f => ({ ...f, precioEspecial: e.target.value }))} />
                <div className="form-hint">Deja vacío para usar el precio estándar del servicio.</div>
              </div>
              <div className="checkbox-item" style={{ marginTop: 8 }} onClick={() => setSvcForm(f => ({ ...f, esObligatorio: !f.esObligatorio }))}>
                <input type="checkbox" readOnly checked={svcForm.esObligatorio} />
                <div className="checkbox-item-label">
                  <div className="checkbox-item-name">Servicio Obligatorio</div>
                  <div className="checkbox-item-mandatory">Se incluye siempre en el precio del plan</div>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setSvcModal(null)}>Cancelar</button>
              <button className="btn btn-primary" onClick={handleAssign}>✓ Asignar</button>
            </div>
          </div>
        </div>
      )}

      {/* ═══ MODAL: Delete Confirm ══════════════════════════════ */}
      {showDelConf && (
        <div className="modal-backdrop" onClick={e => e.target === e.currentTarget && setShowDelConf(null)}>
          <div className="modal slide-up">
            <div className="modal-header">
              <h2>Eliminar Plan</h2>
              <button className="btn btn-ghost btn-icon" onClick={() => setShowDelConf(null)}>✕</button>
            </div>
            <div className="modal-body">
              <p>¿Eliminar el plan <strong style={{ color: 'var(--text-primary)' }}>{showDelConf.nombre}</strong>?</p>
              <p style={{ marginTop: 8, fontSize: '0.8rem', color: 'var(--amber)' }}>⚠️ No podrás eliminar planes con órdenes activas.</p>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowDelConf(null)}>Cancelar</button>
              <button className="btn btn-danger" onClick={() => handleDelete(showDelConf)}>✕ Eliminar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
