<template>
  <div class="suspend-alerts-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>停卡告警</span>
        </div>
      </template>

      <!-- 筛选栏 -->
      <div class="filter-bar">
        <el-radio-group v-model="filterType" @change="handleFilterChange">
          <el-radio-button label="">全部</el-radio-button>
          <el-radio-button label="card">单卡</el-radio-button>
          <el-radio-button label="pool">流量池</el-radio-button>
        </el-radio-group>
        <el-radio-group v-model="filterLevel" @change="handleFilterChange" style="margin-left: 20px">
          <el-radio-button label="">全部级别</el-radio-button>
          <el-radio-button label="warning">警告</el-radio-button>
          <el-radio-button label="critical">紧急</el-radio-button>
          <el-radio-button label="exceed">超限</el-radio-button>
        </el-radio-group>
        <el-radio-group v-model="filterHandled" @change="handleFilterChange" style="margin-left: 20px">
          <el-radio-button label="">全部</el-radio-button>
          <el-radio-button :label="false">未处理</el-radio-button>
          <el-radio-button :label="true">已处理</el-radio-button>
        </el-radio-group>
      </div>

      <!-- 告警列表 -->
      <el-table :data="alertList" v-loading="loading" border>
        <el-table-column prop="target_type_name" label="目标类型" width="100" />
        <el-table-column prop="target_name" label="目标名称" min-width="150">
          <template #default="{ row }">
            {{ row.target_name || `ID: ${row.target_id}` }}
          </template>
        </el-table-column>
        <el-table-column prop="alert_level" label="告警级别" width="100">
          <template #default="{ row }">
            <el-tag :type="getAlertLevelTag(row.alert_level)">
              {{ row.alert_level_name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="用量/阈值" width="150">
          <template #default="{ row }">
            <span :style="{ color: row.usage_percent >= row.threshold ? '#f56c6c' : '' }">
              {{ row.usage_percent }}%
            </span>
            / {{ row.threshold }}%
          </template>
        </el-table-column>
        <el-table-column prop="handled" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.handled ? 'success' : 'danger'" size="small">
              {{ row.handled ? '已处理' : '未处理' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="告警时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="!row.handled"
              link
              type="primary"
              @click="openHandleDialog(row)"
            >
              处理
            </el-button>
            <span v-else style="color: #909399">
              {{ row.handle_remark || '已处理' }}
            </span>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div v-if="alertList.length > 0" class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchAlerts"
          @current-change="fetchAlerts"
        />
      </div>
    </el-card>

    <!-- 处理告警对话框 -->
    <el-dialog v-model="handleDialogVisible" title="处理告警" width="500px">
      <el-form label-width="100px">
        <el-form-item label="处理备注">
          <el-input
            v-model="handleRemark"
            type="textarea"
            :rows="3"
            placeholder="请输入处理备注（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="handleDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="handling" @click="confirmHandle">
          确认处理
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getAlerts, handleAlert, type SuspendAlert } from '@/api/modules/suspend'
import dayjs from 'dayjs'

const loading = ref(false)
const alertList = ref<SuspendAlert[]>([])
const filterType = ref('')
const filterLevel = ref('')
const filterHandled = ref<boolean | ''>('')

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 处理对话框
const handleDialogVisible = ref(false)
const handling = ref(false)
const handleRemark = ref('')
const currentAlertId = ref<number>(0)

// 获取告警列表
const fetchAlerts = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.page_size
    }

    if (filterType.value) params.target_type = filterType.value
    if (filterLevel.value) params.alert_level = filterLevel.value
    if (filterHandled.value !== '') params.handled = filterHandled.value

    const data = await getAlerts(params)
    alertList.value = data.items || []
    pagination.total = data.total || 0
  } catch (error) {
    console.error('获取告警列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 筛选变化
const handleFilterChange = () => {
  pagination.page = 1
  fetchAlerts()
}

// 打开处理对话框
const openHandleDialog = (alert: SuspendAlert) => {
  currentAlertId.value = alert.id
  handleRemark.value = ''
  handleDialogVisible.value = true
}

// 确认处理
const confirmHandle = async () => {
  try {
    handling.value = true
    await handleAlert(currentAlertId.value, {
      handle_remark: handleRemark.value || undefined
    })
    ElMessage.success('处理成功')
    handleDialogVisible.value = false
    fetchAlerts()
  } catch (error) {
    console.error('处理告警失败:', error)
  } finally {
    handling.value = false
  }
}

// 获取告警级别标签
const getAlertLevelTag = (level: string) => {
  const tagMap: Record<string, any> = {
    warning: 'warning',
    critical: 'danger',
    exceed: 'danger'
  }
  return tagMap[level] || 'info'
}

// 格式化日期
const formatDate = (date: string) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

onMounted(() => {
  fetchAlerts()
})
</script>

<style scoped lang="scss">
.suspend-alerts-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-bar {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
