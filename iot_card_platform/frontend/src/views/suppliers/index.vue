<template>
  <div class="supplier-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>供应商管理</h2>
      <p class="page-desc">管理物联网卡供应商信息，配置API对接参数</p>
    </div>

    <!-- 搜索和操作栏 -->
    <el-card class="search-card" shadow="never">
      <el-form :model="searchForm" inline>
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="供应商名称/编码"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="供应商类型">
          <el-select
            v-model="searchForm.type"
            placeholder="全部类型"
            clearable
            style="width: 140px"
          >
            <el-option
              v-for="item in SUPPLIER_TYPE_OPTIONS"
              :key="item.value"
              :label="item.label"
              :value="item.value"
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
              v-for="item in SUPPLIER_STATUS_OPTIONS"
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
          新增供应商
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
        <el-table-column prop="code" label="供应商编码" width="150" fixed />
        <el-table-column prop="name" label="供应商名称" width="180" />
        <el-table-column label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.type)">
              {{ getSupplierTypeLabel(row.type as SupplierType) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="contact_name" label="联系人" width="100" />
        <el-table-column prop="contact_phone" label="联系电话" width="130" />
        <el-table-column prop="contact_email" label="联系邮箱" width="180" show-overflow-tooltip />
        <el-table-column label="API配置" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.api_url" type="success" size="small">已配置</el-tag>
            <el-tag v-else type="info" size="small">未配置</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getSupplierStatusMeta(row.status).type">
              {{ getSupplierStatusMeta(row.status).label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="150" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="110">
          <template #default="{ row }">
            {{ formatDateShort(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button
              v-if="row.api_url"
              link
              type="success"
              size="small"
              @click="handleTestApi(row)"
            >
              测试API
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

    <!-- 供应商表单弹窗 -->
    <SupplierFormDialog
      v-model="dialogVisible"
      :supplier-data="currentSupplier"
      @success="handleFormSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus } from '@element-plus/icons-vue'
import supplierApi from '@/api/modules/supplier'
import type { Supplier, SupplierQueryParams, SupplierType, SupplierStatus } from '@/types/supplier'
import { formatDateShort } from '@/utils/formatter'
import {
  SUPPLIER_TYPE_OPTIONS,
  SUPPLIER_TYPE_MAP,
  SUPPLIER_STATUS_OPTIONS,
  SUPPLIER_STATUS_MAP
} from '@/constants/supplier'
import SupplierFormDialog from './components/SupplierFormDialog.vue'

// 搜索表单
type SupplierSearchForm = Omit<SupplierQueryParams, 'page' | 'page_size'>

const searchForm = reactive<SupplierSearchForm>({
  keyword: '',
  type: undefined,
  status: undefined
})

// 表格数据
const loading = ref(false)
const tableData = ref<Supplier[]>([])

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 弹窗控制
const dialogVisible = ref(false)
const currentSupplier = ref<Supplier | null>(null)

// 获取类型标签类型
const getTypeTagType = (type: string) => {
  const typeMap: Record<string, string> = {
    cmcc: '',
    cucc: 'success',
    ctcc: 'warning',
    mvno: 'info',
    other: 'info'
  }
  return typeMap[type] || ''
}

const getSupplierTypeLabel = (type: SupplierType) => SUPPLIER_TYPE_MAP[type] || type
const getSupplierStatusMeta = (status: SupplierStatus) => SUPPLIER_STATUS_MAP[status] || { label: status, type: 'info' }

// 获取供应商列表
const fetchList = async () => {
  loading.value = true
  try {
    const params: SupplierQueryParams = {
      ...searchForm,
      page: pagination.page,
      page_size: pagination.page_size
    }

    if (!params.keyword) delete params.keyword
    if (!params.type) delete params.type
    if (!params.status) delete params.status
    
    const response = await supplierApi.getSupplierList(params)
    tableData.value = response.list || []
    pagination.total = response.total || 0
  } catch (error) {
    console.error('获取供应商列表失败:', error)
    ElMessage.error('获取供应商列表失败')
  } finally {
    loading.value = false
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
    type: undefined,
    status: undefined
  })
  pagination.page = 1
  fetchList()
}

// 新增
const handleCreate = () => {
  currentSupplier.value = null
  dialogVisible.value = true
}

// 编辑
const handleEdit = (row: Supplier) => {
  currentSupplier.value = { ...row }
  dialogVisible.value = true
}

// 测试API
const handleTestApi = async (row: Supplier) => {
  try {
    ElMessage.info('正在测试API连接...')
    const result = await supplierApi.testApiConnection(row.id)
    
    if (result.success) {
      ElMessage.success(`API连接成功！响应时间: ${result.response_time}ms`)
    } else {
      ElMessage.error(`API连接失败: ${result.message}`)
    }
  } catch (error) {
    console.error('测试API失败:', error)
    ElMessage.error('测试API失败')
  }
}

// 切换状态
const handleToggleStatus = async (row: Supplier) => {
  const newStatus = row.status === 'enable' ? 'disable' : 'enable'
  const action = newStatus === 'enable' ? '启用' : '禁用'
  
  try {
    await ElMessageBox.confirm(
      `确定要${action}供应商"${row.name}"吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await supplierApi.updateSupplier(row.id, { status: newStatus })
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
const handleDelete = async (row: Supplier) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除供应商"${row.name}"吗？删除后不可恢复！`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await supplierApi.deleteSupplier(row.id)
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
  fetchList()
})
</script>

<style scoped lang="scss">
.supplier-page {
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



