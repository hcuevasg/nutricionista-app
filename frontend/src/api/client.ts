import axios, { AxiosError } from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL as string

const axiosInstance = axios.create({
  baseURL: BASE_URL,
})

// Inject auth token on every request
axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 and network errors globally
axiosInstance.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    } else if (!error.response) {
      // Network error (no response from server)
      window.dispatchEvent(
        new CustomEvent('api-network-error', {
          detail: 'Error de red. Verifica tu conexión.',
        })
      )
    }
    return Promise.reject(error)
  }
)

// Typed helpers — return data directly
export const api = {
  get: <T>(url: string, params?: object) =>
    axiosInstance.get<T>(url, { params }).then((r) => r.data),

  post: <T>(url: string, data?: unknown) =>
    axiosInstance.post<T>(url, data).then((r) => r.data),

  put: <T>(url: string, data?: unknown) =>
    axiosInstance.put<T>(url, data).then((r) => r.data),

  patch: <T>(url: string, data?: unknown) =>
    axiosInstance.patch<T>(url, data).then((r) => r.data),

  delete: <T>(url: string) =>
    axiosInstance.delete<T>(url).then((r) => r.data),
}

export default axiosInstance
