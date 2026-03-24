<template>
  <el-dialog
    v-model="visible"
    title="单卡补量"
    width="520px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form label-width="100px">
      <el-form-item label="ICCID">
        <span>{{ card?.iccid || '-' }}</span>
      </el-form-item>

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
        <div style="margin-top: 8px; color: #909399; font-size: 12px;">
          补量仅当月有效，次月自动失效
        </div>
      </el-form-item>

      <el-form-item v-if="isSelfOwned" label="购买金额">
        <span>{{ quotePriceText }}</span>
      </el-form-item>

      <el-form-item v-if="isSelfOwned" label="当前余额">
        <span>{{ balanceText }}</span>
      </el-form-item>

      <el-form-item label="备注">
        <el-input
          v-model="remark"
          type="textarea"
          :rows="3"
          maxlength="200"
          show-word-limit
          placeholder="请输入备注（可选）"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="loading" :disabled="!card?.iccid" @click="handleSubmit">
        确认补量
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { cardApi } from '@/api'
import type { Card } from '@/types/card'
import { FLOW_PACKAGE_OPTIONS, getFlowPackageLabel } from '@/constants/flow'
import { useAuthStore } from '@/stores/modules/auth'
import { formatMoney } from '@/utils/formatter'

interface Props {
  modelValue: boolean
  card: Card | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()
const authStore = useAuthStore()

const loading = ref(false)
const addedFlowMb = ref(1024)
const remark = ref('')
const quotePrice = ref<number | null>(null)
const balance = ref<number | null>(null)

const isSelfOwned = computed(() => !!props.card?.user_id && props.card.user_id === authStore.userInfo?.id)
const quotePriceText = computed(() => quotePrice.value == null ? '-' : formatMoney(quotePrice.value))
const balanceText = computed(() => balance.value == null ? '-' : formatMoney(balance.value))

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

watch(
  () => props.modelValue,
  async (value) => {
    if (value) {
      addedFlowMb.value = FLOW_PACKAGE_OPTIONS[0]?.value || 1024
      remark.value = ''
      if (props.card?.id && isSelfOwned.value) {
        const quote = await cardApi.quoteTopup(props.card.id, addedFlowMb.value)
        quotePrice.value = quote.selected_price
        balance.value = quote.balance
      } else {
        quotePrice.value = null
        balance.value = null
      }
    }
  }
)

watch(addedFlowMb, async (value) => {
  if (!props.modelValue || !props.card?.id || !isSelfOwned.value) return
  const quote = await cardApi.quoteTopup(props.card.id, value)
  quotePrice.value = quote.selected_price
  balance.value = quote.balance
})

const handleSubmit = async () => {
  if (!props.card?.iccid) return

  try {
    await ElMessageBox.confirm(
      isSelfOwned.value
        ? `确定要购买卡片 ${props.card.iccid} 的 ${getFlowPackageLabel(addedFlowMb.value)} 加油包吗？仅当月有效，次月失效。`
        : `确定要为卡片 ${props.card.iccid} 增加 ${getFlowPackageLabel(addedFlowMb.value)} 流量吗？仅当月有效，次月失效。`,
      isSelfOwned.value ? '单卡加油包确认' : '单卡补量确认',
      {
        confirmButtonText: '确认补量',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    loading.value = true
    const result = isSelfOwned.value
      ? await cardApi.purchaseTopup(props.card.id, addedFlowMb.value)
      : await cardApi.batchAddFlowByIccids({
          iccids: [props.card.iccid],
          added_flow_mb: addedFlowMb.value,
          remark: remark.value || undefined
        })

    if (isSelfOwned.value || result.success > 0) {
      ElMessage.success(
        isSelfOwned.value
          ? `购买成功（${getFlowPackageLabel(addedFlowMb.value)}），自动复机 ${result.auto_resumed || 0} 张`
          : `补量成功（${getFlowPackageLabel(addedFlowMb.value)}），自动复机 ${result.auto_resumed || 0} 张`
      )
      emit('success')
      handleClose()
    } else {
      ElMessage.error(result.failed_list?.[0]?.error || '补量失败')
    }
  } catch (error: any) {
    if (error !== 'cancel' && error !== false) {
      console.error('单卡补量失败:', error)
      ElMessage.error(error.message || '单卡补量失败')
    }
  } finally {
    loading.value = false
  }
}

const handleClose = () => {
  visible.value = false
}
</script>
