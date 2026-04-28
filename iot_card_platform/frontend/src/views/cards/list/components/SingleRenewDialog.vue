<template>
  <el-dialog
    v-model="visible"
    title="单卡续费"
    width="520px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form label-width="100px">
      <el-form-item label="ICCID">
        <span>{{ card?.iccid || '-' }}</span>
      </el-form-item>

      <el-form-item label="续费月数">
        <el-select v-model="renewMonths" style="width: 220px">
          <el-option label="1个月" :value="1" />
          <el-option label="3个月" :value="3" />
          <el-option label="6个月" :value="6" />
          <el-option label="12个月" :value="12" />
        </el-select>
      </el-form-item>

      <el-form-item v-if="isSelfOwned" label="续费金额">
        <span>{{ quotePriceText }}</span>
      </el-form-item>

      <el-form-item v-if="isSelfOwned" label="当前余额">
        <span>{{ balanceText }}</span>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="loading" :disabled="!card?.id" @click="handleSubmit">
        确认续费
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { cardApi } from '@/api'
import type { Card } from '@/types/card'
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
const renewMonths = ref(1)
const quotePrice = ref<number | null>(null)
const balance = ref<number | null>(null)

const isSelfOwned = computed(() => !!props.card?.user_id && props.card.user_id === authStore.userInfo?.id)
const quotePriceText = computed(() => quotePrice.value == null ? '-' : formatMoney(quotePrice.value))
const balanceText = computed(() => balance.value == null ? '-' : formatMoney(balance.value))

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const loadQuote = async () => {
  if (!props.card?.id || !isSelfOwned.value) {
    quotePrice.value = null
    balance.value = null
    return
  }
  const quote = await cardApi.quoteRenew(props.card.id, renewMonths.value)
  quotePrice.value = quote.total_price
  balance.value = quote.balance
}

watch(() => props.modelValue, async (value) => {
  if (value) {
    renewMonths.value = 1
    await loadQuote()
  }
})

watch(renewMonths, async () => {
  if (props.modelValue) {
    await loadQuote()
  }
})

const handleSubmit = async () => {
  if (!props.card?.id) return

  try {
    await ElMessageBox.confirm(
      isSelfOwned.value
        ? `确定要为卡片 ${props.card.iccid} 续费 ${renewMonths.value} 个月吗？`
        : `确定要为卡片 ${props.card.iccid} 后台续费 ${renewMonths.value} 个月吗？`,
      '单卡续费确认',
      {
        confirmButtonText: '确认续费',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    loading.value = true
    if (isSelfOwned.value) {
      const result = await cardApi.purchaseRenew(props.card.id, renewMonths.value)
      if (result.warning_message) {
        ElMessage.warning(`续费成功，但${result.warning_message}`)
      } else {
        ElMessage.success(`续费成功，自动复机 ${result.auto_resumed || 0} 张`)
      }
    } else {
      const result = await cardApi.batchRenewByIccids({
        iccids: [props.card.iccid],
        renew_months: renewMonths.value
      })
      if (result.success > 0) {
        if ((result.warning_count || 0) > 0) {
          ElMessage.warning(`后台续费成功 ${result.success} 张，但仅更新了本地套餐周期`)
        } else {
          ElMessage.success(`后台续费成功 ${result.success} 张`)
        }
      } else {
        const firstError = result.failed_list?.[0]?.error
        throw new Error(firstError || '后台续费失败')
      }
    }
    emit('success')
    handleClose()
  } catch (error: any) {
    if (error !== 'cancel' && error !== false) {
      console.error('单卡续费失败:', error)
      ElMessage.error(error.message || '单卡续费失败')
    }
  } finally {
    loading.value = false
  }
}

const handleClose = () => {
  visible.value = false
}
</script>
