<template>
  <el-dialog
    v-model="visible"
    title="H5配置"
    width="640px"
    :close-on-click-modal="false"
    @open="onOpen"
  >
    <el-form label-width="110px">
      <el-form-item label="访问地址">
        <div class="h5-link-wrap">
          <el-input :model-value="h5Url" readonly />
          <el-button type="success" :disabled="!currentH5.slug" @click="handleCopyLink">
            复制链接
          </el-button>
        </div>
      </el-form-item>
      <el-form-item label="H5标题">
        <el-input v-model="form.title" maxlength="100" />
      </el-form-item>
      <el-form-item label="Logo地址">
        <el-input v-model="form.logo" maxlength="255" />
      </el-form-item>
      <el-form-item label="横幅图地址">
        <el-input v-model="form.banner" maxlength="255" />
      </el-form-item>
      <el-form-item label="公告文案">
        <el-input v-model="form.notice" type="textarea" :rows="3" maxlength="1000" show-word-limit />
      </el-form-item>
      <el-form-item label="客服电话">
        <el-input v-model="form.contact_phone" maxlength="30" />
      </el-form-item>
      <el-form-item label="客服微信">
        <el-input v-model="form.contact_wechat" maxlength="50" />
      </el-form-item>
      <el-form-item label="允许停机">
        <el-switch v-model="form.allow_suspend" />
      </el-form-item>
      <el-form-item label="允许复机">
        <el-switch v-model="form.allow_resume" />
      </el-form-item>
      <el-form-item label="允许备注">
        <el-switch v-model="form.allow_remark" />
      </el-form-item>
      <el-form-item label="需要验证">
        <el-switch v-model="form.require_verify" />
      </el-form-item>
      <el-form-item label="链接状态">
        <el-select v-model="form.status" style="width: 100%">
          <el-option label="启用" value="enabled" />
          <el-option label="停用" value="disabled" />
          <el-option label="过期" value="expired" />
        </el-select>
      </el-form-item>
      <el-form-item label="快捷操作">
        <div class="h5-actions-wrap">
          <el-button
            type="warning"
            :disabled="!currentH5.slug"
            :loading="actionLoading === 'reset'"
            @click="handleResetH5"
          >
            重置H5
          </el-button>
          <el-button
            v-if="currentH5.status === 'enabled'"
            type="warning"
            :disabled="!currentH5.slug"
            :loading="actionLoading === 'status'"
            @click="handleToggleStatus('disabled')"
          >
            停用H5
          </el-button>
          <el-button
            v-else
            type="success"
            :disabled="!currentH5.slug"
            :loading="actionLoading === 'status'"
            @click="handleToggleStatus('enabled')"
          >
            启用H5
          </el-button>
        </div>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSubmit">
        保存
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { userApi } from '@/api/modules/user'
import type { User, UserH5Config, UserH5ConfigUpdateRequest } from '@/types/user'

interface Props {
  modelValue: boolean
  user: User | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value)
})

const saving = ref(false)
const actionLoading = ref<'reset' | 'status' | ''>('')
const currentH5 = ref<UserH5Config>({
  enabled: false,
  allow_suspend: true,
  allow_resume: true,
  allow_remark: true,
  require_verify: false,
  status: 'enabled'
})
const form = reactive<UserH5ConfigUpdateRequest>({
  title: '',
  logo: '',
  banner: '',
  notice: '',
  contact_phone: '',
  contact_wechat: '',
  allow_suspend: true,
  allow_resume: true,
  allow_remark: true,
  require_verify: false,
  status: 'enabled'
})

const initForm = () => {
  const h5 = currentH5.value
  form.title = h5?.title || ''
  form.logo = h5?.logo || ''
  form.banner = h5?.banner || ''
  form.notice = h5?.notice || ''
  form.contact_phone = h5?.contact_phone || ''
  form.contact_wechat = h5?.contact_wechat || ''
  form.allow_suspend = h5?.allow_suspend ?? true
  form.allow_resume = h5?.allow_resume ?? true
  form.allow_remark = h5?.allow_remark ?? true
  form.require_verify = h5?.require_verify ?? false
  form.status = h5?.status || 'enabled'
}

const h5Url = computed(() => {
  if (!currentH5.value?.slug) {
    return '未生成H5地址'
  }
  return `${window.location.origin}/h5/${currentH5.value.slug}`
})

const loadH5Detail = async () => {
  if (!props.user?.id) return
  const detail = await userApi.getH5Detail(props.user.id)
  currentH5.value = detail
  initForm()
}

const copyByFallback = (text: string) => {
  const textArea = document.createElement('textarea')
  textArea.value = text
  textArea.style.position = 'fixed'
  textArea.style.opacity = '0'
  document.body.appendChild(textArea)
  textArea.focus()
  textArea.select()
  const copied = document.execCommand('copy')
  document.body.removeChild(textArea)
  if (!copied) {
    throw new Error('copy failed')
  }
}

const handleCopyLink = async () => {
  if (!currentH5.value?.slug) {
    ElMessage.warning('请先生成H5地址')
    return
  }
  const text = h5Url.value
  try {
    if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
    } else {
      copyByFallback(text)
    }
    ElMessage.success('H5链接已复制')
  } catch (error) {
    try {
      copyByFallback(text)
      ElMessage.success('H5链接已复制')
    } catch {
      ElMessage.error('复制失败，请手动复制')
    }
  }
}

const handleResetH5 = async () => {
  if (!props.user?.id) return
  await ElMessageBox.confirm(`确定要重置用户 "${props.user.name}" 的H5地址吗？`, '重置H5', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
  actionLoading.value = 'reset'
  try {
    currentH5.value = await userApi.resetH5(props.user.id)
    initForm()
    ElMessage.success('H5地址已重置')
    emit('success')
  } finally {
    actionLoading.value = ''
  }
}

const handleToggleStatus = async (status: 'enabled' | 'disabled') => {
  if (!props.user?.id) return
  actionLoading.value = 'status'
  try {
    currentH5.value = await userApi.updateH5Status(props.user.id, status)
    form.status = currentH5.value.status
    ElMessage.success(status === 'enabled' ? 'H5已启用' : 'H5已停用')
    emit('success')
  } finally {
    actionLoading.value = ''
  }
}

const handleSubmit = async () => {
  if (!props.user?.id) return
  saving.value = true
  try {
    currentH5.value = await userApi.updateH5Config(props.user.id, form)
    ElMessage.success('H5配置已保存')
    visible.value = false
    emit('success')
  } finally {
    saving.value = false
  }
}

const onOpen = async () => {
  currentH5.value = props.user?.h5 || currentH5.value
  await loadH5Detail()
}
</script>

<style scoped lang="scss">
.h5-link-wrap {
  width: 100%;
  display: flex;
  gap: 8px;
}

.h5-link-wrap :deep(.el-input) {
  flex: 1;
}

.h5-actions-wrap {
  width: 100%;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
