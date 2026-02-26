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

    <!-- 核心统计卡片 - 4列 -->
    <div class="stat-grid stat-grid--4">
      <stat-card
        label="卡片总数"
        :value="formatNumber(overview?.cards?.total || 0)"
        :icon="CreditCard"
        icon-color="#1890ff"
        icon-bg="#e6f7ff"
        :extra="`激活: ${getStatusCount('activated')} | 库存: ${getStatusCount('stock')}`"
        extra-color="#52c41a"
        clickable
        @click="router.push('/cards/list')"
      />
      <stat-card
        label="流量池数量"
        :value="formatNumber(overview?.pools?.total_pools || 0)"
        :icon="Connection"
        icon-color="#52c41a"
        icon-bg="#f6ffed"
        extra="共享流量池"
        extra-color="#52c41a"
        clickable
        @click="router.push('/pools/list')"
      />
      <stat-card
        label="用户数量"
        :value="formatNumber(overview?.users?.total_users || 0)"
        :icon="User"
        icon-color="#722ed1"
        icon-bg="#f9f0ff"
        extra="平台用户"
        extra-color="#722ed1"
        clickable
        @click="router.push('/users')"
      />
      <stat-card
        label="告警数量"
        :value="formatNumber(overview?.alerts?.unhandled || 0)"
        :icon="Warning"
        icon-color="#ff4d4f"
        icon-bg="#fff1f0"
        :extra="overview?.alerts?.unhandled ? '需要处理' : '一切正常'"
        :extra-color="overview?.alerts?.unhandled ? '#ff4d4f' : '#52c41a'"
        clickable
        @click="router.push('/alerts')"
      />
    </div>

    <!-- 运营商统计 - 3列 -->
    <div class="stat-grid stat-grid--3">
      <stat-card label="中国移动" :value="formatNumber(getCarrierCount('cmcc'))" :icon="Phone" icon-color="#1890ff" icon-bg="#e6f7ff" extra="CMCC" clickable @click="router.push('/cards/list?carrier=cmcc')" />
      <stat-card label="中国联通" :value="formatNumber(getCarrierCount('cucc'))" :icon="Phone" icon-color="#ff4d4f" icon-bg="#fff1f0" extra="CUCC" clickable @click="router.push('/cards/list?carrier=cucc')" />
      <stat-card label="中国电信" :value="formatNumber(getCarrierCount('ctcc'))" :icon="Phone" icon-color="#52c41a" icon-bg="#f6ffed" extra="CTCC" clickable @click="router.push('/cards/list?carrier=ctcc')" />
    </div>

    <!-- 账户余额 + 流量池用量 -->
    <el-row :gutter="12" class="section-row">
      <el-col :xs="24" :md="8">
        <account-balance />
      </el-col>
      <el-col :xs="24" :md="16">
        <pool-usage-chart />
      </el-col>
    </el-row>

    <!-- 到期卡 + 超量卡 并排 -->
    <el-row :gutter="12" class="section-row">
      <el-col :xs="24" :lg="12">
        <expiring-card-list />
      </el-col>
      <el-col :xs="24" :lg="12">
        <over-usage-card-list />
      </el-col>
    </el-row>

    <!-- 告警列表 -->
    <div class="section-row">
      <alert-list />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
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
const router = useRouter()

// 用户信息
const userInfo = computed(() => authStore.userInfo)

// 概览数据
const overview = ref<{
  cards: {
    total: number
    by_status: Array<{
      status: string
      status_name: string
      count: number
    }>
    by_carrier: Array<{
      carrier: string
      carrier_name: string
      count: number
    }>
  }
  users: {
    total_users: number
    total_sub_users: number
    active_users: number
  }
  packages: {
    supplier_packages: number
    sale_packages: number
  }
  pools: {
    total_pools: number
    total_data: number
    used_data: number
    usage_percent: number
  }
  alerts: {
    warning: number
    critical: number
    exceed: number
    unhandled: number
  }
} | null>(null)

// 获取状态统计
const getStatusCount = (status: string) => {
  const item = overview.value?.cards?.by_status?.find(s => s.status === status)
  return item?.count || 0
}

// 获取运营商统计
const getCarrierCount = (carrier: string) => {
  const item = overview.value?.cards?.by_carrier?.find(c => c.carrier === carrier)
  return item?.count || 0
}

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
  padding: 16px 20px;
  background: #f0f2f5;
  min-height: 100vh;

  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;

    h2 {
      font-size: 20px;
      font-weight: 600;
      color: #262626;
      margin: 0 0 4px 0;
    }

    p {
      font-size: 13px;
      color: #8c8c8c;
      margin: 0;
    }
  }

  .stat-grid {
    display: grid;
    gap: 12px;
    margin-bottom: 12px;

    &--4 {
      grid-template-columns: repeat(4, 1fr);
    }

    &--3 {
      grid-template-columns: repeat(3, 1fr);
    }
  }

  .section-row {
    margin-bottom: 12px;
  }
}

@media (max-width: 1200px) {
  .dashboard-container .stat-grid--4 {
    grid-template-columns: repeat(2, 1fr);
  }
  .dashboard-container .stat-grid--3 {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 12px;

    .page-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 8px;

      h2 {
        font-size: 18px;
      }
    }

    .stat-grid {
      gap: 8px;

      &--4,
      &--3 {
        grid-template-columns: repeat(2, 1fr);
      }
    }
  }
}
</style>
