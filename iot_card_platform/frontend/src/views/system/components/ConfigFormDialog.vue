<template>
  <el-dialog
    :model-value="modelValue"
    :title="isEdit ? '编辑配置' : '新增配置'"
    width="500px"
    @update:model-value="$emit('update:modelValue', $event)"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="配置键" prop="config_key">
        <el-input
          v-model="form.config_key"
          placeholder="请输入配置键"
          :disabled="isEdit"
        />
      </el-form-item>
      <el-form-item label="配置值" prop="config_value">
        <el-input
          v-model="form.config_value"
          placeholder="请输入配置值"
          type="textarea"
          :rows="3"
        />
      </el-form-item>
      <el-form-item label="类型" prop="config_type">
        <el-select v-model="form.config_type" style="width: 100%">
          <el-option label="字符串" value="string" />
          <el-option label="数字" value="number" />
          <el-option label="布尔" value="boolean" />
          <el-option label="JSON" value="json" />
        </el-select>
      </el-form-item>
      <el-form-item label="描述" prop="description">
        <el-input v-model="form.description" placeholder="请输入描述" />
      </el-form-item>
      <el-form-item label="是否公开" prop="is_public">
        <el-switch v-model="form.is_public" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        确定
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { systemApi } from '@/api/modules/system'
import type { SystemConfig } from '@/types/system'

const props = defineProps<{
  modelValue: boolean
  config: SystemConfig | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: []
}>()

const formRef = ref<FormInstance>()
const submitting = ref(false)
const isEdit = computed(() => !!props.config)

const form = reactive({
  config_key: '',
  config_value: '',
  config_type: 'string',
  description: '',
  is_public: false
})

const rules: FormRules = {
  config_key: [{ required: true, message: '请输入配置键', trigger: 'blur' }]
}

watch(() => props.modelValue, (val) => {
  if (val && props.config) {
    form.config_key = props.config.config_key
    form.config_value = props.config.config_value || ''
    form.config_type = props.config.config_type || 'string'
    form.description = props.config.description || ''
    form.is_public = props.config.is_public
  }
})

const handleClose = () => {
  formRef.value?.resetFields()
  form.config_key = ''
  form.config_value = ''
  form.config_type = 'string'
  form.description = ''
  form.is_public = false
}

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (isEdit.value) {
      await systemApi.updateConfig(form.config_key, {
        config_value: form.config_value,
        description: form.description,
        is_public: form.is_public
      })
      ElMessage.success('更新成功')
    } else {
      await systemApi.createConfig(form)
      ElMessage.success('创建成功')
    }
    emit('success')
  } catch (error) {
    console.error('保存配置失败:', error)
  } finally {
    submitting.value = false
  }
}
</script>
