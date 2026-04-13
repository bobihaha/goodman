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

    <div class="profile-actions">
      <el-button type="primary" size="small" @click="showPasswordDialog = true">修改密码</el-button>
      <el-button type="primary" size="small" @click="openEmailDialog">修改邮箱</el-button>
    </div>

    <el-card v-if="showOpenApiPanel" class="api-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="card-title">开放 API 凭证</span>
          <el-tag type="success" size="small">一级用户</el-tag>
        </div>
      </template>

      <el-alert
        title="AppSecret 仅在重置后完整展示一次，请及时保存。"
        type="warning"
        class="api-alert"
        :closable="false"
        show-icon
      />

      <el-descriptions :column="1" border class="api-descriptions">
        <el-descriptions-item label="APPID">
          <div class="secret-row">
            <span>{{ apiCredential?.app_id || '-' }}</span>
            <el-button
              v-if="apiCredential?.app_id"
              link
              type="primary"
              @click="copyText(apiCredential.app_id, 'APPID')"
            >
              复制
            </el-button>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="当前 AppSecret">
          {{ apiCredential?.app_secret_masked || '未生成' }}
        </el-descriptions-item>
        <el-descriptions-item label="最近重置时间">
          {{ apiCredential?.last_reset_at || '-' }}
        </el-descriptions-item>
      </el-descriptions>

      <el-card v-if="latestSecret" class="secret-card" shadow="never">
        <template #header>新 AppSecret</template>
        <div class="secret-row">
          <span class="secret-value">{{ latestSecret }}</span>
          <el-button link type="primary" @click="copyText(latestSecret, 'AppSecret')">
            复制
          </el-button>
        </div>
      </el-card>

      <div class="api-actions">
        <el-button type="primary" size="small" :loading="apiLoading" @click="loadApiCredential">
          刷新凭证
        </el-button>
        <el-button type="warning" size="small" :loading="resettingApiSecret" @click="handleResetApiSecret">
          重置 AppSecret
        </el-button>
      </div>
    </el-card>

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
import { ref, computed, reactive, watch } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { useAuthStore } from '@/stores'
import { userApi } from '@/api/modules/user'
import type { UserOpenApiCredential } from '@/types/user'

const authStore = useAuthStore()
const userInfo = computed(() => authStore.userInfo)
const showOpenApiPanel = computed(() => userInfo.value?.user_level === 2)

const showPasswordDialog = ref(false)
const showEmailDialog = ref(false)
const submitting = ref(false)
const emailSubmitting = ref(false)
const apiLoading = ref(false)
const resettingApiSecret = ref(false)
const formRef = ref<FormInstance>()
const emailFormRef = ref<FormInstance>()
const apiCredential = ref<UserOpenApiCredential | null>(null)
const latestSecret = ref('')

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

const loadApiCredential = async () => {
  if (!showOpenApiPanel.value || !userInfo.value?.id) return
  apiLoading.value = true
  try {
    apiCredential.value = await userApi.getOpenApiCredentials(userInfo.value.id)
  } catch (error: any) {
    ElMessage.error(error.message || '获取 API 凭证失败')
  } finally {
    apiLoading.value = false
  }
}

const handleResetApiSecret = async () => {
  if (!userInfo.value?.id) return

  await ElMessageBox.confirm(
    '确定要重置当前账号的 AppSecret 吗？原密钥将立即失效。',
    '重置确认',
    {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消'
    }
  )

  resettingApiSecret.value = true
  try {
    const result = await userApi.resetOpenApiCredentials(userInfo.value.id)
    latestSecret.value = result.app_secret
    apiCredential.value = {
      enabled: result.enabled,
      app_id: result.app_id,
      app_secret_masked: `${result.app_secret.slice(0, 4)}******${result.app_secret.slice(-4)}`,
      has_app_secret: true,
      last_reset_at: result.last_reset_at
    }
    ElMessage.success('AppSecret 已重置')
  } catch (error: any) {
    ElMessage.error(error.message || '重置 AppSecret 失败')
  } finally {
    resettingApiSecret.value = false
  }
}

const copyText = async (text: string, label: string) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success(`${label}已复制`)
  } catch (error) {
    console.error(`复制${label}失败:`, error)
    ElMessage.error(`复制${label}失败`)
  }
}

watch(
  () => userInfo.value?.id,
  () => {
    latestSecret.value = ''
    apiCredential.value = null
    if (showOpenApiPanel.value) {
      loadApiCredential()
    }
  },
  { immediate: true }
)
</script>

<style scoped lang="scss">
.profile-actions {
  margin-top: 16px;
  display: flex;
  gap: 10px;
}

.api-card {
  margin-top: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
}

.api-alert {
  :deep(.el-alert__title) {
    font-size: 12px;
  }
}

.api-descriptions {
  margin-top: 12px;

  :deep(.el-descriptions__label),
  :deep(.el-descriptions__content) {
    font-size: 13px;
  }
}

.api-actions {
  margin-top: 14px;
  display: flex;
  gap: 12px;
}

.secret-card {
  margin-top: 14px;

  :deep(.el-card__header) {
    font-size: 13px;
    padding: 12px 16px;
  }

  :deep(.el-card__body) {
    padding: 14px 16px;
  }
}

.secret-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  word-break: break-all;
}

.secret-value {
  font-family: Monaco, Consolas, 'Courier New', monospace;
  font-size: 13px;
}
</style>
