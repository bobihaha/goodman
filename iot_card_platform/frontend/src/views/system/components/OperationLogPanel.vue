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
          <el-option label="订单" value="orders" />
          <el-option label="余额" value="balance" />
          <el-option label="套餐周期" value="package_period" />
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
      <el-form-item label="操作类型">
        <el-select
          v-model="searchForm.action"
          placeholder="全部"
          clearable
          style="width: 140px"
          @change="handleSearch"
        >
          <el-option label="修改备注" value="update_remark" />
          <el-option label="停机" value="suspend" />
          <el-option label="复机" value="resume" />
          <el-option label="重启" value="restart" />
          <el-option label="划拨子账户" value="transfer" />
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
      <el-table-column label="操作人" width="180">
        <template #default="{ row }">
          <span>{{ row.user_name || row.user_id || '-' }}</span>
          <el-tag v-if="row.original_user_id" size="small" type="warning" class="operator-tag">
            超级登录 #{{ row.original_user_id }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="模块" width="100">
        <template #default="{ row }">{{ formatModule(row.module) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="{ row }">{{ formatAction(row.action) }}</template>
      </el-table-column>
      <el-table-column label="目标" min-width="180">
        <template #default="{ row }">
          <span v-if="row.target_name">{{ formatTargetType(row.target_type) }}: {{ row.target_name }}</span>
          <span v-else-if="row.target_id">{{ formatTargetType(row.target_type) }} #{{ row.target_id }}</span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="操作详情" min-width="300" show-overflow-tooltip>
        <template #default="{ row }">{{ formatDetail(row) }}</template>
      </el-table-column>
      <el-table-column label="结果" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="formatResult(row).type" size="small">
            {{ formatResult(row).label }}
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
  action: '',
  is_success: undefined as boolean | undefined
})

const moduleNames: Record<string, string> = {
  card: '卡片',
  cards: '卡片',
  suspend: '停复机',
  user: '用户',
  pool: '流量池',
  stock: '库存',
  orders: '订单',
  balance: '余额'
}

const actionNames: Record<string, string> = {
  update_remark: '修改备注',
  suspend: '停机',
  resume: '复机',
  restart: '重启',
  transfer: '划拨子账户'
}

const formatModule = (module: string) => moduleNames[module] || module || '-'
const formatAction = (action: string) => actionNames[action] || action || '-'
const formatTargetType = (targetType?: string | null) => targetType === 'card' ? '卡片' : (targetType || '目标')

const formatResult = (row: OperationLog): { label: string; type: 'success' | 'warning' | 'danger' } => {
  if (row.detail) {
    try {
      const detail = JSON.parse(row.detail)
      if (detail.source === 'h5' && detail.status === 'processing') {
        return { label: '处理中', type: 'warning' }
      }
    } catch {
      // 兼容历史纯文本详情。
    }
  }
  return row.is_success
    ? { label: '成功', type: 'success' }
    : { label: '失败', type: 'danger' }
}

const formatDetail = (row: OperationLog) => {
  if (!row.detail) return '-'
  try {
    const detail = JSON.parse(row.detail)
    if (row.action === 'update_remark') {
      return `备注：${detail.old_remark || '无'} → ${detail.new_remark || '无'}`
    }
    if (detail.source === 'h5' && ['suspend', 'resume', 'restart'].includes(row.action)) {
      const statusName: Record<string, string> = {
        processing: '处理中',
        success: '成功',
        failed: '失败'
      }
      const phaseName: Record<string, string> = {
        suspend: '停机阶段',
        resume: '复机阶段',
        resume_pending: '等待复机'
      }
      const actionName = actionNames[row.action] || row.action
      const phase = detail.current_phase ? `，${phaseName[detail.current_phase] || detail.current_phase}` : ''
      return `H5${actionName}：${statusName[detail.status] || detail.status || '处理中'}${phase}`
    }
    if (row.action === 'suspend' || row.action === 'resume') {
      return `${row.action === 'suspend' ? '停机' : '复机'}原因：${detail.reason || '未填写'}`
    }
  } catch {
    return row.detail
  }
  return row.detail
}

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
    if (searchForm.action) params.action = searchForm.action
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
  searchForm.action = ''
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

  .operator-tag {
    margin-left: 6px;
  }
}
</style>
