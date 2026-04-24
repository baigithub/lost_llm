import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/login' },
    { path: '/home', name: 'home', component: () => import('@/views/Home.vue') },
    { path: '/login', name: 'login', component: () => import('@/views/Login.vue') },
    { path: '/register', name: 'register', component: () => import('@/views/Register.vue') },
    { path: '/item/:id', name: 'item-detail', component: () => import('@/views/ItemDetail.vue'), props: true },
    { path: '/publish', name: 'publish', meta: { auth: true }, component: () => import('@/views/Publish.vue') },
    { path: '/user', name: 'user-center', meta: { auth: true }, component: () => import('@/views/UserCenter.vue') },
    { path: '/review-center', name: 'review-center', meta: { auth: true }, component: () => import('@/views/ReviewCenter.vue') },
    {
      path: '/admin',
      component: () => import('@/layouts/AdminLayout.vue'),
      meta: { auth: true, admin: true },
      children: [
        { path: '', redirect: '/admin/dashboard' },
        { path: 'dashboard', name: 'admin-dashboard', component: () => import('@/views/admin/Dashboard.vue') },
        { path: 'users', name: 'admin-users', component: () => import('@/views/admin/Users.vue') },
        { path: 'items', name: 'admin-items', component: () => import('@/views/admin/Items.vue') },
        { path: 'claims', name: 'admin-claims', component: () => import('@/views/admin/Claims.vue') },
        { path: 'categories', redirect: { name: 'admin-dictionary-category' } },
        { path: 'item-categories', redirect: { name: 'admin-dictionary-category' } },
        { path: 'dictionary', redirect: { name: 'admin-dictionary-status' } },
        {
          path: 'dictionary/status',
          name: 'admin-dictionary-status',
          component: () => import('@/views/admin/Dictionary.vue'),
          props: { initialTab: 'item_status' },
        },
        {
          path: 'dictionary/category',
          name: 'admin-dictionary-category',
          component: () => import('@/views/admin/Dictionary.vue'),
          props: { initialTab: 'category' },
        },
        { path: 'roles', name: 'admin-roles', component: () => import('@/views/admin/Roles.vue') },
        { path: 'menus', name: 'admin-menus', component: () => import('@/views/admin/Menus.vue') },
        { path: 'logs', name: 'admin-logs', component: () => import('@/views/admin/Logs.vue') },
        {
          path: 'pagination',
          name: 'admin-pagination',
          component: () => import('@/views/admin/Pagination.vue'),
        },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  const u = useUserStore()
  if (to.meta.auth && !u.token) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.admin) {
    if (!u.token) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }
    if (!u.profile) {
      try {
        await u.refreshProfile()
      } catch {
        return { name: 'login' }
      }
    }
    const roles = (u.profile?.roles as { code: string }[] | undefined) || []
    const okAdmin = roles.some(
      (r) => r.code === 'admin' || r.code === 'super_admin' || r.code === 'claim_reviewer',
    )
    if (!okAdmin) {
      return '/home'
    }
    if (u.menus.length === 0) await u.loadMenus()
    if (!u.hasAdminPath(to.path)) {
      return '/admin/dashboard'
    }
  }
  return true
})

export default router
