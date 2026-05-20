<template>
  <div class="supplier-pool-page">
    <div class="page-header">
      <div>
        <h2>供应商流量池管理</h2>
        <p>同步供应商账户侧流量池用量，查看本月预估和历史趋势。</p>
      </div>
      <el-button type="primary" :loading="syncing" @click="handleSync">同步供应商流量池</el-button>
    </div>

    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="query" class="filter-form">
        <el-form-item label="供应商名称">
          <el-input v-model="query.supplier_name" clearable placeholder="请输入供应商名称" />
        </el-form-item>
        <el-form-item label="运营商">
          <el-select v-model="query.carrier" clearable placeholder="全部" style="width: 140px">
            <el-option label="移动" value="cmcc" />
            <el-option label="联通" value="cucc" />
            <el-option label="电信" value="ctcc" />
          </el-select>
        </el-form-item>
        <el-form-item label="流量池规格">
          <el-input-number
            v-model="query.pool_specification"
            :min="-1"
            :controls="false"
            placeholder="MB"
            style="width: 150px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadList">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-table v-loading="loading" :data="items" border @sort-change="handleSortChange">
      <el-table-column prop="supplier_name" label="供应商" min-width="130" />
      <el-table-column label="流量池" min-width="180">
        <template #default="{ row }">
          <div class="pool-name">{{ row.supplier_pool_name || row.supplier_pool_code }}</div>
          <div class="pool-code">{{ row.supplier_pool_code }}</div>
        </template>
      </el-table-column>
      <el-table-column label="运营商" width="90">
        <template #default="{ row }">{{ carrierLabel(row.carrier) }}</template>
      </el-table-column>
      <el-table-column label="规格" width="110" prop="pool_specification" sortable="custom">
        <template #default="{ row }">{{ formatSpec(row.pool_specification) }}</template>
      </el-table-column>
      <el-table-column label="已用/总量" min-width="220" prop="used_flow" sortable="custom">
        <template #default="{ row }">
          <div class="usage-line">
            <span>{{ formatFlow(row.used_flow) }}</span>
            <span>/ {{ formatFlow(row.total_flow) }}</span>
          </div>
          <el-progress
            :percentage="Math.min(Number(row.usage_percent || 0), 100)"
            :color="progressColor(row)"
            :stroke-width="8"
          />
        </template>
      </el-table-column>
      <el-table-column label="使用率" width="110" prop="usage_percent" sortable="custom">
        <template #default="{ row }">{{ Number(row.usage_percent || 0).toFixed(2) }}%</template>
      </el-table-column>
      <el-table-column label="剩余" width="120" prop="remaining_flow" sortable="custom">
        <template #default="{ row }">{{ formatFlow(row.remaining_flow) }}</template>
      </el-table-column>
      <el-table-column label="本月预估" min-width="160" prop="estimated_monthly_used_flow" sortable="custom">
        <template #default="{ row }">
          <div>{{ formatNullableFlow(row.estimated_monthly_used_flow) }}</div>
          <div class="muted">月底剩余 {{ formatNullableFlow(row.estimated_month_end_remaining_flow) }}</div>
        </template>
      </el-table-column>
      <el-table-column label="卡数" width="140">
        <template #default="{ row }">
          <div>总 {{ row.total_card_count || 0 }}</div>
          <div class="muted">激活 {{ row.active_card_count || 0 }}</div>
        </template>
      </el-table-column>
      <el-table-column label="邮件提醒" min-width="190">
        <template #default="{ row }">
          <div>阈值：{{ formatAlertThresholds(row.alert_thresholds, row.alert_threshold) }}</div>
          <div class="muted ellipsis">{{ row.alert_emails || '-' }}</div>
        </template>
      </el-table-column>
      <el-table-column label="同步时间" width="170">
        <template #default="{ row }">{{ row.last_sync_at || '-' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="170" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" link @click="openDetail(row)">详情</el-button>
          <el-button size="small" @click="openAlertDialog(row)">提醒设置</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="query.page"
        v-model:page-size="query.page_size"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @size-change="loadList"
        @current-change="loadList"
      />
    </div>

    <el-dialog v-model="alertDialogVisible" title="阈值邮件提醒" width="500px">
      <el-form label-width="96px">
        <el-form-item label="提醒阈值">
          <el-select
            v-model="alertForm.alert_thresholds"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="默认 60、80、100"
            style="width: 260px"
          >
            <el-option label="60%" :value="60" />
            <el-option label="80%" :value="80" />
            <el-option label="100%" :value="100" />
          </el-select>
        </el-form-item>
        <el-form-item label="提醒邮箱">
          <el-input
            v-model="alertForm.alert_emails"
            type="textarea"
            :rows="3"
            placeholder="多个邮箱用逗号分隔；为空则不发送"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="alertDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingAlert" @click="saveAlert">保存</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="detailVisible" title="流量池详情" size="840px" @closed="disposeHistoryChart">
      <div v-loading="detailLoading" class="detail-panel">
        <el-descriptions v-if="detailPool" :column="2" border>
          <el-descriptions-item label="供应商">{{ detailPool.supplier_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="运营商">{{ carrierLabel(detailPool.carrier) }}</el-descriptions-item>
          <el-descriptions-item label="流量池">{{ detailPool.supplier_pool_name || detailPool.supplier_pool_code }}</el-descriptions-item>
          <el-descriptions-item label="规格">{{ formatSpec(detailPool.pool_specification) }}</el-descriptions-item>
          <el-descriptions-item label="当前用量">{{ formatFlow(detailPool.used_flow) }} / {{ formatFlow(detailPool.total_flow) }}</el-descriptions-item>
          <el-descriptions-item label="当前使用率">{{ Number(detailPool.usage_percent || 0).toFixed(2) }}%</el-descriptions-item>
          <el-descriptions-item label="本月预估">{{ formatNullableFlow(detailPool.estimated_monthly_used_flow) }}</el-descriptions-item>
          <el-descriptions-item label="预计月底剩余">{{ formatNullableFlow(detailPool.estimated_month_end_remaining_flow) }}</el-descriptions-item>
          <el-descriptions-item label="卡数">总 {{ detailPool.total_card_count || 0 }} / 激活 {{ detailPool.active_card_count || 0 }}</el-descriptions-item>
          <el-descriptions-item label="同步时间">{{ detailPool.last_sync_at || '-' }}</el-descriptions-item>
        </el-descriptions>

        <div class="detail-section">
          <div class="section-header">
            <div class="section-title">历史月份使用率</div>
            <el-button size="small" :loading="exportingHistory" @click="handleExportHistory">导出历史用量</el-button>
          </div>
          <div ref="historyChartRef" class="history-chart"></div>
        </div>

        <el-table :data="histories" border empty-text="暂无历史月份数据">
          <el-table-column prop="record_month" label="月份" width="100" sortable />
          <el-table-column label="使用率" width="110" prop="usage_percent" sortable>
            <template #default="{ row }">{{ Number(row.usage_percent || 0).toFixed(2) }}%</template>
          </el-table-column>
          <el-table-column label="已用/总量" min-width="180" prop="used_flow" sortable>
            <template #default="{ row }">{{ formatFlow(row.used_flow) }} / {{ formatFlow(row.total_flow) }}</template>
          </el-table-column>
          <el-table-column label="剩余" width="120" prop="remaining_flow" sortable>
            <template #default="{ row }">{{ formatFlow(row.remaining_flow) }}</template>
          </el-table-column>
          <el-table-column label="本月预估" min-width="150" prop="estimated_monthly_used_flow" sortable>
            <template #default="{ row }">{{ formatNullableFlow(row.estimated_monthly_used_flow) }}</template>
          </el-table-column>
          <el-table-column label="同步时间" min-width="170">
            <template #default="{ row }">{{ row.sync_at || '-' }}</template>
          </el-table-column>
        </el-table>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import * as XLSX from 'xlsx'
import {
  exportSupplierTrafficPoolHistories,
  getSupplierTrafficPoolDetail,
  getSupplierTrafficPools,
  syncSupplierTrafficPools,
  updateSupplierTrafficPoolAlert
} from '@/api/modules/supplierPool'
import type { SupplierTrafficPool, SupplierTrafficPoolHistory } from '@/types/supplierPool'

const loading = ref(false)
const syncing = ref(false)
const savingAlert = ref(false)
const detailLoading = ref(false)
const exportingHistory = ref(false)
const items = ref<SupplierTrafficPool[]>([])
const total = ref(0)
const alertDialogVisible = ref(false)
const detailVisible = ref(false)
const currentPool = ref<SupplierTrafficPool | null>(null)
const detailPool = ref<SupplierTrafficPool | null>(null)
const histories = ref<SupplierTrafficPoolHistory[]>([])
const historyChartRef = ref<HTMLElement>()
let historyChart: ECharts | null = null

const query = reactive({
  supplier_name: '',
  carrier: '',
  pool_specification: undefined as number | undefined,
  order_by: 'usage_percent',
  order_dir: 'desc',
  page: 1,
  page_size: 20
})

const alertForm = reactive({
  alert_thresholds: [60, 80, 100] as Array<number | string>,
  alert_emails: ''
})

const loadList = async () => {
  loading.value = true
  try {
    const params: Record<string, string | number | undefined> = { ...query }
    if (!params.supplier_name) delete params.supplier_name
    if (!params.carrier) delete params.carrier
    if (params.pool_specification === undefined || params.pool_specification === null) delete params.pool_specification
    const response = await getSupplierTrafficPools(params)
    items.value = response.items || []
    total.value = response.total || 0
  } finally {
    loading.value = false
  }
}

const handleReset = () => {
  query.supplier_name = ''
  query.carrier = ''
  query.pool_specification = undefined
  query.order_by = 'usage_percent'
  query.order_dir = 'desc'
  query.page = 1
  loadList()
}

const handleSync = async () => {
  syncing.value = true
  try {
    await syncSupplierTrafficPools()
    ElMessage.success('供应商流量池同步完成')
    await loadList()
  } finally {
    syncing.value = false
  }
}

const openAlertDialog = (pool: SupplierTrafficPool) => {
  currentPool.value = pool
  alertForm.alert_thresholds = parseAlertThresholds(pool.alert_thresholds, pool.alert_threshold)
  alertForm.alert_emails = pool.alert_emails || ''
  alertDialogVisible.value = true
}

const saveAlert = async () => {
  if (!currentPool.value) return
  savingAlert.value = true
  try {
    await updateSupplierTrafficPoolAlert(currentPool.value.id, {
      alert_thresholds: normalizeAlertThresholds(alertForm.alert_thresholds),
      alert_emails: alertForm.alert_emails
    })
    ElMessage.success('提醒配置已保存')
    alertDialogVisible.value = false
    await loadList()
  } finally {
    savingAlert.value = false
  }
}

const handleSortChange = ({ prop, order }: { prop?: string; order?: 'ascending' | 'descending' | null }) => {
  const sortableFields = [
    'usage_percent',
    'pool_specification',
    'used_flow',
    'total_flow',
    'remaining_flow',
    'estimated_monthly_used_flow',
    'estimated_month_end_remaining_flow'
  ]
  if (prop && sortableFields.includes(prop)) {
    query.order_by = prop
    query.order_dir = order === 'ascending' ? 'asc' : 'desc'
  } else {
    query.order_by = 'usage_percent'
    query.order_dir = 'desc'
  }
  query.page = 1
  loadList()
}

const openDetail = async (pool: SupplierTrafficPool) => {
  detailVisible.value = true
  detailPool.value = pool
  histories.value = []
  detailLoading.value = true
  try {
    const response = await getSupplierTrafficPoolDetail(pool.id, 12)
    detailPool.value = response.pool
    histories.value = response.histories || []
    await nextTick()
    renderHistoryChart()
  } finally {
    detailLoading.value = false
  }
}

const handleExportHistory = async () => {
  if (!detailPool.value) return
  exportingHistory.value = true
  try {
    const rows = await exportSupplierTrafficPoolHistories(detailPool.value.id, 36)
    if (!rows.length) {
      ElMessage.warning('暂无历史用量可导出')
      return
    }
    const ws = XLSX.utils.json_to_sheet(rows)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, '历史用量')
    const poolName = detailPool.value.supplier_pool_name || detailPool.value.supplier_pool_code || '流量池'
    XLSX.writeFile(wb, `${sanitizeFilename(poolName)}_历史用量_${new Date().getTime()}.xlsx`)
    ElMessage.success('导出成功')
  } finally {
    exportingHistory.value = false
  }
}

const renderHistoryChart = () => {
  if (!historyChartRef.value) return
  if (!historyChart) historyChart = echarts.init(historyChartRef.value)
  const months = histories.value.map(item => item.record_month)
  const usage = histories.value.map(item => Number(item.usage_percent || 0))
  historyChart.setOption({
    grid: { left: 42, right: 20, top: 28, bottom: 34 },
    tooltip: { trigger: 'axis', valueFormatter: (value: number) => `${Number(value || 0).toFixed(2)}%` },
    xAxis: { type: 'category', data: months, boundaryGap: false },
    yAxis: { type: 'value', min: 0, max: 100, axisLabel: { formatter: '{value}%' } },
    series: [
      {
        name: '使用率',
        type: 'line',
        data: usage,
        smooth: true,
        symbolSize: 7,
        areaStyle: { opacity: 0.08 },
        lineStyle: { width: 3 },
        itemStyle: { color: '#409eff' }
      }
    ]
  })
}

const disposeHistoryChart = () => {
  historyChart?.dispose()
  historyChart = null
}

const carrierLabel = (carrier?: string) => {
  const map: Record<string, string> = { cmcc: '移动', cucc: '联通', ctcc: '电信' }
  return carrier ? (map[carrier] || carrier) : '-'
}

const formatSpec = (value?: number) => {
  if (value === undefined || value === null) return '-'
  if (value === -1) return '全套餐'
  return formatFlow(value)
}

const formatFlow = (value?: number) => {
  const flow = Number(value || 0)
  const sign = flow < 0 ? '-' : ''
  const absolute = Math.abs(flow)
  if (absolute >= 1024) return `${sign}${(absolute / 1024).toFixed(2)} GB`
  return `${flow.toFixed(2)} MB`
}

const formatNullableFlow = (value?: number | null) => {
  if (value === undefined || value === null || Number.isNaN(Number(value))) return '-'
  return formatFlow(Number(value))
}

const sanitizeFilename = (value: string) => {
  return value.replace(/[\\/:*?"<>|]/g, '_')
}

const parseAlertThresholds = (value?: string, legacyValue?: number) => {
  const source = value || (legacyValue !== undefined && legacyValue !== null ? String(legacyValue) : '60,80,100')
  return source
    .split(',')
    .map(item => Number(item.trim()))
    .filter(item => Number.isFinite(item) && item >= 0 && item <= 100)
}

const normalizeAlertThresholds = (values: Array<number | string>) => {
  return Array.from(
    new Set(
      values
        .map(item => Number(item))
        .filter(item => Number.isFinite(item) && item >= 0 && item <= 100)
    )
  ).sort((a, b) => a - b)
}

const formatAlertThresholds = (value?: string, legacyValue?: number) => {
  const thresholds = parseAlertThresholds(value, legacyValue)
  return thresholds.length ? thresholds.map(item => `${item}%`).join(' / ') : '-'
}

const progressColor = (row: SupplierTrafficPool) => {
  const thresholds = parseAlertThresholds(row.alert_thresholds, row.alert_threshold)
  const firstThreshold = thresholds[0]
  if (firstThreshold !== undefined && row.usage_percent >= firstThreshold) {
    return '#e6a23c'
  }
  if (row.usage_percent >= 90) return '#f56c6c'
  if (row.usage_percent >= 75) return '#e6a23c'
  return '#409eff'
}

onMounted(loadList)
onBeforeUnmount(disposeHistoryChart)
</script>

<style scoped lang="scss">
.supplier-pool-page {
  padding: 20px;

  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;

    h2 {
      margin: 0 0 6px;
      font-size: 22px;
      color: #303133;
    }

    p {
      margin: 0;
      color: #606266;
      font-size: 14px;
    }
  }

  .filter-card {
    margin-bottom: 16px;
  }

  .filter-form {
    display: flex;
    flex-wrap: wrap;
    gap: 0 8px;
  }

  .pool-name {
    font-weight: 600;
    color: #303133;
  }

  .pool-code,
  .muted {
    color: #909399;
    font-size: 12px;
  }

  .usage-line {
    display: flex;
    gap: 4px;
    margin-bottom: 6px;
    color: #303133;
  }

  .ellipsis {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .pagination {
    display: flex;
    justify-content: flex-end;
    margin-top: 16px;
  }

  .suffix {
    margin-left: 8px;
    color: #606266;
  }

  .detail-panel {
    min-height: 360px;
  }

  .detail-section {
    margin: 18px 0 12px;
  }

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
  }

  .section-title {
    font-size: 15px;
    font-weight: 600;
    color: #303133;
  }

  .history-chart {
    width: 100%;
    height: 260px;
  }
}
</style>
