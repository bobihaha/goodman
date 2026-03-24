<template>
  <el-dialog
    v-model="visible"
    title="分配余额"
    width="520px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form label-width="100px">
      <el-form-item label="用户">
        <span>{{ user?.name || '-' }}</span>
      </el-form-item>
      <el-form-item label="当前余额">
        <span>{{ formatMoney(user?.quota?.account_balance || 0) }}</span>
      </el-form-item>
      <el-form-item label="分配金额">
        <el-input-number v-model="amount" :min="0.01" :step="100" :precision="2" style="width: 220px" />
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
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        确认分配
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { userApi } from '@/api/modules/user'
import type { User } from '@/types/user'
import { formatMoney } from '@/utils/formatter'

interface Props {
  modelValue: boolean
  user: User | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const amount = ref(100)
const remark = ref('')
const loading = ref(false)
const requestId = ref('')

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

watch(
  () => props.modelValue,
  (value) => {
    if (value) {
      amount.value = 100
      remark.value = ''
      requestId.value = createRequestId()
    }
  }
)

const createRequestId = () => {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return `grant-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

const handleSubmit = async () => {
  if (loading.value) return
  if (!props.user?.id) return
  if (!amount.value || amount.value <= 0) {
    ElMessage.warning('请输入正确的金额')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确认给用户 ${props.user.name} 分配余额 ${formatMoney(amount.value)} 吗？`,
      '确认分配余额',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    loading.value = true
    const result = await userApi.grantBalance(props.user.id, {
      amount: amount.value,
      remark: remark.value || undefined,
      request_id: requestId.value
    })
    ElMessage.success(result?.duplicated ? '余额分配已处理，列表已刷新' : '余额分配成功')
    emit('success')
    handleClose()
  } catch (error: any) {
    if (error !== 'cancel' && error !== false) {
      console.error('余额分配失败:', error)
      ElMessage.error(error.message || '余额分配失败，请重试；系统会自动防止重复加款')
    }
  } finally {
    loading.value = false
  }
}

const handleClose = () => {
  requestId.value = ''
  visible.value = false
}
</script>
