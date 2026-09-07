import api from './axios'

export const getPlanes       = (p = 1, ps = 100) => api.get(`/planes?soloActivos=false`)
export const getPlan         = (id)              => api.get(`/planes/${id}`)
export const createPlan      = (data)            => api.post('/planes', data)
export const updatePlan      = (id, data)        => api.put(`/planes/${id}`, data)
export const deletePlan      = (id)              => api.delete(`/planes/${id}`)
export const assignService   = (planId, data)    => api.post(`/planes/${planId}/servicios`, data)
export const removeService   = (planId, svcId)   => api.delete(`/planes/${planId}/servicios/${svcId}`)
