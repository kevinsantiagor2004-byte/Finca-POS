import api from './axios'

export const getUsuarios  = (p = 1, ps = 20) => api.get(`/usuarios?page=${p}&pageSize=${ps}`)
export const getUsuario   = (id)    => api.get(`/usuarios/${id}`)
export const createUsuario= (data)  => api.post('/usuarios', data)
export const updateUsuario= (id, d) => api.put(`/usuarios/${id}`, d)
export const deleteUsuario= (id)    => api.delete(`/usuarios/${id}`)
