import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor — añade el JWT automáticamente
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('finca_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Response interceptor — maneja expiración de sesión
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('finca_token')
      localStorage.removeItem('finca_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api
