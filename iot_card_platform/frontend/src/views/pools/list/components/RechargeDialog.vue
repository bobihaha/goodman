<template>
  <el-dialog
    v-model="visible"
    title="充值加油包"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-alert
      v-if="pool"
      :title="`流量池：${pool.name} | 当前用量：${formatFlow(pool.data_used)} / ${formatFlow(pool.data_total)} (${pool.usage_percent}%)`"
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
      <el-form-item label="选择加油包" prop="package_id">
        <el-select
          v-model="formData.package_id"
          placeholder="请选择加油包"
          style="width: 100%"
          @change="handlePackageChange"
        >
          <el-option
            v-for="item in packageList"
            :key="item.id"
            :label="`${item.name} - ${formatFlow(item.flow_size)} - ¥${item.price} - 有效期${item.valid_days}天`"
            :value="item.id"
          >
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>{{ item.name }}</span>
              <span style="color: #909399; font-size: 12px">
                {{ formatFlow(item.flow_size) }} | ¥{{ item.price }} | {{ item.valid_days }}天
              </span>
            </div>
          </el-option>
        </el-select>
      </el-form-item>

      <el-form-item v-if="selectedPackage" label="加油包详情">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="流量大小">
            {{ formatFlow(selectedPackage.flow_size) }}
          </el-descriptions-item>
          <el-descriptions-item label="价格">
            <span style="color: #f56c6c; font-weight: bold; font-size: 16px">
              ¥{{ selectedPackage.price }}
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="有效期">
            {{ selectedPackage.valid_days }} 天
          </el-descriptions-item>
          <el-descriptions-item label="运营商">
            {{ CARRIER_MAP[selectedPackage.carrier] }}
          </el-descriptions-item>
        </el-descriptions>
      </el-form-item>

      <el-form-item v-if="selectedPackage" label="充值后">
        <el-alert type="success" :closable="false">
          <template #title>
            <div>
              总流量：{{ formatFlow(pool!.data_total) }} → 
              <span style="color: #67c23a; font-weight: bold">
                {{ formatFlow(pool!.data_total + selectedPackage.flow_size) }}
              </span>
            </div>
            <div style="margin-top: 4px">
              使用率：{{ pool!.usage_percent }}% → 
              <span style="color: #67c23a; font-weight: bold">
                {{ calculateNewUsagePercent() }}%
              </span>
            </div>
          </template>
        </el-alert>
      </el-form-item>

      <el-form-item label="备注">
        <el-input
          v-model="formData.remark"
          type="textarea"
          :rows="3"
          placeholder="请输入备注信息（可选）"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        确认充值
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { getPoolPackages, rechargePool } from '@/api/modules/pool'
import { formatFlow } from '@/utils/formatter'
import { CARRIER_MAP } from '@/constants/card'
import type { Pool, PoolPackage } from '@/types/pool'

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

// 加油包列表
const packageList = ref<PoolPackage[]>([])

// 表单数据
const formData = reactive({
  package_id: undefined as number | undefined,
  remark: ''
})

// 已选择的加油包
const selectedPackage = computed(() => {
  if (!formData.package_id) return null
  return packageList.value.find(p => p.id === formData.package_id)
})

// 表单验证规则
const rules: FormRules = {
  package_id: [
    { required: true, message: '请选择加油包', trigger: 'change' }
  ]
}

/**
 * 获取加油包列表
 */
const fetchPackages = async () => {
  if (!props.pool) return

  try {
    const data = await getPoolPackages(props.pool.carrier)
    packageList.value = data || []
  } catch (error) {
    console.error('获取加油包列表失败:', error)
    ElMessage.error('获取加油包列表失败')
  }
}

/**
 * 加油包选择变化
 */
const handlePackageChange = () => {
  // 可以在这里添加额外的逻辑
}

/**
 * 计算充值后的使用率
 */
const calculateNewUsagePercent = () => {
  if (!props.pool || !selectedPackage.value) return 0
  const newTotal = props.pool.data_total + selectedPackage.value.flow_size
  const percent = (props.pool.data_used / newTotal) * 100
  return Math.round(percent)
}

/**
 * 提交表单
 */
const handleSubmit = async () => {
  if (!formRef.value || !props.pool || !selectedPackage.value) return

  try {
    await formRef.value.validate()

    // 二次确认
    await ElMessageBox.confirm(
      `确认充值 ${selectedPackage.value.name}（¥${selectedPackage.value.price}）吗？`,
      '确认充值',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    submitting.value = true

    await rechargePool({
      pool_id: props.pool.id,
      package_id: formData.package_id!
    })

    ElMessage.success('充值成功')
    emit('success')
    handleClose()
  } catch (error: any) {
    if (error !== 'cancel' && error !== false) {
      console.error('充值失败:', error)
      ElMessage.error(error.message || '充值失败')
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
  formData.package_id = undefined
  formData.remark = ''
  visible.value = false
}

// 监听对话框打开
watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      formData.package_id = undefined
      formData.remark = ''
      fetchPackages()
    }
  }
)
</script>

<style scoped lang="scss">
:deep(.el-select-dropdown__item) {
  height: auto;
  padding: 8px 20px;
}
</style>



