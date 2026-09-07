import api from './axios'

export const getSalesOrders  = (filters = {}) => {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([k, v]) => { if (v !== '' && v != null) params.append(k, v) })
  return api.get(`/salesorders?${params}`)
}
export const getSalesOrder   = (id)    => api.get(`/salesorders/${id}`)
export const createSalesOrder= (data)  => api.post('/salesorders', data)
export const updateStatus    = (id, d) => api.patch(`/salesorders/${id}/status`, d)
export const deleteSalesOrder= (id)    => api.delete(`/salesorders/${id}`)
