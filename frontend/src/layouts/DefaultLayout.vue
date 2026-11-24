<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const displayName = computed(() => auth.user?.displayName || auth.user?.username || '')

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定退出登录吗？', '提示', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <el-container class="layout">
    <el-header class="header">
      <div class="brand" @click="router.push({ name: 'requests' })">审批系统</div>
      <nav class="nav">
        <router-link
          to="/requests"
          class="link"
          :class="{ active: route.path.startsWith('/requests') }"
        >
          我发起的申请
        </router-link>
      </nav>
      <div class="user">
        <span class="name">{{ displayName }}</span>
        <el-button text type="primary" @click="handleLogout">退出登录</el-button>
      </div>
    </el-header>
    <el-main class="main">
      <router-view />
    </el-main>
  </el-container>
</template>

<style scoped>
.layout { min-height: 100vh; }
.header {
  display: flex;
  align-items: center;
  gap: 32px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
}
.brand { font-size: 18px; font-weight: 600; color: #2059a2; cursor: pointer; }
.nav { flex: 1; }
.link { color: #606266; text-decoration: none; font-size: 15px; }
.link:hover { color: #2059a2; }
.link.active { color: #2059a2; font-weight: 600; }
.user { display: flex; align-items: center; gap: 8px; }
.name { color: #606266; }
.main { background: #f5f7fa; }
</style>
