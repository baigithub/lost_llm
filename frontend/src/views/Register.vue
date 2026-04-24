<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import * as authApi from '@/api/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const username = ref('')
const password = ref('')
const phone = ref('')
const real_name = ref('')
const loading = ref(false)

async function submit() {
  loading.value = true
  try {
    await authApi.register({
      username: username.value,
      password: password.value,
      phone: phone.value || undefined,
      real_name: real_name.value || undefined,
    })
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="wrap">
    <el-card class="box">
      <h2>注册</h2>
      <el-form label-position="top" @submit.prevent="submit">
        <el-form-item label="学号/用户名" required>
          <el-input v-model="username" />
        </el-form-item>
        <el-form-item label="密码" required>
          <el-input v-model="password" type="password" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="phone" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="real_name" />
        </el-form-item>
        <el-button type="primary" native-type="submit" :loading="loading" style="width: 100%">注册</el-button>
        <div class="extra"><router-link to="/login">已有账号登录</router-link></div>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
}
.box {
  width: 420px;
}
.extra {
  margin-top: 16px;
}
</style>
