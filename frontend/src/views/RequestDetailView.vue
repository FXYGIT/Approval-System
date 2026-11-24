<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import { ApiError } from '@/api/http'
import { deleteRequest, getRequest } from '@/api/requests'
import RequestStatusTag from '@/components/RequestStatusTag.vue'
import { useAuthStore } from '@/stores/auth'
import type { RequestPublic } from '@/types/request'
import { formatDateTime } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const requestId = computed(() => (typeof route.params.id === 'string' ? route.params.id : ''))

const loading = ref(false)
const detail = ref<RequestPublic | null>(null)

const isOwnerDraft = computed(
  () =>
    detail.value !== null &&
    detail.value.applicantId === auth.user?.id &&
    detail.value.status === 'Draft',
)

async function load() {
  loading.value = true
  try {
    detail.value = await getRequest(requestId.value)
  } catch (err) {
    ElMessage.error(err instanceof ApiError ? err.message : '加载失败，请稍后重试')
    if (err instanceof ApiError && (err.status === 403 || err.status === 404)) {
      router.push({ name: 'requests' })
    }
  } finally {
    loading.value = false
  }
}

async function handleDelete() {
  if (!detail.value) return
  try {
    await ElMessageBox.confirm(`确定删除草稿「${detail.value.title}」吗？`, '提示', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await deleteRequest(detail.value.id)
    ElMessage.success('删除成功')
    router.push({ name: 'requests' })
  } catch (err) {
    ElMessage.error(err instanceof ApiError ? err.message : '删除失败，请稍后重试')
  }
}

onMounted(load)
</script>

<template>
  <div class="page" v-loading="loading">
    <el-card v-if="detail">
      <template #header>
        <div class="header">
          <span class="title">{{ detail.title }}</span>
          <RequestStatusTag :status="detail.status" :current-step="detail.currentStep" />
        </div>
      </template>

      <el-descriptions :column="1" border>
        <el-descriptions-item label="申请内容">
          <div class="content">{{ detail.content }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="申请人">{{ detail.applicant.displayName }}</el-descriptions-item>
        <el-descriptions-item label="一级审批人">{{ detail.firstApprover.displayName }}</el-descriptions-item>
        <el-descriptions-item label="二级审批人">{{ detail.secondApprover.displayName }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDateTime(detail.createdAt) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatDateTime(detail.updatedAt) }}</el-descriptions-item>
        <el-descriptions-item label="提交时间">{{ formatDateTime(detail.submittedAt) }}</el-descriptions-item>
      </el-descriptions>

      <div class="actions">
        <el-button @click="router.push({ name: 'requests' })">返回</el-button>
        <template v-if="isOwnerDraft">
          <el-button
            type="primary"
            @click="router.push({ name: 'request-edit', params: { id: detail.id } })"
          >
            编辑
          </el-button>
          <el-button type="danger" @click="handleDelete">删除</el-button>
        </template>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.page { max-width: 860px; margin: 0 auto; }
.header { display: flex; align-items: center; gap: 12px; }
.title { font-size: 18px; font-weight: 600; }
.content { white-space: pre-wrap; }
.actions { margin-top: 16px; display: flex; gap: 12px; }
</style>
