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
              <el-tooltip
                :disabled="!card || card.card_type === 'single'"
                content="流量池卡请在流量池维度补量"
                placement="top"
              >
                <span>
                  <el-button
                    type="warning"
                    size="small"
                    :disabled="!card || card.card_type !== 'single'"
                    @click="handleAddFlow"
                  >
                    <el-icon><Plus /></el-icon>
                    补量
                  </el-button>
                </span>
              </el-tooltip>
              <el-button
                type="primary"
                size="small"
                :disabled="!card"
                @click="handleRenew"
              >
                <el-icon><Refresh /></el-icon>
                续费
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
                type="success"
                size="small"
                :disabled="!card || card.status !== 'suspended'"
                @click="handleResume"
              >
                <el-icon><CircleCheck /></el-icon>
                复机
              </el-button>
              <el-button
                type="primary"
                size="small"
                :disabled="!card || !['activated', 'testing', 'silent', 'suspended'].includes(card.status)"
                @click="handleRestart"
              >
                <el-icon><Refresh /></el-icon>
                重启
              </el-button>
              <el-button
                v-if="isSuperAdmin"
                type="warning"
                size="small"
                :disabled="!card || card.status !== 'suspended'"
                @click="handleForceResume"
              >
                <el-icon><CircleCheck /></el-icon>
                强制复机
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
          <el-descriptions-item label="机卡分离检测">
            <div class="device-separation-cell">
              <span :class="getDeviceSeparationClass()">
                {{ getDeviceSeparationText() }}
              </span>
              <el-button
                type="primary"
                size="small"
                plain
                :loading="deviceSeparationChecking"
                :disabled="!card?.iccid"
                @click="handleDeviceSeparationCheck"
              >
                检测
              </el-button>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="套餐规格">
            {{ card ? `${formatFlow(card.flow_size)}/${PERIOD_TYPE_MAP[card.period_type]}` : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="激活时间">
            {{ formatDate(card?.activated_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="沉默期到期">
            <span :class="{ 'text-danger': isExpired(card?.silent_expire_date) }">
              {{ formatDate(card?.silent_expire_date) }}
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="到期时间">
            <span :class="{ 'text-danger': isExpired(card?.expired_at) }">
              {{ formatDate(card?.expired_at) }}
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="出库单号">
            {{ card?.stock_out_no || card?.batch_id || '-' }}
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
              :percentage="Math.min(usagePercent, 100)"
              :color="getProgressColor(usagePercent)"
              :width="200"
            >
              <template #default>
                <div class="progress-content">
                  <div class="percentage">{{ usagePercent.toFixed(2) }}%</div>
                  <div class="usage-text">已使用</div>
                </div>
              </template>
            </el-progress>
          </div>

          <div class="flow-details">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="已用流量">
                <span class="flow-value">{{ formatFlowValue(card?.data_used) }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="总流量">
                <span class="flow-value">{{ formatFlowValue(card?.data_total) }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="剩余流量">
                <span class="flow-value remaining">
                  {{ formatFlowValue(Math.max((card?.data_total || 0) - (card?.data_used || 0), 0)) }}
                </span>
              </el-descriptions-item>
              <el-descriptions-item label="使用率">
                <span class="flow-value" :class="{ 'text-danger': usagePercent >= 90 }">
                  {{ usagePercent.toFixed(2) }}%
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

      <!-- 补量日志 -->
      <el-card class="info-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>补量日志</span>
            <el-button type="text" size="small" @click="fetchFlowLogs">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </template>

        <el-table v-loading="flowLogLoading" :data="flowLogs" stripe>
          <el-table-column prop="user_name" label="操作人" width="140" />
          <el-table-column prop="detail" label="操作详情" min-width="320" show-overflow-tooltip />
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
          <el-table-column label="原用户" min-width="160">
            <template #default="{ row }">
              {{ row.from_user_name || row.from_user_id || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="目标用户" min-width="160">
            <template #default="{ row }">
              {{ row.to_user_name || row.to_user_id || '-' }}
            </template>
          </el-table-column>
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
            <el-table-column prop="snapshot_date" label="日期" width="120">
              <template #default="{ row }">
                {{ formatDate(row.snapshot_date) }}
              </template>
            </el-table-column>
            <el-table-column prop="daily_used" label="日用量(MB)" width="140" />
            <el-table-column prop="data_used" label="累计已用(MB)" width="140" />
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

    <SingleAddFlowDialog
      v-model="singleAddFlowVisible"
      :card="card"
      @success="handleAddFlowSuccess"
    />

    <SingleRenewDialog
      v-model="singleRenewVisible"
      :card="card"
      @success="handleRenewSuccess"
    />

    <el-dialog
      v-model="actionDialogVisible"
      :title="actionDialogTitle"
      width="300px"
      :close-on-click-modal="false"
      :close-on-press-escape="!actionDialogProcessing"
      :show-close="!actionDialogProcessing"
      :before-close="handleActionDialogClose"
    >
      <div class="action-dialog">
        <el-icon
          class="action-dialog__icon"
          :class="{
            'is-spinning': actionDialogProcessing,
            'is-success': actionDialogState === 'success',
            'is-danger': actionDialogState === 'failed'
          }"
        >
          <RefreshRight v-if="actionDialogProcessing" />
          <CircleCheckFilled v-else-if="actionDialogState === 'success'" />
          <WarningFilled v-else />
        </el-icon>
        <div class="action-dialog__message">{{ actionDialogMessage }}</div>
      </div>
      <template #footer>
        <el-button v-if="!actionDialogProcessing" type="primary" @click="actionDialogVisible = false">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Connection,
  Edit,
  Plus,
  CircleClose,
  CircleCheck,
  Refresh,
  RefreshRight,
  CircleCheckFilled,
  WarningFilled
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { cardApi } from '@/api'
import { systemApi } from '@/api/modules/system'
import { useAuthStore } from '@/stores/modules/auth'
import type { Card, UsageHistory } from '@/types/card'
import type { OperationLog } from '@/types/system'
import {
  CARRIER_MAP,
  CARD_STATUS_MAP,
  PERIOD_TYPE_MAP,
  SUSPEND_TYPE_MAP
} from '@/constants/card'
import { formatFlow, formatFlowValue, formatDate, formatDateTime, isExpired } from '@/utils/formatter'
import TransferDialog from '../list/components/TransferDialog.vue'
import RemarkDialog from '../list/components/RemarkDialog.vue'
import SingleAddFlowDialog from '../list/components/SingleAddFlowDialog.vue'
import SingleRenewDialog from '../list/components/SingleRenewDialog.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// 数据
const loading = ref(false)
const transferLoading = ref(false)
const card = ref<Card | null>(null)
const transferList = ref<any[]>([])
const deviceSeparationChecking = ref(false)
const deviceSeparationDisplayState = ref<'idle' | 'pending' | 'detected' | 'clear'>('idle')
let deviceSeparationStateTimer: ReturnType<typeof setTimeout> | null = null

// 对话框显示状态
const transferVisible = ref(false)
const remarkVisible = ref(false)
const singleAddFlowVisible = ref(false)
const singleRenewVisible = ref(false)
const actionDialogVisible = ref(false)
const actionDialogState = ref<'processing' | 'success' | 'failed'>('processing')
const actionDialogTitle = ref('正在操作')
const actionDialogMessage = ref('正在处理，请稍候')

// 历史用量
const historyLoading = ref(false)
const historyList = ref<UsageHistory[]>([])
const flowLogLoading = ref(false)
const flowLogs = ref<OperationLog[]>([])
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
const isSuperAdmin = computed(() => authStore.userInfo?.user_level === 1)

const usagePercent = computed(() => {
  if (!card.value || !card.value.data_total) return 0
  const percent = (card.value.data_used / card.value.data_total) * 100
  return Math.max(percent, 0)
})

const clearDeviceSeparationDisplayState = () => {
  deviceSeparationDisplayState.value = 'idle'
  if (deviceSeparationStateTimer) {
    clearTimeout(deviceSeparationStateTimer)
    deviceSeparationStateTimer = null
  }
}

const setDeviceSeparationDisplayState = (state: 'pending' | 'detected' | 'clear') => {
  clearDeviceSeparationDisplayState()
  deviceSeparationDisplayState.value = state
  deviceSeparationStateTimer = setTimeout(() => {
    deviceSeparationDisplayState.value = 'idle'
    deviceSeparationStateTimer = null
  }, 30000)
}

const getDeviceSeparationText = () => {
  if (!card.value) return '-'
  if (deviceSeparationDisplayState.value === 'pending') return '查询中'
  if (deviceSeparationDisplayState.value === 'detected') return '机卡分离停机'
  if (deviceSeparationDisplayState.value === 'clear') return '未机卡分离'
  return '未检测'
}

const getDeviceSeparationClass = () => {
  if (!card.value) return ''
  if (deviceSeparationDisplayState.value === 'pending') return 'text-warning'
  if (deviceSeparationDisplayState.value === 'detected') return 'text-danger'
  if (deviceSeparationDisplayState.value === 'clear') return 'text-success'
  return 'text-info'
}

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))
const restartPollIntervalMs = 5000
const restartMaxPollAttempts = 72
const actionDialogProcessing = computed(() => actionDialogState.value === 'processing')

const openActionDialog = (title: string, message: string) => {
  actionDialogTitle.value = title
  actionDialogMessage.value = message
  actionDialogState.value = 'processing'
  actionDialogVisible.value = true
}

const finishActionDialog = (success: boolean, message: string, title?: string) => {
  actionDialogState.value = success ? 'success' : 'failed'
  actionDialogTitle.value = title || '操作结果'
  actionDialogMessage.value = message
}

const getRestartFailureMessage = (error: unknown) => {
  const rawMessage = error instanceof Error ? error.message : String(error || '')
  const message = rawMessage.trim()
  if (!message) return '重启失败，请手动复机'
  if (message.includes('timeout') || message.includes('exceeded') || message.includes('Network Error')) {
    return '重启失败，请手动复机'
  }
  return message
}
const getCarrierLimitNotice = (carrier?: string) => carrier === 'cmcc' ? '移动卡单日不可超2次停复机操作' : ''

const handleActionDialogClose = (done: () => void) => {
  if (actionDialogProcessing.value) return
  done()
}

const waitForRestartCompletion = async (cardId: number, initialStatus?: string) => {
  let seenSuspended = initialStatus === 'suspended'

  for (let attempt = 0; attempt < restartMaxPollAttempts; attempt += 1) {
    await sleep(restartPollIntervalMs)
    const latestCard = await cardApi.getDetail(cardId)
    card.value = latestCard
    const currentStatus = String(latestCard?.status || '')

    if (currentStatus === 'suspended') {
      seenSuspended = true
      continue
    }

    if (seenSuspended && currentStatus) {
      return true
    }
  }

  return false
}

const resolveDeviceSeparationResult = async (iccid: string) => {
  let result = await cardApi.syncSingleCard(iccid)
  if (result.device_separation_detection_status !== 'pending') {
    return result
  }

  setDeviceSeparationDisplayState('pending')
  for (let i = 0; i < 5; i += 1) {
    await sleep(5000)
    result = await cardApi.syncSingleCard(iccid)
    if (result.device_separation_detection_status !== 'pending') {
      return result
    }
  }

  return result
}

const handleDeviceSeparationCheck = async () => {
  if (!card.value?.iccid) {
    ElMessage.warning('当前卡片缺少 ICCID，无法检测')
    return
  }

  try {
    await ElMessageBox.confirm(
      '确定执行机卡分离检测吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
  } catch {
    return
  }

  deviceSeparationChecking.value = true
  openActionDialog('正在检测', '机卡分离检测进行中，请稍候')
  try {
    const result = await resolveDeviceSeparationResult(card.value.iccid)
    if (result.device_separation_detection_status === 'pending') {
      setDeviceSeparationDisplayState('pending')
      finishActionDialog(false, result.device_separation_detection_message || '供应商正在查询机卡分离状态，请稍后再试。', '检测结果')
      return
    }
    await fetchCardDetail()
    if (result.device_separation_detection_status === 'detected') {
      setDeviceSeparationDisplayState('detected')
      finishActionDialog(true, '机卡分离检测已完成，结果为机卡分离停机', '检测结果')
      return
    }
    if (result.device_separation_detection_status === 'clear') {
      setDeviceSeparationDisplayState('clear')
      finishActionDialog(true, '机卡分离检测已完成，结果为未机卡分离', '检测结果')
      return
    }
    clearDeviceSeparationDisplayState()
    if (result.device_separation_detection_status === 'unsupported') {
      finishActionDialog(false, result.device_separation_detection_message || '请联系客服', '检测结果')
      return
    }
    finishActionDialog(false, '当前未获取到有效检测结果，请稍后再试', '检测结果')
  } catch (error) {
    console.error('机卡分离检测失败:', error)
    const errorMessage = error instanceof Error ? error.message : String(error || '')
    if (errorMessage.includes('请联系客服') || errorMessage.includes('无权')) {
      finishActionDialog(false, errorMessage || '请联系客服', '检测结果')
      return
    }
    finishActionDialog(false, '机卡分离检测失败，请稍后重试', '检测结果')
  } finally {
    deviceSeparationChecking.value = false
  }
}

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
    const response: any = await cardApi.getTransfers(
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

// 获取补量日志
const fetchFlowLogs = async () => {
  flowLogLoading.value = true
  try {
    const res: any = await systemApi.getOperationLogs({
      module: 'cards',
      action: 'add_flow',
      target_type: 'card',
      target_id: cardId.value,
      page: 1,
      page_size: 10
    })
    flowLogs.value = res.items || []
  } catch (error) {
    console.error('获取补量日志失败:', error)
    flowLogs.value = []
  } finally {
    flowLogLoading.value = false
  }
}

// 渲染图表
const renderChart = () => {
  if (!chartRef.value) return

  if (historyList.value.length === 0) {
    chartInstance?.clear()
    return
  }

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const dates = historyList.value.map(h => formatDate(h.snapshot_date))
  const usages = historyList.value.map(h => h.daily_used || 0)

  chartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    xAxis: { type: 'category', data: dates },
    yAxis: { type: 'value', name: '日用量(MB)' },
    series: [{
      data: usages,
      type: 'bar',
      barMaxWidth: 28,
      itemStyle: { color: '#409EFF' }
    }]
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
      getCarrierLimitNotice(card.value?.carrier)
        ? `确定要停机该卡片吗？\n\n提示：${getCarrierLimitNotice(card.value?.carrier)}`
        : '确定要停机该卡片吗？',
      '停机确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    openActionDialog('正在停机', '正在提交停机操作，请稍候')
    await cardApi.batchSuspend({
      card_ids: [cardId.value]
    })

    await fetchCardDetail()
    finishActionDialog(true, '停机成功', '停机结果')
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('停机失败:', error)
      finishActionDialog(false, error?.message || '停机失败，请稍后重试', '停机结果')
    }
  }
}

// 复机
const handleResume = async () => {
  if (!card.value?.iccid) return
  try {
    await ElMessageBox.confirm(
      getCarrierLimitNotice(card.value?.carrier)
        ? `确定要复机该卡片吗？\n\n提示：${getCarrierLimitNotice(card.value?.carrier)}`
        : '确定要复机该卡片吗？',
      '复机确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    openActionDialog('正在复机', '正在提交复机操作，请稍候')
    const result = await cardApi.batchResumeByIccids({
      iccids: [card.value.iccid]
    })

    if (result.success > 0) {
      finishActionDialog(true, '复机成功', '复机结果')
    } else {
      const firstError = result.failed_list?.[0]?.error || '当前不允许复机'
      finishActionDialog(
        false,
        firstError.includes('超级管理员手动停卡') ? '该卡由超级管理员手动停卡，请联系管理员处理' : firstError,
        '复机结果'
      )
    }
    await fetchCardDetail()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('复机失败:', error)
      finishActionDialog(false, error?.message || '复机失败，请稍后重试', '复机结果')
    }
  }
}

const handleRestart = async () => {
  if (!card.value?.id || !card.value?.iccid) return
  try {
    await ElMessageBox.confirm(
      getCarrierLimitNotice(card.value?.carrier)
        ? `确定要重启该卡片吗？系统会执行停机后再复机。\n\n提示：${getCarrierLimitNotice(card.value?.carrier)}`
        : '确定要重启该卡片吗？系统会执行停机后再复机。',
      '重启确认',
      {
        confirmButtonText: '确定重启',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    openActionDialog('正在重启', '正在操作，请稍候')
    const initialStatus = card.value.status
    const result = await cardApi.restartCard(card.value.id)
    if (result.status === 'processing') {
      const success = await waitForRestartCompletion(card.value.id, initialStatus)
      finishActionDialog(success, success ? '重启成功' : '重启失败，请手动复机', '重启结果')
    } else {
      await fetchCardDetail()
      finishActionDialog(true, result.message || '重启成功', '重启结果')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('重启失败:', error)
      finishActionDialog(false, getRestartFailureMessage(error), '重启结果')
    }
  }
}

const handleForceResume = async () => {
  if (!card.value?.iccid) return

  try {
    await ElMessageBox.confirm(
      '确定要强制复机该卡片吗？该操作会绕过人工停卡与超限限制。',
      '强制复机确认',
      {
        confirmButtonText: '确认强制复机',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const result = await cardApi.batchForceResumeByIccids({
      iccids: [card.value.iccid]
    })

    if (result.success > 0) {
      ElMessage.success('强制复机成功')
    } else {
      const firstError = result.failed_list?.[0]?.error || '强制复机失败'
      ElMessage.error(firstError)
    }
    fetchCardDetail()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('强制复机失败:', error)
    }
  }
}

// 单卡补量
const handleAddFlow = () => {
  singleAddFlowVisible.value = true
}

const handleRenew = () => {
  singleRenewVisible.value = true
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

const handleAddFlowSuccess = () => {
  fetchCardDetail()
  fetchFlowLogs()
}

const handleRenewSuccess = () => {
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
  fetchFlowLogs()
  // 默认显示最近30天
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 30)
  historyDateRange.value = [start, end]
  fetchUsageHistory()
})

onBeforeUnmount(() => {
  clearDeviceSeparationDisplayState()
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

.device-separation-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.action-dialog {
  display: grid;
  justify-items: center;
  gap: 12px;
  padding: 2px 0 6px;
  text-align: center;
}

.action-dialog__icon {
  font-size: 28px;
  color: #2563eb;
}

.action-dialog__icon.is-success {
  color: #16a34a;
}

.action-dialog__icon.is-danger {
  color: #ef4444;
}

.action-dialog__message {
  color: #111827;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.6;
}
</style>
