<template>
  <div class="dashboard-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div>
        <h2>仪表盘</h2>
        <p>欢迎回来，{{ userInfo?.name || userInfo?.account }}</p>
      </div>
      <el-button type="primary" @click="handleRefreshAll">
        <el-icon><Refresh /></el-icon>
        刷新数据
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :xs="24" :sm="12" :md="6">
        <stat-card
          label="卡片总数"
          :value="formatNumber(overview?.card_stats.total || 0)"
          :icon="CreditCard"
          icon-color="#1890ff"
          icon-bg="#e6f7ff"
          :extra="`激活: ${overview?.card_stats.activated || 0} | 库存: ${overview?.card_stats.stock || 0}`"
          extra-color="#52c41a"
        />
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <stat-card
          label="流量池数量"
          :value="formatNumber(overview?.pool_count || 0)"
          :icon="Connection"
          icon-color="#52c41a"
          icon-bg="#f6ffed"
          extra="共享流量池"
          extra-color="#52c41a"
        />
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <stat-card
          label="用户数量"
          :value="formatNumber(overview?.user_count || 0)"
          :icon="User"
          icon-color="#722ed1"
          icon-bg="#f9f0ff"
          extra="平台用户"
          extra-color="#722ed1"
        />
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <stat-card
          label="告警数量"
          :value="formatNumber(overview?.alert_count || 0)"
          :icon="Warning"
          icon-color="#ff4d4f"
          icon-bg="#fff1f0"
          :extra="overview?.alert_count ? '需要处理' : '一切正常'"
          :extra-color="overview?.alert_count ? '#ff4d4f' : '#52c41a'"
        />
      </el-col>
    </el-row>

    <!-- 运营商卡片分布 -->
    <el-row :gutter="16" class="carrier-row">
      <el-col :xs="24" :sm="8">
        <stat-card
          label="中国移动"
          :value="formatNumber(overview?.card_stats.by_carrier.cmcc || 0)"
          :icon="Phone"
          icon-color="#1890ff"
          icon-bg="#e6f7ff"
          extra="CMCC"
        />
      </el-col>

      <el-col :xs="24" :sm="8">
        <stat-card
          label="中国联通"
          :value="formatNumber(overview?.card_stats.by_carrier.cucc || 0)"
          :icon="Phone"
          icon-color="#ff4d4f"
          icon-bg="#fff1f0"
          extra="CUCC"
        />
      </el-col>

      <el-col :xs="24" :sm="8">
        <stat-card
          label="中国电信"
          :value="formatNumber(overview?.card_stats.by_carrier.ctcc || 0)"
          :icon="Phone"
          icon-color="#52c41a"
          icon-bg="#f6ffed"
          extra="CTCC"
        />
      </el-col>
    </el-row>

    <!-- 账户余额和流量池用量 -->
    <el-row :gutter="16" class="balance-pool-row">
      <el-col :xs="24" :md="8">
        <account-balance />
      </el-col>

      <el-col :xs="24" :md="16">
        <pool-usage-chart />
      </el-col>
    </el-row>

    <!-- 到期卡明细 -->
    <el-row :gutter="16" class="expiring-row">
      <el-col :span="24">
        <expiring-card-list />
      </el-col>
    </el-row>

    <!-- 超量卡明细 -->
    <el-row :gutter="16" class="over-usage-row">
      <el-col :span="24">
        <over-usage-card-list />
      </el-col>
    </el-row>

    <!-- 告警列表 -->
    <el-row :gutter="16" class="alert-row">
      <el-col :span="24">
        <alert-list />
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Refresh, 
  CreditCard, 
  Connection, 
  User, 
  Warning,
  Phone
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores'
import { dashboardApi } from '@/api'
import { formatNumber } from '@/utils/formatter'
import StatCard from './components/StatCard.vue'
import AccountBalance from './components/AccountBalance.vue'
import ExpiringCardList from './components/ExpiringCardList.vue'
import OverUsageCardList from './components/OverUsageCardList.vue'
import PoolUsageChart from './components/PoolUsageChart.vue'
import AlertList from './components/AlertList.vue'

const authStore = useAuthStore()

// 用户信息
const userInfo = computed(() => authStore.userInfo)

// 概览数据
const overview = ref<{
  card_stats: {
    total: number
    stock: number
    testing: number
    silent: number
    activated: number
    expired: number
    suspended: number
    cancelled: number
    by_carrier: {
      cmcc: number
      cucc: number
      ctcc: number
    }
  }
  pool_count: number
  user_count: number
  alert_count: number
} | null>(null)

// 获取概览数据
const fetchOverview = async () => {
  try {
    overview.value = await dashboardApi.getOverview()
  } catch (error) {
    console.error('获取概览数据失败:', error)
  }
}

// 刷新所有数据
const handleRefreshAll = async () => {
  await fetchOverview()
  ElMessage.success('数据已刷新')
}

onMounted(async () => {
  // 获取用户信息
  if (!authStore.userInfo) {
    try {
      await authStore.getUserInfo()
    } catch (error) {
      console.error('获取用户信息失败:', error)
    }
  }

  // 获取概览数据
  await fetchOverview()
})
</script>

<style scoped lang="scss">
.dashboard-container {
  padding: 24px;
  background: #f0f2f5;
  min-height: 100vh;

  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;

    h2 {
      font-size: 24px;
      font-weight: 600;
      color: #262626;
      margin: 0 0 8px 0;
    }

    p {
      font-size: 14px;
      color: #8c8c8c;
      margin: 0;
    }
  }

  .stat-row,
  .carrier-row,
  .balance-pool-row,
  .expiring-row,
  .over-usage-row,
  .alert-row {
    margin-bottom: 16px;
  }
}

// 响应式布局
@media (max-width: 768px) {
  .dashboard-container {
    padding: 16px;

    .page-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 12px;

      h2 {
        font-size: 20px;
      }
    }
  }
}
</style>
