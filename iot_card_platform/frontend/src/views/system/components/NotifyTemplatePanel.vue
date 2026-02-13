<template>
  <div class="notify-template-panel">
    <!-- 筛选栏 -->
    <el-form :model="searchForm" inline class="search-form">
      <el-form-item label="类型">
        <el-select
          v-model="searchForm.type"
          placeholder="全部"
          clearable
          style="width: 130px"
          @change="handleSearch"
        >
          <el-option label="短信" value="sms" />
          <el-option label="邮件" value="email" />
          <el-option label="微信" value="wechat" />
          <el-option label="Webhook" value="webhook" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态">
        <el-select
          v-model="searchForm.is_enabled"
          placeholder="全部"
          clearable
          style="width: 120px"
          @change="handleSearch"
        >
          <el-option label="启用" :value="true" />
          <el-option label="禁用" :value="false" />
        </el-select>
      </el-form-item>
      <el-form-item label="关键词">
        <el-input
          v-model="searchForm.keyword"
          placeholder="名称/编码"
          clearable
          style="width: 160px"
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
        <el-button :icon="Refresh" @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 操作栏 -->
    <div class="toolbar">
      <el-button type="primary" :icon="Plus" @click="handleCreate">
        新增模板
      </el-button>
    </div>

    <!-- 模板列表 -->
    <el-table
      v-loading="loading"
      :data="templateList"
      stripe
      border
      style="width: 100%"
    >
      <el-table-column prop="code" label="编码" width="160" />
      <el-table-column prop="name" label="名称" width="180" />
      <el-table-column prop="type_name" label="类型" width="100">
        <template #default="{ row }">
          <el-tag size="small">{{ row.type_name }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
      <el-table-column label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_enabled ? 'success' : 'info'" size="small">
            {{ row.is_enabled ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link :icon="Edit" @click="handleEdit(row)">
            编辑
          </el-button>
          <el-button type="danger" link :icon="Delete" @click="handleDelete(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSearch"
        @current-change="fetchTemplates"
      />
    </div>

    <!-- 表单弹窗 -->
    <NotifyTemplateFormDialog
      v-model="formDialogVisible"
      :template-data="currentTemplate"
      @success="handleFormSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, Edit, Delete } from '@element-plus/icons-vue'
import { systemApi } from '@/api/modules/system'
import { formatDateTime } from '@/utils/formatter'
import type { NotifyTemplate } from '@/types/system'
import NotifyTemplateFormDialog from './NotifyTemplateFormDialog.vue'

const templateList = ref<NotifyTemplate[]>([])
const loading = ref(false)
const formDialogVisible = ref(false)
const currentTemplate = ref<NotifyTemplate | null>(null)

const searchForm = reactive({
  type: '',
  is_enabled: undefined as boolean | undefined,
  keyword: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const fetchTemplates = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.page_size
    }
    if (searchForm.type) params.type = searchForm.type
    if (searchForm.is_enabled !== undefined) params.is_enabled = searchForm.is_enabled
    if (searchForm.keyword) params.keyword = searchForm.keyword

    const res = await systemApi.getNotifyTemplates(params)
    templateList.value = res.items || res.list || []
    pagination.total = res.total || 0
  } catch (error) {
    console.error('获取通知模板失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchTemplates()
}

const handleReset = () => {
  searchForm.type = ''
  searchForm.is_enabled = undefined
  searchForm.keyword = ''
  handleSearch()
}

const handleCreate = () => {
  currentTemplate.value = null
  formDialogVisible.value = true
}

const handleEdit = (row: NotifyTemplate) => {
  currentTemplate.value = row
  formDialogVisible.value = true
}

const handleDelete = async (row: NotifyTemplate) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模板 "${row.name}" 吗？`,
      '确认删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await systemApi.deleteNotifyTemplate(row.id)
    ElMessage.success('删除成功')
    fetchTemplates()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除模板失败:', error)
    }
  }
}

const handleFormSuccess = () => {
  formDialogVisible.value = false
  fetchTemplates()
}

onMounted(() => {
  fetchTemplates()
})
</script>

<style scoped lang="scss">
.notify-template-panel {
  .search-form {
    margin-bottom: 16px;
  }

  .toolbar {
    margin-bottom: 16px;
  }

  .pagination-container {
    margin-top: 16px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
