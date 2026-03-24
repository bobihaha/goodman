<template>
  <el-dialog
    v-model="visible"
    title="批量补量"
    width="900px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="batch-add-flow-dialog">
      <div v-if="!operationResult" class="input-section">
        <el-alert
          title="批量补量说明"
          type="info"
          :closable="false"
          style="margin-bottom: 16px"
        >
          <template #default>
            <div>支持输入多个 ICCID，每行一个或用逗号分隔</div>
            <div>仅支持非流量池卡，且一次最多补量 <strong>10000</strong> 张</div>
            <div style="margin-top: 8px; color: #67c23a; font-weight: 600;">
              补量后系统会自动重检，符合条件的卡会自动复机
            </div>
          </template>
        </el-alert>

        <el-form label-width="100px">
          <el-form-item label="补量规格">
            <el-select v-model="addedFlowMb" style="width: 220px">
              <el-option
                v-for="item in FLOW_PACKAGE_OPTIONS"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
            <span style="margin-left: 12px; color: #909399;">固定规格流量包</span>
          </el-form-item>

          <el-form-item label="备注">
            <el-input
              v-model="remark"
              placeholder="请输入备注（可选）"
              maxlength="200"
              show-word-limit
            />
          </el-form-item>

          <el-form-item label="ICCID">
            <el-input
              v-model="iccidText"
              type="textarea"
              :rows="10"
              placeholder="请输入 ICCID，每行一个或用逗号分隔"
            />
          </el-form-item>
        </el-form>

        <div class="input-info">
          <span>已输入: <strong>{{ iccidCount }}</strong> 个 ICCID</span>
          <span v-if="iccidCount > BATCH_MAX_COUNT" class="error-text">
            超出限制，最多支持 {{ BATCH_MAX_COUNT }} 个
          </span>
        </div>
      </div>

      <div v-else class="result-section">
        <el-alert
          :title="`补量完成：成功 ${operationResult.success_count} 张，失败 ${operationResult.failed_count} 张，自动复机 ${operationResult.auto_resumed} 张`"
          :type="operationResult.failed_count > 0 ? 'warning' : 'success'"
          :closable="false"
          style="margin-bottom: 16px"
        />

        <div v-if="operationResult.success_list.length > 0" class="success-cards">
          <div class="section-title">补量成功 ({{ operationResult.success_list.length }})</div>
          <el-table :data="operationResult.success_list" max-height="300" stripe>
            <el-table-column prop="iccid" label="ICCID" width="220" />
            <el-table-column prop="msisdn" label="号码" width="140" />
            <el-table-column prop="message" label="说明" min-width="180" />
          </el-table>
        </div>

        <div v-if="operationResult.failed_list.length > 0" class="failed-cards">
          <div class="section-title">补量失败 ({{ operationResult.failed_list.length }})</div>
          <el-table :data="operationResult.failed_list" max-height="300" stripe>
            <el-table-column prop="iccid" label="ICCID" width="220" />
            <el-table-column prop="error" label="失败原因" min-width="260" />
          </el-table>
        </div>
      </div>
    </div>

    <template #footer>
      <div v-if="!operationResult">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          :loading="loading"
          :disabled="iccidCount === 0 || iccidCount > BATCH_MAX_COUNT || !addedFlowMb"
          @click="handleSubmit"
        >
          确认补量
        </el-button>
      </div>
      <div v-else>
        <el-button @click="handleReset">继续补量</el-button>
        <el-button type="primary" @click="handleClose">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { cardApi } from '@/api'
import { FLOW_PACKAGE_OPTIONS, getFlowPackageLabel } from '@/constants/flow'

const BATCH_MAX_COUNT = 10000

interface Props {
  modelValue: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

interface OperationResult {
  success_count: number
  failed_count: number
  auto_resumed: number
  success_list: Array<{ iccid: string; msisdn?: string; message: string }>
  failed_list: Array<{ iccid: string; error: string }>
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const loading = ref(false)
const iccidText = ref('')
const addedFlowMb = ref(1024)
const remark = ref('')
const operationResult = ref<OperationResult | null>(null)

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const parseICCIDs = (text: string): string[] => {
  if (!text.trim()) return []
  return [...new Set(text.split(/[\n,]/).map(item => item.trim()).filter(Boolean))]
}

const iccidCount = computed(() => parseICCIDs(iccidText.value).length)

const handleSubmit = async () => {
  const iccids = parseICCIDs(iccidText.value)
  if (!iccids.length) {
    ElMessage.warning('请输入 ICCID')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要为 ${iccids.length} 张卡片增加 ${getFlowPackageLabel(addedFlowMb.value)} 流量吗？`,
      '批量补量确认',
      {
        confirmButtonText: '确认补量',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    loading.value = true
    const result = await cardApi.batchAddFlowByIccids({
      iccids,
      added_flow_mb: addedFlowMb.value,
      remark: remark.value || undefined
    })

    operationResult.value = {
      success_count: result.success || 0,
      failed_count: result.failed || 0,
      auto_resumed: result.auto_resumed || 0,
      success_list: result.success_list || [],
      failed_list: result.failed_list || []
    }

    if (result.success > 0) {
      ElMessage.success(`成功补量 ${result.success} 张卡片`)
      emit('success')
    }
    if (result.failed > 0) {
      ElMessage.warning(`${result.failed} 张卡片补量失败`)
    }
  } catch (error: any) {
    if (error !== 'cancel' && error !== false) {
      console.error('批量补量失败:', error)
      ElMessage.error(error.message || '批量补量失败')
    }
  } finally {
    loading.value = false
  }
}

const handleReset = () => {
  operationResult.value = null
  iccidText.value = ''
  addedFlowMb.value = 1024
  remark.value = ''
}

const handleClose = () => {
  handleReset()
  visible.value = false
}
</script>

<style scoped lang="scss">
.batch-add-flow-dialog {
  .section-title {
    margin: 12px 0;
    font-weight: 600;
  }

  .input-info {
    margin-top: 12px;
    display: flex;
    justify-content: space-between;
  }

  .error-text {
    color: #f56c6c;
  }

  .failed-cards {
    margin-top: 16px;
  }
}
</style>
