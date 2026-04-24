import http from './http'

export function login(username: string, password: string) {
  return http.post('/api/v1/auth/login', { username, password })
}

export function register(payload: { username: string; password: string; phone?: string; real_name?: string }) {
  return http.post('/api/v1/auth/register', payload)
}

export function fetchMe() {
  return http.get('/api/v1/auth/me')
}

export function fetchMenus() {
  return http.get('/api/v1/auth/menus')
}

export function fetchNotificationSummary() {
  return http.get('/api/v1/auth/notifications/summary')
}
