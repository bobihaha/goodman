<template>
  <el-dialog
    v-model="visible"
    title="批量续费"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="选中卡片">
        <el-tag type="info">{{ cardIds.length }} 张卡片</el-tag>
      </el-form-item>

      <el-form-item label="续费周期" prop="renew_period">
        <el-radio-group v-model="form.renew_period">
          <el-radio
            v-for="item in RENEW_PERIOD_OPTIONS"
            :key="item.value"
            :label="item.value"
          >
            {{ item.label }}
          </el-radio>
        </el-radio-group>
      </el-form-item>

      <el-alert
        title="续费说明"
        type="info"
        :closable="false"
        style="margin-top: 16px"
      >
        <template #default>
          <div>续费后，卡片到期时间将延长对应的月数</div>
          <div>请确保账户余额充足</div>
        </template>
      </el-alert>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        确定续费
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { cardApi } from '@/api'
import { RENEW_PERIOD_OPTIONS } from '@/constants/card'

interface Props {
  modelValue: boolean
  cardIds: number[]
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 数据
const formRef = ref<FormInstance>()
const loading = ref(false)

const form = ref<{
  renew_period: 1 | 3 | 6 | 12
}>({
  renew_period: 1
})

// 表单验证规则
const rules: FormRules = {
  renew_period: [
    { required: true, message: '请选择续费周期', trigger: 'change' }
  ]
}

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 提交
const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      const result = await cardApi.batchRenew({
        card_ids: props.cardIds,
        renew_period: form.value.renew_period
      })

      ElMessage.success(`成功续费 ${result.success} 张卡片`)
      emit('success')
      handleClose()
    } catch (error) {
      console.error('批量续费失败:', error)
    } finally {
      loading.value = false
    }
  })
}

// 关闭
const handleClose = () => {
  visible.value = false
}

// 重置表单
const resetForm = () => {
  form.value = {
    renew_period: 1
  }
  formRef.value?.clearValidate()
}

// 监听对话框关闭
watch(visible, (newVal) => {
  if (!newVal) {
    setTimeout(resetForm, 300)
  }
})
</script>


