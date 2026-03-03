<template>
  <div class="card-list-page">
    <!-- 统计卡片 -->
    <div class="stats-row">
      <el-row :gutter="16">
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon total">
              <el-icon><CreditCard /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total }}</div>
              <div class="stat-label">总卡片数</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon activated">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.activated }}</div>
              <div class="stat-label">已激活</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon silent">
              <el-icon><Clock /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.silent }}</div>
              <div class="stat-label">沉默期</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon suspended">
              <el-icon><WarningFilled /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.suspended }}</div>
              <div class="stat-label">已停机</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 搜索和筛选 -->
    <el-card class="search-card" shadow="never">
      <el-form :model="searchForm" inline class="search-form">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="ICCID / MSISDN / 后6位"
            clearable
            style="width: 293px"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="状态">
          <el-select
            v-model="searchForm.status"
            placeholder="全部状态"
            clearable
            style="width: 213px"
          >
            <el-option
              v-for="item in CARD_STATUS_OPTIONS"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="运营商">
          <el-select
            v-model="searchForm.carrier"
            placeholder="全部运营商"
            clearable
            style="width: 213px"
          >
            <el-option
              v-for="item in CARRIER_OPTIONS"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="周期">
          <el-select
            v-model="searchForm.period_type"
            placeholder="全部周期"
            clearable
            style="width: 187px"
          >
            <el-option
              v-for="item in PERIOD_TYPE_OPTIONS"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="流量池">
          <el-select
            v-model="searchForm.is_pool_member"
            placeholder="全部"
            clearable
            style="width: 187px"
          >
            <el-option label="在池中" :value="true" />
            <el-option label="不在池中" :value="false" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><RefreshLeft /></el-icon>
            重置
          </el-button>
          <el-button link type="primary" @click="showAdvanced = !showAdvanced">
            <el-icon><ArrowDown v-if="!showAdvanced" /><ArrowUp v-else /></el-icon>
            {{ showAdvanced ? '收起' : '高级搜索' }}
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 高级搜索 -->
      <el-form v-if="showAdvanced" :model="searchForm" inline class="search-form advanced-form">
        <el-form-item label="关联客户">
          <el-select
            v-model="searchForm.customer_id"
            placeholder="全部客户"
            filterable
            remote
            clearable
            :remote-method="searchCustomers"
            :loading="customerLoading"
            style="width: 213px"
          >
            <el-option
              v-for="item in customerList"
              :key="item.id"
              :label="`${item.account} (${item.name})`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="备注">
          <el-input
            v-model="searchForm.remark"
            placeholder="备注关键词"
            clearable
            style="width: 187px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>

        <el-form-item label="出库单号">
          <el-input
            v-model.number="searchForm.batch_id"
            placeholder="批次ID"
            clearable
            style="width: 160px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>

        <el-form-item label="出库时间">
          <el-date-picker
            v-model="stockOutRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 280px"
          />
        </el-form-item>

        <el-form-item label="激活时间">
          <el-date-picker
            v-model="activatedRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 280px"
          />
        </el-form-item>

        <el-form-item label="到期时间">
          <el-date-picker
            v-model="expiredRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 280px"
          />
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作栏 -->
    <el-card class="toolbar-card" shadow="never">
      <div class="toolbar">
        <div class="toolbar-left">
          <el-button type="primary" @click="showBatchQueryDialog">
            <el-icon><Search /></el-icon>
            批量查询
          </el-button>
          <el-button
            type="success"
            @click="showBatchTransferDialog"
          >
            <el-icon><Connection /></el-icon>
            批量划拨
          </el-button>
          <el-button
            type="warning"
            @click="showBatchRemarkDialog"
          >
            <el-icon><Edit /></el-icon>
            批量备注
          </el-button>
          <el-button
            type="primary"
            @click="showBatchRenewDialog"
          >
            <el-icon><Refresh /></el-icon>
            批量续费
          </el-button>
          <el-button
            type="danger"
            @click="showBatchSuspendDialog"
          >
            <el-icon><CircleClose /></el-icon>
            批量停机
          </el-button>
          <el-button
            type="success"
            @click="showBatchResumeDialog"
          >
            <el-icon><CircleCheck /></el-icon>
            批量复机
          </el-button>
        </div>
        <div class="toolbar-right">
          <el-button @click="handleExport">
            <el-icon><Download /></el-icon>
            导出
          </el-button>
          <el-button @click="fetchCardList">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
      <div v-if="selectedCards.length > 0" class="selection-info">
        已选择 <span class="selection-count">{{ selectedCards.length }}</span> 张卡片
        <el-button type="text" @click="clearSelection">清空选择</el-button>
      </div>
    </el-card>

    <!-- 批量查询筛选提示 -->
    <div v-if="isBatchQueryMode" class="batch-query-bar">
      <el-icon><Filter /></el-icon>
      <span>批量查询结果：共 <strong>{{ cardList.length }}</strong> 张卡片</span>
      <span v-if="batchQueryNotFound.length > 0" class="not-found-info">
        ，未找到 <strong>{{ batchQueryNotFound.length }}</strong> 张
      </span>
      <el-button type="primary" link @click="clearBatchQuery">清除筛选</el-button>
    </div>

    <!-- 卡片列表 -->
    <el-card class="table-card" shadow="never">
      <el-table
        v-loading="loading"
        :data="cardList"
        border
        stripe
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column prop="iccid" label="ICCID" width="200" fixed>
          <template #default="{ row }">
            <el-link type="primary" @click="viewDetail(row.id)">
              {{ row.iccid }}
            </el-link>
          </template>
        </el-table-column>

        <el-table-column prop="imsi" label="IMSI" width="180" />

        <el-table-column prop="msisdn" label="号码" width="130" />

        <el-table-column prop="card_type" label="卡片类型" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.card_type === 'pool'" type="success" size="small">
              流量池卡
            </el-tag>
            <el-tag v-else type="info" size="small">
              单卡
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="carrier" label="运营商" width="100">
          <template #default="{ row }">
            {{ CARRIER_MAP[row.carrier] }}
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="CARD_STATUS_MAP[row.status].type">
              {{ CARD_STATUS_MAP[row.status].label }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="本月用量" width="120">
          <template #default="{ row }">
            {{ formatFlow(row.data_used_month) }}
          </template>
        </el-table-column>

        <el-table-column label="套餐总量" width="120">
          <template #default="{ row }">
            {{ formatFlow(row.data_total) }}
          </template>
        </el-table-column>

        <el-table-column label="已用量" width="120">
          <template #default="{ row }">
            {{ formatFlow(row.data_used) }}
          </template>
        </el-table-column>

        <el-table-column label="流量使用" width="200">
          <template #default="{ row }">
            <div class="flow-usage">
              <el-progress
                :percentage="formatUsagePercent(row.data_used, row.data_total)"
                :color="getProgressColor(formatUsagePercent(row.data_used, row.data_total))"
                :format="(val: number) => `${Math.round(val)}%`"
              />
              <div class="flow-text">
                {{ formatFlow(row.data_used) }} / {{ formatFlow(row.data_total) }}
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="套餐规格" width="120">
          <template #default="{ row }">
            {{ formatFlow(row.flow_size) }}/{{ PERIOD_TYPE_MAP[row.period_type] }}
          </template>
        </el-table-column>

        <el-table-column prop="test_expire_date" label="测试期" width="110">
          <template #default="{ row }">
            <span v-if="row.test_expire_date">{{ row.test_expire_date }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="silent_expire_date" label="沉默期" width="110">
          <template #default="{ row }">
            <span v-if="row.silent_expire_date">{{ row.silent_expire_date }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="activated_at" label="激活日期" width="110">
          <template #default="{ row }">
            <span v-if="row.activated_at">{{ row.activated_at }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="stock_out_at" label="出库日期" width="110">
          <template #default="{ row }">
            <span v-if="row.stock_out_at">{{ formatDateShort(row.stock_out_at) }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="expired_at" label="到期日期" width="110">
          <template #default="{ row }">
            <span :class="{ 'text-danger': isExpired(row.expired_at) }">
              {{ row.expired_at || '-' }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="流量池" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_pool_member" type="success" size="small">
              在池中
            </el-tag>
            <el-tag v-else type="info" size="small">
              未入池
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="remark" label="备注" min-width="150" show-overflow-tooltip />

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="text" size="small" @click="viewDetail(row.id)">
              详情
            </el-button>
            <el-button type="text" size="small" @click="showTransferDialog(row)">
              划拨
            </el-button>
            <el-button type="text" size="small" @click="showRemarkDialog(row)">
              备注
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div v-if="!isBatchQueryMode" class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[20, 50, 100, 200]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 批量查询对话框 -->
    <BatchQueryDialog
      v-model="batchQueryVisible"
      @success="handleBatchQuerySuccess"
    />

    <!-- 批量划拨对话框 -->
    <BatchTransferDialog
      v-model="batchTransferVisible"
      @success="handleBatchTransferSuccess"
    />

    <!-- 批量备注对话框 -->
    <BatchRemarkDialog
      v-model="batchRemarkVisible"
      @success="handleBatchRemarkSuccess"
    />

    <!-- 批量续费对话框 -->
    <BatchRenewDialog
      v-model="batchRenewVisible"
      @success="handleBatchRenewSuccess"
    />

    <!-- 批量停机对话框 -->
    <BatchSuspendDialog
      v-model="batchSuspendVisible"
      @success="handleBatchSuspendSuccess"
    />

    <!-- 批量复机对话框 -->
    <BatchResumeDialog
      v-model="batchResumeVisible"
      @success="handleBatchResumeSuccess"
    />

    <!-- 单卡划拨对话框 -->
    <TransferDialog
      v-model="transferVisible"
      :card="currentCard"
      @success="handleTransferSuccess"
    />

    <!-- 单卡备注对话框 -->
    <RemarkDialog
      v-model="remarkVisible"
      :card="currentCard"
      @success="handleRemarkSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  CreditCard,
  CircleCheck,
  Clock,
  WarningFilled,
  Search,
  RefreshLeft,
  Connection,
  Edit,
  Refresh,
  CircleClose,
  Download,
  Filter,
  ArrowDown,
  ArrowUp
} from '@element-plus/icons-vue'
import { cardApi } from '@/api'
import { userApi } from '@/api'
import type { Card, CardListParams, CardStats } from '@/types/card'
import type { User } from '@/types/user'
import {
  CARRIER_MAP,
  CARRIER_OPTIONS,
  CARD_STATUS_MAP,
  CARD_STATUS_OPTIONS,
  PERIOD_TYPE_MAP,
  PERIOD_TYPE_OPTIONS
} from '@/constants/card'
import { formatFlow, formatDateShort, formatUsagePercent, isExpired } from '@/utils/formatter'
import BatchQueryDialog from './components/BatchQueryDialog.vue'
import BatchTransferDialog from './components/BatchTransferDialog.vue'
import BatchRemarkDialog from './components/BatchRemarkDialog.vue'
import BatchRenewDialog from './components/BatchRenewDialog.vue'
import BatchSuspendDialog from './components/BatchSuspendDialog.vue'
import BatchResumeDialog from './components/BatchResumeDialog.vue'
import TransferDialog from './components/TransferDialog.vue'
import RemarkDialog from './components/RemarkDialog.vue'

const router = useRouter()

// 数据
const loading = ref(false)
const cardList = ref<Card[]>([])
const selectedCards = ref<Card[]>([])
const currentCard = ref<Card | null>(null)
const isBatchQueryMode = ref(false)
const batchQueryNotFound = ref<string[]>([])
const showAdvanced = ref(false)
const customerLoading = ref(false)
const customerList = ref<User[]>([])
const stockOutRange = ref<string[]>([])
const activatedRange = ref<string[]>([])
const expiredRange = ref<string[]>([])

// 统计数据
const stats = ref<CardStats>({
  total: 0,
  stock: 0,
  testing: 0,
  silent: 0,
  activated: 0,
  expired: 0,
  suspended: 0,
  cancelled: 0,
  by_carrier: {
    cmcc: 0,
    cucc: 0,
    ctcc: 0
  }
})

// 搜索表单
const searchForm = reactive<CardListParams>({
  keyword: '',
  status: undefined,
  carrier: undefined,
  period_type: undefined,
  is_pool_member: undefined,
  remark: undefined,
  customer_id: undefined,
  batch_id: undefined
})

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 对话框显示状态
const batchQueryVisible = ref(false)
const batchTransferVisible = ref(false)
const batchRemarkVisible = ref(false)
const batchRenewVisible = ref(false)
const batchSuspendVisible = ref(false)
const batchResumeVisible = ref(false)
const transferVisible = ref(false)
const remarkVisible = ref(false)

// 计算属性
const selectedCardIds = computed(() => selectedCards.value.map(card => card.id))

// 获取卡片列表
const fetchCardList = async () => {
  loading.value = true
  try {
    const params: CardListParams = {
      page: pagination.page,
      page_size: pagination.page_size,
      ...searchForm,
      stock_out_start: stockOutRange.value?.[0] || undefined,
      stock_out_end: stockOutRange.value?.[1] || undefined,
      activated_start: activatedRange.value?.[0] || undefined,
      activated_end: activatedRange.value?.[1] || undefined,
      expired_start: expiredRange.value?.[0] || undefined,
      expired_end: expiredRange.value?.[1] || undefined
    }
    
    const response = await cardApi.getList(params)
    
    // 计算使用率
    cardList.value = response.items.map(card => ({
      ...card,
      usage_percent: formatUsagePercent(card.data_used, card.data_total)
    }))
    
    pagination.total = response.total
  } catch (error) {
    console.error('获取卡片列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 获取统计数据
const fetchStats = async () => {
  try {
    stats.value = await cardApi.getStats()
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

// 搜索客户
const searchCustomers = async (query: string) => {
  customerLoading.value = true
  try {
    const response = await userApi.getList({
      keyword: query || undefined,
      page: 1,
      page_size: 50
    })
    customerList.value = response.list
  } catch (error) {
    console.error('搜索客户失败:', error)
  } finally {
    customerLoading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchCardList()
}

// 重置
const handleReset = () => {
  Object.assign(searchForm, {
    keyword: '',
    status: undefined,
    carrier: undefined,
    period_type: undefined,
    is_pool_member: undefined,
    remark: undefined,
    customer_id: undefined,
    batch_id: undefined
  })
  stockOutRange.value = []
  activatedRange.value = []
  expiredRange.value = []
  handleSearch()
}

// 分页变化
const handlePageChange = (page: number) => {
  pagination.page = page
  fetchCardList()
}

const handleSizeChange = (size: number) => {
  pagination.page_size = size
  pagination.page = 1
  fetchCardList()
}

// 选择变化
const handleSelectionChange = (selection: Card[]) => {
  selectedCards.value = selection
}

// 清空选择
const clearSelection = () => {
  selectedCards.value = []
}

// 查看详情
const viewDetail = (id: number) => {
  router.push(`/cards/detail/${id}`)
}

// 显示批量查询对话框
const showBatchQueryDialog = () => {
  batchQueryVisible.value = true
}

// 显示批量划拨对话框
const showBatchTransferDialog = () => {
  batchTransferVisible.value = true
}

// 显示批量备注对话框
const showBatchRemarkDialog = () => {
  batchRemarkVisible.value = true
}

// 显示批量续费对话框
const showBatchRenewDialog = () => {
  batchRenewVisible.value = true
}

// 显示批量停机对话框
const showBatchSuspendDialog = () => {
  batchSuspendVisible.value = true
}

// 显示批量复机对话框
const showBatchResumeDialog = () => {
  batchResumeVisible.value = true
}

// 导出
const handleExport = async () => {
  try {
    const params = {
      ...searchForm,
      card_ids: selectedCardIds.value.length > 0 ? selectedCardIds.value : undefined
    }

    const blob = await cardApi.export(params)
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `卡片列表_${new Date().getTime()}.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)

    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
  }
}

// 显示单卡划拨对话框
const showTransferDialog = (card: Card) => {
  currentCard.value = card
  transferVisible.value = true
}

// 显示单卡备注对话框
const showRemarkDialog = (card: Card) => {
  currentCard.value = card
  remarkVisible.value = true
}

// 批量查询成功回调
const handleBatchQuerySuccess = (data: { found: Card[]; not_found: string[] }) => {
  isBatchQueryMode.value = true
  batchQueryNotFound.value = data.not_found
  cardList.value = data.found.map(card => ({
    ...card,
    usage_percent: formatUsagePercent(card.data_used, card.data_total)
  }))
  pagination.total = data.found.length
  pagination.page = 1
}

// 清除批量查询筛选
const clearBatchQuery = () => {
  isBatchQueryMode.value = false
  batchQueryNotFound.value = []
  fetchCardList()
}

// 批量划拨成功回调
const handleBatchTransferSuccess = () => {
  clearSelection()
  fetchCardList()
  fetchStats()
}

// 批量备注成功回调
const handleBatchRemarkSuccess = () => {
  clearSelection()
  fetchCardList()
}

// 批量续费成功回调
const handleBatchRenewSuccess = () => {
  clearSelection()
  fetchCardList()
}

// 批量停机成功回调
const handleBatchSuspendSuccess = () => {
  clearSelection()
  fetchCardList()
  fetchStats()
}

// 批量复机成功回调
const handleBatchResumeSuccess = () => {
  clearSelection()
  fetchCardList()
  fetchStats()
}

// 单卡划拨成功回调
const handleTransferSuccess = () => {
  fetchCardList()
  fetchStats()
}

// 单卡备注成功回调
const handleRemarkSuccess = () => {
  fetchCardList()
}

// 获取进度条颜色
const getProgressColor = (percent: number) => {
  if (percent >= 90) return '#F56C6C'
  if (percent >= 80) return '#E6A23C'
  return '#67C23A'
}

// 初始化
onMounted(() => {
  fetchCardList()
  fetchStats()
})
</script>

<style scoped lang="scss">
.card-list-page {
  padding: 16px 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
  font-size: 14px;
  color: #1d2129;
}

.stats-row {
  margin-bottom: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  transition: all 0.3s;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .stat-icon {
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 10px;
    font-size: 22px;
    margin-right: 14px;

    &.total {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: #fff;
    }

    &.activated {
      background: linear-gradient(135deg, #67C23A 0%, #85ce61 100%);
      color: #fff;
    }

    &.silent {
      background: linear-gradient(135deg, #E6A23C 0%, #f0c78a 100%);
      color: #fff;
    }

    &.suspended {
      background: linear-gradient(135deg, #F56C6C 0%, #f89898 100%);
      color: #fff;
    }
  }

  .stat-content {
    flex: 1;

    .stat-value {
      font-size: 24px;
      font-weight: 600;
      color: #1d2129;
      line-height: 1.2;
      margin-bottom: 4px;
    }

    .stat-label {
      font-size: 13px;
      color: #86909c;
    }
  }
}

.search-card,
.toolbar-card,
.table-card {
  margin-bottom: 12px;
}

.search-card {
  :deep(.el-card__body) {
    padding: 16px 20px 8px;
  }
}

.search-form {
  :deep(.el-form-item) {
    margin-bottom: 10px;
    margin-right: 16px;
  }

  :deep(.el-form-item__label) {
    font-size: 13px;
    color: #4e5969;
    font-weight: 500;
  }

  :deep(.el-input__wrapper),
  :deep(.el-select .el-input__wrapper) {
    height: 36px;
    font-size: 13px;
  }

  &.advanced-form {
    border-top: 1px dashed #e5e6eb;
    padding-top: 12px;
    margin-top: 4px;
  }
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;

  .toolbar-left,
  .toolbar-right {
    display: flex;
    gap: 8px;
  }

  :deep(.el-button) {
    font-size: 13px;
    padding: 8px 14px;
  }
}

.selection-info {
  padding: 10px 14px;
  background: #e8f3ff;
  border-radius: 4px;
  color: #165dff;
  font-size: 13px;

  .selection-count {
    font-weight: 600;
    font-size: 14px;
    margin: 0 4px;
  }
}

.flow-usage {
  .flow-text {
    font-size: 12px;
    color: #86909c;
    margin-top: 2px;
  }
}

.batch-query-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  margin-bottom: 12px;
  background: #fff7e6;
  border: 1px solid #ffe4b5;
  border-radius: 6px;
  font-size: 13px;
  color: #d46b08;

  strong {
    font-size: 14px;
    margin: 0 2px;
  }

  .not-found-info {
    color: #F56C6C;
  }
}

.text-danger {
  color: #F56C6C;
}

.text-muted {
  color: #c9cdd4;
}

.table-card {
  :deep(.el-table) {
    font-size: 13px;

    th.el-table__cell {
      background: #f7f8fa;
      color: #4e5969;
      font-weight: 500;
      font-size: 13px;
      padding: 10px 0;
    }

    td.el-table__cell {
      padding: 8px 0;
      color: #1d2129;
    }

    .el-tag {
      font-size: 12px;
    }
  }

  :deep(.el-card__body) {
    padding: 16px 20px;
  }
}

.toolbar-card {
  :deep(.el-card__body) {
    padding: 14px 20px;
  }
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;

  :deep(.el-pagination) {
    font-size: 13px;
  }
}
</style>
