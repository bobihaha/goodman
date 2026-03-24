<template>
  <div class="supplier-package-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>底层套餐管理</h2>
      <p class="page-desc">管理供应商提供的底层套餐，支持自动组流量池功能</p>
    </div>

    <!-- 搜索和操作栏 -->
    <el-card class="search-card" shadow="never">
      <el-form :model="searchForm" inline>
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="套餐名称/套餐ID"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="运营商">
          <el-select
            v-model="searchForm.carrier"
            placeholder="全部运营商"
            clearable
            style="width: 140px"
          >
            <el-option
              v-for="item in CARRIER_OPTIONS"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="周期类型">
          <el-select
            v-model="searchForm.period_type"
            placeholder="全部周期"
            clearable
            style="width: 120px"
          >
            <el-option
              v-for="item in PERIOD_TYPE_OPTIONS"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="供应商">
          <el-select
            v-model="searchForm.supplier_id"
            placeholder="全部供应商"
            clearable
            filterable
            style="width: 160px"
          >
            <el-option
              v-for="item in supplierList"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="状态">
          <el-select
            v-model="searchForm.status"
            placeholder="全部状态"
            clearable
            style="width: 120px"
          >
            <el-option
              v-for="item in STATUS_OPTIONS"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>

      <div class="toolbar">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新增套餐
        </el-button>
      </div>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card" shadow="never">
      <el-table
        v-loading="loading"
        :data="tableData"
        stripe
        border
        style="width: 100%"
      >
        <el-table-column prop="code" label="套餐编码" width="150" fixed />
        <el-table-column prop="name" label="套餐名称" width="180" />
        <el-table-column prop="carrier" label="运营商" width="100">
          <template #default="{ row }">
            <el-tag :type="getCarrierType(row.carrier)">
              {{ getCarrierLabel(row.carrier as Carrier) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="flow_size" label="流量规格" width="120">
          <template #default="{ row }">
            {{ formatFlowSize(row.flow_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="period_type" label="周期类型" width="100">
          <template #default="{ row }">
            {{ getPeriodTypeLabel(row.period_type as PeriodType) }}
          </template>
        </el-table-column>
        <el-table-column prop="effective_days" label="有效天数" width="100">
          <template #default="{ row }">
            {{ row.effective_days }}天
          </template>
        </el-table-column>
        <el-table-column prop="price_cost" label="成本价" width="100">
          <template #default="{ row }">
            {{ formatMoney(row.price_cost) }}
          </template>
        </el-table-column>
        <el-table-column prop="supplier_name" label="供应商" width="150" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusMeta(row.status).type">
              {{ getStatusMeta(row.status).label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="150" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="110">
          <template #default="{ row }">
            {{ formatDateShort(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button
              link
              :type="row.status === 'enable' ? 'warning' : 'success'"
              size="small"
              @click="handleToggleStatus(row)"
            >
              {{ row.status === 'enable' ? '禁用' : '启用' }}
            </el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 套餐表单弹窗 -->
    <PackageFormDialog
      v-model="dialogVisible"
      :package-data="currentPackage"
      :supplier-list="supplierList"
      @success="handleFormSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus } from '@element-plus/icons-vue'
import { supplierPackageApi, supplierApi } from '@/api/modules/package'
import type { SupplierPackage, Supplier, SupplierPackageListParams } from '@/types/package'
import type { Carrier, PeriodType } from '@/types/common'
import { formatFlowSize, formatMoney, formatDateShort } from '@/utils/formatter'
import {
  CARRIER_OPTIONS,
  CARRIER_MAP,
  PERIOD_TYPE_OPTIONS,
  PERIOD_TYPE_MAP,
  STATUS_OPTIONS,
  STATUS_MAP
} from '@/constants/package'
import PackageFormDialog from './components/PackageFormDialog.vue'

type SupplierPackageSearchForm = Omit<SupplierPackageListParams, 'page' | 'page_size'>

// 搜索表单
const searchForm = reactive<SupplierPackageSearchForm>({
  keyword: '',
  carrier: undefined,
  period_type: undefined,
  supplier_id: undefined as number | undefined,
  status: undefined
})

// 表格数据
const loading = ref(false)
const tableData = ref<SupplierPackage[]>([])

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 供应商列表
const supplierList = ref<Supplier[]>([])

// 弹窗控制
const dialogVisible = ref(false)
const currentPackage = ref<SupplierPackage | null>(null)

// 获取运营商标签类型
const getCarrierType = (carrier: string) => {
  const typeMap: Record<string, string> = {
    cmcc: '',
    cucc: 'success',
    ctcc: 'warning'
  }
  return typeMap[carrier] || ''
}

const getCarrierLabel = (carrier: Carrier) => CARRIER_MAP[carrier] || carrier
const getPeriodTypeLabel = (periodType: PeriodType) => PERIOD_TYPE_MAP[periodType] || periodType
const getStatusMeta = (status: 'enable' | 'disable') => STATUS_MAP[status]

// 获取套餐列表
const fetchList = async () => {
  loading.value = true
  try {
    const params: SupplierPackageListParams = {
      ...searchForm,
      page: pagination.page,
      page_size: pagination.page_size
    }

    if (!params.keyword) delete params.keyword
    if (!params.carrier) delete params.carrier
    if (!params.period_type) delete params.period_type
    if (!params.supplier_id) delete params.supplier_id
    if (!params.status) delete params.status
    
    console.log('正在请求套餐列表，参数:', params)
    const response = await supplierPackageApi.getList(params)
    console.log('套餐列表响应:', response)
    
    tableData.value = response.list || []
    pagination.total = response.total || 0
    
    if (tableData.value.length === 0) {
      console.log('数据库中暂无套餐数据，请先创建套餐')
    }
  } catch (error) {
    console.error('获取套餐列表失败:', error)
    ElMessage.error('获取套餐列表失败，请查看控制台了解详情')
  } finally {
    loading.value = false
  }
}

// 获取供应商列表
const fetchSuppliers = async () => {
  try {
    console.log('正在请求供应商列表...')
    supplierList.value = await supplierApi.getEnabled()
    console.log('供应商列表响应:', supplierList.value)
    
    if (supplierList.value.length === 0) {
      console.warn('数据库中暂无供应商数据，请先在供应商管理中创建供应商')
      ElMessage.warning('暂无供应商数据，请先创建供应商后再创建套餐')
    }
  } catch (error) {
    console.error('获取供应商列表失败:', error)
    ElMessage.error('获取供应商列表失败，请查看控制台了解详情')
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchList()
}

// 重置
const handleReset = () => {
  Object.assign(searchForm, {
    keyword: '',
    carrier: undefined,
    period_type: undefined,
    supplier_id: undefined,
    status: undefined
  })
  pagination.page = 1
  fetchList()
}

// 新增
const handleCreate = () => {
  currentPackage.value = null
  dialogVisible.value = true
}

// 编辑
const handleEdit = (row: SupplierPackage) => {
  currentPackage.value = { ...row }
  dialogVisible.value = true
}

// 切换状态
const handleToggleStatus = async (row: SupplierPackage) => {
  const newStatus = row.status === 'enable' ? 'disable' : 'enable'
  const action = newStatus === 'enable' ? '启用' : '禁用'
  
  try {
    await ElMessageBox.confirm(
      `确定要${action}套餐"${row.name}"吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await supplierPackageApi.updateStatus(row.id, newStatus)
    ElMessage.success(`${action}成功`)
    fetchList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('切换状态失败:', error)
      ElMessage.error(`${action}失败`)
    }
  }
}

// 删除
const handleDelete = async (row: SupplierPackage) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除套餐"${row.name}"吗？删除后不可恢复！`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await supplierPackageApi.delete(row.id)
    ElMessage.success('删除成功')
    
    // 如果当前页没有数据了，返回上一页
    if (tableData.value.length === 1 && pagination.page > 1) {
      pagination.page--
    }
    
    fetchList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 表单提交成功
const handleFormSuccess = () => {
  fetchList()
}

// 分页大小改变
const handleSizeChange = () => {
  pagination.page = 1
  fetchList()
}

// 页码改变
const handlePageChange = () => {
  fetchList()
}

// 初始化
onMounted(() => {
  fetchSuppliers()
  fetchList()
})
</script>

<style scoped lang="scss">
.supplier-package-page {
  padding: 20px;

  .page-header {
    margin-bottom: 20px;

    h2 {
      margin: 0 0 8px 0;
      font-size: 24px;
      font-weight: 600;
      color: #303133;
    }

    .page-desc {
      margin: 0;
      font-size: 14px;
      color: #909399;
    }
  }

  .search-card {
    margin-bottom: 16px;

    :deep(.el-card__body) {
      padding: 20px;
    }

    .el-form {
      margin-bottom: 0;
    }

    .toolbar {
      margin-top: 16px;
      padding-top: 16px;
      border-top: 1px solid #ebeef5;
    }
  }

  .table-card {
    :deep(.el-card__body) {
      padding: 20px;
    }

    .pagination-wrapper {
      margin-top: 16px;
      display: flex;
      justify-content: flex-end;
    }
  }
}
</style>
