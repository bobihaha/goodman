<template>
  <div class="change-package-page">
    <el-alert
      title="本操作只修改平台本地销售套餐，不调用供应商改套餐接口；流量池卡会自动退出原池并加入目标套餐流量池。"
      type="warning"
      :closable="false"
      show-icon
    />

    <el-card shadow="never">
      <template #header><span>批量修改套餐</span></template>
      <el-form label-width="120px">
        <el-form-item label="目标套餐" required>
          <el-select
            v-model="form.target_sale_package_id"
            filterable
            placeholder="请选择目标月包套餐"
            style="width: 420px"
          >
            <el-option
              v-for="item in packageOptions"
              :key="item.id"
              :label="formatPackageLabel(item)"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="ICCID 列表" required>
          <el-input
            v-model="form.iccidInput"
            type="textarea"
            :rows="8"
            placeholder="请输入 ICCID，每行一个，最多 10000 个"
            resize="vertical"
          />
        </el-form-item>
        <el-form-item label="操作原因">
          <el-input
            v-model="form.reason"
            placeholder="选填，便于后续追踪"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item>
          <el-space>
            <span class="count-tip">已输入 {{ iccidCount }} 个 ICCID</span>
            <el-button @click="resetForm">清空</el-button>
            <el-button type="primary" :loading="loading" @click="handleChangePackage">
              执行修改套餐
            </el-button>
          </el-space>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="result" class="result-card" shadow="never">
      <template #header><span>执行结果</span></template>
      <el-alert
        :title="`成功 ${result.success} 张，失败 ${result.failed} 张`"
        :type="result.failed > 0 ? 'warning' : 'success'"
        :closable="false"
        show-icon
      />
      <el-table :data="result.success_list || []" border stripe style="margin-top: 16px">
        <el-table-column prop="iccid" label="ICCID" min-width="210" />
        <el-table-column prop="old_package_name" label="原套餐" min-width="150" />
        <el-table-column prop="new_package_name" label="新套餐" min-width="150" />
        <el-table-column prop="old_pool_name" label="原流量池" min-width="180">
          <template #default="{ row }">{{ row.old_pool_name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="new_pool_name" label="新流量池" min-width="180">
          <template #default="{ row }">{{ row.new_pool_name || '-' }}</template>
        </el-table-column>
      </el-table>
      <el-table
        v-if="(result.failed_list || []).length"
        :data="result.failed_list"
        border
        stripe
        style="margin-top: 16px"
      >
        <el-table-column prop="iccid" label="失败 ICCID" min-width="220" />
        <el-table-column prop="error" label="失败原因" min-width="300" />
      </el-table>
    </el-card>

    <el-card class="log-card" shadow="never">
      <template #header>
        <div class="log-header">
          <span>修改套餐记录</span>
          <el-space>
            <el-date-picker
              v-model="logDateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
            />
            <el-button type="primary" @click="handleLogSearch">查询</el-button>
            <el-button @click="resetLogFilters">重置</el-button>
          </el-space>
        </div>
      </template>
      <el-table v-loading="logLoading" :data="logList" border stripe>
        <el-table-column prop="operation_time" label="操作时间" width="180">
          <template #default="{ row }">{{ formatDateTime(row.operation_time) }}</template>
        </el-table-column>
        <el-table-column prop="card_no" label="ICCID" min-width="220" />
        <el-table-column prop="operator_name" label="操作人" width="140" />
        <el-table-column prop="detail" label="操作说明" min-width="420" show-overflow-tooltip />
      </el-table>
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handlePageSizeChange"
          @current-change="fetchLogs"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { packagePeriodApi, type PackagePeriodBatchResult, type PackagePeriodLogRecord } from '@/api/modules/packagePeriod'
import type { SalePackage } from '@/types/package'
import { formatDateTime, formatFlowValue } from '@/utils/formatter'

const loading = ref(false)
const logLoading = ref(false)
const packageOptions = ref<SalePackage[]>([])
const result = ref<PackagePeriodBatchResult | null>(null)
const logList = ref<PackagePeriodLogRecord[]>([])
const logDateRange = ref<string[]>([])

const form = reactive({
  target_sale_package_id: undefined as number | undefined,
  iccidInput: '',
  reason: ''
})

const pagination = reactive({ page: 1, page_size: 20, total: 0 })
const parseIccids = (raw: string) => [...new Set(raw.trim().split(/[\n,，\s]+/).filter(Boolean))]
const iccidCount = computed(() => parseIccids(form.iccidInput).length)
const selectedPackage = computed(() => packageOptions.value.find(item => item.id === form.target_sale_package_id))

const formatPackageLabel = (item: SalePackage) => {
  const owner = item.user_id ? `客户专属 #${item.user_id}` : '平台套餐'
  return `${item.name}（${formatFlowValue(item.flow_size)}/月，${owner}）`
}

const fetchPackageOptions = async () => {
  packageOptions.value = await packagePeriodApi.getPackageOptions()
}

const fetchLogs = async () => {
  logLoading.value = true
  try {
    const response = await packagePeriodApi.getLogs({
      action: 'change_package',
      start_time: logDateRange.value?.[0],
      end_time: logDateRange.value?.[1] ? `${logDateRange.value[1]} 23:59:59` : undefined,
      page: pagination.page,
      page_size: pagination.page_size
    })
    logList.value = response.items || []
    pagination.total = response.total || 0
  } finally {
    logLoading.value = false
  }
}

const handleLogSearch = () => {
  pagination.page = 1
  fetchLogs()
}

const handlePageSizeChange = () => {
  pagination.page = 1
  fetchLogs()
}

const resetLogFilters = () => {
  logDateRange.value = []
  handleLogSearch()
}

const resetForm = () => {
  form.target_sale_package_id = undefined
  form.iccidInput = ''
  form.reason = ''
  result.value = null
}

const handleChangePackage = async () => {
  const iccids = parseIccids(form.iccidInput)
  if (!form.target_sale_package_id || !selectedPackage.value) {
    ElMessage.warning('请选择目标套餐')
    return
  }
  if (!iccids.length) {
    ElMessage.warning('请输入 ICCID')
    return
  }
  if (iccids.length > 10000) {
    ElMessage.warning('单次最多处理 10000 个 ICCID')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确认将 ${iccids.length} 张卡修改为“${selectedPackage.value.name}”吗？流量池卡将重新组池，降档后可能触发既有停卡规则。`,
      '确认修改套餐',
      { type: 'warning', confirmButtonText: '确认修改' }
    )
    loading.value = true
    result.value = await packagePeriodApi.batchChangePackage({
      iccids,
      target_sale_package_id: form.target_sale_package_id,
      reason: form.reason || undefined
    })
    if (result.value.pool_check_warnings?.length) {
      ElMessage.warning(`套餐修改完成，但有 ${result.value.pool_check_warnings.length} 个流量池检查失败`)
    } else {
      ElMessage.success(`修改套餐完成，成功 ${result.value.success} 张`)
    }
    pagination.page = 1
    fetchLogs()
  } catch (error: any) {
    if (error !== 'cancel') throw error
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchPackageOptions()
  fetchLogs()
})
</script>

<style scoped lang="scss">
.change-package-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-card,
.log-card {
  margin-top: 16px;
}

.count-tip {
  color: #909399;
  font-size: 13px;
}

.log-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
