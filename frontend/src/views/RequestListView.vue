<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import { ApiError } from '@/api/http'
import { deleteRequest, listRequests } from '@/api/requests'
import RequestStatusTag from '@/components/RequestStatusTag.vue'
import type { RequestPublic, RequestStatus } from '@/types/request'
import { REQUEST_STATUS_LABEL } from '@/types/request'
import { formatDateTime } from '@/utils/format'

const router = useRouter()

const loading = ref(false)
const rows = ref<RequestPublic[]>([])
const total = ref(0)

const query = reactive({
  page: 1,
  pageSize: 10,
  status: '' as RequestStatus | '',
  keyword: '',
})

const statusOptions = [
  { value: '', label: '全部状态' },
  ...(Object.keys(REQUEST_STATUS_LABEL) as RequestStatus[]).map((value) => ({
    value,
    label: REQUEST_STATUS_LABEL[value],
  })),
]

async function load() {
  loading.value = true
  try {
    const result = await listRequests({
      page: query.page,
      pageSize: query.pageSize,
      status: query.status || undefined,
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

function handleStatusChange() {
  query.page = 1
  load()
}

async function handleDelete(row: RequestPublic) {
  try {
    await ElMessageBox.confirm(`确定删除草稿「${row.title}」吗？`, '提示', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await deleteRequest(row.id)
    ElMessage.success('删除成功')
    if (rows.value.length === 1 && query.page > 1) {
      query.page -= 1
    }
    load()
  } catch (err) {
    ElMessage.error(err instanceof ApiError ? err.message : '删除失败，请稍后重试')
  }
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
          <el-select
            v-model="query.status"
            class="status"
            placeholder="状态"
            @change="handleStatusChange"
          >
            <el-option
              v-for="opt in statusOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <div class="spacer" />
          <el-button type="primary" @click="router.push({ name: 'request-new' })">新建申请</el-button>
        </div>
      </template>

      <el-table v-loading="loading" :data="rows">
        <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <RequestStatusTag :status="row.status" :current-step="row.currentStep" />
          </template>
        </el-table-column>
        <el-table-column label="一级审批人" min-width="120">
          <template #default="{ row }">{{ row.firstApprover.displayName }}</template>
        </el-table-column>
        <el-table-column label="二级审批人" min-width="120">
          <template #default="{ row }">{{ row.secondApprover.displayName }}</template>
        </el-table-column>
        <el-table-column label="创建时间" width="170">
          <template #default="{ row }">{{ formatDateTime(row.createdAt) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              @click="router.push({ name: 'request-detail', params: { id: row.id } })"
            >
              查看
            </el-button>
            <template v-if="row.status === 'Draft'">
              <el-button
                link
                type="primary"
                @click="router.push({ name: 'request-edit', params: { id: row.id } })"
              >
                编辑
              </el-button>
              <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
            </template>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无申请记录" />
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
.status { width: 140px; }
.spacer { flex: 1; }
.pagination { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>
