<script setup lang="ts">
import { onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { getToken } from '@/api/http'

const u = useUserStore()
onMounted(async () => {
  if (getToken()) {
    try {
      await u.refreshProfile()
      await u.loadMenus()
      await u.loadNotifications()
    } catch {
      u.logout()
    }
  }
})
</script>

<template>
  <router-view />
</template>
