<template>
  <div class="sale-package-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>销售套餐管理</h2>
      <p class="page-desc">管理面向客户的销售套餐，关联底层套餐并设置销售价格</p>
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

        <el-form-item label="底层套餐">
          <el-select
            v-model="searchForm.base_package_id"
            placeholder="全部套餐"
            clearable
            filterable
            style="width: 200px"
          >
            <el-option
              v-for="item in supplierPackageList"
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
          新增销售套餐
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
        <el-table-column prop="name" label="销售套餐名称" width="200" />
        <el-table-column label="底层套餐" width="200">
          <template #default="{ row }">
            <div v-if="row.base_package_name">
              {{ row.base_package_name }}
            </div>
            <div v-else class="text-muted">-</div>
          </template>
        </el-table-column>
        <el-table-column label="运营商" width="100">
          <template #default="{ row }">
            <el-tag :type="getCarrierType(row.carrier)">
              {{ CARRIER_MAP[row.carrier] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="流量规格" width="120">
          <template #default="{ row }">
            {{ formatFlowSize(row.flow_size) }}
          </template>
        </el-table-column>
        <el-table-column label="周期类型" width="100">
          <template #default="{ row }">
            {{ PERIOD_TYPE_MAP[row.period_type] }}
          </template>
        </el-table-column>
        <el-table-column label="成本价" width="100">
          <template #default="{ row }">
            <span class="text-muted">
              {{ formatMoney(row.price_cost) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="price_sale" label="销售价" width="100">
          <template #default="{ row }">
            <span class="text-primary">{{ formatMoney(row.price_sale) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="利润率" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.profit_margin !== undefined" :type="getProfitType(row.profit_margin)">
              {{ formatPercent(row.profit_margin) }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="STATUS_MAP[row.status].type">
              {{ STATUS_MAP[row.status].label }}
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

    <!-- 销售套餐表单弹窗 -->
    <SalePackageFormDialog
      v-model="dialogVisible"
      :package-data="currentPackage"
      :supplier-package-list="supplierPackageList"
      @success="handleFormSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus } from '@element-plus/icons-vue'
import { salePackageApi, supplierPackageApi } from '@/api/modules/package'
import type { SalePackage, SupplierPackage } from '@/types/package'
import { formatFlowSize, formatMoney, formatDateShort, formatPercent } from '@/utils/formatter'
import {
  CARRIER_MAP,
  PERIOD_TYPE_MAP,
  STATUS_OPTIONS,
  STATUS_MAP
} from '@/constants/package'
import SalePackageFormDialog from './components/SalePackageFormDialog.vue'

// 搜索表单
const searchForm = reactive({
  keyword: '',
  base_package_id: undefined as number | undefined,
  status: ''
})

// 表格数据
const loading = ref(false)
const tableData = ref<SalePackage[]>([])

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 底层套餐列表
const supplierPackageList = ref<SupplierPackage[]>([])

// 弹窗控制
const dialogVisible = ref(false)
const currentPackage = ref<SalePackage | null>(null)

// 获取运营商标签类型
const getCarrierType = (carrier: string) => {
  const typeMap: Record<string, string> = {
    cmcc: '',
    cucc: 'success',
    ctcc: 'warning'
  }
  return typeMap[carrier] || ''
}

// 获取利润率标签类型
const getProfitType = (profit: number) => {
  if (profit < 0) return 'danger'
  if (profit < 10) return 'warning'
  if (profit < 30) return ''
  return 'success'
}

// 获取销售套餐列表
const fetchList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      ...searchForm
    }
    
    // 过滤空值
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === undefined) {
        delete params[key]
      }
    })
    
    console.log('正在请求销售套餐列表，参数:', params)
    const response = await salePackageApi.getList(params)
    console.log('销售套餐列表响应:', response)
    
    tableData.value = response.list || []
    pagination.total = response.total || 0
    
    if (tableData.value.length === 0) {
      console.log('数据库中暂无销售套餐数据，请先创建销售套餐')
    }
  } catch (error) {
    console.error('获取销售套餐列表失败:', error)
    ElMessage.error('获取销售套餐列表失败，请查看控制台了解详情')
  } finally {
    loading.value = false
  }
}

// 获取底层套餐列表
const fetchSupplierPackages = async () => {
  try {
    console.log('正在请求底层套餐列表...')
    supplierPackageList.value = await supplierPackageApi.getEnabled()
    console.log('底层套餐列表响应:', supplierPackageList.value)
    
    if (supplierPackageList.value.length === 0) {
      console.warn('数据库中暂无底层套餐数据，请先在底层套餐管理中创建套餐')
      ElMessage.warning('暂无底层套餐数据，请先创建底层套餐后再创建销售套餐')
    }
  } catch (error) {
    console.error('获取底层套餐列表失败:', error)
    ElMessage.error('获取底层套餐列表失败，请查看控制台了解详情')
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
    base_package_id: undefined,
    status: ''
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
const handleEdit = (row: SalePackage) => {
  currentPackage.value = { ...row }
  dialogVisible.value = true
}

// 切换状态
const handleToggleStatus = async (row: SalePackage) => {
  const newStatus = row.status === 'enable' ? 'disable' : 'enable'
  const action = newStatus === 'enable' ? '启用' : '禁用'
  
  try {
    await ElMessageBox.confirm(
      `确定要${action}销售套餐"${row.name}"吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await salePackageApi.updateStatus(row.id, newStatus)
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
const handleDelete = async (row: SalePackage) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除销售套餐"${row.name}"吗？删除后不可恢复！`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await salePackageApi.delete(row.id)
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
  fetchSupplierPackages()
  fetchList()
})
</script>

<style scoped lang="scss">
.sale-package-page {
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

  .text-muted {
    color: #909399;
  }

  .text-primary {
    color: #409eff;
    font-weight: 600;
  }
}
</style>

