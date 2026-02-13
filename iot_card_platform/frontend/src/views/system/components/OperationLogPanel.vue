<template>
  <div class="operation-log-panel">
    <!-- 筛选栏 -->
    <el-form :model="searchForm" inline class="search-form">
      <el-form-item label="模块">
        <el-select
          v-model="searchForm.module"
          placeholder="全部"
          clearable
          style="width: 130px"
          @change="handleSearch"
        >
          <el-option label="用户" value="user" />
          <el-option label="卡片" value="card" />
          <el-option label="流量池" value="pool" />
          <el-option label="套餐" value="package" />
          <el-option label="库存" value="stock" />
          <el-option label="停卡" value="suspend" />
          <el-option label="系统" value="system" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态">
        <el-select
          v-model="searchForm.is_success"
          placeholder="全部"
          clearable
          style="width: 120px"
          @change="handleSearch"
        >
          <el-option label="成功" :value="true" />
          <el-option label="失败" :value="false" />
        </el-select>
      </el-form-item>
      <el-form-item label="时间范围">
        <el-date-picker
          v-model="dateRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          value-format="YYYY-MM-DD HH:mm:ss"
          style="width: 360px"
          @change="handleSearch"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
        <el-button :icon="Refresh" @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 日志列表 -->
    <el-table
      v-loading="loading"
      :data="logList"
      stripe
      border
      style="width: 100%"
    >
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="user_name" label="操作人" width="120" />
      <el-table-column prop="module" label="模块" width="100" />
      <el-table-column prop="action" label="操作" width="120" />
      <el-table-column label="目标" min-width="180">
        <template #default="{ row }">
          <span v-if="row.target_name">{{ row.target_type }}: {{ row.target_name }}</span>
          <span v-else-if="row.target_id">{{ row.target_type }} #{{ row.target_id }}</span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="结果" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_success ? 'success' : 'danger'" size="small">
            {{ row.is_success ? '成功' : '失败' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="error_msg" label="错误信息" min-width="160" show-overflow-tooltip />
      <el-table-column prop="ip" label="IP" width="130" />
      <el-table-column prop="created_at" label="操作时间" width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSearch"
        @current-change="fetchLogs"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import { systemApi } from '@/api/modules/system'
import { formatDateTime } from '@/utils/formatter'
import type { OperationLog } from '@/types/system'

const logList = ref<OperationLog[]>([])
const loading = ref(false)
const dateRange = ref<string[] | null>(null)

const searchForm = reactive({
  module: '',
  is_success: undefined as boolean | undefined
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const fetchLogs = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.page_size
    }
    if (searchForm.module) params.module = searchForm.module
    if (searchForm.is_success !== undefined) params.is_success = searchForm.is_success
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_time = dateRange.value[0]
      params.end_time = dateRange.value[1]
    }

    const res = await systemApi.getOperationLogs(params)
    logList.value = res.items || res.list || []
    pagination.total = res.total || 0
  } catch (error) {
    console.error('获取操作日志失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchLogs()
}

const handleReset = () => {
  searchForm.module = ''
  searchForm.is_success = undefined
  dateRange.value = null
  handleSearch()
}

onMounted(() => {
  fetchLogs()
})
</script>

<style scoped lang="scss">
.operation-log-panel {
  .search-form {
    margin-bottom: 16px;
  }

  .pagination-container {
    margin-top: 16px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
