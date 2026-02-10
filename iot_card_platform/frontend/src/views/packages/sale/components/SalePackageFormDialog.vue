<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑销售套餐' : '新增销售套餐'"
    width="650px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
    >
      <el-form-item label="底层套餐" prop="base_package_id">
        <el-select
          v-model="formData.base_package_id"
          placeholder="请选择底层套餐（可选）"
          filterable
          clearable
          style="width: 100%"
          @change="handleSupplierPackageChange"
        >
          <el-option
            v-for="item in supplierPackageList"
            :key="item.id"
            :label="`${item.name} (${CARRIER_MAP[item.carrier]} / ${formatFlowSize(item.flow_size)} / ${PERIOD_TYPE_MAP[item.period_type]})`"
            :value="item.id"
          >
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>{{ item.name }}</span>
              <span style="color: #909399; font-size: 12px; margin-left: 10px;">
                成本: {{ formatMoney(item.price_cost) }}
              </span>
            </div>
          </el-option>
        </el-select>
        <div v-if="selectedSupplierPackage" class="package-info">
          <el-descriptions :column="2" size="small" border>
            <el-descriptions-item label="运营商">
              {{ CARRIER_MAP[selectedSupplierPackage.carrier] }}
            </el-descriptions-item>
            <el-descriptions-item label="流量规格">
              {{ formatFlowSize(selectedSupplierPackage.flow_size) }}
            </el-descriptions-item>
            <el-descriptions-item label="周期类型">
              {{ PERIOD_TYPE_MAP[selectedSupplierPackage.period_type] }}
            </el-descriptions-item>
            <el-descriptions-item label="成本价">
              <span style="color: #f56c6c; font-weight: 600;">
                {{ formatMoney(selectedSupplierPackage.price_cost) }}
              </span>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </el-form-item>

      <el-form-item label="套餐编码" prop="code">
        <el-input
          v-model="formData.code"
          placeholder="请输入套餐编码，如：CMCC-1G-M-SALE"
          maxlength="50"
          show-word-limit
        />
        <div class="form-tip">建议使用底层套餐编码 + 后缀的方式命名</div>
      </el-form-item>

      <el-form-item label="销售套餐名称" prop="name">
        <el-input
          v-model="formData.name"
          placeholder="请输入销售套餐名称"
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
          v-model="formData.flow_size"
          :min="1"
          :max="999999"
          :precision="0"
          style="width: 150px"
        />
        <span style="margin-left: 10px; color: #909399">MB（{{ formatFlowSize(formData.flow_size) }}）</span>
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
          <el-form-item label="有效天数" prop="effective_days">
            <el-input-number
              v-model="formData.effective_days"
              :min="1"
              :max="3650"
              :precision="0"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="销售价格" prop="price_sale">
        <el-input-number
          v-model="formData.price_sale"
          :min="0"
          :max="999999"
          :precision="2"
          style="width: 200px"
        />
        <span style="margin-left: 10px; color: #909399">元</span>
        <div v-if="profitInfo.show" class="profit-info">
          <span :style="{ color: profitInfo.color }">
            利润率: {{ formatPercent(profitInfo.margin) }}
            (利润: {{ formatMoney(profitInfo.profit) }})
          </span>
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
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { salePackageApi } from '@/api/modules/package'
import type { SalePackage, SupplierPackage, CreateSalePackageRequest } from '@/types/package'
import { formatFlowSize, formatMoney, formatPercent } from '@/utils/formatter'
import { CARRIER_MAP, PERIOD_TYPE_MAP, CARRIER_OPTIONS, PERIOD_TYPE_OPTIONS } from '@/constants/package'

interface Props {
  modelValue: boolean
  packageData: SalePackage | null
  supplierPackageList: SupplierPackage[]
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

// 表单数据
const formData = reactive<CreateSalePackageRequest>({
  code: '',
  name: '',
  base_package_id: undefined,
  carrier: 'cmcc',
  flow_size: 1024,
  period_type: 'monthly',
  effective_days: 30,
  price_cost: 0,
  price_sale: 0,
  is_public: false,
  sort_order: 0,
  status: 'enable',
  remark: ''
})

// 选中的底层套餐
const selectedSupplierPackage = ref<SupplierPackage | null>(null)

// 提交状态
const submitting = ref(false)

// 重置表单
const resetForm = () => {
  Object.assign(formData, {
    code: '',
    name: '',
    base_package_id: undefined,
    carrier: 'cmcc',
    flow_size: 1024,
    period_type: 'monthly',
    effective_days: 30,
    price_cost: 0,
    price_sale: 0,
    is_public: false,
    sort_order: 0,
    status: 'enable',
    remark: ''
  })
  selectedSupplierPackage.value = null
  formRef.value?.clearValidate()
}

// 利润信息
const profitInfo = computed(() => {
  if (!selectedSupplierPackage.value || !formData.price_sale) {
    return { show: false, margin: 0, profit: 0, color: '#909399' }
  }
  
  const costPrice = selectedSupplierPackage.value.price_cost
  const salePrice = formData.price_sale
  const profit = salePrice - costPrice
  const margin = costPrice > 0 ? (profit / costPrice) * 100 : 0
  
  let color = '#67c23a' // 绿色
  if (margin < 0) {
    color = '#f56c6c' // 红色（亏损）
  } else if (margin < 10) {
    color = '#e6a23c' // 橙色（低利润）
  }
  
  return {
    show: true,
    margin,
    profit,
    color
  }
})

// 底层套餐变化
const handleSupplierPackageChange = (id: number | undefined) => {
  if (!id) {
    selectedSupplierPackage.value = null
    return
  }
  
  const found = props.supplierPackageList.find(p => p.id === id)
  selectedSupplierPackage.value = found || null
  
  if (found) {
    // 自动填充字段
    if (!isEdit.value) {
      formData.code = `${found.code}-SALE`
      formData.name = `${found.name}（销售）`
      formData.carrier = found.carrier
      formData.flow_size = found.flow_size
      formData.period_type = found.period_type
      formData.effective_days = found.effective_days
      formData.price_cost = found.price_cost
    }
    
    // 建议销售价格（成本价 * 1.2）
    if (!formData.price_sale || formData.price_sale === 0) {
      formData.price_sale = Math.ceil(found.price_cost * 1.2 * 100) / 100
    }
  }
}

// 监听套餐数据变化
watch(
  () => props.packageData,
  (data) => {
    if (data) {
      // 编辑模式，填充数据
      Object.assign(formData, {
        code: data.code,
        name: data.name,
        base_package_id: data.base_package_id,
        carrier: data.carrier,
        flow_size: data.flow_size,
        period_type: data.period_type,
        effective_days: data.effective_days,
        price_cost: data.price_cost,
        price_sale: data.price_sale,
        is_public: data.is_public || false,
        sort_order: data.sort_order || 0,
        status: data.status,
        remark: data.remark || ''
      })
      
      // 设置选中的底层套餐
      if (data.base_package_id) {
        const found = props.supplierPackageList.find(p => p.id === data.base_package_id)
        selectedSupplierPackage.value = found || null
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
    { required: true, message: '请输入销售套餐名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  carrier: [
    { required: true, message: '请选择运营商', trigger: 'change' }
  ],
  flow_size: [
    { required: true, message: '请输入流量规格', trigger: 'blur' }
  ],
  period_type: [
    { required: true, message: '请选择周期类型', trigger: 'change' }
  ],
  price_cost: [
    { required: true, message: '请输入成本价', trigger: 'blur' },
    { type: 'number', min: 0, message: '成本价不能为负数', trigger: 'blur' }
  ],
  price_sale: [
    { required: true, message: '请输入销售价格', trigger: 'blur' },
    { type: 'number', min: 0, message: '销售价格不能为负数', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value < formData.price_cost) {
          callback(new Error('销售价格不能低于成本价'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
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
      await salePackageApi.update(props.packageData.id, formData)
      ElMessage.success('更新成功')
    } else {
      // 新增
      await salePackageApi.create(formData)
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

.package-info {
  margin-top: 10px;
}

.profit-info {
  margin-top: 8px;
  font-size: 13px;
  font-weight: 500;
}

:deep(.el-input-number) {
  width: 100%;
}

:deep(.el-select-dropdown__item) {
  height: auto;
  padding: 8px 20px;
}
</style>

