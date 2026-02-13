<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>流量池用量实时百分比</span>
        <el-button type="primary" size="small" link @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </template>

    <div v-loading="loading" class="pool-usage-content">
      <div v-if="poolUsageList.length > 0" class="pool-list">
        <div
          v-for="pool in poolUsageList"
          :key="pool.id"
          class="pool-item"
          :class="{ 'is-alert': pool.is_alert }"
        >
          <div class="pool-header">
            <div class="pool-info">
              <h4 class="pool-name">{{ pool.name }}</h4>
              <span class="pool-meta">
                {{ formatCarrier(pool.carrier) }} · {{ pool.card_count }}张卡
              </span>
            </div>
            <div class="pool-percent" :class="{ 'is-alert': pool.is_alert }">
              {{ formatPercent(pool.usage_percent) }}
            </div>
          </div>

          <div class="pool-progress">
            <el-progress
              :percentage="pool.usage_percent"
              :color="getProgressColor(pool.usage_percent)"
              :show-text="false"
            />
          </div>

          <div class="pool-footer">
            <span class="pool-usage">
              已用: {{ formatFlowSize(pool.data_used) }}
            </span>
            <span class="pool-total">
              总量: {{ formatFlowSize(pool.data_total) }}
            </span>
          </div>
        </div>
      </div>

      <el-empty v-else-if="!loading" description="暂无流量池数据" />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { dashboardApi, type PoolUsage } from '@/api'
import { formatCarrier, formatFlowSize, formatPercent } from '@/utils/formatter'

const loading = ref(false)
const poolUsageList = ref<PoolUsage[]>([])

// 获取流量池用量数据
const fetchPoolUsage = async () => {
  loading.value = true
  try {
    poolUsageList.value = await dashboardApi.getPoolsUsagePercent()
  } catch (error) {
    console.error('获取流量池用量失败:', error)
  } finally {
    loading.value = false
  }
}

// 获取进度条颜色
const getProgressColor = (percent: number): string => {
  if (percent >= 90) return '#ff4d4f'
  if (percent >= 80) return '#faad14'
  if (percent >= 60) return '#1890ff'
  return '#52c41a'
}

// 刷新
const handleRefresh = () => {
  fetchPoolUsage()
  ElMessage.success('刷新成功')
}

onMounted(() => {
  fetchPoolUsage()
})
</script>

<style scoped lang="scss">
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}

.pool-usage-content {
  .pool-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
    max-height: 500px;
    overflow-y: auto;

    .pool-item {
      padding: 16px;
      background: #fafafa;
      border-radius: 8px;
      border: 1px solid #f0f0f0;
      transition: all 0.3s;

      &:hover {
        background: #f5f5f5;
        border-color: #d9d9d9;
      }

      &.is-alert {
        background: #fff1f0;
        border-color: #ffccc7;
      }

      .pool-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;

        .pool-info {
          flex: 1;
          min-width: 0;

          .pool-name {
            font-size: 15px;
            font-weight: 600;
            color: #262626;
            margin: 0 0 4px 0;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }

          .pool-meta {
            font-size: 12px;
            color: #8c8c8c;
          }
        }

        .pool-percent {
          font-size: 20px;
          font-weight: 600;
          color: #262626;
          margin-left: 16px;

          &.is-alert {
            color: #ff4d4f;
          }
        }
      }

      .pool-progress {
        margin-bottom: 8px;
      }

      .pool-footer {
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 12px;
        color: #8c8c8c;

        .pool-usage {
          color: #1890ff;
          font-weight: 500;
        }
      }
    }
  }
}
</style>








