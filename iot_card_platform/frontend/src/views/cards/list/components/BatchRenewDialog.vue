<template>
  <el-dialog
    v-model="visible"
    title="批量续费"
    width="900px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="batch-renew-dialog">
      <!-- 输入区域 -->
      <div v-if="!operationResult" class="input-section">
        <el-alert
          v-if="hasInitialIccids"
          :title="`已选择 ${iccidCount} 张卡片，将直接对勾选卡片执行批量续费`"
          type="success"
          :closable="false"
          style="margin-bottom: 16px"
        />

        <el-alert
          v-else
          title="批量续费说明"
          type="info"
          :closable="false"
          style="margin-bottom: 16px"
        >
          <template #default>
            <div>支持输入多个ICCID，每行一个或用逗号分隔</div>
            <div>一次最多续费 <strong>10000</strong> 张卡片</div>
            <div style="color: #E6A23C; font-weight: 600; margin-top: 8px;">
              ⚠ 续费将延长卡片到期日期
            </div>
          </template>
        </el-alert>

        <el-input
          v-if="!hasInitialIccids"
          v-model="iccidText"
          type="textarea"
          :rows="8"
          placeholder="请输入ICCID，每行一个或用逗号分隔&#10;例如：&#10;89860123456789012345&#10;89860123456789012346&#10;89860123456789012347"
          @input="handleInput"
        />

        <div v-if="!hasInitialIccids" class="input-info">
          <span>已输入: <strong>{{ iccidCount }}</strong> 个ICCID</span>
          <span v-if="iccidCount > BATCH_MAX_COUNT" class="error-text">
            超出限制！最多支持 {{ BATCH_MAX_COUNT }} 个
          </span>
        </div>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-width="100px"
          style="margin-top: 20px"
        >
          <el-form-item label="续费月数" prop="renew_months">
            <el-select
              v-model="form.renew_months"
              placeholder="请选择续费月数"
              style="width: 200px"
            >
              <el-option
                v-for="option in RENEW_PERIOD_OPTIONS"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </el-form-item>
        </el-form>
      </div>

      <!-- 操作结果 -->
      <div v-else class="result-section">
        <div class="result-summary">
          <el-alert
            :title="`续费完成：成功 ${operationResult.success_count} 张，失败 ${operationResult.failed_count} 张`"
            :type="operationResult.failed_count > 0 ? 'warning' : 'success'"
            :closable="false"
            style="margin-bottom: 16px"
          />
          <el-alert
            v-if="operationResult.warning_list.length > 0"
            title="存在供应商同步提示"
            type="warning"
            :closable="false"
            style="margin-bottom: 16px"
          >
            <template #default>
              <div>以下卡片本次只更新了本地套餐周期，当前版本未同步供应商续费周期。</div>
              <div>如后续又被供应商生命周期同步覆盖，请优先补供应商续费接口。</div>
            </template>
          </el-alert>
        </div>

        <!-- 成功的卡片 -->
        <div v-if="operationResult.success_list.length > 0" class="success-cards">
          <div class="section-title">
            成功续费 ({{ operationResult.success_list.length }})
          </div>

          <el-table
            :data="operationResult.success_list"
            max-height="300"
            stripe
          >
            <el-table-column prop="iccid" label="ICCID" width="200" />
            <el-table-column prop="msisdn" label="号码" width="130" />
            <el-table-column label="原到期日" width="120">
              <template #default="{ row }">
                {{ row.old_expired_at || '-' }}
              </template>
            </el-table-column>
            <el-table-column label="新到期日" width="120">
              <template #default="{ row }">
                {{ row.new_expired_at || '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="message" label="说明" min-width="150" />
          </el-table>
        </div>

        <!-- 失败的卡片 -->
        <div v-if="operationResult.failed_list.length > 0" class="failed-cards">
          <div class="section-title">
            续费失败 ({{ operationResult.failed_list.length }})
            <el-button type="text" size="small" @click="handleCopyFailed">
              <el-icon><CopyDocument /></el-icon>
              复制ICCID
            </el-button>
          </div>

          <el-table
            :data="operationResult.failed_list"
            max-height="300"
            stripe
          >
            <el-table-column prop="iccid" label="ICCID" width="200" />
            <el-table-column prop="error" label="失败原因" min-width="300">
              <template #default="{ row }">
                <span class="error-text">{{ row.error }}</span>
              </template>
            </el-table-column>
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
          :disabled="iccidCount === 0 || iccidCount > BATCH_MAX_COUNT || !form.renew_months"
          @click="handleRenew"
        >
          确认续费
        </el-button>
      </div>
      <div v-else>
        <el-button @click="handleReset">继续续费</el-button>
        <el-button type="primary" @click="handleClose">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { CopyDocument } from '@element-plus/icons-vue'
import { cardApi } from '@/api'
import { RENEW_PERIOD_OPTIONS } from '@/constants/card'

const BATCH_MAX_COUNT = 10000

interface Props {
  modelValue: boolean
  initialIccids?: string[]
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

interface OperationResult {
  success_count: number
  failed_count: number
  warning_list: Array<{ iccid: string; warning: string }>
  success_list: Array<{
    iccid: string
    msisdn?: string
    old_expired_at?: string | null
    new_expired_at?: string | null
    message: string
    warning?: string
  }>
  failed_list: Array<{ iccid: string; error: string }>
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 数据
const formRef = ref<FormInstance>()
const loading = ref(false)
const iccidText = ref('')
const operationResult = ref<OperationResult | null>(null)

const form = ref({
  renew_months: undefined as number | undefined
})

// 表单验证规则
const rules: FormRules = {
  renew_months: [
    { required: true, message: '请选择续费月数', trigger: 'change' }
  ]
}

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})
const hasInitialIccids = computed(() => (props.initialIccids?.length || 0) > 0)
const initialIccidText = computed(() => [...new Set(props.initialIccids || [])].join('\n'))

const syncInitialIccids = () => {
  if (hasInitialIccids.value) {
    iccidText.value = initialIccidText.value
  }
}

const iccidCount = computed(() => {
  if (!iccidText.value.trim()) return 0
  
  const iccids = parseICCIDs(iccidText.value)
  return iccids.length
})

// 解析ICCID
const parseICCIDs = (text: string): string[] => {
  if (!text.trim()) return []
  
  // 先按换行分割，再按逗号分割
  const lines = text.split(/[\n,]/)
  
  // 过滤空行和去除空格
  const iccids = lines
    .map(line => line.trim())
    .filter(line => line.length > 0)
  
  // 去重
  return [...new Set(iccids)]
}

// 输入处理
const handleInput = () => {
  // 实时统计数量
}

// 续费操作
const handleRenew = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    const iccids = parseICCIDs(iccidText.value)
    
    if (iccids.length === 0) {
      ElMessage.warning('请输入ICCID')
      return
    }
    
    if (iccids.length > BATCH_MAX_COUNT) {
      ElMessage.warning(`一次最多续费 ${BATCH_MAX_COUNT} 张卡片`)
      return
    }

    try {
      await ElMessageBox.confirm(
        `确定要为 ${iccids.length} 张卡片续费 ${form.value.renew_months} 个月吗？`,
        '批量续费确认',
        {
          confirmButtonText: '确定续费',
          cancelButtonText: '取消',
          type: 'warning',
          distinguishCancelAndClose: true
        }
      )

      loading.value = true
      try {
        const result = await cardApi.batchRenewByIccids({
          iccids,
          renew_months: form.value.renew_months!
        })
        
        operationResult.value = {
          success_count: result.success || 0,
          failed_count: result.failed || 0,
          warning_list: result.warning_list || [],
          success_list: result.success_list || [],
          failed_list: result.failed_list || []
        }
        
        if (result.success > 0) {
          if ((result.warning_count || 0) > 0) {
            ElMessage.warning(`成功续费 ${result.success} 张，其中 ${result.warning_count} 张仅更新本地套餐周期`)
          } else {
            ElMessage.success(`成功续费 ${result.success} 张卡片`)
          }
          emit('success')
        }
        
        if (result.failed > 0) {
          ElMessage.warning(`${result.failed} 张卡片续费失败`)
        }
      } catch (error) {
        console.error('批量续费失败:', error)
        ElMessage.error('批量续费操作失败')
      } finally {
        loading.value = false
      }
    } catch (error) {
      // 用户取消操作
    }
  })
}

// 复制失败的ICCID
const handleCopyFailed = async () => {
  if (!operationResult.value || operationResult.value.failed_list.length === 0) return

  try {
    const text = operationResult.value.failed_list.map(item => item.iccid).join('\n')
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败')
  }
}

// 重置
const handleReset = () => {
  operationResult.value = null
  iccidText.value = hasInitialIccids.value ? initialIccidText.value : ''
  form.value.renew_months = undefined
  formRef.value?.clearValidate()
}

// 关闭
const handleClose = () => {
  visible.value = false
}

// 监听对话框关闭，重置数据
watch(visible, (newVal) => {
  if (newVal) {
    syncInitialIccids()
    return
  }
  if (!newVal) {
    setTimeout(() => {
      handleReset()
    }, 300)
  }
})
</script>

<style scoped lang="scss">
.batch-renew-dialog {
  .input-section {
    .input-info {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 12px;
      font-size: 14px;
      color: #606266;

      strong {
        color: #409eff;
        font-size: 16px;
        margin: 0 4px;
      }

      .error-text {
        color: #F56C6C;
        font-weight: 600;
      }
    }
  }

  .result-section {
    .section-title {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 16px;
      font-weight: 600;
      color: #303133;
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 2px solid #DCDFE6;
    }

    .success-cards {
      margin-bottom: 24px;
    }

    .failed-cards {
      .error-text {
        color: #F56C6C;
      }
    }
  }
}
</style>
