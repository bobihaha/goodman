<template>
  <div class="stock-out-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span class="title">卡片出库</span>
        </div>
      </template>

      <el-steps :active="currentStep" finish-status="success" align-center class="steps">
        <el-step title="选择卡片" />
        <el-step title="选择用户和套餐" />
        <el-step title="确认出库" />
      </el-steps>

      <!-- 步骤1: 选择卡片 -->
      <div v-if="currentStep === 0" class="step-content">
        <div class="select-cards-section">
          <!-- 搜索栏 -->
          <el-form :inline="true" :model="queryParams" class="search-form">
            <el-form-item label="供应商">
              <el-select v-model="queryParams.supplier_id" placeholder="请选择" clearable style="width: 150px">
                <el-option
                  v-for="supplier in suppliers"
                  :key="supplier.id"
                  :label="supplier.name"
                  :value="supplier.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="运营商">
              <el-select v-model="queryParams.carrier" placeholder="请选择" clearable style="width: 120px">
                <el-option label="中国移动" value="cmcc" />
                <el-option label="中国联通" value="cucc" />
                <el-option label="中国电信" value="ctcc" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleQuery">查询</el-button>
              <el-button @click="handleReset">重置</el-button>
            </el-form-item>
          </el-form>

          <!-- 已选卡片提示 -->
          <el-alert
            v-if="selectedCards.length > 0"
            :title="`已选择 ${selectedCards.length} 张卡片`"
            type="success"
            :closable="false"
            style="margin-bottom: 20px"
          />

          <!-- 表格 -->
          <el-table
            :data="tableData"
            v-loading="loading"
            border
            stripe
            @selection-change="handleSelectionChange"
          >
            <el-table-column type="selection" width="55" />
            <el-table-column prop="iccid" label="ICCID" width="200" />
            <el-table-column prop="imsi" label="IMSI" width="150" />
            <el-table-column prop="msisdn" label="MSISDN" width="130" />
            <el-table-column prop="supplier_name" label="供应商" width="120" />
            <el-table-column label="规格" width="200">
              <template #default="{ row }">
                {{ row.carrier_name }} / {{ formatFlow(row.flow_size) }} / {{ row.period_name }}
              </template>
            </el-table-column>
            <el-table-column label="生命周期" width="180">
              <template #default="{ row }">
                <div style="font-size: 12px">
                  <div v-if="row.test_expire_date">测试: {{ row.test_expire_date }}</div>
                  <div>沉默: {{ row.silent_expire_date }}</div>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="stock_in_at" label="入库时间" width="160" />
          </el-table>

          <!-- 分页 -->
          <el-pagination
            v-model:current-page="queryParams.page"
            v-model:page-size="queryParams.page_size"
            :total="total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleQuery"
            @current-change="handleQuery"
            class="pagination"
          />

          <div class="step-actions">
            <el-button type="primary" @click="nextStep" :disabled="selectedCards.length === 0">
              下一步（已选 {{ selectedCards.length }} 张）
            </el-button>
          </div>
        </div>
      </div>

      <!-- 步骤2: 选择用户和套餐 -->
      <div v-if="currentStep === 1" class="step-content">
        <el-form :model="outForm" :rules="rules" ref="formRef" label-width="120px" style="max-width: 600px; margin: 40px auto">
          <el-form-item label="目标用户" prop="to_user_id">
            <el-select v-model="outForm.to_user_id" placeholder="请选择目标用户" filterable style="width: 100%">
              <el-option
                v-for="user in users"
                :key="user.id"
                :label="`${user.name} (${user.account})`"
                :value="user.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="销售套餐" prop="sale_package_id">
            <el-select v-model="outForm.sale_package_id" placeholder="请选择销售套餐" filterable style="width: 100%">
              <el-option
                v-for="pkg in salePackages"
                :key="pkg.id"
                :label="`${pkg.name} - ${pkg.carrier_name}/${formatFlow(pkg.flow_size)}/${pkg.period_name} - ¥${pkg.price_sale}`"
                :value="pkg.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="备注">
            <el-input v-model="outForm.remark" type="textarea" :rows="3" placeholder="请输入备注" />
          </el-form-item>
        </el-form>

        <div class="step-actions">
          <el-button @click="prevStep">上一步</el-button>
          <el-button type="primary" @click="nextStep">下一步</el-button>
        </div>
      </div>

      <!-- 步骤3: 确认出库 -->
      <div v-if="currentStep === 2" class="step-content">
        <div class="confirm-section">
          <el-descriptions title="出库信息" :column="2" border>
            <el-descriptions-item label="目标用户">
              {{ selectedUser?.name }} ({{ selectedUser?.account }})
            </el-descriptions-item>
            <el-descriptions-item label="销售套餐">
              {{ selectedPackage?.name }}
            </el-descriptions-item>
            <el-descriptions-item label="套餐价格">
              ¥{{ selectedPackage?.price_sale }}
            </el-descriptions-item>
            <el-descriptions-item label="卡片数量">
              <el-tag type="success">{{ selectedCards.length }} 张</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="总金额">
              <el-tag type="danger" size="large">
                ¥{{ (selectedCards.length * (selectedPackage?.price_sale || 0)).toFixed(2) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="备注" :span="2">
              {{ outForm.remark || '-' }}
            </el-descriptions-item>
          </el-descriptions>

          <!-- 卡片列表 -->
          <div class="card-list-preview">
            <div class="list-title">出库卡片列表</div>
            <el-table :data="selectedCards" border stripe max-height="300">
              <el-table-column type="index" label="序号" width="60" />
              <el-table-column prop="iccid" label="ICCID" />
              <el-table-column prop="imsi" label="IMSI" />
              <el-table-column prop="msisdn" label="MSISDN" />
              <el-table-column prop="supplier_name" label="供应商" />
            </el-table>
          </div>

          <div class="step-actions">
            <el-button @click="prevStep">上一步</el-button>
            <el-button type="primary" @click="handleSubmit" :loading="submitting">
              确认出库
            </el-button>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { stockApi } from '@/api/modules/stock'
import { supplierApi } from '@/api/modules/supplier'
import { packageApi } from '@/api/modules/package'
import { userApi } from '@/api/modules/user'
import { useRouter } from 'vue-router'

const router = useRouter()

// 当前步骤
const currentStep = ref(0)

// 查询参数
const queryParams = reactive({
  supplier_id: undefined,
  carrier: undefined,
  page: 1,
  page_size: 20
})

// 表格数据
const tableData = ref([])
const total = ref(0)
const loading = ref(false)

// 选中的卡片
const selectedCards = ref<any[]>([])

// 供应商、用户、套餐列表
const suppliers = ref([])
const users = ref([])
const salePackages = ref([])

// 出库表单
const outForm = reactive({
  to_user_id: undefined as number | undefined,
  sale_package_id: undefined as number | undefined,
  remark: ''
})

const formRef = ref()
const submitting = ref(false)

// 表单验证规则
const rules = {
  to_user_id: [{ required: true, message: '请选择目标用户', trigger: 'change' }],
  sale_package_id: [{ required: true, message: '请选择销售套餐', trigger: 'change' }]
}

// 选中的用户
const selectedUser = computed(() => {
  return users.value.find((u: any) => u.id === outForm.to_user_id)
})

// 选中的套餐
const selectedPackage = computed(() => {
  return salePackages.value.find((p: any) => p.id === outForm.sale_package_id)
})

// 获取库存卡片
const fetchInventory = async () => {
  loading.value = true
  try {
    const res = await stockApi.getInventory(queryParams)
    tableData.value = res.items || []  // 库存API返回 items
    total.value = res.total || 0
  } catch (error) {
    ElMessage.error('获取库存卡片失败')
  } finally {
    loading.value = false
  }
}

// 获取供应商列表
const fetchSuppliers = async () => {
  try {
    const res = await supplierApi.getList({ page: 1, page_size: 100 })
    suppliers.value = res.list || res.data?.items || res.data?.list || []
  } catch (error) {
    console.error('获取供应商列表失败', error)
  }
}

// 获取用户列表
const fetchUsers = async () => {
  try {
    const res = await userApi.getList({ page: 1, page_size: 100 })
    users.value = (res.list || res.data?.items || res.data?.list || []).filter((u: any) => u.user_level === 2) // 只显示普通用户
  } catch (error) {
    console.error('获取用户列表失败', error)
  }
}

// 获取销售套餐列表
const fetchSalePackages = async () => {
  try {
    const res = await packageApi.getSalePackages({ page: 1, page_size: 100, status: 'enable' })
    salePackages.value = res.list || []  // 销售套餐API返回 list
  } catch (error) {
    console.error('获取销售套餐列表失败', error)
  }
}

// 查询
const handleQuery = () => {
  queryParams.page = 1
  fetchInventory()
}

// 重置
const handleReset = () => {
  queryParams.supplier_id = undefined
  queryParams.carrier = undefined
  queryParams.page = 1
  fetchInventory()
}

// 选择变化
const handleSelectionChange = (selection: any[]) => {
  selectedCards.value = selection
}

// 下一步
const nextStep = async () => {
  if (currentStep.value === 1) {
    // 验证表单
    if (!formRef.value) return
    const valid = await formRef.value.validate().catch(() => false)
    if (!valid) return
  }
  
  if (currentStep.value < 2) {
    currentStep.value++
  }
}

// 上一步
const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

// 提交出库
const handleSubmit = async () => {
  submitting.value = true
  try {
    const card_ids = selectedCards.value.map(card => card.id)
    const res = await stockApi.stockOut({
      card_ids,
      to_user_id: outForm.to_user_id!,
      sale_package_id: outForm.sale_package_id!,
      remark: outForm.remark
    })
    
    ElMessage.success(`出库成功！成功 ${res.success} 张，失败 ${res.failed} 张`)
    
    // 跳转到出库记录
    router.push('/stock/out-records')
  } catch (error: any) {
    ElMessage.error(error.message || '出库失败')
  } finally {
    submitting.value = false
  }
}

// 格式化流量
const formatFlow = (mb: number) => {
  if (mb >= 1024) {
    return `${(mb / 1024).toFixed(0)}GB`
  }
  return `${mb}MB`
}

onMounted(() => {
  fetchInventory()
  fetchSuppliers()
  fetchUsers()
  fetchSalePackages()
})
</script>

<style scoped lang="scss">
.stock-out-container {
  padding: 20px;

  .card-header {
    .title {
      font-size: 16px;
      font-weight: 600;
    }
  }

  .steps {
    margin: 30px 0;
  }

  .step-content {
    min-height: 400px;
    padding: 20px 0;
  }

  .select-cards-section {
    .search-form {
      margin-bottom: 20px;
    }

    .pagination {
      margin-top: 20px;
      justify-content: flex-end;
    }
  }

  .confirm-section {
    max-width: 900px;
    margin: 40px auto;

    .card-list-preview {
      margin-top: 30px;

      .list-title {
        font-weight: 600;
        margin-bottom: 10px;
      }
    }
  }

  .step-actions {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-top: 40px;
  }
}
</style>

