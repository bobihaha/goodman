<template>
  <el-dialog
    v-model="visible"
    title="后台补量"
    width="560px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-alert
      v-if="pool"
      :title="`流量池：${pool.name} | 当前用量：${formatFlow(pool.data_used)} / ${formatFlow(pool.data_total)} (${Number(pool.usage_percent || 0).toFixed(2)}%)`"
      type="info"
      :closable="false"
      style="margin-bottom: 16px"
    />

    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
    >
      <el-form-item label="增加流量" prop="added_flow_mb">
        <template v-if="isSelfOwned">
          <div class="purchase-quantity-row">
            <el-input-number v-model="purchaseQuantity" :min="1" :step="1" style="width: 220px" />
            <span class="quantity-summary">
              x {{ perPackageFlowText }} = {{ totalAddedFlowText }}
            </span>
          </div>
          <div class="purchase-summary-line">
            当前购买：{{ quantity }} 份 / {{ totalAddedFlowText }}
          </div>
          <div style="margin-top: 8px; color: #909399; font-size: 12px;">
            每份 {{ pool ? formatFlow(pool.flow_size) : '-' }}，按流量池套餐规格整数倍购买，仅当月有效，次月失效
          </div>
        </template>
        <template v-else>
          <el-select v-model="formData.added_flow_mb" style="width: 100%">
            <el-option
              v-for="item in FLOW_PACKAGE_OPTIONS"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
          <div style="margin-top: 8px; color: #909399; font-size: 12px;">
            固定规格加油包，仅当月有效，次月失效
          </div>
          <div class="package-options">
            <el-tag
              v-for="item in FLOW_PACKAGE_OPTIONS"
              :key="item.value"
              class="package-tag"
              :type="formData.added_flow_mb === item.value ? 'warning' : 'info'"
              :effect="formData.added_flow_mb === item.value ? 'dark' : 'plain'"
              @click="formData.added_flow_mb = item.value"
            >
              {{ item.label }}
            </el-tag>
          </div>
        </template>
      </el-form-item>

      <el-form-item v-if="pool && totalAddedFlowMb" label="补量后">
        <el-alert type="success" :closable="false">
          <template #title>
            <div>
              总流量：{{ formatFlow(pool.data_total) }} ->
              <span style="color: #67c23a; font-weight: bold">
                {{ formatFlow(pool.data_total + totalAddedFlowMb) }}
              </span>
            </div>
            <div style="margin-top: 4px">
              使用率：{{ Number(pool.usage_percent || 0).toFixed(2) }}% ->
              <span style="color: #67c23a; font-weight: bold">
                {{ calculateNewUsagePercent() }}%
              </span>
            </div>
          </template>
        </el-alert>
      </el-form-item>

      <el-form-item label="备注">
        <el-input
          v-model="formData.remark"
          type="textarea"
          :rows="3"
          placeholder="请输入备注信息（可选）"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>

      <el-form-item v-if="isSelfOwned" label="购买金额">
        <span>{{ quotePriceText }}</span>
      </el-form-item>

      <el-form-item v-if="isSelfOwned" label="当前余额">
        <span>{{ balanceText }}</span>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        {{ isSelfOwned ? '确认购买' : '确认补量' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { purchasePoolTopup, quotePoolTopup, rechargePool } from '@/api/modules/pool'
import { formatFlow, formatMoney } from '@/utils/formatter'
import type { Pool } from '@/types/pool'
import { FLOW_PACKAGE_OPTIONS, getFlowPackageLabel } from '@/constants/flow'

interface Props {
  modelValue: boolean
  pool?: Pool | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()
const formRef = ref<FormInstance>()
const submitting = ref(false)

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const formData = reactive({
  added_flow_mb: 1024,
  remark: ''
})
const purchaseQuantity = ref(1)
const quotePrice = ref<number | null>(null)
const balance = ref<number | null>(null)
const isSelfOwned = computed(() => !!props.pool?.can_self_topup)
const totalAddedFlowMb = computed(() => {
  if (isSelfOwned.value) {
    return (props.pool?.flow_size || 0) * (purchaseQuantity.value || 1)
  }
  return formData.added_flow_mb || 0
})
const quantity = computed(() => {
  if (isSelfOwned.value) {
    return purchaseQuantity.value || 1
  }
  if (!props.pool?.flow_size || !formData.added_flow_mb) return 0
  return Math.max(Math.round(formData.added_flow_mb / props.pool.flow_size), 0)
})
const perPackageFlowText = computed(() => props.pool?.flow_size ? formatFlow(props.pool.flow_size) : '-')
const totalAddedFlowText = computed(() => totalAddedFlowMb.value ? formatFlow(totalAddedFlowMb.value) : '-')
const quotePriceText = computed(() => quotePrice.value == null ? '-' : formatMoney(quotePrice.value))
const balanceText = computed(() => balance.value == null ? '-' : formatMoney(balance.value))

const rules: FormRules = {
  added_flow_mb: [
    { required: true, message: '请输入增加流量', trigger: 'blur' }
  ]
}

const calculateNewUsagePercent = () => {
  if (!props.pool || !totalAddedFlowMb.value) return 0
  const newTotal = props.pool.data_total + totalAddedFlowMb.value
  const percent = (props.pool.data_used / newTotal) * 100
  return Math.round(percent * 100) / 100
}

watch(
  () => [props.modelValue, purchaseQuantity.value, props.pool?.id, props.pool?.flow_size, isSelfOwned.value] as const,
  async ([visibleValue]) => {
    if (!visibleValue || !props.pool?.id || !props.pool?.flow_size || !isSelfOwned.value) {
      quotePrice.value = null
      balance.value = null
      return
    }
    const quote = await quotePoolTopup(props.pool.id, quantity.value || 1)
    quotePrice.value = quote.total_price
    balance.value = quote.balance
  }
)

const handleSubmit = async () => {
  if (!formRef.value || !props.pool) return

  try {
    await formRef.value.validate()
    await ElMessageBox.confirm(
      isSelfOwned.value
        ? `确认购买流量池 ${props.pool.name} 的 ${quantity.value} 份加油包吗？共 ${totalAddedFlowText.value}，金额 ${quotePriceText.value}。仅当月有效，次月失效。`
        : `确认给流量池 ${props.pool.name} 增加 ${getFlowPackageLabel(formData.added_flow_mb)} 吗？仅当月有效，次月失效。`,
      isSelfOwned.value ? '确认购买' : '确认补量',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    submitting.value = true
    const result: any = isSelfOwned.value
      ? await purchasePoolTopup({
          pool_id: props.pool.id,
          quantity: quantity.value || 1,
          remark: formData.remark || undefined
        })
      : await rechargePool({
          pool_id: props.pool.id,
          added_flow_mb: formData.added_flow_mb,
          remark: formData.remark || undefined
        })

    ElMessage.success(
      isSelfOwned.value
        ? `购买成功，自动复机 ${result.auto_resumed || 0} 张卡片`
        : `补量成功，自动复机 ${result.auto_resumed || 0} 张卡片`
    )
    emit('success')
    handleClose()
  } catch (error: any) {
    if (error !== 'cancel' && error !== false) {
      console.error('流量池补量失败:', error)
      ElMessage.error(error.message || '流量池补量失败')
    }
  } finally {
    submitting.value = false
  }
}

const handleClose = () => {
  formRef.value?.resetFields()
  formData.added_flow_mb = 1024
  purchaseQuantity.value = 1
  formData.remark = ''
  visible.value = false
}
</script>

<style scoped lang="scss">
.package-options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.package-tag {
  cursor: pointer;
  user-select: none;
}

.purchase-quantity-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.quantity-summary {
  color: #606266;
  font-size: 13px;
  white-space: nowrap;
}

.purchase-summary-line {
  margin-top: 8px;
  color: #303133;
  font-size: 13px;
  font-weight: 500;
}
</style>
