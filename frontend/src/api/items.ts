import http from './http'

export function fetchCategories() {
  return http.get('/api/v1/items/meta/categories')
}

export function fetchHomeListPageSize() {
  return http.get('/api/v1/items/meta/home-list-page-size')
}

export function fetchItems(params: Record<string, unknown>) {
  return http.get('/api/v1/items', { params })
}

export function fetchItem(id: number) {
  return http.get(`/api/v1/items/${id}`)
}

export function createItem(payload: Record<string, unknown>) {
  return http.post('/api/v1/items', payload)
}

export function createClaim(itemId: number, payload: { verification_proof: string; contact_info?: string }) {
  return http.post(`/api/v1/items/${itemId}/claims`, payload)
}

export function offlineItem(itemId: number) {
  return http.post(`/api/v1/items/${itemId}/offline`)
}

export function onlineItem(itemId: number) {
  return http.post(`/api/v1/items/${itemId}/online`)
}

export function myPublished() {
  return http.get('/api/v1/items/published/my')
}

export function myClaims() {
  return http.get('/api/v1/items/claims/my')
}

export function itemClaims(itemId: number) {
  return http.get(`/api/v1/items/${itemId}/claims`)
}

export function approveClaim(claimId: number) {
  return http.post(`/api/v1/items/claims/${claimId}/approve`)
}

export function rejectClaim(claimId: number) {
  return http.post(`/api/v1/items/claims/${claimId}/reject`)
}

export function recognitionUpload(formData: FormData) {
  return http.post('/api/v1/recognition/upload', formData)
}
