<template>
  <el-card class="expiring-card" shadow="never">
    <template #header>
      <div class="card-header">
        <span>本月到期卡明细</span>
        <el-button type="primary" size="small" link @click="handleViewAll">
          查看全部
        </el-button>
      </div>
    </template>

    <div v-loading="loading">
      <el-table
        :data="expiringCards"
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
        <el-table-column prop="expired_at" label="到期日期" width="90">
          <template #default="{ row }">
            {{ formatDateShort(row.expired_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="days_left" label="剩余" width="60">
          <template #default="{ row }">
            <el-tag :type="getDaysLeftType(row.days_left)" size="small">
              {{ row.days_left }}天
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && expiringCards.length === 0" description="暂无到期卡片" :image-size="80" />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { dashboardApi, type ExpiringCard } from '@/api'
import { formatCarrier, formatDateShort } from '@/utils/formatter'

const props = defineProps<{
  carrier?: string
}>()

const router = useRouter()
const loading = ref(false)
const expiringCards = ref<ExpiringCard[]>([])

// 获取到期卡数据
const fetchExpiringCards = async () => {
  loading.value = true
  try {
    expiringCards.value = await dashboardApi.getExpiringCards(props.carrier)
  } catch (error) {
    console.error('获取到期卡明细失败:', error)
  } finally {
    loading.value = false
  }
}

// 监听 carrier 变化
watch(() => props.carrier, () => {
  fetchExpiringCards()
})

// 获取剩余天数标签类型
const getDaysLeftType = (days: number): string => {
  if (days <= 3) return 'danger'
  if (days <= 7) return 'warning'
  return 'success'
}

// 续费
const handleRenew = (card: ExpiringCard) => {
  ElMessage.info(`续费卡片: ${card.iccid}`)
}

// 查看全部
const handleViewAll = () => {
  router.push('/cards/list')
}

onMounted(() => {
  fetchExpiringCards()
})
</script>

<style scoped lang="scss">
.expiring-card {
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
