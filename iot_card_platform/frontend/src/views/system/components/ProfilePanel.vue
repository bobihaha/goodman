<template>
  <div class="profile-panel">
    <el-descriptions :column="2" border>
      <el-descriptions-item label="用户名称">{{ userInfo?.name }}</el-descriptions-item>
      <el-descriptions-item label="登录账号">{{ userInfo?.account }}</el-descriptions-item>
      <el-descriptions-item label="手机号">{{ userInfo?.phone || '-' }}</el-descriptions-item>
      <el-descriptions-item label="邮箱">{{ userInfo?.email || '-' }}</el-descriptions-item>
      <el-descriptions-item label="状态">
        <el-tag :type="userInfo?.status === 'enable' ? 'success' : 'danger'">
          {{ userInfo?.status === 'enable' ? '启用' : '禁用' }}
        </el-tag>
      </el-descriptions-item>
    </el-descriptions>

    <div style="margin-top: 24px">
      <el-button type="primary" @click="showPasswordDialog = true">修改密码</el-button>
      <el-button type="primary" @click="openEmailDialog">修改邮箱</el-button>
    </div>

    <el-dialog v-model="showPasswordDialog" title="修改密码" width="420px">
      <el-form ref="formRef" :model="passwordForm" :rules="rules" label-width="100px">
        <el-form-item label="新密码" prop="password">
          <el-input v-model="passwordForm.password" type="password" show-password placeholder="请输入新密码" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="passwordForm.confirmPassword" type="password" show-password placeholder="请再次输入新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPasswordDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleChangePassword">确定</el-button>
      </template>
    </el-dialog>

    <!-- 修改邮箱对话框 -->
    <el-dialog v-model="showEmailDialog" title="修改邮箱" width="420px">
      <el-form ref="emailFormRef" :model="emailForm" :rules="emailRules" label-width="100px">
        <el-form-item label="新邮箱" prop="email">
          <el-input v-model="emailForm.email" placeholder="请输入新邮箱" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEmailDialog = false">取消</el-button>
        <el-button type="primary" :loading="emailSubmitting" @click="handleChangeEmail">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useAuthStore } from '@/stores'
import { userApi } from '@/api/modules/user'

const authStore = useAuthStore()
const userInfo = computed(() => authStore.userInfo)

const showPasswordDialog = ref(false)
const showEmailDialog = ref(false)
const submitting = ref(false)
const emailSubmitting = ref(false)
const formRef = ref<FormInstance>()
const emailFormRef = ref<FormInstance>()

const passwordForm = reactive({ password: '', confirmPassword: '' })
const emailForm = reactive({ email: '' })

const rules: FormRules = {
  password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 50, message: '密码长度 6-50 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        value !== passwordForm.password ? callback(new Error('两次输入的密码不一致')) : callback()
      },
      trigger: 'blur'
    }
  ]
}

const emailRules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ]
}

const handleChangePassword = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  submitting.value = true
  try {
    await userApi.updatePassword(userInfo.value!.id, passwordForm.password)
    ElMessage.success('密码修改成功')
    showPasswordDialog.value = false
    passwordForm.password = ''
    passwordForm.confirmPassword = ''
  } catch (error: any) {
    ElMessage.error(error.message || '修改密码失败')
  } finally {
    submitting.value = false
  }
}

const openEmailDialog = () => {
  emailForm.email = userInfo.value?.email || ''
  showEmailDialog.value = true
}

const handleChangeEmail = async () => {
  if (!emailFormRef.value) return
  await emailFormRef.value.validate()
  emailSubmitting.value = true
  try {
    await userApi.update(userInfo.value!.id, { email: emailForm.email })
    ElMessage.success('邮箱修改成功')
    showEmailDialog.value = false
    await authStore.getUserInfo()
  } catch (error: any) {
    ElMessage.error(error.message || '修改邮箱失败')
  } finally {
    emailSubmitting.value = false
  }
}
</script>
