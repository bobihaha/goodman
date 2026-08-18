<template>
  <div class="package-period-page">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="强制激活管理" name="force_activate">
        <el-card shadow="never">
          <template #header>
            <span>批量强制激活</span>
          </template>

          <el-alert
            title="SIMBOSS 卡请先联系供应商完成激活；平台仅同步沉默期卡的本地状态，并自动加入对应流量池"
            type="warning"
            :closable="false"
            show-icon
            style="margin-bottom: 16px"
          />

          <el-form label-width="120px">
            <el-form-item label="ICCID 列表">
              <el-input
                v-model="forceForm.iccidInput"
                type="textarea"
                :rows="6"
                placeholder="请输入 ICCID，每行一个，最多 10000 个"
                resize="vertical"
              />
            </el-form-item>
            <el-form-item label="操作原因">
              <el-input
                v-model="forceForm.reason"
                placeholder="选填，便于后续追踪"
                maxlength="500"
                show-word-limit
              />
            </el-form-item>
            <el-form-item>
              <el-space>
                <span class="count-tip">已输入 {{ forceIccidCount }} 个 ICCID</span>
                <el-button @click="resetForceForm">清空</el-button>
                <el-button type="primary" :loading="forceLoading" @click="handleForceActivate">
                  执行强制激活
                </el-button>
              </el-space>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card v-if="forceResult" class="result-card" shadow="never">
          <template #header>
            <span>执行结果</span>
          </template>

          <el-alert
            :title="`成功 ${forceResult.success} 张，失败 ${forceResult.failed} 张`"
            :type="forceResult.failed > 0 ? 'warning' : 'success'"
            :closable="false"
            show-icon
          />

          <el-table :data="forceResult.success_list || []" border stripe style="margin-top: 16px">
            <el-table-column prop="iccid" label="ICCID" min-width="220" />
            <el-table-column prop="activated_at" label="激活日期" width="120" />
            <el-table-column prop="expired_at" label="到期日期" width="120" />
          </el-table>

          <el-table
            v-if="(forceResult.failed_list || []).length > 0"
            :data="forceResult.failed_list || []"
            border
            stripe
            style="margin-top: 16px"
          >
            <el-table-column prop="iccid" label="失败 ICCID" min-width="220" />
            <el-table-column prop="error" label="失败原因" min-width="260" />
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="取消计划套餐" name="cancel_period">
        <el-card shadow="never">
          <template #header>
            <span>批量取消计划套餐</span>
          </template>

          <el-form label-width="120px">
            <el-form-item label="ICCID 列表">
              <el-input
                v-model="cancelForm.iccidInput"
                type="textarea"
                :rows="6"
                placeholder="请输入 ICCID，每行一个，最多 10000 个"
                resize="vertical"
              />
            </el-form-item>
            <el-form-item label="减少周期数">
              <el-input-number v-model="cancelForm.cancel_count" :min="1" :max="120" />
              <span class="form-tip">按卡片自身套餐类型扣减：月包按月，年包按年</span>
            </el-form-item>
            <el-form-item label="操作原因">
              <el-input
                v-model="cancelForm.reason"
                placeholder="选填，便于后续追踪"
                maxlength="500"
                show-word-limit
              />
            </el-form-item>
            <el-form-item>
              <el-space>
                <span class="count-tip">已输入 {{ cancelIccidCount }} 个 ICCID</span>
                <el-button @click="resetCancelForm">清空</el-button>
                <el-button type="primary" :loading="cancelLoading" @click="handleCancelPeriod">
                  执行取消计划套餐
                </el-button>
              </el-space>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card v-if="cancelResult" class="result-card" shadow="never">
          <template #header>
            <span>执行结果</span>
          </template>

          <el-alert
            :title="`成功 ${cancelResult.success} 张，失败 ${cancelResult.failed} 张`"
            :type="cancelResult.failed > 0 ? 'warning' : 'success'"
            :closable="false"
            show-icon
          />

          <el-table :data="cancelResult.success_list || []" border stripe style="margin-top: 16px">
            <el-table-column prop="iccid" label="ICCID" min-width="220" />
            <el-table-column prop="old_expired_at" label="原到期日期" width="130" />
            <el-table-column prop="new_expired_at" label="新到期日期" width="130" />
          </el-table>

          <el-table
            v-if="(cancelResult.failed_list || []).length > 0"
            :data="cancelResult.failed_list || []"
            border
            stripe
            style="margin-top: 16px"
          >
            <el-table-column prop="iccid" label="失败 ICCID" min-width="220" />
            <el-table-column prop="error" label="失败原因" min-width="260" />
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <el-card class="log-card" shadow="never">
      <template #header>
        <div class="log-header">
          <span>{{ activeTab === 'force_activate' ? '强制激活记录' : '取消计划套餐记录' }}</span>
          <el-space>
            <el-date-picker
              v-model="logDateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
            />
            <el-button type="primary" @click="fetchLogs">查询</el-button>
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
        <el-table-column prop="detail" label="操作说明" min-width="360" show-overflow-tooltip />
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchLogs"
          @current-change="fetchLogs"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatDateTime } from '@/utils/formatter'
import { packagePeriodApi, type PackagePeriodBatchResult, type PackagePeriodLogRecord } from '@/api/modules/packagePeriod'

const activeTab = ref<'force_activate' | 'cancel_period'>('force_activate')
const forceLoading = ref(false)
const cancelLoading = ref(false)
const logLoading = ref(false)
const forceResult = ref<PackagePeriodBatchResult | null>(null)
const cancelResult = ref<PackagePeriodBatchResult | null>(null)
const logList = ref<PackagePeriodLogRecord[]>([])
const logDateRange = ref<string[]>([])

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const forceForm = reactive({
  iccidInput: '',
  reason: ''
})

const cancelForm = reactive({
  iccidInput: '',
  cancel_count: 1,
  reason: ''
})

const parseIccids = (raw: string) => raw.trim().split(/[\n,，\s]+/).filter(Boolean)

const forceIccidCount = computed(() => parseIccids(forceForm.iccidInput).length)
const cancelIccidCount = computed(() => parseIccids(cancelForm.iccidInput).length)

const resetForceForm = () => {
  forceForm.iccidInput = ''
  forceForm.reason = ''
  forceResult.value = null
}

const resetCancelForm = () => {
  cancelForm.iccidInput = ''
  cancelForm.cancel_count = 1
  cancelForm.reason = ''
  cancelResult.value = null
}

const fetchLogs = async () => {
  logLoading.value = true
  try {
    const res = await packagePeriodApi.getLogs({
      action: activeTab.value,
      start_time: logDateRange.value?.[0],
      end_time: logDateRange.value?.[1] ? `${logDateRange.value[1]} 23:59:59` : undefined,
      page: pagination.page,
      page_size: pagination.page_size
    })
    logList.value = res.items || []
    pagination.total = res.total || 0
  } finally {
    logLoading.value = false
  }
}

const resetLogFilters = () => {
  logDateRange.value = []
  pagination.page = 1
  fetchLogs()
}

const handleForceActivate = async () => {
  const iccids = parseIccids(forceForm.iccidInput)
  if (iccids.length === 0) {
    ElMessage.warning('请输入 ICCID')
    return
  }
  if (iccids.length > 10000) {
    ElMessage.warning('单次最多处理 10000 个 ICCID')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确认强制激活这 ${iccids.length} 张卡吗？SIMBOSS 卡须已由供应商完成激活。`,
      '确认操作',
      { type: 'warning' }
    )
    forceLoading.value = true
    forceResult.value = await packagePeriodApi.batchForceActivate({
      iccids,
      reason: forceForm.reason || undefined
    })
    ElMessage.success(`强制激活完成，成功 ${forceResult.value.success} 张`)
    pagination.page = 1
    fetchLogs()
  } catch (error: any) {
    if (error !== 'cancel') {
      throw error
    }
  } finally {
    forceLoading.value = false
  }
}

const handleCancelPeriod = async () => {
  const iccids = parseIccids(cancelForm.iccidInput)
  if (iccids.length === 0) {
    ElMessage.warning('请输入 ICCID')
    return
  }
  if (iccids.length > 10000) {
    ElMessage.warning('单次最多处理 10000 个 ICCID')
    return
  }

  try {
    await ElMessageBox.confirm(`确认给这 ${iccids.length} 张卡减少 ${cancelForm.cancel_count} 个套餐周期吗？`, '确认操作', { type: 'warning' })
    cancelLoading.value = true
    cancelResult.value = await packagePeriodApi.batchCancelPeriod({
      iccids,
      cancel_count: cancelForm.cancel_count,
      reason: cancelForm.reason || undefined
    })
    ElMessage.success(`取消计划套餐完成，成功 ${cancelResult.value.success} 张`)
    pagination.page = 1
    fetchLogs()
  } catch (error: any) {
    if (error !== 'cancel') {
      throw error
    }
  } finally {
    cancelLoading.value = false
  }
}

watch(activeTab, () => {
  pagination.page = 1
  fetchLogs()
})

onMounted(() => {
  fetchLogs()
})
</script>

<style scoped lang="scss">
.package-period-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-card,
.log-card {
  margin-top: 16px;
}

.count-tip,
.form-tip {
  color: #909399;
  font-size: 13px;
}

.form-tip {
  margin-left: 12px;
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
