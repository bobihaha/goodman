<template>
  <div class="config-panel">
    <!-- 操作栏 -->
    <div class="toolbar">
      <el-button type="primary" :icon="Plus" @click="handleCreate">
        新增配置
      </el-button>
    </div>

    <!-- 配置列表 -->
    <el-table
      v-loading="loading"
      :data="configList"
      stripe
      border
      style="width: 100%"
    >
      <el-table-column prop="config_key" label="配置键" min-width="180" />
      <el-table-column prop="config_value" label="配置值" min-width="200" show-overflow-tooltip />
      <el-table-column prop="config_type" label="类型" width="100">
        <template #default="{ row }">
          <el-tag size="small">{{ row.config_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
      <el-table-column label="公开" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_public ? 'success' : 'info'" size="small">
            {{ row.is_public ? '是' : '否' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="updated_at" label="更新时间" width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.updated_at) }}
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

    <!-- 表单弹窗 -->
    <ConfigFormDialog
      v-model="formDialogVisible"
      :config="currentConfig"
      @success="handleFormSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import { systemApi } from '@/api/modules/system'
import { formatDateTime } from '@/utils/formatter'
import type { SystemConfig } from '@/types/system'
import ConfigFormDialog from './ConfigFormDialog.vue'

const configList = ref<SystemConfig[]>([])
const loading = ref(false)
const formDialogVisible = ref(false)
const currentConfig = ref<SystemConfig | null>(null)

const fetchConfigs = async () => {
  loading.value = true
  try {
    const data = await systemApi.getConfigs()
    configList.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error('获取配置列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  currentConfig.value = null
  formDialogVisible.value = true
}

const handleEdit = (row: SystemConfig) => {
  currentConfig.value = row
  formDialogVisible.value = true
}

const handleDelete = async (row: SystemConfig) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除配置 "${row.config_key}" 吗？`,
      '确认删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await systemApi.deleteConfig(row.config_key)
    ElMessage.success('删除成功')
    fetchConfigs()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除配置失败:', error)
    }
  }
}

const handleFormSuccess = () => {
  formDialogVisible.value = false
  fetchConfigs()
}

onMounted(() => {
  fetchConfigs()
})
</script>

<style scoped lang="scss">
.config-panel {
  .toolbar {
    margin-bottom: 16px;
  }
}
</style>
