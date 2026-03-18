<template>
  <div class="card-detail-page">
    <el-page-header @back="goBack" title="返回">
      <template #content>
        <span class="page-title">卡片详情</span>
      </template>
    </el-page-header>

    <div v-loading="loading" class="detail-content">
      <!-- 基本信息 -->
      <el-card class="info-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>基本信息</span>
            <div class="header-actions">
              <el-button type="primary" size="small" @click="showTransferDialog">
                <el-icon><Connection /></el-icon>
                划拨
              </el-button>
              <el-button type="warning" size="small" @click="showRemarkDialog">
                <el-icon><Edit /></el-icon>
                备注
              </el-button>
              <el-button
                v-if="card?.status === 'activated'"
                type="danger"
                size="small"
                @click="handleSuspend"
              >
                <el-icon><CircleClose /></el-icon>
                停机
              </el-button>
              <el-button
                v-if="card?.status === 'suspended'"
                type="success"
                size="small"
                @click="handleResume"
              >
                <el-icon><CircleCheck /></el-icon>
                复机
              </el-button>
            </div>
          </div>
        </template>

        <el-descriptions :column="3" border>
          <el-descriptions-item label="ICCID">
            {{ card?.iccid }}
          </el-descriptions-item>
          <el-descriptions-item label="IMSI">
            {{ card?.imsi || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="号码">
            {{ card?.msisdn || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="运营商">
            {{ card ? CARRIER_MAP[card.carrier] : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag v-if="card" :type="CARD_STATUS_MAP[card.status].type">
              {{ CARD_STATUS_MAP[card.status].label }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="套餐规格">
            {{ card ? `${formatFlow(card.flow_size)}/${PERIOD_TYPE_MAP[card.period_type]}` : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="激活时间">
            {{ formatDateTime(card?.activated_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="沉默期到期">
            <span :class="{ 'text-danger': isExpired(card?.silent_expire_date) }">
              {{ formatDate(card?.silent_expire_date) }}
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="到期时间">
            <span :class="{ 'text-danger': isExpired(card?.expired_at) }">
              {{ formatDateTime(card?.expired_at) }}
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="出库时间">
            {{ formatDateTime(card?.stock_out_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDateTime(card?.created_at) }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 生命周期信息 -->
      <el-card class="info-card" shadow="never">
        <template #header>
          <span>生命周期信息</span>
        </template>

        <el-descriptions :column="3" border>
          <el-descriptions-item label="测试期到期">
            <span :class="{ 'text-danger': isExpired(card?.test_expire_date) }">
              {{ formatDate(card?.test_expire_date) }}
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="停机时间">
            {{ formatDateTime(card?.suspend_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="停机类型">
            {{ card?.suspend_type ? SUSPEND_TYPE_MAP[card.suspend_type] : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="停机原因" :span="3">
            {{ card?.suspend_reason || '-' }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 流量使用情况 -->
      <el-card class="info-card" shadow="never">
        <template #header>
          <span>流量使用情况</span>
        </template>

        <div class="flow-usage-section">
          <div class="flow-chart">
            <el-progress
              type="dashboard"
              :percentage="usagePercent"
              :color="getProgressColor(usagePercent)"
              :width="200"
            >
              <template #default>
                <div class="progress-content">
                  <div class="percentage">{{ usagePercent.toFixed(0) }}%</div>
                  <div class="usage-text">已使用</div>
                </div>
              </template>
            </el-progress>
          </div>

          <div class="flow-details">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="已用流量">
                <span class="flow-value">{{ formatFlow(card?.data_used) }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="总流量">
                <span class="flow-value">{{ formatFlow(card?.data_total) }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="剩余流量">
                <span class="flow-value remaining">
                  {{ formatFlow(Math.max((card?.data_total || 0) - (card?.data_used || 0), 0)) }}
                </span>
              </el-descriptions-item>
              <el-descriptions-item label="使用率">
                <span class="flow-value" :class="{ 'text-danger': usagePercent >= 90 }">
                  {{ usagePercent.toFixed(0) }}%
                </span>
              </el-descriptions-item>
              <el-descriptions-item label="数据同步时间" :span="2">
                {{ formatDateTime(card?.data_sync_at) }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
      </el-card>

      <!-- 流量池信息 -->
      <el-card class="info-card" shadow="never">
        <template #header>
          <span>流量池信息</span>
        </template>

        <el-descriptions :column="2" border>
          <el-descriptions-item label="是否在池中">
            <el-tag v-if="card?.is_pool_member" type="success">在池中</el-tag>
            <el-tag v-else type="info">未入池</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="流量池ID">
            {{ card?.pool_id || '-' }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 备注信息 -->
      <el-card class="info-card" shadow="never">
        <template #header>
          <span>备注信息</span>
        </template>

        <div class="remark-content">
          {{ card?.remark || '暂无备注' }}
        </div>
      </el-card>

      <!-- 划拨记录 -->
      <el-card class="info-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>划拨记录</span>
            <el-button type="text" size="small" @click="fetchTransfers">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </template>

        <el-table
          v-loading="transferLoading"
          :data="transferList"
          stripe
        >
          <el-table-column prop="from_user_id" label="原用户ID" width="120" />
          <el-table-column prop="to_user_id" label="目标用户ID" width="120" />
          <el-table-column prop="remark" label="备注" min-width="200" show-overflow-tooltip />
          <el-table-column prop="created_at" label="划拨时间" width="180">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
        </el-table>

        <div v-if="transferList.length > 0" class="pagination">
          <el-pagination
            v-model:current-page="transferPagination.page"
            v-model:page-size="transferPagination.page_size"
            :total="transferPagination.total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @size-change="fetchTransfers"
            @current-change="fetchTransfers"
          />
        </div>
      </el-card>

      <!-- 历史用量 -->
      <el-card class="info-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>历史用量</span>
            <div>
              <el-date-picker
                v-model="historyDateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                size="small"
                style="margin-right: 10px"
                @change="fetchUsageHistory"
              />
              <el-button type="text" size="small" @click="fetchUsageHistory">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </div>
        </template>

        <div v-loading="historyLoading">
          <el-empty v-if="historyList.length === 0" description="暂无历史数据" />
          <template v-else>
            <div ref="chartRef" style="width: 100%; height: 300px; margin-bottom: 20px"></div>

            <el-table :data="historyList" stripe>
            <el-table-column prop="snapshot_date" label="快照日期" width="120" />
            <el-table-column prop="snapshot_type" label="类型" width="100">
              <template #default="{ row }">
                {{ row.snapshot_type === 'month_end' ? '月末' : '周期末' }}
              </template>
            </el-table-column>
            <el-table-column prop="snapshot_month" label="月份" width="100" />
            <el-table-column prop="data_used" label="已用流量(MB)" width="140" />
            <el-table-column prop="data_total" label="总流量(MB)" width="140" />
            <el-table-column label="使用率" width="120">
              <template #default="{ row }">
                {{ ((row.data_used / row.data_total) * 100).toFixed(2) }}%
              </template>
            </el-table-column>
          </el-table>
          </template>
        </div>
      </el-card>
    </div>

    <!-- 单卡划拨对话框 -->
    <TransferDialog
      v-model="transferVisible"
      :card="card"
      @success="handleTransferSuccess"
    />

    <!-- 单卡备注对话框 -->
    <RemarkDialog
      v-model="remarkVisible"
      :card="card"
      @success="handleRemarkSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Connection,
  Edit,
  CircleClose,
  CircleCheck,
  Refresh
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { cardApi } from '@/api'
import type { Card, UsageHistory } from '@/types/card'
import {
  CARRIER_MAP,
  CARD_STATUS_MAP,
  PERIOD_TYPE_MAP,
  SUSPEND_TYPE_MAP
} from '@/constants/card'
import { formatFlow, formatDate, formatDateTime, isExpired } from '@/utils/formatter'
import TransferDialog from '../list/components/TransferDialog.vue'
import RemarkDialog from '../list/components/RemarkDialog.vue'

const router = useRouter()
const route = useRoute()

// 数据
const loading = ref(false)
const transferLoading = ref(false)
const card = ref<Card | null>(null)
const transferList = ref<any[]>([])

// 对话框显示状态
const transferVisible = ref(false)
const remarkVisible = ref(false)

// 历史用量
const historyLoading = ref(false)
const historyList = ref<UsageHistory[]>([])
const historyDateRange = ref<[Date, Date]>()
const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

// 划拨记录分页
const transferPagination = ref({
  page: 1,
  page_size: 20,
  total: 0
})

// 计算属性
const cardId = computed(() => Number(route.params.id))

const usagePercent = computed(() => {
  if (!card.value || !card.value.data_total) return 0
  const percent = (card.value.data_used / card.value.data_total) * 100
  return Math.min(Math.max(percent, 0), 100)
})

// 获取卡片详情
const fetchCardDetail = async () => {
  loading.value = true
  try {
    card.value = await cardApi.getDetail(cardId.value)
  } catch (error) {
    console.error('获取卡片详情失败:', error)
    ElMessage.error('获取卡片详情失败')
  } finally {
    loading.value = false
  }
}

// 获取划拨记录
const fetchTransfers = async () => {
  transferLoading.value = true
  try {
    const response = await cardApi.getTransfers(
      cardId.value,
      transferPagination.value.page,
      transferPagination.value.page_size
    )
    transferList.value = response?.items || response?.list || []
    transferPagination.value.total = response?.total || 0
  } catch (error) {
    console.error('获取划拨记录失败:', error)
    transferList.value = []
    transferPagination.value.total = 0
  } finally {
    transferLoading.value = false
  }
}

// 获取历史用量
const fetchUsageHistory = async () => {
  historyLoading.value = true
  try {
    const startDate = historyDateRange.value?.[0] ? formatDateToString(historyDateRange.value[0]) : undefined
    const endDate = historyDateRange.value?.[1] ? formatDateToString(historyDateRange.value[1]) : undefined
    const response = await cardApi.getUsageHistory(cardId.value, startDate, endDate)
    historyList.value = Array.isArray(response) ? response : []
    await nextTick()
    renderChart()
  } catch (error) {
    console.error('获取历史用量失败:', error)
    historyList.value = []
  } finally {
    historyLoading.value = false
  }
}

// 渲染图表
const renderChart = () => {
  if (!chartRef.value || historyList.value.length === 0) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
  const dates = historyList.value.map(h => h.snapshot_date).reverse()
  const usages = historyList.value.map(h => h.data_used).reverse()
  chartInstance.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: dates },
    yAxis: { type: 'value', name: '流量(MB)' },
    series: [{ data: usages, type: 'line', smooth: true }]
  })
}

const formatDateToString = (date: Date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// 返回
const goBack = () => {
  router.back()
}

// 显示划拨对话框
const showTransferDialog = () => {
  transferVisible.value = true
}

// 显示备注对话框
const showRemarkDialog = () => {
  remarkVisible.value = true
}

// 停机
const handleSuspend = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要停机该卡片吗？',
      '停机确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await cardApi.batchSuspend({
      card_ids: [cardId.value]
    })

    ElMessage.success('停机成功')
    fetchCardDetail()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('停机失败:', error)
    }
  }
}

// 复机
const handleResume = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要复机该卡片吗？',
      '复机确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await cardApi.batchResume([cardId.value])

    ElMessage.success('复机成功')
    fetchCardDetail()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('复机失败:', error)
    }
  }
}

// 划拨成功回调
const handleTransferSuccess = () => {
  fetchCardDetail()
  fetchTransfers()
}

// 备注成功回调
const handleRemarkSuccess = () => {
  fetchCardDetail()
}

// 获取进度条颜色
const getProgressColor = (percent: number) => {
  if (percent >= 90) return '#F56C6C'
  if (percent >= 80) return '#E6A23C'
  return '#67C23A'
}

// 初始化
onMounted(() => {
  fetchCardDetail()
  fetchTransfers()
  // 默认显示最近30天
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 30)
  historyDateRange.value = [start, end]
  fetchUsageHistory()
})
</script>

<style scoped lang="scss">
.card-detail-page {
  padding: 20px;

  .page-title {
    font-size: 18px;
    font-weight: 600;
    color: #303133;
  }

  .detail-content {
    margin-top: 20px;
  }

  .info-card {
    margin-bottom: 20px;

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .header-actions {
        display: flex;
        gap: 8px;
      }
    }
  }

  .flow-usage-section {
    display: flex;
    gap: 40px;
    align-items: center;

    .flow-chart {
      flex-shrink: 0;

      .progress-content {
        text-align: center;

        .percentage {
          font-size: 32px;
          font-weight: 600;
          color: #303133;
          line-height: 1;
          margin-bottom: 8px;
        }

        .usage-text {
          font-size: 14px;
          color: #909399;
        }
      }
    }

    .flow-details {
      flex: 1;

      .flow-value {
        font-size: 16px;
        font-weight: 600;
        color: #409eff;

        &.remaining {
          color: #67C23A;
        }
      }
    }
  }

  .remark-content {
    padding: 16px;
    background: #f5f7fa;
    border-radius: 4px;
    color: #606266;
    line-height: 1.6;
    min-height: 60px;
  }

  .text-danger {
    color: #F56C6C;
  }

  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>






