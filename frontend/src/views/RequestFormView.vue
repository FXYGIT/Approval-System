<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

import { ApiError } from '@/api/http'
import { createRequest, getRequest, updateRequest } from '@/api/requests'
import { listUsers } from '@/api/users'
import { useAuthStore } from '@/stores/auth'
import type { UserSummary } from '@/types/user'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const isEdit = computed(() => Boolean(route.params.id))
const requestId = computed(() => (typeof route.params.id === 'string' ? route.params.id : ''))

const formRef = ref<FormInstance>()
const loading = ref(false)
const submitting = ref(false)

const form = reactive({
  title: '',
  content: '',
  firstApproverId: '',
  secondApproverId: '',
  version: 1,
})

const approverOptions = ref<UserSummary[]>([])

const rules: FormRules = {
  title: [
    { required: true, whitespace: true, message: '请输入标题', trigger: 'blur' },
    { max: 100, message: '标题最长 100 字符', trigger: 'blur' },
  ],
  content: [
    { required: true, whitespace: true, message: '请输入申请内容', trigger: 'blur' },
    { max: 2000, message: '内容最长 2000 字符', trigger: 'blur' },
  ],
  firstApproverId: [{ required: true, message: '请选择一级审批人', trigger: 'change' }],
  secondApproverId: [{ required: true, message: '请选择二级审批人', trigger: 'change' }],
}

function approverLabel(user: UserSummary): string {
  return `${user.displayName}（${user.username}）`
}

async function loadApprovers() {
  try {
    const result = await listUsers({ pageSize: 100 })
    const meId = auth.user?.id
    approverOptions.value = result.items.filter((u) => u.id !== meId)
  } catch {
    approverOptions.value = []
  }
}

async function loadRequest() {
  if (!isEdit.value) return
  loading.value = true
  try {
    const detail = await getRequest(requestId.value)
    if (detail.applicantId !== auth.user?.id || detail.status !== 'Draft') {
      ElMessage.error('只有申请人可以编辑草稿')
      router.push({ name: 'requests' })
      return
    }
    form.title = detail.title
    form.content = detail.content
    form.firstApproverId = detail.firstApproverId
    form.secondApproverId = detail.secondApproverId
    form.version = detail.version
    for (const approver of [detail.firstApprover, detail.secondApprover]) {
      if (!approverOptions.value.some((u) => u.id === approver.id)) {
        approverOptions.value.unshift(approver)
      }
    }
  } catch (err) {
    ElMessage.error(err instanceof ApiError ? err.message : '加载失败，请稍后重试')
    router.push({ name: 'requests' })
  } finally {
    loading.value = false
  }
}

async function onSubmit() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    if (isEdit.value) {
      await updateRequest(requestId.value, {
        title: form.title,
        content: form.content,
        firstApproverId: form.firstApproverId,
        secondApproverId: form.secondApproverId,
        version: form.version,
      })
      ElMessage.success('保存成功')
      router.push({ name: 'request-detail', params: { id: requestId.value } })
    } else {
      const created = await createRequest({
        title: form.title,
        content: form.content,
        firstApproverId: form.firstApproverId,
        secondApproverId: form.secondApproverId,
      })
      ElMessage.success('创建成功')
      router.push({ name: 'request-detail', params: { id: created.id } })
    }
  } catch (err) {
    ElMessage.error(err instanceof ApiError ? err.message : '保存失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await loadApprovers()
  await loadRequest()
})
</script>

<template>
  <div class="page" v-loading="loading">
    <el-card>
      <template #header>
        <div class="title">{{ isEdit ? '编辑申请' : '新建申请' }}</div>
      </template>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入标题" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="申请内容" prop="content">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="6"
            placeholder="请输入申请内容"
            maxlength="2000"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="一级审批人" prop="firstApproverId">
          <el-select
            v-model="form.firstApproverId"
            placeholder="请选择一级审批人"
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="user in approverOptions"
              :key="user.id"
              :label="approverLabel(user)"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="二级审批人" prop="secondApproverId">
          <el-select
            v-model="form.secondApproverId"
            placeholder="请选择二级审批人"
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="user in approverOptions"
              :key="user.id"
              :label="approverLabel(user)"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="onSubmit">
            {{ isEdit ? '保存' : '创建' }}
          </el-button>
          <el-button @click="router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.page { max-width: 760px; margin: 0 auto; }
.title { font-size: 18px; font-weight: 600; }
</style>
