<template>
  <div class="pool-detail-container">
    <!-- 返回按钮 -->
    <el-page-header @back="handleBack" style="margin-bottom: 20px">
      <template #content>
        <span class="page-title">{{ poolDetail.name }}</span>
      </template>
      <template #extra>
        <span class="sync-time">最近同步时间：{{ formatDateTime(poolDetail.last_sync_at) }}</span>
      </template>
    </el-page-header>

    <!-- 操作按钮 -->
    <div class="action-buttons">
      <el-button type="primary" @click="handleRecharge">后台补量</el-button>
      <el-button type="success" @click="handleAutoPool">自动续池</el-button>
      <el-button @click="handleEdit">告警设置</el-button>
    </div>

    <!-- 三个圆环图 -->
    <el-row :gutter="20" class="charts-row">
      <!-- 卡片使用情况 -->
      <el-col :span="8">
        <el-card shadow="hover" class="chart-card">
          <div class="chart-title">卡片使用情况</div>
          <div ref="cardChartRef" class="chart-container"></div>
          <div class="chart-info">
            <span class="info-label">总卡量：</span>
            <span class="info-value">{{ poolDetail.card_count }}</span>
          </div>
        </el-card>
      </el-col>

      <!-- 流量使用情况 -->
      <el-col :span="8">
        <el-card shadow="hover" class="chart-card">
          <div class="chart-title">流量使用情况</div>
          <div ref="flowChartRef" class="chart-container"></div>
          <div class="chart-info">
            <div class="info-item">
              <span class="dot" style="background: #409eff"></span>
              <span>已用流量：{{ formatFlowValue(poolDetail.data_used) }}</span>
            </div>
            <div class="info-item">
              <span class="dot" style="background: #67c23a"></span>
              <span>剩余流量：{{ formatFlowValue(poolDetail.data_remaining) }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 流量组成情况 -->
      <el-col :span="8">
        <el-card shadow="hover" class="chart-card">
          <div class="chart-title">流量组成情况</div>
          <div ref="compositionChartRef" class="chart-container"></div>
          <div class="chart-info">
            <div class="info-item">
              <span class="dot" style="background: #409eff"></span>
              <span>套餐流量：{{ formatFlow(poolDetail.package_flow || poolDetail.data_total || 0) }}</span>
            </div>
            <div class="info-item">
              <span class="dot" style="background: #ffa500"></span>
              <span>叠加流量包：{{ formatFlow(poolDetail.addon_flow || 0) }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- ICCID搜索和操作 -->
    <el-card class="search-card" shadow="never">
      <el-row :gutter="16">
        <el-col :span="12">
          <el-input
            v-model="iccidKeyword"
            placeholder="请输入ICCID"
            clearable
            @keyup.enter="handleSearchIccid"
          >
            <template #append>
              <el-button :icon="Search" @click="handleSearchIccid" />
            </template>
          </el-input>
        </el-col>
        <el-col :span="12" style="text-align: right">
          <el-button @click="handleBatchCloseNetwork" :disabled="selectedCardIds.length === 0">
            关闭网络
          </el-button>
          <el-button type="primary" @click="handleBatchOpenNetwork" :disabled="selectedCardIds.length === 0">
            打开网络
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 卡片列表 -->
    <el-card class="table-card" shadow="never">
      <el-table
        v-loading="cardsLoading"
        :data="cardList"
        border
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="iccid" label="ICCID" width="200" />
        <el-table-column prop="msisdn" label="电话号码" width="130" />
        <el-table-column prop="imsi" label="IMSI" width="150" />
        <el-table-column prop="network_status" label="网络状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.network_status === 'open' ? 'success' : 'info'">
              {{ row.network_status === 'open' ? '开启' : '关闭' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="卡状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusMeta(row.status).type">
              {{ getStatusMeta(row.status).label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="套餐总量" width="100">
          <template #default="{ row }">
            {{ formatFlow(row.data_total) }}
          </template>
        </el-table-column>
        <el-table-column prop="data_used" label="本月已用" width="120">
          <template #default="{ row }">
            {{ formatFlowValue(row.data_used) }}
          </template>
        </el-table-column>
        <el-table-column prop="data_sync_at" label="最近同步时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.data_sync_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="expired_at" label="过期时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.expired_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button
              type="text"
              size="small"
              :disabled="row.status !== 'suspended'"
              @click="handleRowResume(row)"
            >
              复机
            </el-button>
            <el-button
              v-if="isSuperAdmin"
              type="text"
              size="small"
              :disabled="row.status !== 'suspended'"
              @click="handleRowForceResume(row)"
            >
              强制复机
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchCards"
        @current-change="fetchCards"
      />
    </el-card>

    <!-- 补量日志 -->
    <el-card class="table-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>补量日志</span>
          <el-button type="text" size="small" @click="fetchFlowLogs">
            刷新
          </el-button>
        </div>
      </template>

      <el-table v-loading="flowLogLoading" :data="flowLogs" stripe>
        <el-table-column prop="user_name" label="操作人" width="140" />
        <el-table-column prop="detail" label="操作详情" min-width="360" show-overflow-tooltip />
        <el-table-column label="结果" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_success ? 'success' : 'danger'">
              {{ row.is_success ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 流量池表单对话框 -->
    <PoolFormDialog
      v-model="formDialogVisible"
      :pool="poolDetail"
      @success="fetchDetail"
    />

    <!-- 充值加油包对话框 -->
    <RechargeDialog
      v-model="rechargeDialogVisible"
      :pool="poolDetail"
      @success="handleRefresh"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import {
  getPoolDetail,
  getPoolCards
} from '@/api/modules/pool'
import { cardApi } from '@/api'
import { systemApi } from '@/api/modules/system'
import { useAuthStore } from '@/stores/modules/auth'
import { formatDate, formatDateTime, formatFlow, formatFlowValue } from '@/utils/formatter'
import { CARD_STATUS_MAP } from '@/constants/card'
import type { PoolDetail } from '@/types/pool'
import type { OperationLog } from '@/types/system'
import PoolFormDialog from '../list/components/PoolFormDialog.vue'
import RechargeDialog from '../list/components/RechargeDialog.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const poolId = Number(route.params.id)

// 流量池详情
const poolDetail = ref<PoolDetail>({} as PoolDetail)

// 卡片列表
const cardList = ref<any[]>([])
const cardsLoading = ref(false)
const selectedCardIds = ref<number[]>([])
const iccidKeyword = ref('')
const flowLogLoading = ref(false)
const flowLogs = ref<OperationLog[]>([])

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 图表实例
const cardChartRef = ref<HTMLElement>()
const flowChartRef = ref<HTMLElement>()
const compositionChartRef = ref<HTMLElement>()
let cardChart: ECharts | null = null
let flowChart: ECharts | null = null
let compositionChart: ECharts | null = null

// 对话框
const formDialogVisible = ref(false)
const rechargeDialogVisible = ref(false)
const getStatusMeta = (status: any) => CARD_STATUS_MAP[status as keyof typeof CARD_STATUS_MAP] || CARD_STATUS_MAP.stock
const isSuperAdmin = computed(() => authStore.userInfo?.user_level === 1)

/**
 * 获取流量池详情
 */
const fetchDetail = async () => {
  try {
    const data: any = await getPoolDetail(poolId)
    poolDetail.value = data
    await nextTick()
    renderCharts()
  } catch (error) {
    console.error('获取流量池详情失败:', error)
    ElMessage.error('获取流量池详情失败')
  }
}

/**
 * 获取池内卡片
 */
const fetchCards = async () => {
  cardsLoading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.page_size
    }
    if (iccidKeyword.value) {
      params.iccid = iccidKeyword.value
    }
    const response: any = await getPoolCards(poolId, params)
    cardList.value = response.items || response.list || []
    pagination.total = response.total || 0
  } catch (error) {
    console.error('获取卡片列表失败:', error)
    ElMessage.error('获取卡片列表失败')
  } finally {
    cardsLoading.value = false
  }
}

/**
 * 获取补量日志
 */
const fetchFlowLogs = async () => {
  flowLogLoading.value = true
  try {
    const res: any = await systemApi.getOperationLogs({
      module: 'pools',
      action: 'add_flow',
      target_type: 'pool',
      target_id: poolId,
      page: 1,
      page_size: 10
    })
    flowLogs.value = res.items || []
  } catch (error) {
    console.error('获取流量池补量日志失败:', error)
    flowLogs.value = []
  } finally {
    flowLogLoading.value = false
  }
}

/**
 * 渲染图表
 */
const renderCharts = () => {
  renderCardChart()
  renderFlowChart()
  renderCompositionChart()
}

/**
 * 渲染卡片使用情况图表
 */
const renderCardChart = () => {
  if (!cardChartRef.value) return

  if (!cardChart) {
    cardChart = echarts.init(cardChartRef.value)
  }

  const stats = poolDetail.value.card_stats || {
    activated: 0,
    suspended: 0,
    stock: 0,
    testing: 0,
    cancelled: 0
  }

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    color: ['#FFA500', '#909399', '#E6E6E6', '#FFD700', '#CCCCCC'],
    series: [
      {
        type: 'pie',
        radius: ['50%', '70%'],
        avoidLabelOverlap: false,
        label: {
          show: false
        },
        labelLine: {
          show: false
        },
        data: [
          { value: stats.activated, name: '已激活' },
          { value: stats.suspended, name: '已停卡' },
          { value: stats.stock, name: '库存' },
          { value: stats.testing, name: '测试期' },
          { value: stats.cancelled, name: '已销卡' }
        ]
      }
    ]
  }

  cardChart.setOption(option)
}

/**
 * 渲染流量使用情况图表
 */
const renderFlowChart = () => {
  if (!flowChartRef.value) return

  if (!flowChart) {
    flowChart = echarts.init(flowChartRef.value)
  }

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        return `${params.name}: ${formatFlow(params.value)} (${params.percent}%)`
      }
    },
    color: ['#409EFF', '#67C23A'],
    series: [
      {
        type: 'pie',
        radius: ['50%', '70%'],
        avoidLabelOverlap: false,
        label: {
          show: false
        },
        labelLine: {
          show: false
        },
        data: [
          { value: poolDetail.value.data_used, name: '已用流量' },
          { value: poolDetail.value.data_remaining, name: '剩余流量' }
        ]
      }
    ]
  }

  flowChart.setOption(option)
}

/**
 * 渲染流量组成情况图表
 */
const renderCompositionChart = () => {
  if (!compositionChartRef.value) return

  if (!compositionChart) {
    compositionChart = echarts.init(compositionChartRef.value)
  }

  const packageFlow = poolDetail.value.package_flow || poolDetail.value.data_total
  const addonFlow = poolDetail.value.addon_flow || 0

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        return `${params.name}: ${formatFlow(params.value)} (${params.percent}%)`
      }
    },
    color: ['#409EFF', '#FFA500'],
    series: [
      {
        type: 'pie',
        radius: ['50%', '70%'],
        avoidLabelOverlap: false,
        label: {
          show: false
        },
        labelLine: {
          show: false
        },
        data: [
          { value: packageFlow, name: '套餐流量' },
          { value: addonFlow, name: '叠加流量包' }
        ]
      }
    ]
  }

  compositionChart.setOption(option)
}

/**
 * 返回
 */
const handleBack = () => {
  router.back()
}

/**
 * 编辑
 */
const handleEdit = () => {
  formDialogVisible.value = true
}

/**
 * 后台补量
 */
const handleRecharge = () => {
  rechargeDialogVisible.value = true
}

/**
 * 自动续池
 */
const handleAutoPool = () => {
  ElMessage.info('自动续池功能开发中')
}

/**
 * 搜索ICCID
 */
const handleSearchIccid = () => {
  pagination.page = 1
  fetchCards()
}

/**
 * 选择变化
 */
const handleSelectionChange = (selection: any[]) => {
  selectedCardIds.value = selection.map(c => c.id)
}

/**
 * 单行复机
 */
const handleRowResume = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要复机卡片 ${row.iccid} 吗？`,
      '复机确认',
      {
        confirmButtonText: '确定复机',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const result = await cardApi.batchResumeByIccids({
      iccids: [row.iccid]
    })

    if (result.success > 0) {
      ElMessage.success('复机成功')
      handleRefresh()
    } else {
      const firstError = result.failed_list?.[0]?.error || '复机失败'
      ElMessage.error(firstError.includes('超级管理员手动停卡')
        ? '该卡由超级管理员手动停卡，请联系管理员处理'
        : firstError)
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('池内单卡复机失败:', error)
    }
  }
}

/**
 * 单行强制复机
 */
const handleRowForceResume = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要强制复机卡片 ${row.iccid} 吗？该操作会绕过人工停卡与超限限制。`,
      '强制复机确认',
      {
        confirmButtonText: '确认强制复机',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const result = await cardApi.batchForceResumeByIccids({
      iccids: [row.iccid]
    })

    if (result.success > 0) {
      ElMessage.success('强制复机成功')
      handleRefresh()
    } else {
      ElMessage.error(result.failed_list?.[0]?.error || '强制复机失败')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('池内单卡强制复机失败:', error)
    }
  }
}

/**
 * 批量关闭网络
 */
const handleBatchCloseNetwork = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要关闭 ${selectedCardIds.value.length} 张卡片的网络吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    ElMessage.success('关闭网络成功')
    fetchCards()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('关闭网络失败:', error)
      ElMessage.error('关闭网络失败')
    }
  }
}

/**
 * 批量打开网络
 */
const handleBatchOpenNetwork = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要打开 ${selectedCardIds.value.length} 张卡片的网络吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    ElMessage.success('打开网络成功')
    fetchCards()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('打开网络失败:', error)
      ElMessage.error('打开网络失败')
    }
  }
}

/**
 * 刷新数据
 */
const handleRefresh = () => {
  fetchDetail()
  fetchCards()
  fetchFlowLogs()
}

onMounted(() => {
  fetchDetail()
  fetchCards()
  fetchFlowLogs()
})
</script>

<style scoped lang="scss">
.pool-detail-container {
  padding: 20px;

  .page-title {
    font-size: 20px;
    font-weight: bold;
  }

  .sync-time {
    font-size: 14px;
    color: #909399;
  }

  .action-buttons {
    margin-bottom: 20px;
    display: flex;
    gap: 12px;
  }

  .charts-row {
    margin-bottom: 20px;

    .chart-card {
      .chart-title {
        text-align: center;
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 16px;
        color: #303133;
      }

      .chart-container {
        width: 100%;
        height: 200px;
      }

      .chart-info {
        margin-top: 16px;
        text-align: center;

        .info-label {
          color: #606266;
          font-size: 14px;
        }

        .info-value {
          color: #303133;
          font-size: 18px;
          font-weight: 600;
        }

        .info-item {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          margin-bottom: 8px;
          font-size: 14px;
          color: #606266;

          .dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
          }

          &:last-child {
            margin-bottom: 0;
          }
        }
      }
    }
  }

  .search-card {
    margin-bottom: 20px;
  }

  .table-card {
    :deep(.el-pagination) {
      margin-top: 16px;
      justify-content: flex-end;
    }
  }
}
</style>
