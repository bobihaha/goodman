<template>
  <el-card>
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
        <el-table-column prop="package_name" label="套餐" width="150" />
        <el-table-column prop="expired_at" label="到期日期" width="120">
          <template #default="{ row }">
            {{ formatDateShort(row.expired_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="days_left" label="剩余天数" width="100">
          <template #default="{ row }">
            <el-tag :type="getDaysLeftType(row.days_left)" size="small">
              {{ row.days_left }}天
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="handleRenew(row)">
              续费
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && expiringCards.length === 0" description="暂无到期卡片" />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { dashboardApi, type ExpiringCard } from '@/api'
import { formatCarrier, formatDateShort } from '@/utils/formatter'

const router = useRouter()
const loading = ref(false)
const expiringCards = ref<ExpiringCard[]>([])

// 获取到期卡数据
const fetchExpiringCards = async () => {
  loading.value = true
  try {
    expiringCards.value = await dashboardApi.getExpiringCards()
  } catch (error) {
    console.error('获取到期卡明细失败:', error)
  } finally {
    loading.value = false
  }
}

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
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}
</style>
