<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑策略' : '新增策略'"
    width="600px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="120px"
    >
      <el-form-item label="策略名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入策略名称" />
      </el-form-item>

      <el-form-item label="策略类型" prop="type">
        <el-select v-model="form.type" placeholder="请选择策略类型" style="width: 100%">
          <el-option label="到期自动停卡" value="expire" />
          <el-option label="流量池超限停卡" value="pool_limit" />
          <el-option label="单卡超量停卡" value="card_limit" />
          <el-option label="手动停卡" value="manual" />
        </el-select>
      </el-form-item>

      <el-form-item label="策略描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="请输入策略描述"
        />
      </el-form-item>

      <!-- 到期自动停卡配置 -->
      <template v-if="form.type === 'expire'">
        <el-form-item label="提前天数" prop="config.days_before">
          <el-input-number
            v-model="form.config.days_before"
            :min="0"
            :max="30"
            placeholder="提前几天停卡"
          />
          <span style="margin-left: 10px; color: #909399">天</span>
        </el-form-item>
        <el-form-item label="自动停卡" prop="config.auto_suspend">
          <el-switch v-model="form.config.auto_suspend" />
          <span style="margin-left: 10px; color: #909399">
            启用后将在到期时自动停卡
          </span>
        </el-form-item>
      </template>

      <!-- 流量池超限停卡配置 -->
      <template v-if="form.type === 'pool_limit'">
        <el-form-item label="告警阈值" prop="config.threshold">
          <el-input-number
            v-model="form.config.threshold"
            :min="50"
            :max="100"
            placeholder="流量使用百分比"
          />
          <span style="margin-left: 10px; color: #909399">%</span>
        </el-form-item>
        <el-form-item label="自动停卡" prop="config.auto_suspend">
          <el-switch v-model="form.config.auto_suspend" />
          <span style="margin-left: 10px; color: #909399">
            启用后将在超过阈值时自动停卡
          </span>
        </el-form-item>
      </template>

      <!-- 单卡超量停卡配置 -->
      <template v-if="form.type === 'card_limit'">
        <el-form-item label="告警阈值" prop="config.threshold">
          <el-input-number
            v-model="form.config.threshold"
            :min="80"
            :max="150"
            placeholder="流量使用百分比"
          />
          <span style="margin-left: 10px; color: #909399">%</span>
        </el-form-item>
        <el-form-item label="自动停卡" prop="config.auto_suspend">
          <el-switch v-model="form.config.auto_suspend" />
          <span style="margin-left: 10px; color: #909399">
            启用后将在超过阈值时自动停卡
          </span>
        </el-form-item>
      </template>

      <el-form-item label="启用状态" prop="enabled">
        <el-switch v-model="form.enabled" />
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
import { ref, reactive, watch, computed } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { createPolicy, updatePolicy, type SuspendPolicy } from '@/api/modules/suspend'

interface Props {
  modelValue: boolean
  policy: SuspendPolicy | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const submitting = ref(false)

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const isEdit = computed(() => !!props.policy)

const form = reactive({
  name: '',
  type: '',
  description: '',
  enabled: true,
  config: {
    threshold: 80,
    days_before: 0,
    auto_suspend: false
  }
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入策略名称', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择策略类型', trigger: 'change' }
  ],
  description: [
    { required: true, message: '请输入策略描述', trigger: 'blur' }
  ]
}

// 监听策略变化，初始化表单
watch(() => props.policy, (policy) => {
  if (policy) {
    form.name = policy.name
    form.type = policy.type
    form.description = policy.description
    form.enabled = policy.enabled
    form.config = { ...policy.config }
  } else {
    resetForm()
  }
}, { immediate: true })

// 重置表单
const resetForm = () => {
  form.name = ''
  form.type = ''
  form.description = ''
  form.enabled = true
  form.config = {
    threshold: 80,
    days_before: 0,
    auto_suspend: false
  }
  formRef.value?.clearValidate()
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()

    submitting.value = true

    if (isEdit.value && props.policy) {
      await updatePolicy(props.policy.id, form)
      ElMessage.success('更新成功')
    } else {
      await createPolicy(form)
      ElMessage.success('创建成功')
    }

    emit('success')
  } catch (error: any) {
    if (error !== false) {
      console.error('提交失败:', error)
    }
  } finally {
    submitting.value = false
  }
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
}
</script>
