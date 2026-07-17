<template>
  <div
    class="h5-page"
    @touchstart.passive="handleTouchStart"
    @touchmove="handleTouchMove"
    @touchend="handleTouchEnd"
    @touchcancel="handleTouchEnd"
  >
    <div
      class="pull-refresh"
      :class="{
        'is-visible': pullDistance > 0 || pullRefreshing,
        'is-ready': pullReady,
        'is-refreshing': pullRefreshing
      }"
      :style="{ height: `${pullIndicatorHeight}px` }"
    >
      <span>{{ pullRefreshText }}</span>
    </div>

    <main class="content" :style="{ transform: `translateY(${pullOffset}px)` }">
      <template v-if="!detail">
        <el-card class="panel query-panel" shadow="never">
          <div class="panel-title panel-title--large">卡片查询</div>
          <el-form @submit.prevent>
            <el-form-item class="query-form-item">
              <el-input
                v-model="keyword"
                size="large"
                clearable
                maxlength="32"
                placeholder="输入6位卡号进行模糊查询"
                @keyup.enter="handleQuery"
              >
                <template #prefix>
                  <el-icon class="field-icon"><Search /></el-icon>
                </template>
                <template #append>
                  <el-button type="primary" :loading="searching" @click="handleQuery">查询</el-button>
                </template>
              </el-input>
            </el-form-item>
          </el-form>
          <div class="query-hint">移动卡输入最后6位，联通/电信卡输入去除字母后6位</div>
          <div v-if="recentKeywords.length" class="recent-searches">
            <div class="recent-searches__header">
              <span>最近查询</span>
              <button type="button" class="recent-searches__clear" @click="clearRecentKeywords">清空</button>
            </div>
            <div class="recent-searches__list">
              <button
                v-for="item in recentKeywords"
                :key="item"
                type="button"
                class="recent-searches__item"
                @click="handleRecentKeywordClick(item)"
              >
                {{ item }}
              </button>
            </div>
          </div>
        </el-card>

        <el-card v-if="config?.notice" class="panel" shadow="never">
          <div class="section-head">
            <el-icon class="section-icon"><Bell /></el-icon>
            <span>公告通知</span>
          </div>
          <el-collapse v-model="noticeCollapse">
            <el-collapse-item name="notice">
              <template #title>
                <div class="notice-title-wrap">
                  <span class="notice-badge">普通</span>
                  <div class="notice-meta">
                    <div class="notice-title">使用注意事项</div>
                    <div class="notice-date">{{ todayLabel }}</div>
                  </div>
                </div>
              </template>
              <div class="notice-content">{{ config.notice }}</div>
            </el-collapse-item>
          </el-collapse>
        </el-card>

        <el-card class="panel support-panel" shadow="never">
          <div class="support-title">客服支持</div>
          <div class="support-box">
            <div class="support-row">
              <div class="support-label">
                <el-icon class="support-icon is-blue"><Phone /></el-icon>
                <span>客服电话：</span>
              </div>
              <a :href="config?.contact_phone ? `tel:${config.contact_phone}` : undefined" class="support-link">
                {{ config?.contact_phone || '-' }}
              </a>
            </div>
            <div class="support-row">
              <div class="support-label">
                <el-icon class="support-icon is-purple"><Message /></el-icon>
                <span>微信：</span>
              </div>
              <strong>{{ config?.contact_wechat || '-' }}</strong>
            </div>
            <div class="support-row">
              <div class="support-label">
                <el-icon class="support-icon is-orange"><Clock /></el-icon>
                <span>服务时间：</span>
              </div>
              <strong>工作日 9:00-18:00</strong>
            </div>
          </div>
        </el-card>
      </template>

      <el-card v-if="candidates.length" class="panel" shadow="never">
        <div class="panel-title">请选择对应卡片</div>
        <div class="candidate-list">
          <button
            v-for="item in candidates"
            :key="item.id"
            class="candidate-item"
            @click="selectCandidate(item.id)"
          >
            <div class="candidate-title">{{ item.iccid_masked }}</div>
            <div class="candidate-meta">
              <span>{{ item.spec_name || '-' }}</span>
              <span>{{ item.status_name || '-' }}</span>
              <span>{{ formatDate(item.activated_at) }}</span>
            </div>
          </button>
        </div>
      </el-card>

      <template v-if="detail">
        <div class="page-topbar">
          <button class="back-button" @click="handleBackToSearch">
            <el-icon><ArrowLeft /></el-icon>
            <span>返回</span>
          </button>
        </div>

        <el-card class="panel detail-main-panel" shadow="never">
          <div class="detail-header">
            <div class="panel-title">核心信息</div>
            <div class="status-chip" :class="getStatusClass(detail.card.status_name || detail.card.status)">
              {{ detail.card.status_name || detail.card.status || '-' }}
            </div>
          </div>

          <div class="info-list">
            <div class="info-row">
              <span>ICCID</span>
              <strong>{{ detail.card.iccid }}</strong>
            </div>
            <div class="info-row">
              <span>电话号码</span>
              <strong>{{ detail.card.msisdn || '-' }}</strong>
            </div>
            <div class="info-row">
              <span>卡状态</span>
              <strong>{{ detail.card.status_name || '-' }}</strong>
            </div>
            <div class="info-row">
              <span>套餐</span>
              <strong>{{ detail.card.spec_name || '-' }}</strong>
            </div>
          </div>

          <div class="usage-box">
            <div class="usage-box__title">本月用量</div>
            <div class="usage-row">
              <span>流量</span>
              <strong>{{ formatFlow(detail.card.data_used || 0) }} / {{ formatFlow(detail.card.data_total || 0) }}</strong>
            </div>
            <el-progress
              :percentage="usagePercentDisplay"
              :stroke-width="8"
              :show-text="false"
              color="#0f1128"
            />
          </div>

          <div class="info-list">
            <div class="info-row">
              <span>使用率</span>
              <strong>{{ usagePercentLabel }}</strong>
            </div>
            <div class="info-row">
              <span>剩余流量</span>
              <strong>{{ formatFlow(remainFlow) }}</strong>
            </div>
            <div class="info-row">
              <span>激活时间</span>
              <strong>{{ formatDate(detail.card.activated_at) }}</strong>
            </div>
            <div class="info-row">
              <span>到期时间</span>
              <strong>{{ formatDate(detail.card.expired_at) }}</strong>
            </div>
            <div class="info-row">
              <span>备注</span>
              <strong class="remark-text">{{ detail.card.remark || '暂无备注' }}</strong>
            </div>
          </div>
        </el-card>

        <el-card class="panel operation-panel" shadow="never">
          <div class="panel-title">操作</div>
          <div class="operation-grid">
            <button class="operation-button" :disabled="isActionBusy || diagnosisLoading" @click="handleDiagnosisAction">
              <el-icon class="operation-icon" :class="{ 'is-spinning': diagnosisLoading }"><Opportunity /></el-icon>
              <span>{{ diagnosisLoading ? '诊断中' : '智能诊断' }}</span>
            </button>
            <button
              v-if="showSuspendButton"
              class="operation-button operation-button--danger"
              :disabled="isActionBusy"
              @click="handleSuspendAction"
            >
              <el-icon class="operation-icon"><SwitchButton /></el-icon>
              <span>{{ getActionButtonText('suspend') }}</span>
            </button>
            <button
              v-if="showResumeButton"
              class="operation-button operation-button--success"
              :disabled="isActionBusy"
              @click="handleResumeAction"
            >
              <el-icon class="operation-icon"><Right /></el-icon>
              <span>{{ getActionButtonText('resume') }}</span>
            </button>
            <button
              v-if="showRefreshButton"
              class="operation-button operation-button--refresh"
              :disabled="isActionBusy"
              @click="handleRefreshAction"
            >
              <el-icon class="operation-icon" :class="{ 'is-spinning': isRefreshing }"><RefreshRight /></el-icon>
              <span>{{ getActionButtonText('refresh') }}</span>
            </button>
            <button
              class="operation-button operation-button--primary"
              :disabled="isActionBusy || actionLoading === 'deviceSeparation'"
              @click="handleDeviceSeparationAction"
            >
              <el-icon class="operation-icon" :class="{ 'is-spinning': actionLoading === 'deviceSeparation' }"><Search /></el-icon>
              <span>{{ getActionButtonText('deviceSeparation') }}</span>
            </button>
            <button
              v-if="detail.actions.allow_remark"
              class="operation-button operation-button--wide"
              @click="remarkDialogVisible = true"
            >
              <el-icon class="operation-icon"><EditPen /></el-icon>
              <span>添加/编辑备注</span>
            </button>
          </div>
        </el-card>
      </template>
    </main>

    <el-dialog v-model="diagnosisDialogVisible" title="智能诊断" width="420px" v-loading="diagnosisLoading">
      <div class="diag-summary">
        <span>整体状态</span>
        <div class="status-chip" :class="diagnosisTone.className">{{ diagnosisTone.label }}</div>
      </div>
      <div class="diag-list">
        <div class="diag-item" v-for="item in diagnosisItems" :key="item.label">
          <div>
            <div class="diag-item__label">{{ item.label }}</div>
            <div class="diag-item__desc">{{ item.desc }}</div>
          </div>
          <el-tag :type="item.tagType" effect="light">{{ item.value }}</el-tag>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="remarkDialogVisible" title="修改备注" width="420px">
      <el-form @submit.prevent>
        <el-form-item label="备注">
          <el-input
            v-model="remarkForm.remark"
            type="textarea"
            :rows="4"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="remarkForm.operatorName" maxlength="50" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="remarkForm.operatorPhone" maxlength="20" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="remarkDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="actionLoading === 'remark'" @click="handleRemarkSubmit">
          保存
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="refreshDialogVisible"
      :title="refreshDialogTitle"
      width="300px"
      :close-on-click-modal="false"
      :close-on-press-escape="!refreshDialogProcessing"
      :show-close="!refreshDialogProcessing"
      :before-close="handleRefreshDialogClose"
    >
      <div class="refresh-dialog">
        <el-icon
          class="refresh-dialog__icon"
          :class="{
            'is-spinning': refreshDialogProcessing,
            'is-success': refreshDialogState === 'success',
            'is-danger': refreshDialogState === 'failed'
          }"
        >
          <RefreshRight v-if="refreshDialogProcessing" />
          <CircleCheckFilled v-else-if="refreshDialogState === 'success'" />
          <WarningFilled v-else />
        </el-icon>
        <div class="refresh-dialog__message">{{ refreshDialogMessage }}</div>
      </div>
      <template #footer>
        <el-button v-if="!refreshDialogProcessing" type="primary" @click="refreshDialogVisible = false">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Bell,
  CircleCheckFilled,
  Clock,
  EditPen,
  Message,
  Opportunity,
  Phone,
  RefreshRight,
  Right,
  Search,
  WarningFilled,
  SwitchButton
} from '@element-plus/icons-vue'
import { h5Api, type H5PortalConfig, type H5CardCandidate, type H5CardDetail, type H5CardActionResult } from '@/api/modules/h5'

const route = useRoute()
const slug = computed(() => String(route.params.slug || ''))
const recentKeywordsStorageKey = computed(() => `h5-card-query-history:${slug.value}`)

const config = ref<H5PortalConfig | null>(null)
const keyword = ref('')
const recentKeywords = ref<string[]>([])
const searching = ref(false)
const candidates = ref<H5CardCandidate[]>([])
const detail = ref<H5CardDetail | null>(null)
const actionLoading = ref<'suspend' | 'resume' | 'refresh' | 'remark' | 'deviceSeparation' | ''>('')
const actionResultText = reactive({
  suspend: '',
  resume: '',
  refresh: '',
  deviceSeparation: ''
})
const diagnosisLoading = ref(false)
const diagnosisDialogVisible = ref(false)
const remarkDialogVisible = ref(false)
const refreshDialogVisible = ref(false)
const noticeCollapse = ref(['notice'])
const remarkForm = reactive({
  remark: '',
  operatorName: '',
  operatorPhone: ''
})
const refreshDialogState = ref<'processing' | 'pending' | 'success' | 'failed'>('processing')
const refreshDialogMessage = ref('正在重启')
const touchStartY = ref(0)
const pullDistance = ref(0)
const pullRefreshing = ref(false)

const pullThreshold = 72
const pullMaxDistance = 108

const todayLabel = computed(() => {
  const today = new Date()
  const yyyy = today.getFullYear()
  const mm = String(today.getMonth() + 1).padStart(2, '0')
  const dd = String(today.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
})

const remainFlow = computed(() => {
  if (!detail.value?.card) return 0
  return Math.max((detail.value.card.data_total || 0) - (detail.value.card.data_used || 0), 0)
})

const usagePercent = computed(() => {
  if (!detail.value?.card?.data_total) return 0
  return ((detail.value.card.data_used || 0) / detail.value.card.data_total) * 100
})

const usagePercentDisplay = computed(() => Number(Math.min(usagePercent.value, 100).toFixed(2)))
const usagePercentLabel = computed(() => `${Math.round(usagePercentDisplay.value)}%`)
const isActionBusy = computed(() => ['suspend', 'resume', 'refresh'].includes(actionLoading.value))
const isRefreshing = computed(() => actionLoading.value === 'refresh')
const showSuspendButton = computed(() =>
  Boolean(detail.value?.actions.allow_suspend) && detail.value?.card?.status !== 'suspended'
)
const showResumeButton = computed(() =>
  Boolean(detail.value?.actions.allow_resume) && detail.value?.card?.status === 'suspended'
)
const showRefreshButton = computed(() =>
  Boolean(detail.value?.actions.allow_suspend) && Boolean(detail.value?.actions.allow_resume)
)
const pullReady = computed(() => pullDistance.value >= pullThreshold)
const pullIndicatorHeight = computed(() => (pullRefreshing.value ? 56 : Math.max(pullDistance.value, 0)))
const pullOffset = computed(() => (pullRefreshing.value ? 56 : Math.max(pullDistance.value, 0)))
const pullRefreshText = computed(() => {
  if (pullRefreshing.value) return '刷新中...'
  if (pullReady.value) return '释放立即刷新'
  return pullDistance.value > 0 ? '下拉刷新页面' : ''
})
const refreshDialogProcessing = computed(() => refreshDialogState.value === 'processing')
const refreshDialogTitle = computed(() => {
  if (refreshDialogProcessing.value) return '正在重启'
  return refreshDialogState.value === 'pending' ? '重启状态' : '重启结果'
})
const getCarrierLimitNotice = (carrier?: string) => carrier === 'cmcc' ? '移动卡单日不可超2次停复机操作' : ''

const getActionButtonText = (action: 'suspend' | 'resume' | 'refresh' | 'deviceSeparation') => {
  if (action === 'suspend') {
    if (actionLoading.value === 'suspend') return '停机中'
    return actionResultText.suspend || '停机'
  }
  if (action === 'resume') {
    if (actionLoading.value === 'resume') return '复机中'
    return actionResultText.resume || '复机'
  }
  if (action === 'refresh') {
    if (actionLoading.value === 'refresh') return '重启中'
    return actionResultText.refresh || '重启'
  }
  if (actionLoading.value === 'deviceSeparation') return '检测中'
  return actionResultText.deviceSeparation || '机卡分离检测'
}

const diagnosisTone = computed(() => {
  const card = detail.value?.card
  const diagnostics = detail.value?.diagnostics
  if (!card) return { label: '待诊断', className: 'is-neutral' }
  if (card.status === 'suspended' || diagnostics?.work_status_msg === '离线') {
    return { label: '异常', className: 'is-danger' }
  }
  if (usagePercent.value >= 80 || diagnostics?.power_status_msg === '关机') {
    return { label: '关注', className: 'is-warning' }
  }
  return { label: '正常', className: 'is-success' }
})

const diagnosisItems = computed(() => {
  const card = detail.value?.card
  const diagnostics = detail.value?.diagnostics
  return [
    {
      label: '卡片状态',
      value: card?.status_name || card?.status || '未知',
      desc: card?.status === 'suspended' ? '当前卡片已停机，请按需复机。' : '当前卡片状态正常。',
      tagType: card?.status === 'suspended' ? 'danger' : 'success'
    },
    {
      label: '开机状态',
      value: diagnostics?.power_status_msg || '未知',
      desc: diagnostics?.power_status_msg === '开机' ? '设备当前已上电。' : '设备可能未上电或平台未同步。',
      tagType: diagnostics?.power_status_msg === '开机' ? 'success' : 'warning'
    },
    {
      label: '工作状态',
      value: diagnostics?.work_status_msg || '未知',
      desc: diagnostics?.work_status_msg === '在线' ? '设备连接正常。' : '设备可能离线，请检查设备与网络。',
      tagType: diagnostics?.work_status_msg === '在线' ? 'success' : 'danger'
    },
    {
      label: '流量诊断',
      value: usagePercent.value >= 80 ? '高占用' : '正常',
      desc: usagePercent.value >= 80 ? '流量消耗较高，请关注剩余流量。' : '当前套餐流量使用处于正常范围。',
      tagType: usagePercent.value >= 80 ? 'warning' : 'success'
    }
  ]
})

const loadConfig = async () => {
  config.value = await h5Api.getConfig(slug.value)
}

const loadRecentKeywords = () => {
  if (typeof window === 'undefined' || !slug.value) return
  const raw = window.localStorage.getItem(recentKeywordsStorageKey.value)
  if (!raw) {
    recentKeywords.value = []
    return
  }

  try {
    const parsed = JSON.parse(raw)
    recentKeywords.value = Array.isArray(parsed) ? parsed.filter(item => typeof item === 'string').slice(0, 10) : []
  } catch {
    recentKeywords.value = []
  }
}

const saveRecentKeyword = (value: string) => {
  const normalized = value.trim()
  if (!normalized || typeof window === 'undefined') return
  recentKeywords.value = [normalized, ...recentKeywords.value.filter(item => item !== normalized)].slice(0, 10)
  window.localStorage.setItem(recentKeywordsStorageKey.value, JSON.stringify(recentKeywords.value))
}

const clearRecentKeywords = () => {
  recentKeywords.value = []
  if (typeof window !== 'undefined') {
    window.localStorage.removeItem(recentKeywordsStorageKey.value)
  }
}

const handleRecentKeywordClick = (value: string) => {
  keyword.value = value
  handleQuery()
}

const resetState = () => {
  candidates.value = []
  detail.value = null
  diagnosisDialogVisible.value = false
  actionResultText.suspend = ''
  actionResultText.resume = ''
  actionResultText.refresh = ''
  actionResultText.deviceSeparation = ''
}

const refreshCurrentView = async () => {
  if (detail.value?.card?.id) {
    await refreshDetail()
    return
  }

  if (candidates.value.length && keyword.value.trim()) {
    const result = await h5Api.queryCard(slug.value, keyword.value.trim())
    if (result.match_type === 'fuzzy_multiple') {
      candidates.value = result.items as H5CardCandidate[]
      detail.value = null
      return
    }
    if (result.match_type !== 'none') {
      detail.value = (result.items[0] as H5CardDetail) || null
      candidates.value = []
      fillRemark()
      return
    }
  }

  await loadConfig()
}

const resetPullState = () => {
  pullDistance.value = 0
  touchStartY.value = 0
}

const handleTouchStart = (event: TouchEvent) => {
  if (pullRefreshing.value || window.scrollY > 0) return
  touchStartY.value = event.touches[0]?.clientY || 0
}

const handleTouchMove = (event: TouchEvent) => {
  if (pullRefreshing.value || !touchStartY.value || window.scrollY > 0) return

  const currentY = event.touches[0]?.clientY || 0
  const deltaY = currentY - touchStartY.value

  if (deltaY <= 0) {
    pullDistance.value = 0
    return
  }

  pullDistance.value = Math.min(deltaY * 0.45, pullMaxDistance)
  if (pullDistance.value > 0) {
    event.preventDefault()
  }
}

const handleTouchEnd = async () => {
  if (pullRefreshing.value) return
  const shouldRefresh = pullDistance.value >= pullThreshold
  if (!shouldRefresh) {
    resetPullState()
    return
  }

  pullRefreshing.value = true
  pullDistance.value = 56
  try {
    await refreshCurrentView()
    ElMessage.success('页面已刷新')
  } finally {
    pullRefreshing.value = false
    resetPullState()
  }
}

const fillRemark = () => {
  remarkForm.remark = detail.value?.card.remark || ''
}

const handleQuery = async () => {
  if (!keyword.value.trim()) {
    ElMessage.warning('请输入查询内容')
    return
  }

  searching.value = true
  resetState()
  try {
    const normalizedKeyword = keyword.value.trim()
    const result = await h5Api.queryCard(slug.value, normalizedKeyword)
    saveRecentKeyword(normalizedKeyword)
    if (result.match_type === 'none') {
      ElMessage.warning('未查询到对应卡片')
      return
    }
    if (result.match_type === 'fuzzy_multiple') {
      candidates.value = result.items as H5CardCandidate[]
      return
    }
    detail.value = (result.items[0] as H5CardDetail) || null
    fillRemark()
  } finally {
    searching.value = false
  }
}

const selectCandidate = async (cardId: number) => {
  detail.value = await h5Api.getCardDetail(slug.value, cardId)
  fillRemark()
  candidates.value = []
}

const refreshDetail = async () => {
  if (!detail.value?.card?.id) return
  detail.value = await h5Api.getCardDetail(slug.value, detail.value.card.id)
  fillRemark()
}

const handleBackToSearch = () => {
  resetState()
}

const handleDiagnosisAction = async () => {
  if (!detail.value?.card?.id || diagnosisLoading.value) return
  diagnosisLoading.value = true
  try {
    await refreshDetail()
    diagnosisDialogVisible.value = true
  } finally {
    diagnosisLoading.value = false
  }
}

const handleRefreshAction = async () => {
  if (!detail.value?.card?.id) return
  const carrierNotice = getCarrierLimitNotice(detail.value?.card?.carrier)
  try {
    await ElMessageBox.confirm(
      carrierNotice ? `确定要重启当前卡片吗？系统会执行停机后再复机。\n\n提示：${carrierNotice}` : '确定要重启当前卡片吗？系统会执行停机后再复机。',
      '重启确认',
      {
        confirmButtonText: '确定重启',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
  } catch {
    return
  }
  actionLoading.value = 'refresh'
  refreshDialogState.value = 'processing'
  refreshDialogMessage.value = '正在重启'
  refreshDialogVisible.value = true
  try {
    const result = await h5Api.refreshCard(slug.value, detail.value.card.id)
    actionLoading.value = ''
    await handleRefreshSubmitted(result)
  } catch (error) {
    actionLoading.value = ''
    refreshDialogState.value = 'failed'
    refreshDialogMessage.value = '重启失败，请手动复机'
    throw error
  }
}

const getDeviceSeparationAlertType = (status?: string) => {
  if (status === 'detected') return 'warning'
  if (status === 'clear') return 'success'
  return 'info'
}

const waitForDeviceSeparationResult = async (cardId: number) => {
  let latestResult: H5CardActionResult | null = null

  for (let attempt = 0; attempt < 5; attempt += 1) {
    await sleep(5000)
    latestResult = await h5Api.detectDeviceSeparation(slug.value, cardId)
    const latestStatus = latestResult.device_separation_detection_status
    const latestMessage = latestResult.device_separation_detection_message || latestResult.message || '请联系客服'
    actionResultText.deviceSeparation = latestMessage

    if (latestStatus && latestStatus !== 'pending') {
      return latestResult
    }
  }

  return latestResult
}

const handleDeviceSeparationAction = async () => {
  if (!detail.value?.card?.id) return
  actionLoading.value = 'deviceSeparation'
  try {
    let result = await h5Api.detectDeviceSeparation(slug.value, detail.value.card.id)
    let detectionStatus = result.device_separation_detection_status
    let message = result.device_separation_detection_message || result.message || '请联系客服'
    actionResultText.deviceSeparation = message

    if (detectionStatus === 'pending') {
      actionLoading.value = ''
      result = (await waitForDeviceSeparationResult(detail.value.card.id)) || result
      detectionStatus = result.device_separation_detection_status
      message = result.device_separation_detection_message || result.message || '请联系客服'
      actionResultText.deviceSeparation = message
    } else {
      actionLoading.value = ''
    }

    if (detectionStatus === 'pending') {
      message = '正在查询中，请稍后再试'
      actionResultText.deviceSeparation = message
    }

    await ElMessageBox.alert(message, '机卡分离检测', {
      confirmButtonText: '知道了',
      type: getDeviceSeparationAlertType(detectionStatus)
    })
    actionResultText.deviceSeparation = ''
  } catch (error) {
    actionLoading.value = ''
    throw error
  }
}

const handleSuspendAction = async () => {
  if (!detail.value?.card?.id) return
  const carrierNotice = getCarrierLimitNotice(detail.value?.card?.carrier)
  try {
    await ElMessageBox.confirm(
      carrierNotice ? `确定要停机当前卡片吗？\n\n提示：${carrierNotice}` : '确定要停机当前卡片吗？',
      '停机确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
  } catch {
    return
  }
  actionLoading.value = 'suspend'
  try {
    const result = await h5Api.suspendCard(slug.value, detail.value.card.id)
    actionLoading.value = ''
    await handleActionSubmitted(result)
  } catch (error) {
    actionLoading.value = ''
    throw error
  }
}

const handleResumeAction = async () => {
  if (!detail.value?.card?.id) return
  const carrierNotice = getCarrierLimitNotice(detail.value?.card?.carrier)
  try {
    await ElMessageBox.confirm(
      carrierNotice ? `确定要复机当前卡片吗？\n\n提示：${carrierNotice}` : '确定要复机当前卡片吗？',
      '复机确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
  } catch {
    return
  }
  actionLoading.value = 'resume'
  try {
    const result = await h5Api.resumeCard(slug.value, detail.value.card.id)
    actionLoading.value = ''
    await handleActionSubmitted(result)
  } catch (error) {
    actionLoading.value = ''
    throw error
  }
}

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))
const refreshPollIntervalMs = 5000
const actionMaxPollAttempts = 120
const refreshMaxPollAttempts = 120

const waitForRefreshCompletion = async () => {
  const initialStatus = detail.value?.card?.status
  let seenSuspended = initialStatus === 'suspended'

  for (let attempt = 0; attempt < refreshMaxPollAttempts; attempt += 1) {
    await sleep(refreshPollIntervalMs)
    await refreshDetail()

    const currentStatus = String(detail.value?.card?.status || '')
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

const refreshDetailUntilRecovered = async (action: H5CardActionResult) => {
  const expectRecovered = action.action === 'refresh' || action.action === 'resume'
  const expectSuspended = action.action === 'suspend'

  for (let attempt = 0; attempt < actionMaxPollAttempts; attempt += 1) {
    await sleep(refreshPollIntervalMs)
    await refreshDetail()

    const currentStatus = detail.value?.card?.status
    if (expectRecovered && currentStatus && currentStatus !== 'suspended') {
      return
    }
    if (expectSuspended && currentStatus === 'suspended') {
      return
    }
  }
}

const handleRefreshSubmitted = async (result: H5CardActionResult) => {
  const resultMessage = (result.message || '').replace(/刷新/g, '重启')

  if (result.status !== 'processing') {
    refreshDialogState.value = result.status === 'success' ? 'success' : 'failed'
    refreshDialogMessage.value = result.status === 'success'
      ? (resultMessage || '重启成功')
      : '重启失败，请手动复机'
    await refreshDetail()
    return
  }

  const success = await waitForRefreshCompletion()
  refreshDialogState.value = success ? 'success' : 'pending'
  refreshDialogMessage.value = success ? '重启成功' : '重启仍在处理中，请稍后刷新页面查看状态，请勿重复提交'
}

const handleActionSubmitted = async (result: H5CardActionResult) => {
  const actionText = result.action === 'refresh'
    ? '重启'
    : result.action === 'suspend'
      ? '停机'
      : '复机'
  const actionKey = result.action as 'suspend' | 'resume' | 'refresh'
  const resultMessage = result.action === 'refresh'
    ? (result.message || '').replace(/刷新/g, '重启')
    : (result.message || '')
  actionResultText[actionKey] = resultMessage || `${actionText}已提交`

  if (result.status === 'processing') {
    await ElMessageBox.alert(resultMessage || `${actionText}请求已提交，处理中`, `${actionText}`, {
      confirmButtonText: '知道了',
      type: 'info'
    })
    actionResultText[actionKey] = ''
    void refreshDetailUntilRecovered(result)
    return
  }

  await ElMessageBox.alert(resultMessage || `${actionText}成功`, `${actionText}`, {
    confirmButtonText: '知道了',
    type: 'success'
  })
  actionResultText[actionKey] = ''
  await refreshDetail()
}

const handleRemarkSubmit = async () => {
  if (!detail.value?.card?.id) return
  actionLoading.value = 'remark'
  try {
    await h5Api.updateRemark(
      slug.value,
      detail.value.card.id,
      remarkForm.remark,
      remarkForm.operatorName,
      remarkForm.operatorPhone
    )
    ElMessage.success('备注已更新')
    remarkDialogVisible.value = false
    await refreshDetail()
  } finally {
    actionLoading.value = ''
  }
}

const handleRefreshDialogClose = (done: () => void) => {
  if (refreshDialogProcessing.value) return
  done()
}

const formatFlow = (value: number) => {
  if (!value) return '0 MB'
  if (value >= 1024) {
    const gb = value / 1024
    return `${gb.toFixed(2)} GB`
  }
  return `${value} MB`
}

const formatDate = (value?: string) => {
  if (!value) return '-'
  const text = String(value).trim()
  if (!text) return '-'

  const matched = text.match(/(\d{2,4})[\/\-](\d{1,2})[\/\-](\d{1,2})/)
  if (!matched) return text

  const rawYear = matched[1] || ''
  const rawMonth = matched[2] || ''
  const rawDay = matched[3] || ''
  let year = rawYear
  const month = rawMonth.padStart(2, '0')
  const day = rawDay.padStart(2, '0')

  if (year.length === 2) {
    year = `20${year}`
  }

  return `${year}-${month}-${day}`
}

const getStatusClass = (status?: string) => {
  const value = String(status || '').toLowerCase()
  if (value.includes('正常') || value.includes('active') || value.includes('activated')) return 'is-success'
  if (value.includes('停') || value.includes('suspend')) return 'is-danger'
  if (value.includes('未') || value.includes('silent') || value.includes('expire')) return 'is-warning'
  return 'is-neutral'
}

onMounted(async () => {
  await loadConfig()
  loadRecentKeywords()
})
</script>

<style scoped lang="scss">
.h5-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #fbfbff 0%, #f9f7ff 100%);
  color: #111827;
  font-family: "PingFang SC", "Hiragino Sans GB", "Noto Sans SC", sans-serif;
  overscroll-behavior-y: contain;
}

.pull-refresh {
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  color: #667085;
  font-size: 13px;
  font-weight: 600;
  transition: height 0.2s ease;
}

.pull-refresh.is-ready {
  color: #2563eb;
}

.pull-refresh.is-refreshing {
  color: #111827;
}

.content {
  max-width: 500px;
  margin: 0 auto;
  padding: 2px 0 28px;
  transition: transform 0.2s ease;
}

.panel {
  margin-top: 16px;
  border: 1px solid #ebe7f0;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.035);
}

.panel :deep(.el-card__body) {
  padding: 20px;
}

.query-panel {
  margin-top: 0;
}

.panel-title {
  color: #111827;
  font-size: 16px;
  font-weight: 700;
}

.panel-title--large {
  margin-bottom: 16px;
  font-size: 18px;
}

.section-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  color: #111827;
  font-size: 16px;
  font-weight: 700;
}

.section-icon {
  color: #4f86ff;
}

.query-form-item {
  margin-bottom: 10px;
}

.field-icon {
  color: #98a2b3;
}

.query-panel :deep(.el-input__wrapper) {
  min-height: 40px;
  background: #f6f7fb;
  box-shadow: none;
  border-radius: 10px 0 0 10px;
}

.query-panel :deep(.el-input-group__append) {
  padding: 0;
}

.query-panel :deep(.el-input-group__append .el-button) {
  min-width: 68px;
  height: 40px;
  border-radius: 0 10px 10px 0;
  background: #0c1026;
  border-color: #0c1026;
  font-weight: 700;
}

.query-hint {
  color: #667085;
  font-size: 12px;
  line-height: 1.6;
}

.recent-searches {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid #ece7f2;
}

.recent-searches__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  color: #475467;
  font-size: 13px;
  font-weight: 600;
}

.recent-searches__clear {
  border: none;
  background: transparent;
  color: #667085;
  font-size: 12px;
  cursor: pointer;
}

.recent-searches__list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.recent-searches__item {
  padding: 6px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  background: #f8fafc;
  color: #111827;
  font-size: 12px;
  cursor: pointer;
}

.notice-title-wrap {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding-right: 12px;
}

.notice-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 42px;
  height: 24px;
  margin-top: 4px;
  border-radius: 999px;
  background: #4f86ff;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
}

.notice-meta {
  display: grid;
  gap: 4px;
}

.notice-title {
  color: #111827;
  font-size: 15px;
  font-weight: 700;
}

.notice-date {
  color: #667085;
  font-size: 12px;
}

.notice-content {
  color: #475467;
  font-size: 13px;
  line-height: 1.8;
  white-space: pre-wrap;
}

.panel :deep(.el-collapse) {
  border-top: none;
  border-bottom: none;
}

.panel :deep(.el-collapse-item__header) {
  align-items: flex-start;
  min-height: 70px;
  border-bottom: 1px solid #ece7f2;
  background: transparent;
  padding-right: 2px;
}

.panel :deep(.el-collapse-item:last-child .el-collapse-item__header) {
  border-bottom: none;
}

.panel :deep(.el-collapse-item__wrap) {
  border-bottom: none;
}

.panel :deep(.el-collapse-item__content) {
  padding: 0 0 8px 0;
}

.support-title {
  margin-bottom: 16px;
  color: #111827;
  font-size: 16px;
  font-weight: 700;
  text-align: center;
}

.support-box {
  padding: 18px 18px;
  border-radius: 12px;
  background: linear-gradient(90deg, #eff6ff 0%, #f9f2ff 100%);
}

.support-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.support-row + .support-row {
  margin-top: 14px;
}

.support-label {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #475467;
  font-size: 14px;
}

.support-icon {
  font-size: 16px;
}

.support-icon.is-blue {
  color: #4f86ff;
}

.support-icon.is-purple {
  color: #7c3aed;
}

.support-icon.is-orange {
  color: #f97316;
}

.support-link {
  color: #4f46e5;
  font-size: 14px;
  font-weight: 700;
  text-decoration: none;
}

.support-row strong {
  color: #111827;
  font-size: 14px;
  font-weight: 600;
}

.candidate-list {
  display: grid;
  gap: 12px;
}

.candidate-item {
  width: 100%;
  padding: 14px;
  border: 1px solid #e7e3ec;
  border-radius: 12px;
  background: #fff;
  text-align: left;
  cursor: pointer;
}

.candidate-title {
  color: #111827;
  font-size: 15px;
  font-weight: 700;
}

.candidate-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  margin-top: 8px;
  color: #667085;
  font-size: 12px;
}

.page-topbar {
  display: flex;
  align-items: center;
  padding: 10px 4px 0;
}

.back-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: none;
  background: transparent;
  color: #111827;
  font-size: 14px;
  cursor: pointer;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.status-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 42px;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.info-list {
  border-top: 1px solid #ece7f2;
}

.info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 52px;
  border-bottom: 1px solid #ece7f2;
}

.info-row span {
  color: #475467;
  font-size: 13px;
}

.info-row strong {
  color: #111827;
  font-size: 13px;
  font-weight: 600;
  text-align: right;
  word-break: break-all;
}

.remark-text {
  color: #98a2b3 !important;
}

.usage-box {
  margin: 10px 0 8px;
  padding: 14px 12px 12px;
  border-radius: 10px;
  background: #f8f9fc;
}

.usage-box__title {
  margin-bottom: 12px;
  color: #111827;
  font-size: 13px;
  font-weight: 700;
}

.usage-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.usage-row span {
  color: #475467;
  font-size: 12px;
}

.usage-row strong {
  color: #111827;
  font-size: 13px;
  font-weight: 600;
}

.usage-box :deep(.el-progress-bar__outer) {
  background: #d8dbe5;
  border-radius: 999px;
}

.usage-box :deep(.el-progress-bar__inner) {
  border-radius: 999px;
}

.operation-panel .panel-title {
  margin-bottom: 18px;
}

.operation-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.operation-button {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60px;
  gap: 5px;
  border: 1px solid #dfe3ea;
  border-radius: 8px;
  background: #fff;
  color: #111827;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

.operation-button--wide {
  grid-column: 1 / -1;
}

.operation-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.operation-button--danger {
  color: #ef4444;
  border-color: #f4d4d7;
  background: #fff;
}

.operation-button--success {
  color: #16a34a;
  border-color: #cfead8;
  background: #fff;
}

.operation-button--refresh {
  color: #2563eb;
  border-color: #cfe0ff;
  background: #fff;
}

.operation-button--primary {
  color: #7c3aed;
  border-color: #e6dcff;
  background: #fff;
}

.operation-icon {
  font-size: 17px;
}

.operation-icon.is-spinning {
  animation: operation-rotate 0.8s linear infinite;
}

@keyframes operation-rotate {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

.diag-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.refresh-dialog {
  display: grid;
  justify-items: center;
  gap: 12px;
  padding: 2px 0 6px;
  text-align: center;
}

.refresh-dialog__icon {
  font-size: 28px;
  color: #2563eb;
}

.refresh-dialog__icon.is-success {
  color: #16a34a;
}

.refresh-dialog__icon.is-danger {
  color: #ef4444;
}

.refresh-dialog__message {
  color: #111827;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.6;
}

.diag-list {
  display: grid;
  gap: 10px;
}

.diag-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  border-radius: 10px;
  background: #f8fafc;
}

.diag-item__label {
  color: #111827;
  font-size: 14px;
  font-weight: 700;
}

.diag-item__desc {
  margin-top: 4px;
  color: #667085;
  font-size: 12px;
  line-height: 1.6;
}

.is-success {
  background: #22c55e;
  color: #fff;
}

.is-warning {
  background: #f59e0b;
  color: #fff;
}

.is-danger {
  background: #ef4444;
  color: #fff;
}

.is-neutral {
  background: #98a2b3;
  color: #fff;
}

@media (max-width: 640px) {
  .content {
    max-width: 100%;
  }

  .panel {
    margin-top: 14px;
    border-radius: 14px;
  }

  .panel :deep(.el-card__body) {
    padding: 18px 16px 16px;
  }

  .support-row,
  .diag-item {
    align-items: flex-start;
  }

  .support-row,
  .diag-item {
    flex-direction: column;
  }

  .info-row,
  .usage-row {
    align-items: center;
  }

  .notice-title-wrap {
    gap: 10px;
  }

  .info-row {
    min-height: 50px;
  }
}
</style>
