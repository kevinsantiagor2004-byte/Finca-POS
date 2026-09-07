import { useEffect, useState, useCallback } from 'react'
import { getSalesOrders, createSalesOrder, updateStatus, deleteSalesOrder } from '../api/salesOrders'
import { getPlanes } from '../api/planes'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

const STATUS_MAP = {
  Pendiente:  { label: 'Pendiente',   cls: 'badge-amber',  next: ['EnProceso', 'Cancelada'] },
  EnProceso:  { label: 'En Proceso',  cls: 'badge-blue',   next: ['Completada','Cancelada'] },
  Completada: { label: 'Completada',  cls: 'badge-purple', next: ['Facturada', 'Cancelada'] },
  Facturada:  { label: 'Facturada',   cls: 'badge-green',  next: [] },
  Cancelada:  { label: 'Cancelada',   cls: 'badge-red',    next: [] },
}
const STATUS_LABELS = { EnProceso: 'En Proceso', ...Object.fromEntries(Object.entries(STATUS_MAP).map(([k,v])=>[k,v.label])) }

const fmt = (n) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(n || 0)
const fmtDate = (d) => new Date(d).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })

export default function SalesOrders() {
  const { isAdmin } = useAuth()
  const { toast }   = useToast()

  const [orders,  setOrders]  = useState([])
  const [planes,  setPlanes]  = useState([])
  const [loading, setLoading] = useState(true)
  const [page,    setPage]    = useState(1)
  const [total,   setTotal]   = useState(0)
  const PAGE_SIZE = 12

  // Filters
  const [search,    setSearch]    = useState('')
  const [statusF,   setStatusF]   = useState('')

  // Modals
  const [showCreate,     setShowCreate]     = useState(false)
  const [showStatus,     setShowStatus]     = useState(null)  // order object
  const [showDeleteConf, setShowDeleteConf] = useState(null)  // order object

  // New order form
  const [form, setForm] = useState({
    clienteNombre: '', planId: '', serviciosOpcionalesIds: [], notas: '', descuento: 0
  })
  const [selectedPlan, setSelectedPlan] = useState(null)
  const [submitting,   setSubmitting]   = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await getSalesOrders({
        page, pageSize: PAGE_SIZE,
        ...(search   ? { clienteNombre: search } : {}),
        ...(statusF  ? { estado: statusF }       : {}),
      })
      setOrders(data?.items || [])
      setTotal(data?.totalCount || 0)
    } catch { toast('Error al cargar órdenes', 'error') }
    finally { setLoading(false) }
  }, [page, search, statusF])

  useEffect(() => { load() }, [load])

  useEffect(() => {
    getPlanes().then(({ data }) => setPlanes(Array.isArray(data) ? data : (data?.items || []))).catch(() => {})
  }, [])

  // ── Plan selection logic ───────────────────────────────
  const onPlanChange = (planId) => {
    const plan = planes.find(p => p.id === planId)
    setSelectedPlan(plan || null)
    setForm(f => ({ ...f, planId, serviciosOpcionalesIds: [] }))
  }

  const toggleOptional = (svcId) => {
    setForm(f => ({
      ...f,
      serviciosOpcionalesIds: f.serviciosOpcionalesIds.includes(svcId)
        ? f.serviciosOpcionalesIds.filter(x => x !== svcId)
        : [...f.serviciosOpcionalesIds, svcId]
    }))
  }

  // ── Live price calc ────────────────────────────────────
  const calcPrice = () => {
    if (!selectedPlan) return { subtotal: 0, descuento: 0, impuesto: 0, total: 0 }
    const IVA = 0.13
    let sub = selectedPlan.precioBase || 0

    // mandatory services — use precioEfectivo (backend field)
    selectedPlan.servicios?.filter(s => s.esObligatorio).forEach(s => {
      sub += s.precioEfectivo ?? 0
    })
    // optional selected
    selectedPlan.servicios?.filter(s => !s.esObligatorio && form.serviciosOpcionalesIds.includes(s.serviceId)).forEach(s => {
      sub += s.precioEfectivo ?? 0
    })

    const desc = parseFloat(form.descuento) || 0
    const imp  = (sub - desc) * IVA
    return { subtotal: sub, descuento: desc, impuesto: imp, total: (sub - desc) * (1 + IVA) }
  }

  const price = calcPrice()

  // ── Create order ───────────────────────────────────────
  const handleCreate = async () => {
    if (!form.clienteNombre || !form.planId) { toast('Nombre del cliente y plan son requeridos', 'error'); return }
    setSubmitting(true)
    try {
      await createSalesOrder({ ...form, descuento: parseFloat(form.descuento) || 0 })
      toast('Orden creada exitosamente ✓', 'success')
      setShowCreate(false)
      setForm({ clienteNombre: '', planId: '', serviciosOpcionalesIds: [], notas: '', descuento: 0 })
      setSelectedPlan(null)
      load()
    } catch (e) {
      toast(e.response?.data?.message || 'Error al crear la orden', 'error')
    } finally { setSubmitting(false) }
  }

  // ── Update status ──────────────────────────────────────
  const handleStatusChange = async (order, newStatus) => {
    try {
      await updateStatus(order.id, { nuevoEstado: newStatus, notas: '' })
      toast(`Estado cambiado a ${STATUS_LABELS[newStatus]}`, 'success')
      setShowStatus(null)
      load()
    } catch (e) { toast(e.response?.data?.message || 'Error al cambiar estado', 'error') }
  }

  // ── Delete ─────────────────────────────────────────────
  const handleDelete = async (order) => {
    try {
      await deleteSalesOrder(order.id)
      toast('Orden eliminada', 'info')
      setShowDeleteConf(null)
      load()
    } catch { toast('No se puede eliminar esta orden', 'error') }
  }

  const pages = Math.ceil(total / PAGE_SIZE)

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h1>Órdenes de Venta</h1>
          <p>{total} órdenes en total</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
          + Nueva Orden
        </button>
      </div>

      {/* Filters */}
      <div className="filter-bar">
        <input
          className="form-input"
          placeholder="🔍 Buscar por cliente..."
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(1) }}
        />
        <select className="form-select" value={statusF} onChange={e => { setStatusF(e.target.value); setPage(1) }}>
          <option value="">Todos los estados</option>
          {Object.entries(STATUS_MAP).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
        </select>
        {(search || statusF) && (
          <button className="btn btn-ghost btn-sm" onClick={() => { setSearch(''); setStatusF(''); setPage(1) }}>
            ✕ Limpiar
          </button>
        )}
      </div>

      {/* Table */}
      <div className="card">
        <div className="table-wrapper">
          {loading ? (
            <div className="spinner-center"><div className="spinner spinner-lg" /></div>
          ) : orders.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📭</div>
              <h4>No hay órdenes</h4>
              <p>Crea una nueva orden haciendo clic en "+ Nueva Orden".</p>
              <button className="btn btn-primary btn-sm" onClick={() => setShowCreate(true)}>+ Nueva Orden</button>
            </div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Cliente</th>
                  <th>Plan</th>
                  <th>Total</th>
                  <th>Estado</th>
                  <th>Fecha</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {orders.map(o => {
                  const st = STATUS_MAP[o.estado] || { label: o.estado, cls: 'badge-gray', next: [] }
                  return (
                    <tr key={o.id}>
                      <td><span style={{ fontFamily: 'monospace', fontSize: '0.72rem', color: 'var(--text-muted)' }}>#{o.id?.slice(0,8)}</span></td>
                      <td style={{ fontWeight: 600 }}>{o.clienteNombre}</td>
                      <td style={{ color: 'var(--text-secondary)' }}>{o.planNombre}</td>
                      <td style={{ color: 'var(--green)', fontWeight: 700 }} className="font-mono">{fmt(o.total)}</td>
                      <td><span className={`badge ${st.cls}`}>{st.label}</span></td>
                      <td style={{ color: 'var(--text-muted)' }}>{fmtDate(o.fechaCreacion)}</td>
                      <td>
                        <div className="flex-gap">
                          {st.next.length > 0 && (
                            <button className="btn btn-ghost btn-sm" onClick={() => setShowStatus(o)}>
                              Cambiar Estado
                            </button>
                          )}
                          {isAdmin && o.estado === 'Pendiente' && (
                            <button className="btn btn-danger btn-sm btn-icon" onClick={() => setShowDeleteConf(o)} title="Eliminar">✕</button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination */}
        {pages > 1 && (
          <div className="pagination">
            <span>Mostrando {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, total)} de {total}</span>
            <div className="pagination-btns">
              <button className="page-btn" disabled={page === 1} onClick={() => setPage(p => p - 1)}>←</button>
              {Array.from({ length: Math.min(pages, 5) }, (_, i) => i + 1).map(p => (
                <button key={p} className={`page-btn ${p === page ? 'active' : ''}`} onClick={() => setPage(p)}>{p}</button>
              ))}
              <button className="page-btn" disabled={page === pages} onClick={() => setPage(p => p + 1)}>→</button>
            </div>
          </div>
        )}
      </div>

      {/* ═══ MODAL: Create Order ═══════════════════════════════ */}
      {showCreate && (
        <div className="modal-backdrop" onClick={e => e.target === e.currentTarget && setShowCreate(false)}>
          <div className="modal modal-lg slide-up">
            <div className="modal-header">
              <h2>Nueva Orden de Venta</h2>
              <button className="btn btn-ghost btn-icon" onClick={() => setShowCreate(false)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="grid-2">
                <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                  <label className="form-label">Nombre del Cliente <span className="required">*</span></label>
                  <input className="form-input" placeholder="Ej: Juan Pérez" value={form.clienteNombre}
                    onChange={e => setForm(f => ({ ...f, clienteNombre: e.target.value }))} />
                </div>

                <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                  <label className="form-label">Plan <span className="required">*</span></label>
                  <select className="form-select" value={form.planId} onChange={e => onPlanChange(e.target.value)}>
                    <option value="">Selecciona un plan...</option>
                    {planes.map(p => (
                      <option key={p.id} value={p.id}>
                        {p.nombre} — {fmt(p.precioBase)}
                      </option>
                    ))}
                  </select>
                </div>

                {selectedPlan && (
                  <div style={{ gridColumn: '1 / -1' }}>
                    <div className="section-label">Servicios del Plan</div>
                    <div className="checkbox-group">
                      {/* Mandatory — DTO: nombreServicio, esObligatorio, precioEfectivo */}
                      {selectedPlan.servicios?.filter(s => s.esObligatorio).map(s => (
                        <div key={s.serviceId} className="checkbox-item" style={{ cursor: 'default', opacity: 0.8 }}>
                          <input type="checkbox" checked readOnly />
                          <div className="checkbox-item-label">
                            <div className="checkbox-item-name">{s.nombreServicio}</div>
                            <div className="checkbox-item-mandatory">Servicio obligatorio · {fmt(s.precioEfectivo)}</div>
                          </div>
                          <span className="badge badge-green" style={{ fontSize: '0.6rem' }}>Incluido</span>
                        </div>
                      ))}
                      {/* Optional */}
                      {selectedPlan.servicios?.filter(s => !s.esObligatorio).map(s => (
                        <div key={s.serviceId} className="checkbox-item" onClick={() => toggleOptional(s.serviceId)}>
                          <input type="checkbox" readOnly
                            checked={form.serviciosOpcionalesIds.includes(s.serviceId)} />
                          <div className="checkbox-item-label">
                            <div className="checkbox-item-name">{s.nombreServicio}</div>
                            <div className="checkbox-item-price">+{fmt(s.precioEfectivo)}</div>
                          </div>
                        </div>
                      ))}
                      {!selectedPlan.servicios?.length && <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Este plan no tiene servicios configurados.</p>}
                    </div>
                  </div>
                )}

                <div className="form-group">
                  <label className="form-label">Descuento (COP)</label>
                  <input type="number" className="form-input" placeholder="0" min="0"
                    value={form.descuento} onChange={e => setForm(f => ({ ...f, descuento: e.target.value }))} />
                </div>

                <div className="form-group">
                  <label className="form-label">Notas</label>
                  <input className="form-input" placeholder="Notas adicionales..."
                    value={form.notas} onChange={e => setForm(f => ({ ...f, notas: e.target.value }))} />
                </div>
              </div>

              {/* Price Preview */}
              {selectedPlan && (
                <div className="price-preview">
                  <div className="section-label" style={{ marginBottom: 8 }}>Resumen de Precio</div>
                  <div className="price-row"><span>Subtotal</span><span className="font-mono">{fmt(price.subtotal)}</span></div>
                  {price.descuento > 0 && <div className="price-row"><span>Descuento</span><span className="font-mono" style={{ color: 'var(--red)' }}>-{fmt(price.descuento)}</span></div>}
                  <div className="price-row"><span>IVA (13%)</span><span className="font-mono">{fmt(price.impuesto)}</span></div>
                  <div className="price-row total"><span>Total a Pagar</span><span className="font-mono">{fmt(price.total)}</span></div>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowCreate(false)}>Cancelar</button>
              <button className="btn btn-primary" onClick={handleCreate} disabled={submitting || !form.clienteNombre || !form.planId}>
                {submitting ? <><span className="spinner" style={{ width: 14, height: 14 }} /> Creando…</> : '✓ Crear Orden'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ═══ MODAL: Change Status ══════════════════════════════ */}
      {showStatus && (
        <div className="modal-backdrop" onClick={e => e.target === e.currentTarget && setShowStatus(null)}>
          <div className="modal slide-up">
            <div className="modal-header">
              <h2>Cambiar Estado de Orden</h2>
              <button className="btn btn-ghost btn-icon" onClick={() => setShowStatus(null)}>✕</button>
            </div>
            <div className="modal-body">
              <p style={{ marginBottom: 16 }}>
                Orden de <strong style={{ color: 'var(--text-primary)' }}>{showStatus.clienteNombre}</strong>
                &nbsp;— Estado actual: <span className={`badge ${STATUS_MAP[showStatus.estado]?.cls}`}>{STATUS_MAP[showStatus.estado]?.label}</span>
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {STATUS_MAP[showStatus.estado]?.next.map(ns => (
                  <button
                    key={ns}
                    className={`btn ${ns === 'Cancelada' ? 'btn-danger' : 'btn-secondary'} w-full`}
                    onClick={() => handleStatusChange(showStatus, ns)}
                  >
                    → {STATUS_LABELS[ns]}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ═══ MODAL: Delete Confirm ══════════════════════════════ */}
      {showDeleteConf && (
        <div className="modal-backdrop" onClick={e => e.target === e.currentTarget && setShowDeleteConf(null)}>
          <div className="modal slide-up">
            <div className="modal-header">
              <h2>Confirmar Eliminación</h2>
              <button className="btn btn-ghost btn-icon" onClick={() => setShowDeleteConf(null)}>✕</button>
            </div>
            <div className="modal-body">
              <p>¿Estás seguro de eliminar la orden de <strong style={{ color: 'var(--text-primary)' }}>{showDeleteConf.clienteNombre}</strong>?</p>
              <p style={{ marginTop: 8, fontSize: '0.8rem', color: 'var(--red)' }}>⚠️ Esta acción no se puede deshacer.</p>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowDeleteConf(null)}>Cancelar</button>
              <button className="btn btn-danger" onClick={() => handleDelete(showDeleteConf)}>✕ Eliminar Orden</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
