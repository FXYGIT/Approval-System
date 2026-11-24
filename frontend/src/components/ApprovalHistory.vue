<script setup lang="ts">
import { computed } from 'vue'

import type { ApprovalAction, HistoryEntry } from '@/types/history'
import { APPROVAL_ACTION_LABEL } from '@/types/history'
import { formatDateTime } from '@/utils/format'

type TimelineType = 'primary' | 'success' | 'warning' | 'danger' | 'info'

const props = defineProps<{
  entries: HistoryEntry[]
}>()

// 后端已按 createdAt ASC、id ASC 返回，此处再排序一次保证展示稳定。
const sorted = computed(() =>
  [...props.entries].sort((a, b) => {
    if (a.createdAt === b.createdAt) return a.id.localeCompare(b.id)
    return a.createdAt.localeCompare(b.createdAt)
  }),
)

function timelineType(action: ApprovalAction): TimelineType {
  switch (action) {
    case 'Submit':
      return 'primary'
    case 'FirstApprove':
    case 'SecondApprove':
      return 'success'
    case 'FirstReject':
    case 'SecondReject':
      return 'danger'
  }
}
</script>

<template>
  <div class="history">
    <div v-if="sorted.length === 0" class="empty">暂无审批记录</div>
    <el-timeline v-else>
      <el-timeline-item
        v-for="entry in sorted"
        :key="entry.id"
        :timestamp="formatDateTime(entry.createdAt)"
        :type="timelineType(entry.action)"
        placement="top"
      >
        <div class="action">{{ APPROVAL_ACTION_LABEL[entry.action] }}</div>
        <div class="operator">操作人：{{ entry.operator.displayName }}</div>
        <div v-if="entry.comment" class="comment">审批意见：{{ entry.comment }}</div>
      </el-timeline-item>
    </el-timeline>
  </div>
</template>

<style scoped>
.history { padding: 4px 0; }
.empty { color: #909399; font-size: 14px; padding: 8px 0; }
.action { font-weight: 600; color: #303133; }
.operator { color: #606266; font-size: 13px; margin-top: 2px; }
.comment {
  color: #909399;
  font-size: 13px;
  margin-top: 4px;
  white-space: pre-wrap;
}
</style>
