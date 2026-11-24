<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { fetchHealth } from './api/health'

const loading = ref(false)
const message = ref('')
async function checkHealth() {
  loading.value = true
  message.value = '正在检查服务连接…'
  try {
    const health = await fetchHealth()
    message.value = health.status === 'ok' && health.database === 'ok'
      ? '服务已就绪' : '服务状态异常'
  } catch {
    message.value = '连接失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
onMounted(checkHealth)
</script>

<template>
  <main>
    <p class="label">APPROVAL SYSTEM</p>
    <h1>审批系统</h1>
    <p>工程初始化阶段，审批功能将逐步开放。</p>
    <section aria-label="服务状态">
      <h2>服务连接</h2>
      <p role="status" aria-live="polite">{{ message }}</p>
      <button :disabled="loading" @click="checkHealth">{{ loading ? '检查中…' : '重新检查' }}</button>
    </section>
  </main>
</template>

<style>
:root { font-family: system-ui, sans-serif; color: #183047; background: #f3f6f9; }
body { margin: 0; }
main { max-width: 720px; margin: 12vh auto; padding: 24px; }
.label { color: #526b80; letter-spacing: .16em; font-size: 12px; }
h1 { font-size: 40px; }
section { margin-top: 36px; padding: 28px; background: white; border: 1px solid #d8e2eb; border-radius: 12px; }
h2 { font-size: 20px; }
button { padding: 10px 18px; background: #2059a2; color: white; border: 0; border-radius: 6px; cursor: pointer; }
button:disabled { opacity: .6; cursor: wait; }
</style>
