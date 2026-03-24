<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑用户' : '新增用户'"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
    >
      <el-form-item label="姓名" prop="name">
        <el-input
          v-model="formData.name"
          placeholder="请输入姓名"
          maxlength="50"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="账号" prop="account">
        <el-input
          v-model="formData.account"
          placeholder="请输入账号"
          maxlength="50"
          show-word-limit
          :disabled="isEdit"
        />
      </el-form-item>

      <el-form-item v-if="!isEdit" label="密码" prop="password">
        <el-input
          v-model="formData.password"
          type="password"
          placeholder="请输入密码（6-50位）"
          maxlength="50"
          show-password
        />
      </el-form-item>

      <el-form-item label="手机号" prop="phone">
        <el-input
          v-model="formData.phone"
          placeholder="请输入手机号"
          maxlength="11"
        />
      </el-form-item>

      <el-form-item label="邮箱" prop="email">
        <el-input
          v-model="formData.email"
          placeholder="请输入邮箱"
          maxlength="100"
        />
      </el-form-item>

      <el-form-item label="卡片配额" prop="quota.max_cards">
        <el-input-number
          v-model="formData.quota.max_cards"
          :min="0"
          :max="100000"
          :step="100"
          controls-position="right"
        />
      </el-form-item>

      <el-form-item label="子用户配额" prop="quota.max_sub_users">
        <el-input-number
          v-model="formData.quota.max_sub_users"
          :min="0"
          :max="100"
          :step="1"
          controls-position="right"
        />
      </el-form-item>

      <el-divider content-position="left">流量池设置</el-divider>

      <el-form-item label="停卡阈值">
        <div class="pool-threshold-input">
          <el-input-number
            v-model="formData.quota.pool_stop_threshold"
            :min="50"
            :max="200"
            :step="5"
            controls-position="right"
            placeholder="不限制"
          />
          <span class="unit">%</span>
        </div>
        <div class="form-tip">流量池用量达到此阈值时，池内所有卡片将被停卡。留空表示不限制。</div>
      </el-form-item>

      <el-divider content-position="left">通知设置</el-divider>

      <el-form-item label="短信通知">
        <el-switch v-model="formData.alert_notify.sms" />
      </el-form-item>

      <el-form-item label="邮件通知">
        <el-switch v-model="formData.alert_notify.email" />
      </el-form-item>

      <el-form-item label="状态" prop="status">
        <el-radio-group v-model="formData.status">
          <el-radio value="enable">启用</el-radio>
          <el-radio value="disable">禁用</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="备注" prop="remark">
        <el-input
          v-model="formData.remark"
          type="textarea"
          :rows="3"
          placeholder="请输入备注"
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
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { userApi } from '@/api/modules/user'
import type { User, UserCreateRequest, UserUpdateRequest } from '@/types/user'

type UserFormModel = UserCreateRequest & {
  alert_notify: {
    sms: boolean
    email: boolean
  }
  quota: {
    max_cards: number
    max_sub_users: number
    pool_stop_threshold?: number
  }
}

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

// 是否编辑模式
const isEdit = computed(() => !!props.user)

// 表单引用
const formRef = ref<FormInstance>()

// 表单数据
const formData = reactive<UserFormModel>({
  name: '',
  account: '',
  password: '',
  phone: '',
  email: '',
  alert_notify: {
    sms: true,
    email: true
  },
  quota: {
    max_cards: 100,
    max_sub_users: 5,
    pool_stop_threshold: 100,
    account_balance: 0,
    balance_alert_threshold: 1000
  },
  remark: '',
  status: 'enable'
})

// 表单验证规则
const formRules: FormRules = {
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { min: 2, max: 50, message: '姓名长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  account: [
    { required: true, message: '请输入账号', trigger: 'blur' },
    { min: 2, max: 50, message: '账号长度在 2 到 50 个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '账号只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 50, message: '密码长度在 6 到 50 个字符', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
}

// 提交状态
const submitting = ref(false)

/**
 * 初始化表单数据
 */
const initFormData = () => {
  if (props.user) {
    // 编辑模式：填充用户数据
    formData.name = props.user.name
    formData.account = props.user.account
    formData.phone = props.user.phone || ''
    formData.email = props.user.email || ''
    formData.alert_notify = props.user.alert_notify || { sms: true, email: true }
    formData.quota = props.user.quota || { max_cards: 100, max_sub_users: 5, pool_stop_threshold: 100, account_balance: 0, balance_alert_threshold: 1000 }
    formData.remark = props.user.remark || ''
    formData.status = props.user.status
  } else {
    // 新增模式：重置表单
    formData.name = ''
    formData.account = ''
    formData.password = ''
    formData.phone = ''
    formData.email = ''
    formData.alert_notify = { sms: true, email: true }
    formData.quota = { max_cards: 100, max_sub_users: 5, pool_stop_threshold: 100, account_balance: 0, balance_alert_threshold: 1000 }
    formData.remark = ''
    formData.status = 'enable'
  }
}

/**
 * 提交表单
 */
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    // 验证表单
    await formRef.value.validate()

    submitting.value = true

    if (isEdit.value && props.user) {
      // 编辑用户
      const updateData: UserUpdateRequest = {
        name: formData.name,
        phone: formData.phone || undefined,
        email: formData.email || undefined,
        alert_notify: formData.alert_notify,
        quota: formData.quota,
        remark: formData.remark || undefined,
        status: formData.status
      }
      await userApi.update(props.user.id, updateData)
      ElMessage.success('更新成功')
    } else {
      // 创建用户
      await userApi.create(formData)
      ElMessage.success('创建成功')
    }

    emit('success')
  } catch (error) {
    console.error('提交失败:', error)
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
  visible.value = false
}

// 监听弹窗打开，初始化表单数据
watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal) {
      initFormData()
    }
  }
)
</script>

<style scoped lang="scss">
:deep(.el-input-number) {
  width: 100%;
}

.pool-threshold-input {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;

  .unit {
    color: #606266;
    font-size: 14px;
    white-space: nowrap;
  }
}

.form-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
  margin-top: 4px;
}
</style>





