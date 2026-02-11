<template>
  <el-dialog
    v-model="visible"
    title="单卡备注"
    width="500px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="ICCID">
        <el-input :value="card?.iccid" disabled />
      </el-form-item>

      <el-form-item label="当前备注">
        <el-input :value="card?.remark || '无'" disabled />
      </el-form-item>

      <el-form-item label="新备注" prop="remark">
        <el-input
          v-model="form.remark"
          type="textarea"
          :rows="4"
          placeholder="请输入备注内容"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        确定
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { cardApi } from '@/api'
import type { Card } from '@/types/card'

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

// 数据
const formRef = ref<FormInstance>()
const loading = ref(false)

const form = ref({
  remark: ''
})

// 表单验证规则
const rules: FormRules = {
  remark: [
    { required: true, message: '请输入备注内容', trigger: 'blur' },
    { min: 1, max: 200, message: '备注长度在 1 到 200 个字符', trigger: 'blur' }
  ]
}

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 提交
const handleSubmit = async () => {
  if (!formRef.value || !props.card) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      await cardApi.updateRemark(props.card!.id, form.value.remark)

      ElMessage.success('备注成功')
      emit('success')
      handleClose()
    } catch (error) {
      console.error('备注失败:', error)
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
    remark: props.card?.remark || ''
  }
  formRef.value?.clearValidate()
}

// 监听对话框打开，初始化备注
watch(visible, (newVal) => {
  if (newVal && props.card) {
    form.value.remark = props.card.remark || ''
  } else if (!newVal) {
    setTimeout(resetForm, 300)
  }
})
</script>





