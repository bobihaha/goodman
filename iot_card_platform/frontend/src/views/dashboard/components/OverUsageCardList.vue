<template>
  <el-card class="over-usage-card" shadow="never">
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
        :max-height="280"
        size="small"
      >
        <el-table-column prop="iccid" label="ICCID" min-width="150" show-overflow-tooltip />
        <el-table-column prop="msisdn" label="号码" min-width="100" show-overflow-tooltip />
        <el-table-column prop="carrier" label="运营商" width="70">
          <template #default="{ row }">
            {{ formatCarrier(row.carrier) }}
          </template>
        </el-table-column>
        <el-table-column prop="user_name" label="客户" min-width="80" show-overflow-tooltip />
        <el-table-column prop="data_used" label="已用" width="80">
          <template #default="{ row }">
            {{ formatFlowSize(row.data_used) }}
          </template>
        </el-table-column>
        <el-table-column prop="usage_percent" label="使用率" width="70">
          <template #default="{ row }">
            <el-tag type="danger" size="small">
              {{ formatPercent(row.usage_percent) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="over_usage" label="超量" width="80">
          <template #default="{ row }">
            <span style="color: #ff4d4f; font-weight: 600;">
              {{ formatFlowSize(row.over_usage) }}
            </span>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && overUsageCards.length === 0" description="暂无超量卡片" :image-size="80" />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { dashboardApi, type OverUsageCard } from '@/api'
import { formatCarrier, formatFlowSize, formatPercent } from '@/utils/formatter'

const props = defineProps<{
  carrier?: string
}>()

const router = useRouter()
const loading = ref(false)
const overUsageCards = ref<OverUsageCard[]>([])

// 获取超量卡数据
const fetchOverUsageCards = async () => {
  loading.value = true
  try {
    overUsageCards.value = await dashboardApi.getOverUsageCards(props.carrier)
  } catch (error) {
    console.error('获取超量卡明细失败:', error)
  } finally {
    loading.value = false
  }
}

// 监听 carrier 变化
watch(() => props.carrier, () => {
  fetchOverUsageCards()
})

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
  router.push({ path: '/cards/list', query: { over_usage: 'true' } })
}

onMounted(() => {
  fetchOverUsageCards()
})
</script>

<style scoped lang="scss">
.over-usage-card {
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
}
</style>
