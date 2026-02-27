<template>
  <div class="renewal-page">
    <el-card shadow="never">
      <template #header>
        <span>续费价格查询</span>
      </template>

      <div class="query-section">
        <el-input
          v-model="iccidInput"
          type="textarea"
          :rows="6"
          placeholder="请输入ICCID，每行一个，最多10000个"
          resize="vertical"
        />
        <div class="query-actions">
          <span class="count-tip">已输入 {{ iccidCount }} 个ICCID</span>
          <div>
            <el-button @click="handleClear">清空</el-button>
            <el-button type="primary" :loading="loading" @click="handleQuery">
              查询续费价格
            </el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 查询结果 -->
    <el-card v-if="queried" class="result-card" shadow="never">
      <template #header>
        <div class="result-header">
          <span>查询结果</span>
          <div class="result-actions">
            <span class="result-summary">
              找到 <b>{{ resultList.length }}</b> 张卡片
              <template v-if="notFoundList.length > 0">
                ，未找到 <b class="text-danger">{{ notFoundList.length }}</b> 个ICCID
              </template>
            </span>
            <el-button type="success" size="small" :disabled="resultList.length === 0" @click="handleExport">
              下载Excel
            </el-button>
          </div>
        </div>
      </template>

      <!-- 未找到提示 -->
      <el-alert
        v-if="notFoundList.length > 0"
        type="warning"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      >
        <template #title>
          未找到的ICCID（{{ notFoundList.length }}个）：{{ notFoundList.slice(0, 10).join('、') }}
          <span v-if="notFoundList.length > 10">...等</span>
        </template>
      </el-alert>

      <el-table :data="resultList" border stripe style="width: 100%">
        <el-table-column prop="iccid" label="ICCID" width="220" show-overflow-tooltip />
        <el-table-column prop="msisdn" label="号码" width="140">
          <template #default="{ row }">{{ row.msisdn || '-' }}</template>
        </el-table-column>
        <el-table-column prop="carrier_name" label="运营商" width="100" />
        <el-table-column label="套餐规格" width="150">
          <template #default="{ row }">
            {{ row.spec_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="续费价格" width="120" align="center">
          <template #default="{ row }">
            <span v-if="row.price_sale !== null" class="price-value">
              ¥{{ row.price_sale }}
            </span>
            <span v-else class="text-muted">未设置</span>
          </template>
        </el-table-column>
        <el-table-column prop="status_name" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ row.status_name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="到期时间" width="120">
          <template #default="{ row }">
            {{ row.expired_at || '-' }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { cardApi } from '@/api'
import * as XLSX from 'xlsx'

const iccidInput = ref('')
const loading = ref(false)
const queried = ref(false)
const resultList = ref<any[]>([])
const notFoundList = ref<string[]>([])

const iccidCount = computed(() => {
  if (!iccidInput.value.trim()) return 0
  return iccidInput.value.trim().split(/[\n,，\s]+/).filter(Boolean).length
})

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    stock: 'info',
    testing: 'warning',
    silent: '',
    activated: 'success',
    expired: 'danger',
    suspended: 'danger',
    cancelled: 'info'
  }
  return map[status] || 'info'
}

const handleQuery = async () => {
  const iccids = iccidInput.value.trim().split(/[\n,，\s]+/).filter(Boolean)
  if (iccids.length === 0) {
    ElMessage.warning('请输入ICCID')
    return
  }
  if (iccids.length > 10000) {
    ElMessage.warning('单次最多查询10000个ICCID')
    return
  }

  loading.value = true
  try {
    const res = await cardApi.queryRenewPrice(iccids)
    resultList.value = res.found || []
    notFoundList.value = res.not_found || []
    queried.value = true
  } catch (error) {
    console.error('查询续费价格失败:', error)
    ElMessage.error('查询失败')
  } finally {
    loading.value = false
  }
}

const handleExport = () => {
  if (resultList.value.length === 0) return
  const data = resultList.value.map(row => ({
    'ICCID': row.iccid,
    '号码': row.msisdn || '',
    '运营商': row.carrier_name || '',
    '套餐规格': row.spec_name || '',
    '续费价格(元)': row.price_sale !== null ? row.price_sale : '',
    '状态': row.status_name || '',
    '到期时间': row.expired_at || ''
  }))
  const ws = XLSX.utils.json_to_sheet(data)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '续费价格查询')
  XLSX.writeFile(wb, `续费价格查询_${new Date().getTime()}.xlsx`)
}

const handleClear = () => {
  iccidInput.value = ''
  queried.value = false
  resultList.value = []
  notFoundList.value = []
}
</script>

<style scoped lang="scss">
.renewal-page {
  padding: 20px;

  .query-section {
    .query-actions {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 12px;

      .count-tip {
        font-size: 13px;
        color: #909399;
      }
    }
  }

  .result-card {
    margin-top: 20px;

    .result-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .result-actions {
        display: flex;
        align-items: center;
        gap: 16px;
      }

      .result-summary {
        font-size: 13px;
        color: #606266;
      }
    }
  }

  .price-value {
    font-weight: 600;
    color: #e6a23c;
    font-size: 15px;
  }

  .text-danger {
    color: #f56c6c;
  }

  .text-muted {
    color: #c0c4cc;
  }
}
</style>
