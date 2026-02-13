<template>
  <el-dialog
    v-model="visible"
    title="编辑流量池"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-alert
      title="说明：流量池由系统自动创建，只能修改告警阈值和备注"
      type="info"
      :closable="false"
      style="margin-bottom: 16px"
    />

    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
    >
      <el-form-item label="告警阈值1" prop="alert_threshold_1">
        <el-input-number
          v-model="formData.alert_threshold_1"
          :min="0"
          :max="100"
          :step="1"
        />
        <span style="margin-left: 8px">%</span>
        <div class="form-tip">流量使用率达到此阈值时触发第一次告警</div>
      </el-form-item>

      <el-form-item label="告警阈值2" prop="alert_threshold_2">
        <el-input-number
          v-model="formData.alert_threshold_2"
          :min="0"
          :max="100"
          :step="1"
        />
        <span style="margin-left: 8px">%</span>
        <div class="form-tip">流量使用率达到此阈值时触发第二次告警</div>
      </el-form-item>

      <el-form-item label="告警阈值3" prop="alert_threshold_3">
        <el-input-number
          v-model="formData.alert_threshold_3"
          :min="0"
          :max="100"
          :step="1"
        />
        <span style="margin-left: 8px">%</span>
        <div class="form-tip">流量使用率达到此阈值时触发第三次告警</div>
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
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { updatePool } from '@/api/modules/pool'
import type { Pool, PoolUpdateData } from '@/types/pool'

interface Props {
  modelValue: boolean
  pool?: Pool | null
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

// 表单数据
const formData = reactive<PoolUpdateData>({
  alert_threshold_1: 70,
  alert_threshold_2: 85,
  alert_threshold_3: 95,
  remark: ''
})

// 表单验证规则
const rules: FormRules = {
  alert_threshold_1: [
    { type: 'number', min: 0, max: 100, message: '告警阈值范围为 0-100', trigger: 'blur' }
  ],
  alert_threshold_2: [
    { type: 'number', min: 0, max: 100, message: '告警阈值范围为 0-100', trigger: 'blur' }
  ],
  alert_threshold_3: [
    { type: 'number', min: 0, max: 100, message: '告警阈值范围为 0-100', trigger: 'blur' }
  ]
}

/**
 * 初始化表单数据
 */
const initFormData = () => {
  if (props.pool) {
    Object.assign(formData, {
      alert_threshold_1: props.pool.alert_threshold_1 || 70,
      alert_threshold_2: props.pool.alert_threshold_2 || 85,
      alert_threshold_3: props.pool.alert_threshold_3 || 95,
      remark: props.pool.remark || ''
    })
  }
}

/**
 * 提交表单
 */
const handleSubmit = async () => {
  if (!formRef.value || !props.pool) return

  try {
    await formRef.value.validate()
    submitting.value = true

    await updatePool(props.pool.id, formData)
    ElMessage.success('更新成功')

    emit('success')
    handleClose()
  } catch (error: any) {
    if (error !== false) {
      console.error('提交失败:', error)
      ElMessage.error(error.message || '操作失败')
    }
  } finally {
    submitting.value = false
  }
}

/**
 * 关闭对话框
 */
const handleClose = () => {
  formRef.value?.resetFields()
  visible.value = false
}

// 监听对话框打开，初始化表单数据
watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      initFormData()
    }
  }
)
</script>

<style scoped lang="scss">
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
