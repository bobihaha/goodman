<template>
  <el-dialog
    :model-value="modelValue"
    :title="isEdit ? '编辑通知模板' : '新增通知模板'"
    width="600px"
    @update:model-value="$emit('update:modelValue', $event)"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="模板编码" prop="code">
        <el-input
          v-model="form.code"
          placeholder="请输入模板编码"
          :disabled="isEdit"
        />
      </el-form-item>
      <el-form-item label="模板名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入模板名称" />
      </el-form-item>
      <el-form-item label="通知类型" prop="type">
        <el-select v-model="form.type" style="width: 100%" :disabled="isEdit">
          <el-option label="短信" value="sms" />
          <el-option label="邮件" value="email" />
          <el-option label="微信" value="wechat" />
          <el-option label="Webhook" value="webhook" />
        </el-select>
      </el-form-item>
      <el-form-item label="标题" prop="title">
        <el-input v-model="form.title" placeholder="请输入标题模板" />
      </el-form-item>
      <el-form-item label="内容" prop="content">
        <el-input
          v-model="form.content"
          type="textarea"
          :rows="5"
          placeholder="请输入内容模板，变量使用 {{变量名}} 格式"
        />
      </el-form-item>
      <el-form-item label="变量列表">
        <el-input
          v-model="variablesStr"
          placeholder="多个变量用逗号分隔，如：user_name,card_iccid"
        />
      </el-form-item>
      <el-form-item label="是否启用">
        <el-switch v-model="form.is_enabled" />
      </el-form-item>
      <el-form-item label="备注">
        <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="备注" />
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
import type { NotifyTemplate } from '@/types/system'

const props = defineProps<{
  modelValue: boolean
  templateData: NotifyTemplate | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: []
}>()

const formRef = ref<FormInstance>()
const submitting = ref(false)
const isEdit = computed(() => !!props.templateData)
const variablesStr = ref('')

const form = reactive({
  code: '',
  name: '',
  type: 'sms',
  title: '',
  content: '',
  is_enabled: true,
  remark: ''
})

const rules: FormRules = {
  code: [{ required: true, message: '请输入模板编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择通知类型', trigger: 'change' }],
  content: [{ required: true, message: '请输入内容模板', trigger: 'blur' }]
}

watch(() => props.modelValue, (val) => {
  if (val && props.templateData) {
    const t = props.templateData
    form.code = t.code
    form.name = t.name
    form.type = t.type
    form.title = t.title || ''
    form.content = t.content
    form.is_enabled = t.is_enabled
    form.remark = t.remark || ''
    variablesStr.value = (t.variables || []).join(',')
  }
})

const handleClose = () => {
  formRef.value?.resetFields()
  form.code = ''
  form.name = ''
  form.type = 'sms'
  form.title = ''
  form.content = ''
  form.is_enabled = true
  form.remark = ''
  variablesStr.value = ''
}

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const variables = variablesStr.value
      ? variablesStr.value.split(',').map(v => v.trim()).filter(Boolean)
      : []

    if (isEdit.value) {
      await systemApi.updateNotifyTemplate(props.templateData!.id, {
        name: form.name,
        title: form.title || undefined,
        content: form.content,
        variables,
        is_enabled: form.is_enabled,
        remark: form.remark || undefined
      })
      ElMessage.success('更新成功')
    } else {
      await systemApi.createNotifyTemplate({
        ...form,
        variables,
        title: form.title || undefined,
        remark: form.remark || undefined
      })
      ElMessage.success('创建成功')
    }
    emit('success')
  } catch (error) {
    console.error('保存模板失败:', error)
  } finally {
    submitting.value = false
  }
}
</script>
