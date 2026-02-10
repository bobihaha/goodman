<template>
  <el-dialog
    v-model="visible"
    title="批量备注"
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

      <el-form-item label="备注内容" prop="remark">
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
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      const result = await cardApi.batchRemark({
        card_ids: props.cardIds,
        remark: form.value.remark
      })

      ElMessage.success(`成功备注 ${result.success} 张卡片`)
      emit('success')
      handleClose()
    } catch (error) {
      console.error('批量备注失败:', error)
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
    remark: ''
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


