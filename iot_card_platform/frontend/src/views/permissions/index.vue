<template>
  <div class="permissions-container">
    <el-card shadow="never" class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="模块">
          <el-select v-model="searchForm.module" placeholder="全部模块" clearable style="width: 180px">
            <el-option label="全部模块" value="" />
            <el-option v-for="mod in moduleOptions" :key="mod.value" :label="mod.label" :value="mod.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="权限名称/代码" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button type="success" @click="handleCreate">新建权限</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" class="table-card">
      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="code" label="权限代码" min-width="180" />
        <el-table-column prop="name" label="权限名称" min-width="150" />
        <el-table-column prop="module_name" label="所属模块" width="120" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
        class="pagination"
      />
    </el-card>

    <!-- 权限表单对话框 -->
    <PermissionFormDialog
      v-model="dialogVisible"
      :permission="currentPermission"
      @success="handleFormSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPermissionList, deletePermission } from '@/api/modules/permission'
import type { Permission, PermissionListParams } from '@/types/permission'
import PermissionFormDialog from './components/PermissionFormDialog.vue'

// 模块选项
const moduleOptions = [
  { label: '卡片管理', value: 'card' },
  { label: '流量池管理', value: 'pool' },
  { label: '用户管理', value: 'user' },
  { label: '套餐管理', value: 'package' },
  { label: '库存管理', value: 'stock' },
  { label: '供应商管理', value: 'supplier' },
  { label: '停复机管理', value: 'suspend' },
  { label: '系统管理', value: 'system' },
  { label: '数据看板', value: 'dashboard' }
]

// 搜索表单
const searchForm = reactive<PermissionListParams>({
  module: '',
  keyword: ''
})

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 表格数据
const tableData = ref<Permission[]>([])
const loading = ref(false)

// 对话框
const dialogVisible = ref(false)
const currentPermission = ref<Permission | null>(null)

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const params: PermissionListParams = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...searchForm
    }
    const res = await getPermissionList(params)
    tableData.value = res.items
    pagination.total = res.total
  } catch (error) {
    ElMessage.error('加载权限列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadData()
}

// 重置
const handleReset = () => {
  searchForm.module = ''
  searchForm.keyword = ''
  pagination.page = 1
  loadData()
}

// 新建
const handleCreate = () => {
  currentPermission.value = null
  dialogVisible.value = true
}

// 编辑
const handleEdit = (row: Permission) => {
  currentPermission.value = { ...row }
  dialogVisible.value = true
}

// 删除
const handleDelete = async (row: Permission) => {
  try {
    await ElMessageBox.confirm(`确定要删除权限"${row.name}"吗？`, '提示', {
      type: 'warning'
    })
    await deletePermission(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

// 表单提交成功
const handleFormSuccess = () => {
  loadData()
}

// 分页变化
const handlePageChange = () => {
  loadData()
}

const handleSizeChange = () => {
  pagination.page = 1
  loadData()
}

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.permissions-container {
  padding: 20px;

  .search-card {
    margin-bottom: 20px;
  }

  .search-form {
    margin-bottom: 0;
  }

  .table-card {
    .pagination {
      margin-top: 20px;
      justify-content: flex-end;
    }
  }
}
</style>


