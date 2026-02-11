<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>告警消息</span>
        <el-button type="primary" size="small" link @click="handleViewAll">
          查看全部
        </el-button>
      </div>
    </template>

    <div v-loading="loading" class="alert-content">
      <div v-if="alerts.length > 0" class="alert-list">
        <div
          v-for="alert in alerts"
          :key="alert.id"
          class="alert-item"
          :class="[`alert-${alert.level}`, { 'is-read': alert.is_read }]"
        >
          <div class="alert-icon">
            <el-icon :size="20">
              <Warning v-if="alert.level === 'warning'" />
              <CircleClose v-else-if="alert.level === 'error'" />
              <InfoFilled v-else />
            </el-icon>
          </div>
          <div class="alert-body">
            <h4 class="alert-title">{{ alert.title }}</h4>
            <p class="alert-content-text">{{ alert.content }}</p>
            <span class="alert-time">{{ formatRelativeTime(alert.created_at) }}</span>
          </div>
        </div>
      </div>

      <el-empty v-else-if="!loading" description="暂无告警消息" />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Warning, CircleClose, InfoFilled } from '@element-plus/icons-vue'
import { dashboardApi, type Alert } from '@/api'
import { formatRelativeTime } from '@/utils/formatter'

const loading = ref(false)
const alerts = ref<Alert[]>([])

// 获取告警数据
const fetchAlerts = async () => {
  loading.value = true
  try {
    alerts.value = await dashboardApi.getAlerts(10)
  } catch (error) {
    console.error('获取告警列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 查看全部
const handleViewAll = () => {
  ElMessage.info('跳转到告警管理页面')
}

onMounted(() => {
  fetchAlerts()
})
</script>

<style scoped lang="scss">
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}

.alert-content {
  .alert-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
    max-height: 400px;
    overflow-y: auto;

    .alert-item {
      display: flex;
      gap: 12px;
      padding: 12px;
      background: #fafafa;
      border-radius: 8px;
      border-left: 3px solid transparent;
      transition: all 0.3s;

      &:hover {
        background: #f5f5f5;
      }

      &.is-read {
        opacity: 0.6;
      }

      &.alert-info {
        border-left-color: #1890ff;

        .alert-icon {
          color: #1890ff;
        }
      }

      &.alert-warning {
        border-left-color: #faad14;

        .alert-icon {
          color: #faad14;
        }
      }

      &.alert-error {
        border-left-color: #ff4d4f;

        .alert-icon {
          color: #ff4d4f;
        }
      }

      .alert-icon {
        flex-shrink: 0;
        margin-top: 2px;
      }

      .alert-body {
        flex: 1;
        min-width: 0;

        .alert-title {
          font-size: 14px;
          font-weight: 600;
          color: #262626;
          margin: 0 0 4px 0;
        }

        .alert-content-text {
          font-size: 13px;
          color: #595959;
          margin: 0 0 4px 0;
          line-height: 1.5;
        }

        .alert-time {
          font-size: 12px;
          color: #8c8c8c;
        }
      }
    }
  }
}
</style>






