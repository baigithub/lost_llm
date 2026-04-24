<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { House, Fold, Expand } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import * as Icons from '@element-plus/icons-vue'
import { buildMenuTree } from '@/utils/menu-tree'

const collapsed = ref(false)
const route = useRoute()
const router = useRouter()
const u = useUserStore()

const active = computed(() => route.path)

const menuTree = computed(() => buildMenuTree(u.menus))

function icon(name?: string | null) {
  if (!name) return Icons.Menu
  const k = name as keyof typeof Icons
  return Icons[k] || Icons.Menu
}

async function logout() {
  u.logout()
  router.push('/login')
}
</script>

<template>
  <el-container class="admin-wrap">
    <el-aside :width="collapsed ? '64px' : '220px'" class="aside">
      <div class="logo">{{ collapsed ? 'LF' : '失物招领管理' }}</div>
      <el-menu :default-active="active" router :collapse="collapsed">
        <template v-for="m in menuTree" :key="m.id">
          <el-sub-menu v-if="m.children?.length" :index="'g' + m.id">
            <template #title>
              <el-icon><component :is="icon(m.icon)" /></el-icon>
              <span>{{ m.name }}</span>
            </template>
            <el-menu-item v-for="c in m.children" :key="c.id" :index="c.path || '/admin/dashboard'">
              <el-icon><component :is="icon(c.icon)" /></el-icon>
              <template #title>{{ c.name }}</template>
            </el-menu-item>
          </el-sub-menu>
          <el-menu-item v-else :index="m.path && m.path.length > 0 ? m.path : '/admin/dashboard'">
            <el-icon><component :is="icon(m.icon)" /></el-icon>
            <template #title>{{ m.name }}</template>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <el-button :icon="collapsed ? Expand : Fold" circle text @click="collapsed = !collapsed" />
        <div class="spacer" />
        <el-tag v-if="u.pendingClaims > 0" type="warning" size="small">待审核认领 {{ u.pendingClaims }}</el-tag>
        <el-button text @click="router.push('/home')"><el-icon><House /></el-icon> 前台</el-button>
        <el-button type="danger" text @click="logout">退出</el-button>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.admin-wrap {
  min-height: 100vh;
  background:
    radial-gradient(circle at 12% 15%, rgba(56, 189, 248, 0.12), transparent 36%),
    radial-gradient(circle at 88% 8%, rgba(99, 102, 241, 0.1), transparent 30%),
    linear-gradient(180deg, #f7fbff 0%, #eff5ff 100%);
}
.aside {
  background: rgba(255, 255, 255, 0.88);
  color: #1f2a44;
  border-right: 1px solid rgba(77, 126, 255, 0.22);
  backdrop-filter: blur(14px);
  box-shadow: 6px 0 24px rgba(62, 99, 220, 0.08);
}
.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: #18407b;
  letter-spacing: 0.08em;
  border-bottom: 1px solid rgba(77, 126, 255, 0.18);
  background: linear-gradient(90deg, rgba(226, 240, 255, 0.8), rgba(241, 249, 255, 0.8));
}
.header {
  display: flex;
  align-items: center;
  height: 64px;
  padding: 0 14px;
  border-bottom: 1px solid rgba(77, 126, 255, 0.2);
  background: rgba(255, 255, 255, 0.86);
  backdrop-filter: blur(12px);
  box-shadow: 0 8px 24px rgba(59, 102, 220, 0.08);
}
.spacer {
  flex: 1;
}
.main {
  background: transparent;
  min-height: calc(100vh - 60px);
  padding: 18px;
  font-size: 130%;
  line-height: 1.55;
}

:deep(.el-menu) {
  border-right: none;
  background: transparent;
}

:deep(.el-menu-item),
:deep(.el-sub-menu__title) {
  margin: 6px 10px;
  border-radius: 10px;
  height: 44px;
  line-height: 44px;
  color: #304465;
}

:deep(.el-menu-item:hover),
:deep(.el-sub-menu__title:hover) {
  background: rgba(62, 129, 255, 0.12);
  color: #1f4ea1;
}

:deep(.el-menu-item.is-active) {
  background: linear-gradient(120deg, rgba(56, 189, 248, 0.2), rgba(37, 99, 235, 0.22));
  color: #113d86;
  font-weight: 600;
  box-shadow: inset 0 0 0 1px rgba(56, 119, 255, 0.26);
}

:deep(.el-main .el-card) {
  border: 1px solid rgba(83, 140, 255, 0.18);
  box-shadow: 0 10px 24px rgba(37, 99, 235, 0.08);
}

:deep(.el-table) {
  --el-table-header-bg-color: #edf4ff;
  --el-table-row-hover-bg-color: #f5f9ff;
}
</style>
