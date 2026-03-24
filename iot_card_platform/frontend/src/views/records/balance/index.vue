<template>
  <div class="records-page">
    <el-card shadow="never" class="search-card">
      <div class="page-head">
        <div class="page-title">余额变动记录</div>
        <el-button @click="fetchLogs">刷新</el-button>
      </div>

      <el-form :model="searchForm" inline>
        <el-form-item label="类型">
          <el-select v-model="searchForm.action" clearable placeholder="全部类型" style="width: 180px">
            <el-option label="余额分配" value="grant" />
            <el-option label="余额消费" value="consume" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="logs" border stripe>
        <el-table-column prop="action" label="类型" width="120">
          <template #default="{ row }">
            {{ actionLabelMap[row.action] || row.action }}
          </template>
        </el-table-column>
        <el-table-column prop="target_name" label="对象" width="180" />
        <el-table-column prop="detail" label="详情" min-width="460" show-overflow-tooltip />
        <el-table-column label="结果" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_success ? 'success' : 'danger'">
              {{ row.is_success ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchLogs"
          @current-change="fetchLogs"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { systemApi } from '@/api/modules/system'
import type { OperationLog } from '@/types/system'
import { formatDateTime } from '@/utils/formatter'

const loading = ref(false)
const logs = ref<OperationLog[]>([])
const dateRange = ref<string[]>([])

const actionLabelMap: Record<string, string> = {
  grant: '余额分配',
  consume: '余额消费'
}

const searchForm = reactive({
  action: undefined as string | undefined
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const fetchLogs = async () => {
  loading.value = true
  try {
    const res: any = await systemApi.getBalanceLogs({
      action: searchForm.action,
      start_time: dateRange.value?.[0],
      end_time: dateRange.value?.[1],
      page: pagination.page,
      page_size: pagination.page_size
    })
    logs.value = res.items || []
    pagination.total = res.total || 0
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchLogs()
}

const handleReset = () => {
  searchForm.action = undefined
  dateRange.value = []
  handleSearch()
}

onMounted(fetchLogs)
</script>

<style scoped lang="scss">
.records-page {
  padding: 20px;
}

.search-card {
  margin-bottom: 16px;
}

.page-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
