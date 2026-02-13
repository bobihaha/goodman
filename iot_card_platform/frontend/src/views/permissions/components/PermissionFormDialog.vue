<template>
  <el-dialog
    :model-value="modelValue"
    :title="isEdit ? '编辑权限' : '新建权限'"
    width="600px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="权限代码" prop="code">
        <el-input v-model="formData.code" placeholder="如：card:view" />
      </el-form-item>
      <el-form-item label="权限名称" prop="name">
        <el-input v-model="formData.name" placeholder="如：查看卡片" />
      </el-form-item>
      <el-form-item label="所属模块" prop="module">
        <el-select v-model="formData.module" placeholder="请选择模块" style="width: 100%">
          <el-option v-for="mod in moduleOptions" :key="mod.value" :label="mod.label" :value="mod.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="模块名称" prop="module_name">
        <el-input v-model="formData.module_name" placeholder="如：卡片管理" />
      </el-form-item>
      <el-form-item label="描述">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="3"
          placeholder="权限描述"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { createPermission, updatePermission } from '@/api/modules/permission'
import type { Permission } from '@/types/permission'

interface Props {
  modelValue: boolean
  permission: Permission | null
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue', 'success'])

// 模块选项
const moduleOptions = [
  { label: '卡片管理', value: 'card' },
  { label: '流量池管理', value: 'pool' },
  { label: '用户管理', value: 'user' },
  { label: '套餐管理', value: 'package' },
  { label: '库存管理', value: 'stock' },
  { label: '供应商管理', value: 'supplier' },
  { label: '停复机管理', value: 'suspend' },
  { label: '系统管理', value: 'system' },
  { label: '数据看板', value: 'dashboard' }
]

const isEdit = computed(() => !!props.permission)

const formRef = ref<FormInstance>()
const submitting = ref(false)

const formData = reactive({
  code: '',
  name: '',
  module: '',
  module_name: '',
  description: ''
})

const rules: FormRules = {
  code: [
    { required: true, message: '请输入权限代码', trigger: 'blur' },
    { pattern: /^[a-z_]+:[a-z_]+$/, message: '格式：模块:操作（如card:view）', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入权限名称', trigger: 'blur' }
  ],
  module: [
    { required: true, message: '请选择所属模块', trigger: 'change' }
  ],
  module_name: [
    { required: true, message: '请输入模块名称', trigger: 'blur' }
  ]
}

// 监听权限变化，初始化表单
watch(() => props.permission, (val) => {
  if (val) {
    Object.assign(formData, {
      code: val.code,
      name: val.name,
      module: val.module,
      module_name: val.module_name,
      description: val.description || ''
    })
  } else {
    resetForm()
  }
}, { immediate: true })

// 监听模块选择，自动填充模块名称
watch(() => formData.module, (val) => {
  const option = moduleOptions.find(opt => opt.value === val)
  if (option && !isEdit.value) {
    formData.module_name = option.label
  }
})

const resetForm = () => {
  formData.code = ''
  formData.name = ''
  formData.module = ''
  formData.module_name = ''
  formData.description = ''
  formRef.value?.clearValidate()
}

const handleClose = () => {
  emit('update:modelValue', false)
  resetForm()
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitting.value = true

    if (isEdit.value && props.permission) {
      await updatePermission(props.permission.id, formData)
      ElMessage.success('更新成功')
    } else {
      await createPermission(formData)
      ElMessage.success('创建成功')
    }

    emit('success')
    handleClose()
  } catch (error: any) {
    if (error !== false) {
      ElMessage.error(error.message || '操作失败')
    }
  } finally {
    submitting.value = false
  }
}
</script>




