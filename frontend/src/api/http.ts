import axios, { type AxiosError } from 'axios'
import { ElMessage } from 'element-plus'

const TOKEN_KEY = 'lf_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(t: string | null) {
  if (t) localStorage.setItem(TOKEN_KEY, t)
  else localStorage.removeItem(TOKEN_KEY)
}

const http = axios.create({
  baseURL: '',
  timeout: 120000,
})

http.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (res) => {
    const body = res.data
    if (body && typeof body.access_token === 'string') {
      return body
    }
    if (body && typeof body.code === 'number') {
      if (body.code === 200) return body.data
      ElMessage.error(body.message || '请求失败')
      return Promise.reject(body)
    }
    return body
  },
  (err: AxiosError<{ message?: string; detail?: string | unknown }>) => {
    const data = err.response?.data as { message?: string; detail?: string } | undefined
    const msg = data?.message || (typeof data?.detail === 'string' ? data.detail : '') || err.message || '网络错误'
    ElMessage.error(String(msg))
    if (err.response?.status === 401) {
      setToken(null)
      if (window.location.pathname !== '/login') window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

/** 拦截器已解包为业务 data，类型放宽为 any 以便与 vue-tsc 一致 */
export default http as any
