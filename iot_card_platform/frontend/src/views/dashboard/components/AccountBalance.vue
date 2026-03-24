<template>
  <el-card class="balance-card" shadow="never">
    <template #header>
      <div class="card-header">
        <span>账户余额</span>
        <div class="header-actions">
          <el-button size="small" @click="handleViewLogs">余额记录</el-button>
          <el-button type="primary" size="small" @click="handleRecharge">
            <el-icon><CreditCard /></el-icon>
            充值
          </el-button>
        </div>
      </div>
    </template>

    <div v-loading="loading" class="balance-content">
      <div class="balance-main">
        <p class="balance-label">当前余额</p>
        <h2 class="balance-value" :class="{ 'is-alert': balanceData?.is_alert }">
          {{ formatMoney(balanceData?.balance) }}
        </h2>
        <p v-if="balanceData?.is_alert" class="balance-alert">
          <el-icon><Warning /></el-icon>
          余额不足，请及时充值
        </p>
      </div>

      <el-divider />

      <div class="balance-info">
        <div class="info-item">
          <span class="info-label">预警阈值</span>
          <span class="info-value">{{ formatMoney(balanceData?.alert_threshold) }}</span>
        </div>
        <div v-if="balanceData?.last_recharge_at" class="info-item">
          <span class="info-label">最后充值</span>
          <span class="info-value">
            {{ formatMoney(balanceData?.last_recharge_amount) }}
            <span class="info-time">{{ formatRelativeTime(balanceData?.last_recharge_at) }}</span>
          </span>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { CreditCard, Warning } from '@element-plus/icons-vue'
import { dashboardApi, type AccountBalance } from '@/api'
import { formatMoney, formatRelativeTime } from '@/utils/formatter'
import { useRouter } from 'vue-router'

const loading = ref(false)
const balanceData = ref<AccountBalance | null>(null)
const router = useRouter()

// 获取余额数据
const fetchBalance = async () => {
  loading.value = true
  try {
    balanceData.value = await dashboardApi.getAccountBalance()
  } catch (error) {
    console.error('获取账户余额失败:', error)
  } finally {
    loading.value = false
  }
}

// 充值
const handleRecharge = () => {
  ElMessage.info('充值功能开发中...')
}

const handleViewLogs = () => {
  router.push('/records/balance')
}

onMounted(() => {
  fetchBalance()
})
</script>

<style scoped lang="scss">
.balance-card {
  border-radius: 12px;
  border: 1px solid #e8e8e8;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
  height: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  font-size: 14px;

  .header-actions {
    display: flex;
    gap: 8px;
  }
}

.balance-content {
  .balance-main {
    text-align: center;
    padding: 8px 0;

    .balance-label {
      font-size: 13px;
      color: #8c8c8c;
      margin: 0 0 8px 0;
    }

    .balance-value {
      font-size: 32px;
      font-weight: 600;
      color: #262626;
      margin: 0 0 6px 0;

      &.is-alert {
        color: #ff4d4f;
      }
    }

    .balance-alert {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 4px;
      font-size: 12px;
      color: #ff4d4f;
      margin: 0;
    }
  }

  .balance-info {
    .info-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 6px 0;

      .info-label {
        font-size: 13px;
        color: #8c8c8c;
      }

      .info-value {
        font-size: 13px;
        color: #262626;
        font-weight: 500;

        .info-time {
          font-size: 12px;
          color: #8c8c8c;
          margin-left: 6px;
        }
      }
    }
  }
}
</style>







