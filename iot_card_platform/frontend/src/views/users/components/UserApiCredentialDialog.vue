<template>
  <el-dialog
    v-model="visible"
    title="API凭证"
    width="640px"
    :close-on-click-modal="false"
    @closed="handleClosed"
  >
    <div v-loading="loading" class="credential-dialog">
      <el-alert
        title="AppSecret 仅在重置后完整展示一次，请及时保存给对接方。"
        type="warning"
        :closable="false"
        show-icon
      />

      <el-descriptions :column="1" border class="credential-panel">
        <el-descriptions-item label="用户">{{ user?.name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="账号">{{ user?.account || '-' }}</el-descriptions-item>
        <el-descriptions-item label="APPID">
          <div class="credential-row">
            <span>{{ credential?.app_id || '-' }}</span>
            <el-button
              v-if="credential?.app_id"
              link
              type="primary"
              @click="copyText(credential.app_id, 'APPID')"
            >
              复制
            </el-button>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="当前Secret">
          {{ credential?.app_secret_masked || '未生成' }}
        </el-descriptions-item>
        <el-descriptions-item label="最近重置时间">
          {{ formatDateTime(credential?.last_reset_at) || '-' }}
        </el-descriptions-item>
      </el-descriptions>

      <el-card v-if="latestSecret" shadow="never" class="secret-card">
        <template #header>新 AppSecret</template>
        <div class="credential-row secret-value">
          <span>{{ latestSecret }}</span>
          <el-button link type="primary" @click="copyText(latestSecret, 'AppSecret')">
            复制
          </el-button>
        </div>
      </el-card>
    </div>

    <template #footer>
      <el-button @click="visible = false">关闭</el-button>
      <el-button type="primary" :loading="resetting" @click="handleReset">
        重置 AppSecret
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { userApi } from '@/api/modules/user'
import { formatDateTime } from '@/utils/formatter'
import type { User, UserOpenApiCredential } from '@/types/user'

const props = defineProps<{
  modelValue: boolean
  user: User | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: []
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const loading = ref(false)
const resetting = ref(false)
const credential = ref<UserOpenApiCredential | null>(null)
const latestSecret = ref('')

const loadCredential = async () => {
  if (!props.user?.id || !visible.value) {
    return
  }
  loading.value = true
  try {
    credential.value = await userApi.getOpenApiCredentials(props.user.id)
  } finally {
    loading.value = false
  }
}

const handleReset = async () => {
  if (!props.user?.id) {
    return
  }
  await ElMessageBox.confirm(
    `确定要重置用户“${props.user.name}”的 AppSecret 吗？原密钥将立即失效。`,
    '重置确认',
    {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消'
    }
  )

  resetting.value = true
  try {
    const result = await userApi.resetOpenApiCredentials(props.user.id)
    latestSecret.value = result.app_secret
    credential.value = {
      enabled: result.enabled,
      app_id: result.app_id,
      app_secret_masked: `${result.app_secret.slice(0, 4)}******${result.app_secret.slice(-4)}`,
      has_app_secret: true,
      last_reset_at: result.last_reset_at
    }
    ElMessage.success('AppSecret 已重置')
    emit('success')
  } finally {
    resetting.value = false
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

const handleClosed = () => {
  credential.value = null
  latestSecret.value = ''
}

watch(
  () => visible.value,
  (value) => {
    if (value) {
      latestSecret.value = ''
      loadCredential()
    }
  }
)
</script>

<style scoped lang="scss">
.credential-dialog {
  display: grid;
  gap: 16px;
}

.credential-panel,
.secret-card {
  margin-top: 8px;
}

.credential-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  word-break: break-all;
}

.secret-value {
  font-family: Monaco, Consolas, 'Courier New', monospace;
}
</style>
