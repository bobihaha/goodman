<template>
  <div class="batches-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span class="title">采购批次管理</span>
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            创建批次
          </el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="queryParams" class="search-form">
        <el-form-item label="供应商">
          <el-select v-model="queryParams.supplier_id" placeholder="请选择供应商" clearable style="width: 200px">
            <el-option
              v-for="supplier in suppliers"
              :key="supplier.id"
              :label="supplier.name"
              :value="supplier.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryParams.status" placeholder="请选择状态" clearable style="width: 150px">
            <el-option label="待入库" value="pending" />
            <el-option label="已入库" value="stocked" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="batch_no" label="批次号" width="180" />
        <el-table-column prop="supplier_name" label="供应商" width="150" />
        <el-table-column prop="package_name" label="底层套餐" width="150" />
        <el-table-column label="规格" width="200">
          <template #default="{ row }">
            {{ row.carrier_name }} / {{ formatFlow(row.flow_size) }} / {{ row.period_name }}
          </template>
        </el-table-column>
        <el-table-column prop="card_count" label="卡片总数" width="100" align="center" />
        <el-table-column prop="stocked_count" label="已入库" width="100" align="center" />
        <el-table-column prop="out_count" label="已出库" width="100" align="center" />
        <el-table-column prop="stock_remain" label="库存" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.stock_remain > 0 ? 'success' : 'info'">
              {{ row.stock_remain }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="生命周期" width="200">
          <template #default="{ row }">
            <div class="lifecycle-info">
              <div v-if="row.test_expire_date">测试期: {{ row.test_expire_date }}</div>
              <div>沉默期: {{ row.silent_expire_date }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="purchase_date" label="采购日期" width="120" />
        <el-table-column prop="status_name" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ row.status_name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleView(row)">详情</el-button>
            <el-button link type="primary" size="small" @click="handleStockIn(row)" v-if="row.status === 'pending'">
              入库
            </el-button>
          </template>
        </el-table-column>
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
    </el-card>

    <!-- 创建批次对话框 -->
    <el-dialog v-model="dialogVisible" title="创建采购批次" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="供应商" prop="supplier_id">
          <el-select v-model="form.supplier_id" placeholder="请选择供应商" style="width: 100%">
            <el-option
              v-for="supplier in suppliers"
              :key="supplier.id"
              :label="supplier.name"
              :value="supplier.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="底层套餐" prop="package_id">
          <el-select v-model="form.package_id" placeholder="请选择底层套餐" style="width: 100%">
            <el-option
              v-for="pkg in packages"
              :key="pkg.id"
              :label="`${pkg.name} (${pkg.carrier_name}/${formatFlow(pkg.flow_size)}/${pkg.period_name})`"
              :value="pkg.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="测试期到期日">
          <el-date-picker
            v-model="form.test_expire_date"
            type="date"
            placeholder="选择测试期到期日"
            style="width: 100%"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="沉默期到期日" prop="silent_expire_date">
          <el-date-picker
            v-model="form.silent_expire_date"
            type="date"
            placeholder="选择沉默期到期日"
            style="width: 100%"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="采购日期" prop="purchase_date">
          <el-date-picker
            v-model="form.purchase_date"
            type="date"
            placeholder="选择采购日期"
            style="width: 100%"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="3" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { stockApi } from '@/api/modules/stock'
import { supplierApi } from '@/api/modules/supplier'
import { packageApi } from '@/api/modules/package'
import { useRouter } from 'vue-router'

const router = useRouter()

// 查询参数
const queryParams = reactive({
  supplier_id: undefined,
  status: undefined,
  page: 1,
  page_size: 20
})

// 表格数据
const tableData = ref([])
const total = ref(0)
const loading = ref(false)

// 供应商和套餐列表
const suppliers = ref([])
const packages = ref([])

// 对话框
const dialogVisible = ref(false)
const formRef = ref()
const submitting = ref(false)

// 表单数据
const form = reactive({
  supplier_id: undefined,
  package_id: undefined,
  test_expire_date: '',
  silent_expire_date: '',
  purchase_date: '',
  remark: ''
})

// 表单验证规则
const rules = {
  supplier_id: [{ required: true, message: '请选择供应商', trigger: 'change' }],
  package_id: [{ required: true, message: '请选择底层套餐', trigger: 'change' }],
  silent_expire_date: [{ required: true, message: '请选择沉默期到期日', trigger: 'change' }],
  purchase_date: [{ required: true, message: '请选择采购日期', trigger: 'change' }]
}

// 获取批次列表
const fetchBatches = async () => {
  loading.value = true
  try {
    const res = await stockApi.getBatches(queryParams)
    tableData.value = res.items || []  // 批次API返回 items
    total.value = res.total || 0
  } catch (error) {
    ElMessage.error('获取批次列表失败')
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

// 获取底层套餐列表
const fetchPackages = async () => {
  try {
    const res = await packageApi.getSupplierPackages({ page: 1, page_size: 100 })
    packages.value = res.items || []  // 套餐API返回 items
  } catch (error) {
    console.error('获取套餐列表失败', error)
  }
}

// 查询
const handleQuery = () => {
  queryParams.page = 1
  fetchBatches()
}

// 重置
const handleReset = () => {
  queryParams.supplier_id = undefined
  queryParams.status = undefined
  queryParams.page = 1
  fetchBatches()
}

// 创建批次
const handleCreate = () => {
  dialogVisible.value = true
  Object.assign(form, {
    supplier_id: undefined,
    package_id: undefined,
    test_expire_date: '',
    silent_expire_date: '',
    purchase_date: new Date().toISOString().split('T')[0],
    remark: ''
  })
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid: boolean) => {
    if (valid) {
      submitting.value = true
      try {
        await stockApi.createBatch(form)
        ElMessage.success('批次创建成功')
        dialogVisible.value = false
        fetchBatches()
      } catch (error) {
        ElMessage.error('批次创建失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

// 查看详情
const handleView = (row: any) => {
  ElMessage.info('批次详情功能开发中')
}

// 入库
const handleStockIn = (row: any) => {
  router.push({ path: '/stock/in', query: { batch_id: row.id } })
}

// 格式化流量
const formatFlow = (mb: number) => {
  if (mb >= 1024) {
    return `${(mb / 1024).toFixed(0)}GB`
  }
  return `${mb}MB`
}

// 获取状态类型
const getStatusType = (status: string) => {
  const map: Record<string, any> = {
    pending: 'warning',
    stocked: 'success',
    completed: 'info'
  }
  return map[status] || 'info'
}

onMounted(() => {
  fetchBatches()
  fetchSuppliers()
  fetchPackages()
})
</script>

<style scoped lang="scss">
.batches-container {
  padding: 20px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .title {
      font-size: 16px;
      font-weight: 600;
    }
  }

  .search-form {
    margin-bottom: 20px;
  }

  .lifecycle-info {
    font-size: 12px;
    line-height: 1.6;
  }

  .pagination {
    margin-top: 20px;
    justify-content: flex-end;
  }
}
</style>

