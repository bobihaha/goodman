<template>
  <el-dialog
    v-model="visible"
    title="重置密码"
    width="500px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-alert
      type="warning"
      :closable="false"
      show-icon
      style="margin-bottom: 20px"
    >
      <template #title>
        <div>即将为用户 <strong>{{ user?.name }}</strong> 重置密码</div>
      </template>
    </el-alert>

    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
    >
      <el-form-item label="新密码" prop="password">
        <el-input
          v-model="formData.password"
          type="password"
          placeholder="请输入新密码（6-50位）"
          maxlength="50"
          show-password
        />
      </el-form-item>

      <el-form-item label="确认密码" prop="confirmPassword">
        <el-input
          v-model="formData.confirmPassword"
          type="password"
          placeholder="请再次输入新密码"
          maxlength="50"
          show-password
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        确定
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { userApi } from '@/api/modules/user'
import type { User } from '@/types/user'

// Props
const props = defineProps<{
  modelValue: boolean
  user: User | null
}>()

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: []
}>()

// 弹窗显示状态
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 表单引用
const formRef = ref<FormInstance>()

// 表单数据
const formData = reactive({
  password: '',
  confirmPassword: ''
})

// 表单验证规则
const formRules: FormRules = {
  password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 50, message: '密码长度在 6 到 50 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== formData.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 提交状态
const submitting = ref(false)

/**
 * 提交表单
 */
const handleSubmit = async () => {
  if (!formRef.value || !props.user) return

  try {
    // 验证表单
    await formRef.value.validate()

    submitting.value = true

    // 重置密码
    await userApi.updatePassword(props.user.id, formData.password)
    ElMessage.success('密码重置成功')

    emit('success')
    handleClose()
  } catch (error) {
    console.error('重置密码失败:', error)
    // 错误信息已在 request.ts 中处理
  } finally {
    submitting.value = false
  }
}

/**
 * 关闭弹窗
 */
const handleClose = () => {
  formRef.value?.resetFields()
  formData.password = ''
  formData.confirmPassword = ''
  visible.value = false
}
</script>


