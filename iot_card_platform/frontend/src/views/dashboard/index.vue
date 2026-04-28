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

    <!-- 核心统计卡片 -->
    <div class="stats-section">
      <div class="stat-grid">
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
          @click="router.push('/suspend/alerts')"
        />
      </div>
    </div>

    <!-- 运营商统计 -->
    <div class="carrier-section">
      <div class="carrier-grid">
        <stat-card label="中国移动" :value="formatNumber(getCarrierCount('cmcc'))" :icon="Phone" icon-color="#1890ff" icon-bg="#e6f7ff" extra="CMCC" clickable @click="router.push('/cards/list?carrier=cmcc')" />
        <stat-card label="中国联通" :value="formatNumber(getCarrierCount('cucc'))" :icon="Phone" icon-color="#ff4d4f" icon-bg="#fff1f0" extra="CUCC" clickable @click="router.push('/cards/list?carrier=cucc')" />
        <stat-card label="中国电信" :value="formatNumber(getCarrierCount('ctcc'))" :icon="Phone" icon-color="#52c41a" icon-bg="#f6ffed" extra="CTCC" clickable @click="router.push('/cards/list?carrier=ctcc')" />
        <stat-card label="本月到期卡" :value="formatNumber(overview?.cards?.expiring_count || 0)" :icon="Clock" icon-color="#fa8c16" icon-bg="#fff7e6" extra="即将到期" clickable @click="router.push('/cards/list?expiring=true')" />
        <stat-card label="超量卡" :value="formatNumber(overview?.cards?.over_usage_count || 0)" :icon="WarningFilled" icon-color="#ff4d4f" icon-bg="#fff1f0" extra="超套餐用量" clickable @click="router.push('/cards/list?over_usage=true')" />
      </div>
    </div>

    <!-- 账户余额 -->
    <div class="balance-section">
      <div class="balance-wrapper">
        <account-balance />
      </div>
    </div>

    <!-- 到期卡 + 超量卡 -->
    <div class="cards-section">
      <div class="card-list-wrapper">
        <expiring-card-list />
      </div>
      <div class="card-list-wrapper">
        <over-usage-card-list />
      </div>
    </div>

    <!-- 告警列表 -->
    <div class="alert-section">
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
  Phone,
  Clock,
  WarningFilled
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores'
import { dashboardApi } from '@/api'
import { formatNumber } from '@/utils/formatter'
import StatCard from './components/StatCard.vue'
import AccountBalance from './components/AccountBalance.vue'
import ExpiringCardList from './components/ExpiringCardList.vue'
import OverUsageCardList from './components/OverUsageCardList.vue'
import AlertList from './components/AlertList.vue'

const authStore = useAuthStore()
const router = useRouter()

// 用户信息
const userInfo = computed(() => authStore.userInfo)

// 概览数据
const overview = ref<any>(null)

// 获取状态统计
const getStatusCount = (status: string) => {
  const item = overview.value?.cards?.by_status?.find((s: any) => s.status === status)
  return item?.count || 0
}

// 获取运营商统计
const getCarrierCount = (carrier: string) => {
  const item = overview.value?.cards?.by_carrier?.find((c: any) => c.carrier === carrier)
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
  padding: 16px;
  background: #f0f2f5;
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;

  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    flex-shrink: 0;

    h2 {
      font-size: 18px;
      font-weight: 600;
      color: #262626;
      margin: 0 0 2px 0;
    }

    p {
      font-size: 12px;
      color: #8c8c8c;
      margin: 0;
    }
  }

  // 统计卡片区域
  .stats-section {
    margin-bottom: 12px;
    flex-shrink: 0;

    .stat-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
    }
  }

  // 运营商区域
  .carrier-section {
    margin-bottom: 12px;
    flex-shrink: 0;

    .carrier-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
    }
  }

  // 账户余额区域
  .balance-section {
    display: flex;
    margin-bottom: 12px;
    flex-shrink: 0;
    min-height: 0;

    .balance-wrapper {
      width: 280px;
      max-width: 100%;
    }
  }

  // 到期卡和超量卡区域
  .cards-section {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    flex: 1;
    min-height: 0;
    overflow: hidden;

    .card-list-wrapper {
      min-height: 0;
      overflow: auto;
    }
  }

  // 告警区域 - 隐藏或折叠
  .alert-section {
    display: none;
  }
}

@media (max-width: 1400px) {
  .dashboard-container {
    .stats-section .stat-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }
}

@media (max-width: 1200px) {
  .dashboard-container {
    .balance-section .balance-wrapper {
      width: 100%;
    }
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
        font-size: 16px;
      }
    }

    .stats-section .stat-grid,
    .carrier-section .carrier-grid {
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
    }

    .cards-section {
      grid-template-columns: 1fr;
      gap: 8px;
    }
  }
}
</style>
