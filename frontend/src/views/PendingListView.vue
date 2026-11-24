<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { ApiError } from '@/api/http'
import { listRequests } from '@/api/requests'
import RequestStatusTag from '@/components/RequestStatusTag.vue'
import type { RequestPublic } from '@/types/request'
import { formatDateTime } from '@/utils/format'

const router = useRouter()

const loading = ref(false)
const rows = ref<RequestPublic[]>([])
const total = ref(0)

const query = reactive({
  page: 1,
  pageSize: 10,
  keyword: '',
})

async function load() {
  loading.value = true
  try {
    const result = await listRequests({
      scope: 'pending',
      page: query.page,
      pageSize: query.pageSize,
      keyword: query.keyword.trim() || undefined,
    })
    rows.value = result.items
    total.value = result.total
  } catch (err) {
    ElMessage.error(err instanceof ApiError ? err.message : '加载失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  query.page = 1
  load()
}

onMounted(load)
</script>

<template>
  <div class="page">
    <el-card>
      <template #header>
        <div class="toolbar">
          <el-input
            v-model="query.keyword"
            placeholder="按标题搜索"
            clearable
            class="search"
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          />
          <el-button type="primary" @click="handleSearch">查询</el-button>
        </div>
      </template>

      <el-table v-loading="loading" :data="rows">
        <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
        <el-table-column label="申请人" width="140">
          <template #default="{ row }">{{ row.applicant.displayName }}</template>
        </el-table-column>
        <el-table-column label="状态" width="140">
          <template #default="{ row }">
            <RequestStatusTag :status="row.status" :current-step="row.currentStep" />
          </template>
        </el-table-column>
        <el-table-column label="提交时间" width="170">
          <template #default="{ row }">{{ formatDateTime(row.submittedAt) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              @click="router.push({ name: 'request-detail', params: { id: row.id } })"
            >
              去审批
            </el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无待审批的申请" />
        </template>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="query.page"
          v-model:page-size="query.pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @current-change="load"
          @size-change="handleSearch"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.page { max-width: 1080px; margin: 0 auto; }
.toolbar { display: flex; align-items: center; gap: 12px; }
.search { width: 220px; }
.pagination { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>
