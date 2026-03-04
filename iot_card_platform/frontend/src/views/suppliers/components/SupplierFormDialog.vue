<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑供应商' : '新增供应商'"
    width="700px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
    >
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="供应商编码" prop="code">
            <el-input
              v-model="formData.code"
              placeholder="请输入供应商编码"
              :disabled="isEdit"
              maxlength="50"
              show-word-limit
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="供应商名称" prop="name">
            <el-input
              v-model="formData.name"
              placeholder="请输入供应商名称"
              maxlength="100"
              show-word-limit
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="供应商类型" prop="type">
        <el-select v-model="formData.type" placeholder="请选择供应商类型" style="width: 100%">
          <el-option
            v-for="item in SUPPLIER_TYPE_OPTIONS"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
      </el-form-item>

      <el-divider content-position="left">联系信息</el-divider>

      <el-row :gutter="20">
        <el-col :span="8">
          <el-form-item label="联系人" prop="contact_name">
            <el-input
              v-model="formData.contact_name"
              placeholder="请输入联系人"
              maxlength="50"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="联系电话" prop="contact_phone">
            <el-input
              v-model="formData.contact_phone"
              placeholder="请输入联系电话"
              maxlength="20"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="联系邮箱" prop="contact_email">
            <el-input
              v-model="formData.contact_email"
              placeholder="请输入联系邮箱"
              maxlength="100"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-divider content-position="left">API配置</el-divider>

      <el-form-item label="API地址" prop="api_url">
        <el-input
          v-model="formData.api_url"
          placeholder="请输入API地址，如：https://api.supplier.com"
          maxlength="255"
        />
      </el-form-item>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="API Key" prop="api_key">
            <el-input
              v-model="formData.api_key"
              :placeholder="isEdit && hasApiKey ? '已设置，留空则不修改' : '请输入API Key'"
              maxlength="255"
              show-password
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="API Secret" prop="api_secret">
            <el-input
              v-model="formData.api_secret"
              :placeholder="isEdit && hasApiSecret ? '已设置，留空则不修改' : '请输入API Secret'"
              maxlength="255"
              show-password
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="API配置" prop="api_config">
        <el-input
          v-model="apiConfigText"
          type="textarea"
          :rows="4"
          placeholder='请输入JSON格式的API配置，如：{"timeout": 30, "retry": 3}'
        />
        <div class="form-tip">
          可选配置项：超时时间、重试次数、其他自定义参数等
        </div>
      </el-form-item>

      <el-form-item label="同步间隔" prop="sync_interval">
        <el-input-number
          v-model="formData.sync_interval"
          :min="1"
          :max="1440"
          placeholder="请输入同步间隔"
          style="width: 200px"
        />
        <span style="margin-left: 10px; color: #909399;">分钟</span>
        <div class="form-tip">
          设置流量数据自动同步的时间间隔，范围：1-1440分钟
        </div>
      </el-form-item>

      <el-form-item label="状态" prop="status">
        <el-radio-group v-model="formData.status">
          <el-radio label="enable">启用</el-radio>
          <el-radio label="disable">禁用</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="备注">
        <el-input
          v-model="formData.remark"
          type="textarea"
          :rows="3"
          placeholder="请输入备注信息"
          maxlength="500"
          show-word-limit
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

  <!-- 密码确认弹窗 -->
  <el-dialog
    v-model="passwordDialogVisible"
    title="身份验证"
    width="380px"
    :close-on-click-modal="false"
    append-to-body
    @close="handlePasswordDialogClose"
  >
    <div style="margin-bottom: 12px; color: #606266; font-size: 14px;">
      请输入您的登录密码以确认此操作
    </div>
    <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules">
      <el-form-item prop="password">
        <el-input
          v-model="passwordForm.password"
          type="password"
          placeholder="请输入登录密码"
          show-password
          @keyup.enter="confirmWithPassword"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="handlePasswordDialogClose">取消</el-button>
      <el-button type="primary" :loading="verifying" @click="confirmWithPassword">
        确认
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import supplierApi from '@/api/modules/supplier'
import { authApi } from '@/api'
import { useAuthStore } from '@/stores/modules/auth'
import type { Supplier, CreateSupplierRequest } from '@/types/supplier'
import { SUPPLIER_TYPE_OPTIONS } from '@/constants/supplier'

interface Props {
  modelValue: boolean
  supplierData: Supplier | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 弹窗显示控制
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 是否编辑模式
const isEdit = computed(() => !!props.supplierData)

// 表单引用
const formRef = ref<FormInstance>()

// 表单数据
const formData = reactive<CreateSupplierRequest>({
  name: '',
  code: '',
  type: 'other',
  contact_name: '',
  contact_phone: '',
  contact_email: '',
  api_url: '',
  api_key: '',
  api_secret: '',
  api_config: undefined,
  sync_interval: 60,
  remark: ''
})

// API配置文本（用于编辑JSON）
const apiConfigText = ref('')

// 是否已设置过密钥（用于编辑时显示占位符）
const hasApiKey = ref(false)
const hasApiSecret = ref(false)

// 提交状态
const submitting = ref(false)

// 密码确认弹窗
const passwordDialogVisible = ref(false)
const passwordFormRef = ref<FormInstance>()
const passwordForm = reactive({ password: '' })
const verifying = ref(false)
const passwordRules: FormRules = {
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

// 暂存待提交的数据
let pendingSubmitData: any = null

// 重置表单
const resetForm = () => {
  Object.assign(formData, {
    name: '',
    code: '',
    type: 'other',
    contact_name: '',
    contact_phone: '',
    contact_email: '',
    api_url: '',
    api_key: '',
    api_secret: '',
    api_config: undefined,
    sync_interval: 60,
    remark: ''
  })
  apiConfigText.value = ''
  hasApiKey.value = false
  hasApiSecret.value = false
  formRef.value?.clearValidate()
}

// 监听供应商数据变化
watch(
  () => props.supplierData,
  (data) => {
    if (data) {
      // 编辑模式，填充数据
      hasApiKey.value = !!data.has_api_key
      hasApiSecret.value = !!data.has_api_secret
      Object.assign(formData, {
        name: data.name,
        code: data.code,
        type: data.type,
        contact_name: data.contact_name || '',
        contact_phone: data.contact_phone || '',
        contact_email: data.contact_email || '',
        api_url: data.api_url || '',
        api_key: '',
        api_secret: '',
        api_config: data.api_config,
        sync_interval: data.sync_interval || 60,
        remark: data.remark || ''
      })
      
      // 格式化API配置为JSON字符串
      if (data.api_config) {
        try {
          apiConfigText.value = JSON.stringify(data.api_config, null, 2)
        } catch (e) {
          apiConfigText.value = ''
        }
      } else {
        apiConfigText.value = ''
      }
    } else {
      // 新增模式，重置表单
      resetForm()
    }
  },
  { immediate: true }
)

// 表单验证规则
const rules: FormRules = {
  code: [
    { required: true, message: '请输入供应商编码', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' },
    { pattern: /^[A-Za-z0-9_-]+$/, message: '只能包含字母、数字、下划线和横线', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入供应商名称', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择供应商类型', trigger: 'change' }
  ],
  contact_phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
  ],
  contact_email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  api_url: [
    { type: 'url', message: '请输入正确的URL地址', trigger: 'blur' }
  ],
  sync_interval: [
    { required: true, message: '请输入同步间隔', trigger: 'blur' },
    { type: 'number', min: 1, max: 1440, message: '同步间隔范围为1-1440分钟', trigger: 'blur' }
  ]
}

// 关闭弹窗
const handleClose = () => {
  visible.value = false
  resetForm()
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()

    // 解析API配置JSON
    if (apiConfigText.value.trim()) {
      try {
        formData.api_config = JSON.parse(apiConfigText.value)
      } catch (e) {
        ElMessage.error('API配置JSON格式不正确')
        return
      }
    } else {
      formData.api_config = undefined
    }

    if (isEdit.value && props.supplierData) {
      // 编辑模式：先弹出密码确认
      const updateData: any = { ...formData }
      if (!updateData.api_key) delete updateData.api_key
      if (!updateData.api_secret) delete updateData.api_secret
      pendingSubmitData = updateData
      passwordForm.password = ''
      passwordDialogVisible.value = true
    } else {
      // 新增模式：直接提交
      submitting.value = true
      await supplierApi.createSupplier(formData)
      ElMessage.success('创建成功')
      emit('success')
      handleClose()
    }
  } catch (error) {
    console.error('提交失败:', error)
    if (error !== false) {
      ElMessage.error('创建失败')
    }
  } finally {
    submitting.value = false
  }
}

// 密码验证通过后执行保存
const confirmWithPassword = async () => {
  if (!passwordFormRef.value) return
  try {
    await passwordFormRef.value.validate()
  } catch {
    return
  }

  const authStore = useAuthStore()
  const account = authStore.userInfo?.account
  if (!account) {
    ElMessage.error('无法获取当前用户信息')
    return
  }

  verifying.value = true
  try {
    await authApi.login({ account, password: passwordForm.password })
  } catch {
    ElMessage.error('密码错误，操作已取消')
    return
  } finally {
    verifying.value = false
  }

  // 密码验证通过，执行保存
  passwordDialogVisible.value = false
  submitting.value = true
  try {
    await supplierApi.updateSupplier(props.supplierData!.id, pendingSubmitData)
    ElMessage.success('更新成功')
    emit('success')
    handleClose()
  } catch (error) {
    console.error('更新失败:', error)
    ElMessage.error('更新失败')
  } finally {
    submitting.value = false
    pendingSubmitData = null
  }
}

const handlePasswordDialogClose = () => {
  passwordDialogVisible.value = false
  passwordForm.password = ''
  pendingSubmitData = null
}
</script>

<style scoped lang="scss">
.form-tip {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}

:deep(.el-divider__text) {
  font-weight: 600;
  color: #606266;
}
</style>






