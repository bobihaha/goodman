<template>
  <div class="projects-container">
    <!-- 搜索栏 -->
    <el-card class="search-card" shadow="never">
      <el-form :model="searchForm" inline>
        <el-form-item label="项目名称">
          <el-input
            v-model="searchForm.keyword"
            placeholder="请输入项目名称"
            clearable
            style="width: 200px"
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">
            搜索
          </el-button>
          <el-button :icon="Refresh" @click="handleReset">
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作栏 -->
    <el-card class="toolbar-card" shadow="never">
      <el-button type="primary" :icon="Plus" @click="handleCreate">
        新增项目
      </el-button>
    </el-card>

    <!-- 项目列表 -->
    <el-card class="table-card" shadow="never">
      <el-table
        v-loading="loading"
        :data="projectList"
        stripe
        border
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="项目名称" min-width="150" />
        <el-table-column prop="card_count" label="卡片数量" width="120" />
        <el-table-column prop="remark" label="备注" min-width="200" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              :icon="Edit"
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-button
              type="danger"
              link
              :icon="Delete"
              @click="handleDelete(row)"
            >
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
          @current-change="handleSearch"
        />
      </div>
    </el-card>

    <!-- 项目表单弹窗 -->
    <ProjectFormDialog
      v-model="formDialogVisible"
      :project="currentProject"
      @success="handleFormSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, Edit, Delete } from '@element-plus/icons-vue'
import { projectApi } from '@/api/modules/project'
import { formatDateTime } from '@/utils/formatter'
import type { Project, ProjectListParams } from '@/types/project'
import ProjectFormDialog from './components/ProjectFormDialog.vue'

const searchForm = reactive<ProjectListParams>({
  keyword: ''
})

const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

const projectList = ref<Project[]>([])
const loading = ref(false)
const formDialogVisible = ref(false)
const currentProject = ref<Project | null>(null)

const fetchProjectList = async () => {
  loading.value = true
  try {
    const params: ProjectListParams = {
      page: pagination.page,
      page_size: pagination.page_size,
      ...searchForm
    }

    const response = await projectApi.getList(params)
    projectList.value = response.list || []
    pagination.total = response.total || 0
  } catch (error) {
    console.error('获取项目列表失败:', error)
    ElMessage.error('获取项目列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchProjectList()
}

const handleReset = () => {
  searchForm.keyword = ''
  handleSearch()
}

const handleCreate = () => {
  currentProject.value = null
  formDialogVisible.value = true
}

const handleEdit = (project: Project) => {
  currentProject.value = project
  formDialogVisible.value = true
}

const handleDelete = async (project: Project) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除项目 "${project.name}" 吗？该项目下的卡片将不再关联此项目。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'error'
      }
    )

    await projectApi.delete(project.id)
    ElMessage.success('删除成功')
    fetchProjectList()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除项目失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const handleFormSuccess = () => {
  formDialogVisible.value = false
  fetchProjectList()
}

onMounted(() => {
  fetchProjectList()
})
</script>

<style scoped lang="scss">
.projects-container {
  padding: 20px;

  .search-card,
  .toolbar-card,
  .table-card {
    margin-bottom: 20px;
  }

  .pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
