import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import * as authApi from '@/api/auth'
import { setToken, getToken } from '@/api/http'

export interface MenuItem {
  id: number
  parent_id: number
  name: string
  path: string | null
  icon: string | null
  permission: string | null
  sort: number
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string | null>(getToken())
  const profile = ref<Record<string, unknown> | null>(null)
  const menus = ref<MenuItem[]>([])
  const pendingClaims = ref(0)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => {
    const roles = (profile.value?.roles as { code: string }[] | undefined) || []
    return roles.some(
      (r) => r.code === 'admin' || r.code === 'super_admin' || r.code === 'claim_reviewer',
    )
  })

  async function login(username: string, password: string) {
    const res = (await authApi.login(username, password)) as { access_token: string }
    token.value = res.access_token
    setToken(res.access_token)
    await refreshProfile()
    await loadMenus()
  }

  function logout() {
    token.value = null
    profile.value = null
    menus.value = []
    setToken(null)
  }

  async function refreshProfile() {
    profile.value = (await authApi.fetchMe()) as Record<string, unknown>
  }

  async function loadMenus() {
    try {
      menus.value = ((await authApi.fetchMenus()) as MenuItem[]) || []
    } catch {
      menus.value = []
    }
  }

  async function loadNotifications() {
    try {
      const s = (await authApi.fetchNotificationSummary()) as { pending_claim_reviews: number }
      pendingClaims.value = s?.pending_claim_reviews ?? 0
    } catch {
      pendingClaims.value = 0
    }
  }

  function hasAdminPath(path: string) {
    if (!path.startsWith('/admin')) return true
    if (path === '/admin' || path === '/admin/dashboard') return true
    return menus.value.some((m) => m.path === path)
  }

  return {
    token,
    profile,
    menus,
    pendingClaims,
    isLoggedIn,
    isAdmin,
    login,
    logout,
    refreshProfile,
    loadMenus,
    loadNotifications,
    hasAdminPath,
  }
})
