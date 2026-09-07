import api from './axios'

export const getServices  = (p = 1, ps = 50, cat = '') =>
  api.get(`/services?page=${p}&pageSize=${ps}${cat ? `&category=${cat}` : ''}`)
export const getService   = (id)    => api.get(`/services/${id}`)
export const createService= (data)  => api.post('/services', data)
export const updateService= (id, d) => api.put(`/services/${id}`, d)
export const deleteService= (id)    => api.delete(`/services/${id}`)
