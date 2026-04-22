<template>
  <div class="renewal-page">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="续费价格查询" name="price">
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
                <el-button type="primary" :loading="priceLoading" @click="handleQuery">
                  查询续费价格
                </el-button>
              </div>
            </div>
          </div>
        </el-card>

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
                {{ formatDate(row.expired_at) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="续费记录" name="renew">
        <el-card shadow="never">
          <template #header>
            <div class="record-header">
              <span>续费记录</span>
              <div class="record-actions">
                <el-date-picker
                  v-model="renewDateRange"
                  type="daterange"
                  range-separator="至"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  value-format="YYYY-MM-DD"
                />
                <el-button type="primary" @click="handleRecordSearch('renew')">查询</el-button>
                <el-button @click="handleRecordReset('renew')">重置</el-button>
              </div>
            </div>
          </template>

          <el-table v-loading="renewLoading" :data="renewRecords" border stripe>
            <el-table-column prop="operation_time" label="操作时间" width="180">
              <template #default="{ row }">{{ formatDateTime(row.operation_time) }}</template>
            </el-table-column>
            <el-table-column prop="card_no" label="卡号信息" min-width="220" show-overflow-tooltip />
            <el-table-column prop="renew_period" label="具体续费周期" width="140">
              <template #default="{ row }">{{ row.renew_period || '-' }}</template>
            </el-table-column>
            <el-table-column prop="detail" label="操作说明" min-width="320" show-overflow-tooltip />
          </el-table>

          <div class="pagination">
            <el-pagination
              v-model:current-page="renewPagination.page"
              v-model:page-size="renewPagination.page_size"
              :total="renewPagination.total"
              :page-sizes="[20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="fetchRecords('renew')"
              @current-change="fetchRecords('renew')"
            />
          </div>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="补量记录" name="topup">
        <el-card shadow="never">
          <template #header>
            <div class="record-header">
              <span>补量记录</span>
              <div class="record-actions">
                <el-date-picker
                  v-model="topupDateRange"
                  type="daterange"
                  range-separator="至"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  value-format="YYYY-MM-DD"
                />
                <el-button type="primary" @click="handleRecordSearch('topup')">查询</el-button>
                <el-button @click="handleRecordReset('topup')">重置</el-button>
              </div>
            </div>
          </template>

          <el-table v-loading="topupLoading" :data="topupRecords" border stripe>
            <el-table-column prop="operation_time" label="操作时间" width="180">
              <template #default="{ row }">{{ formatDateTime(row.operation_time) }}</template>
            </el-table-column>
            <el-table-column prop="card_no" label="卡号信息" min-width="220" show-overflow-tooltip />
            <el-table-column prop="topup_detail" label="补量情况" width="140">
              <template #default="{ row }">{{ row.topup_detail || '-' }}</template>
            </el-table-column>
            <el-table-column prop="detail" label="操作说明" min-width="320" show-overflow-tooltip />
          </el-table>

          <div class="pagination">
            <el-pagination
              v-model:current-page="topupPagination.page"
              v-model:page-size="topupPagination.page_size"
              :total="topupPagination.total"
              :page-sizes="[20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="fetchRecords('topup')"
              @current-change="fetchRecords('topup')"
            />
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { cardApi } from '@/api'
import { systemApi } from '@/api/modules/system'
import { formatDate, formatDateTime } from '@/utils/formatter'
import * as XLSX from 'xlsx'

interface CardRecordItem {
  id: number
  operation_time: string | null
  card_no: string | null
  renew_period?: string | null
  topup_detail?: string | null
  detail?: string | null
}

const activeTab = ref('price')
const iccidInput = ref('')
const priceLoading = ref(false)
const queried = ref(false)
const resultList = ref<any[]>([])
const notFoundList = ref<string[]>([])

const renewLoading = ref(false)
const renewRecords = ref<CardRecordItem[]>([])
const renewDateRange = ref<string[]>([])
const renewPagination = ref({
  page: 1,
  page_size: 20,
  total: 0
})

const topupLoading = ref(false)
const topupRecords = ref<CardRecordItem[]>([])
const topupDateRange = ref<string[]>([])
const topupPagination = ref({
  page: 1,
  page_size: 20,
  total: 0
})

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

  priceLoading.value = true
  try {
    const res = await cardApi.queryRenewPrice(iccids)
    resultList.value = res.found || []
    notFoundList.value = res.not_found || []
    queried.value = true
  } catch (error) {
    console.error('查询续费价格失败:', error)
    ElMessage.error('查询失败')
  } finally {
    priceLoading.value = false
  }
}

const handleExport = () => {
  if (resultList.value.length === 0) return
  const data = resultList.value.map(row => ({
    ICCID: row.iccid,
    号码: row.msisdn || '',
    运营商: row.carrier_name || '',
    套餐规格: row.spec_name || '',
    '续费价格(元)': row.price_sale !== null ? row.price_sale : '',
    状态: row.status_name || '',
    到期时间: formatDate(row.expired_at)
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

const fetchRecords = async (type: 'renew' | 'topup') => {
  const isRenew = type === 'renew'
  const loading = isRenew ? renewLoading : topupLoading
  const records = isRenew ? renewRecords : topupRecords
  const pagination = isRenew ? renewPagination.value : topupPagination.value
  const dateRange = isRenew ? renewDateRange.value : topupDateRange.value

  loading.value = true
  try {
    const res: any = await systemApi.getCardRecords({
      record_type: type,
      start_time: dateRange?.[0],
      end_time: dateRange?.[1] ? `${dateRange[1]} 23:59:59` : undefined,
      page: pagination.page,
      page_size: pagination.page_size
    })
    records.value = res.items || []
    pagination.total = res.total || 0
  } catch (error) {
    console.error(`获取${type === 'renew' ? '续费' : '补量'}记录失败:`, error)
  } finally {
    loading.value = false
  }
}

const handleRecordSearch = (type: 'renew' | 'topup') => {
  if (type === 'renew') {
    renewPagination.value.page = 1
  } else {
    topupPagination.value.page = 1
  }
  fetchRecords(type)
}

const handleRecordReset = (type: 'renew' | 'topup') => {
  if (type === 'renew') {
    renewDateRange.value = []
    renewPagination.value.page = 1
  } else {
    topupDateRange.value = []
    topupPagination.value.page = 1
  }
  fetchRecords(type)
}

watch(activeTab, (tab) => {
  if (tab === 'renew' && renewRecords.value.length === 0) {
    fetchRecords('renew')
  }
  if (tab === 'topup' && topupRecords.value.length === 0) {
    fetchRecords('topup')
  }
})

onMounted(() => {
  fetchRecords('renew')
})
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
  }

  .result-header,
  .record-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
  }

  .result-actions,
  .record-actions {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .result-summary {
    font-size: 13px;
    color: #606266;
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

  .pagination {
    margin-top: 16px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
