<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>超套餐用量卡明细</span>
        <el-button type="primary" size="small" link @click="handleViewAll">
          查看全部
        </el-button>
      </div>
    </template>

    <div v-loading="loading">
      <el-table
        :data="overUsageCards"
        style="width: 100%"
        :max-height="400"
      >
        <el-table-column prop="iccid" label="ICCID" width="180" />
        <el-table-column prop="msisdn" label="号码" width="120" />
        <el-table-column prop="carrier" label="运营商" width="100">
          <template #default="{ row }">
            {{ formatCarrier(row.carrier) }}
          </template>
        </el-table-column>
        <el-table-column prop="user_name" label="所属客户" width="120" />
        <el-table-column prop="data_used" label="已用流量" width="120">
          <template #default="{ row }">
            {{ formatFlowSize(row.data_used) }}
          </template>
        </el-table-column>
        <el-table-column prop="data_total" label="套餐流量" width="120">
          <template #default="{ row }">
            {{ formatFlowSize(row.data_total) }}
          </template>
        </el-table-column>
        <el-table-column prop="usage_percent" label="使用率" width="100">
          <template #default="{ row }">
            <el-tag type="danger" size="small">
              {{ formatPercent(row.usage_percent) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="over_usage" label="超量流量" width="120">
          <template #default="{ row }">
            <span style="color: #ff4d4f; font-weight: 600;">
              {{ formatFlowSize(row.over_usage) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="warning" size="small" link @click="handleSuspend(row)">
              停机
            </el-button>
            <el-button type="primary" size="small" link @click="handleRecharge(row)">
              充值
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && overUsageCards.length === 0" description="暂无超量卡片" />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { dashboardApi, type OverUsageCard } from '@/api'
import { formatCarrier, formatFlowSize, formatPercent } from '@/utils/formatter'

const loading = ref(false)
const overUsageCards = ref<OverUsageCard[]>([])

// 获取超量卡数据
const fetchOverUsageCards = async () => {
  loading.value = true
  try {
    overUsageCards.value = await dashboardApi.getOverUsageCards()
  } catch (error) {
    console.error('获取超量卡明细失败:', error)
  } finally {
    loading.value = false
  }
}

// 停机
const handleSuspend = (card: OverUsageCard) => {
  ElMessage.warning(`停机卡片: ${card.iccid}`)
}

// 充值
const handleRecharge = (card: OverUsageCard) => {
  ElMessage.info(`充值卡片: ${card.iccid}`)
}

// 查看全部
const handleViewAll = () => {
  ElMessage.info('跳转到卡片管理页面')
}

onMounted(() => {
  fetchOverUsageCards()
})
</script>

<style scoped lang="scss">
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}
</style>



