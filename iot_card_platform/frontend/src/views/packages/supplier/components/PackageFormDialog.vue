<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑底层套餐' : '新增底层套餐'"
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
      <el-form-item label="套餐编码" prop="code">
        <el-input
          v-model="formData.code"
          placeholder="请输入套餐唯一编码，如：CMCC-1G-M"
          :disabled="isEdit"
          maxlength="50"
          show-word-limit
        />
        <div class="form-tip">套餐的唯一标识符，用于系统识别</div>
      </el-form-item>

      <el-form-item label="套餐名称" prop="name">
        <el-input
          v-model="formData.name"
          placeholder="请输入套餐名称，如：移动1G/月"
          maxlength="100"
          show-word-limit
        />
      </el-form-item>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="运营商" prop="carrier">
            <el-select v-model="formData.carrier" placeholder="请选择运营商" style="width: 100%">
              <el-option
                v-for="item in CARRIER_OPTIONS"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="周期类型" prop="period_type">
            <el-select v-model="formData.period_type" placeholder="请选择周期类型" style="width: 100%">
              <el-option
                v-for="item in PERIOD_TYPE_OPTIONS"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="流量规格" prop="flow_size">
        <el-input-number
          v-model="flowValue"
          :min="1"
          :max="999999"
          :precision="0"
          style="width: 150px"
        />
        <el-select v-model="flowUnit" style="width: 100px; margin-left: 10px">
          <el-option
            v-for="item in FLOW_UNIT_OPTIONS"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
        <div class="form-tip">实际流量：{{ formatFlowSize(formData.flow_size) }}</div>
      </el-form-item>

      <el-form-item
        v-if="formData.period_type === 'monthly'"
        label="套餐周期"
        prop="period_months"
      >
        <el-input-number
          v-model="formData.period_months"
          :min="1"
          :max="120"
          :precision="0"
          style="width: 200px"
        />
        <span style="margin-left: 10px; color: #909399">个月（按自然月计算）</span>
      </el-form-item>

      <el-form-item
        v-if="formData.period_type === 'yearly'"
        label="周期规则"
      >
        <span>自激活后 12 个月，首月不足 30 天按一个月</span>
      </el-form-item>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="成本价" prop="price_cost">
            <el-input-number
              v-model="formData.price_cost"
              :min="0"
              :max="999999"
              :precision="2"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="供应商" prop="supplier_id">
            <el-select
              v-model="formData.supplier_id"
              placeholder="请选择供应商"
              filterable
              style="width: 100%"
            >
              <el-option
                v-for="item in supplierList"
                :key="item.id"
                :label="item.name"
                :value="item.id"
              />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

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
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { supplierPackageApi } from '@/api/modules/package'
import type { SupplierPackage, Supplier, CreateSupplierPackageRequest } from '@/types/package'
import { formatFlowSize } from '@/utils/formatter'
import {
  CARRIER_OPTIONS,
  PERIOD_TYPE_OPTIONS,
  FLOW_UNIT_OPTIONS
} from '@/constants/package'

interface Props {
  modelValue: boolean
  packageData: SupplierPackage | null
  supplierList: Supplier[]
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
const isEdit = computed(() => !!props.packageData)

// 表单引用
const formRef = ref<FormInstance>()

// 流量单位（用于输入）
const flowValue = ref(1)
const flowUnit = ref(1) // 1=MB, 1024=GB

// 表单数据
const formData = reactive<CreateSupplierPackageRequest>({
  code: '',
  name: '',
  carrier: 'cmcc',
  flow_size: 1024,
  period_type: 'monthly',
  period_months: 1,
  period_days: undefined,
  price_cost: 0,
  supplier_id: 0,
  status: 'enable',
  remark: ''
})

// 提交状态
const submitting = ref(false)

// 重置表单
const resetForm = () => {
  Object.assign(formData, {
    code: '',
    name: '',
    carrier: 'cmcc',
    flow_size: 1024,
    period_type: 'monthly',
    period_months: 1,
    period_days: undefined,
    price_cost: 0,
    supplier_id: 0,
    status: 'enable',
    remark: ''
  })
  flowValue.value = 1
  flowUnit.value = 1024
  formRef.value?.clearValidate()
}

// 监听流量输入变化
watch([flowValue, flowUnit], () => {
  formData.flow_size = flowValue.value * flowUnit.value
})

// 监听周期类型变化
watch(() => formData.period_type, (newType) => {
  if (newType === 'monthly') {
    formData.period_months = formData.period_months || 1
    formData.period_days = undefined
  } else {
    formData.period_days = formData.period_days || 360
    formData.period_months = undefined
  }
})

// 监听套餐数据变化
watch(
  () => props.packageData,
  (data) => {
    if (data) {
      // 编辑模式，填充数据
      Object.assign(formData, {
        code: data.code,
        name: data.name,
        carrier: data.carrier,
        flow_size: data.flow_size,
        period_type: data.period_type,
        period_months: data.period_months,
        period_days: data.period_days,
        price_cost: data.price_cost,
        supplier_id: data.supplier_id,
        status: data.status,
        remark: data.remark || ''
      })

      // 计算流量单位
      if (data.flow_size >= 1024 && data.flow_size % 1024 === 0) {
        flowValue.value = data.flow_size / 1024
        flowUnit.value = 1024
      } else {
        flowValue.value = data.flow_size
        flowUnit.value = 1
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
    { required: true, message: '请输入套餐编码', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' },
    { pattern: /^[A-Za-z0-9_-]+$/, message: '只能包含字母、数字、下划线和横线', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入套餐名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  carrier: [
    { required: true, message: '请选择运营商', trigger: 'change' }
  ],
  flow_size: [
    { required: true, message: '请输入流量规格', trigger: 'blur' },
    { type: 'number', min: 1, message: '流量规格必须大于0', trigger: 'blur' }
  ],
  period_type: [
    { required: true, message: '请选择周期类型', trigger: 'change' }
  ],
  period_months: [
    {
      validator: (_rule, value, callback) => {
        if (formData.period_type === 'monthly' && !value) {
          callback(new Error('请输入套餐周期（月）'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  period_days: [
    {
      validator: (_rule, _value, callback) => {
        callback()
      },
      trigger: 'blur'
    }
  ],
  price_cost: [
    { required: true, message: '请输入成本价', trigger: 'blur' },
    { type: 'number', min: 0, message: '成本价不能为负数', trigger: 'blur' }
  ],
  supplier_id: [
    { required: true, message: '请选择供应商', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
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
    
    submitting.value = true
    
    if (isEdit.value && props.packageData) {
      // 编辑
      await supplierPackageApi.update(props.packageData.id, formData)
      ElMessage.success('更新成功')
    } else {
      // 新增
      await supplierPackageApi.create(formData)
      ElMessage.success('创建成功')
    }
    
    emit('success')
    handleClose()
  } catch (error) {
    console.error('提交失败:', error)
    if (error !== false) {
      ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
    }
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped lang="scss">
.form-tip {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}

:deep(.el-input-number) {
  width: 100%;
}
</style>
