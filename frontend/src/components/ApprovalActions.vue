<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { approveRequest, rejectRequest } from '@/api/requests'
import { ApiError } from '@/api/http'
import type { RequestPublic } from '@/types/request'

const props = defineProps<{
  request: RequestPublic
  currentUserId: string
}>()

const emit = defineEmits<{ (e: 'done'): void }>()

const canApprove = computed(() => {
  if (props.request.status !== 'InProgress') return false
  if (props.request.currentStep === 'First') {
    return props.request.firstApproverId === props.currentUserId
  }
  if (props.request.currentStep === 'Second') {
    return props.request.secondApproverId === props.currentUserId
  }
  return false
})

const dialogVisible = ref(false)
const mode = ref<'approve' | 'reject'>('approve')
const comment = ref('')
const submitting = ref(false)

const isReject = computed(() => mode.value === 'reject')
const dialogTitle = computed(() => (isReject.value ? '驳回申请' : '审批通过'))

function open(next: 'approve' | 'reject') {
  mode.value = next
  comment.value = ''
  dialogVisible.value = true
}

function handleError(err: unknown) {
  if (err instanceof ApiError) {
    if (err.status === 409) {
      ElMessage.error('申请状态已发生变化，请刷新后重试')
      dialogVisible.value = false
      emit('done')
      return
    }
    if (err.status === 403) {
      ElMessage.error('您当前无权审批该申请')
      dialogVisible.value = false
      emit('done')
      return
    }
    ElMessage.error(err.message)
    return
  }
  ElMessage.error('操作失败，请稍后重试')
}

async function confirm() {
  const text = comment.value.trim()
  if (isReject.value && !text) {
    ElMessage.warning('驳回意见不能为空')
    return
  }
  submitting.value = true
  try {
    if (isReject.value) {
      await rejectRequest(props.request.id, { comment: text, version: props.request.version })
      ElMessage.success('已驳回')
    } else {
      await approveRequest(props.request.id, {
        comment: text || null,
        version: props.request.version,
      })
      ElMessage.success('已通过')
    }
    dialogVisible.value = false
    emit('done')
  } catch (err) {
    handleError(err)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div v-if="canApprove" class="approval-actions">
    <el-button type="success" @click="open('approve')">审批通过</el-button>
    <el-button type="danger" @click="open('reject')">驳回</el-button>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="480px">
      <el-form label-position="top">
        <el-form-item :label="isReject ? '驳回意见（必填）' : '审批意见（可选）'">
          <el-input
            v-model="comment"
            type="textarea"
            :rows="4"
            maxlength="500"
            show-word-limit
            :placeholder="isReject ? '请输入驳回意见' : '可填写审批意见'"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button
          :type="isReject ? 'danger' : 'success'"
          :loading="submitting"
          @click="confirm"
        >
          确认{{ isReject ? '驳回' : '通过' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.approval-actions { display: flex; gap: 12px; }
</style>
