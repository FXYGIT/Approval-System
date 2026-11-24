<script setup lang="ts">
import { computed } from 'vue'

import type { ApprovalStep, RequestStatus } from '@/types/request'

type TagType = 'primary' | 'success' | 'warning' | 'info' | 'danger'

const props = defineProps<{
  status: RequestStatus
  currentStep?: ApprovalStep | null
}>()

const label = computed<string>(() => {
  switch (props.status) {
    case 'Draft':
      return '草稿'
    case 'InProgress':
      return props.currentStep === 'Second' ? '二级审批中' : '一级审批中'
    case 'Approved':
      return '已通过'
    case 'Rejected':
      return '已驳回'
  }
})

const type = computed<TagType>(() => {
  switch (props.status) {
    case 'Draft':
      return 'info'
    case 'InProgress':
      return 'warning'
    case 'Approved':
      return 'success'
    case 'Rejected':
      return 'danger'
  }
})
</script>

<template>
  <el-tag :type="type" size="small">{{ label }}</el-tag>
</template>
