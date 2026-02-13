<template>
  <div class="users-container">
    <!-- 搜索栏 -->
    <el-card class="search-card" shadow="never">
      <el-form :model="searchForm" inline>
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="账号/姓名/手机号"
            clearable
            style="width: 200px"
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="searchForm.status"
            placeholder="全部"
            clearable
            style="width: 120px"
            @change="handleSearch"
          >
            <el-option label="启用" value="enable" />
            <el-option label="禁用" value="disable" />
          </el-select>
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
        新增用户
      </el-button>
    </el-card>

    <!-- 用户列表 -->
    <el-card class="table-card" shadow="never">
      <el-table
        v-loading="loading"
        :data="userList"
        stripe
        border
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="account" label="账号" width="150" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column label="配额" width="150">
          <template #default="{ row }">
            <div v-if="row.quota">
              <div>卡片: {{ row.quota.max_cards }}</div>
              <div>子用户: {{ row.quota.max_sub_users }}</div>
            </div>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'enable' ? 'success' : 'danger'">
              {{ row.status === 'enable' ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="420" fixed="right">
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
              v-if="canAssignPermission()"
              type="primary"
              link
              :icon="Setting"
              @click="handleAssignPermission(row)"
            >
              分配权限
            </el-button>
            <el-button
              v-if="canSuperLogin(row)"
              type="success"
              link
              :icon="SwitchButton"
              @click="handleSuperLogin(row)"
            >
              超级登录
            </el-button>
            <el-button
              type="warning"
              link
              :icon="Key"
              @click="handleResetPassword(row)"
            >
              重置密码
            </el-button>
            <el-button
              v-if="row.status === 'enable'"
              type="warning"
              link
              :icon="Lock"
              @click="handleToggleStatus(row)"
            >
              禁用
            </el-button>
            <el-button
              v-else
              type="success"
              link
              :icon="Unlock"
              @click="handleToggleStatus(row)"
            >
              启用
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

    <!-- 用户表单弹窗 -->
    <UserFormDialog
      v-model="formDialogVisible"
      :user="currentUser"
      @success="handleFormSuccess"
    />

    <!-- 重置密码弹窗 -->
    <ResetPasswordDialog
      v-model="passwordDialogVisible"
      :user="currentUser"
      @success="handlePasswordSuccess"
    />

    <!-- 权限分配弹窗 -->
    <UserPermissionDialog
      v-model="permissionDialogVisible"
      :user-id="currentUser?.id || null"
      :user-name="currentUser?.name || ''"
      @success="handlePermissionSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, Edit, Delete, Key, Lock, Unlock, SwitchButton, Setting } from '@element-plus/icons-vue'
import { userApi } from '@/api/modules/user'
import { formatDateTime } from '@/utils/formatter'
import type { User, UserListParams } from '@/types/user'
import UserFormDialog from './components/UserFormDialog.vue'
import ResetPasswordDialog from './components/ResetPasswordDialog.vue'
import UserPermissionDialog from './components/UserPermissionDialog.vue'
import { useAuthStore } from '@/stores/modules/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

// 搜索表单
const searchForm = reactive<UserListParams>({
  keyword: '',
  status: undefined
})

// 分页
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

// 用户列表
const userList = ref<User[]>([])
const loading = ref(false)

// 弹窗控制
const formDialogVisible = ref(false)
const passwordDialogVisible = ref(false)
const permissionDialogVisible = ref(false)
const currentUser = ref<User | null>(null)

/**
 * 获取用户列表
 */
const fetchUserList = async () => {
  loading.value = true
  try {
    const params: UserListParams = {
      page: pagination.page,
      page_size: pagination.page_size,
      ...searchForm
    }
    
    const response = await userApi.getList(params)
    userList.value = response.list || []
    pagination.total = response.total || 0
  } catch (error) {
    console.error('获取用户列表失败:', error)
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 检查是否可以分配权限
 * 只有超级管理员可以分配权限
 */
const canAssignPermission = (): boolean => {
  const currentUser = authStore.userInfo
  if (!currentUser) {
    return false
  }
  
  // 只有超级管理员（user_level = 1）可以分配权限
  return currentUser.user_level === 1
}

/**
 * 检查是否可以超级登录
 */
const canSuperLogin = (user: User): boolean => {
  const currentUser = authStore.userInfo
  if (!currentUser) {
    console.log('当前用户信息未加载')
    return false
  }
  
  console.log('当前用户:', currentUser.name, 'user_level:', currentUser.user_level)
  console.log('目标用户:', user.name, 'user_level:', user.user_level, 'parent_id:', user.parent_id)
  
  // 超级管理员可以登录到普通用户 (user_level = 2)
  if (currentUser.user_level === 1 && user.user_level === 2) {
    console.log('✅ 超级管理员可以登录到普通用户')
    return true
  }
  
  // 普通用户可以登录到自己的子用户 (user_level = 3)
  if (currentUser.user_level === 2 && user.user_level === 3 && user.parent_id === currentUser.id) {
    console.log('✅ 普通用户可以登录到子用户')
    return true
  }
  
  console.log('❌ 不满足超级登录条件')
  return false
}

/**
 * 超级登录
 */
const handleSuperLogin = async (user: User) => {
  try {
    await ElMessageBox.confirm(
      `确定要超级登录到用户 "${user.name}" (${user.account}) 吗？`,
      '超级登录确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const loading = ElMessage({
      message: '正在切换用户...',
      type: 'info',
      duration: 0
    })
    
    try {
      await authStore.superLogin(user.id)
      loading.close()
      ElMessage.success(`已切换到用户 "${user.name}"`)
      
      // 刷新页面以更新界面
      setTimeout(() => {
        router.push('/dashboard')
        router.go(0)
      }, 500)
    } catch (error) {
      loading.close()
      console.error('超级登录失败:', error)
      ElMessage.error('超级登录失败')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('超级登录失败:', error)
    }
  }
}

/**
 * 搜索
 */
const handleSearch = () => {
  pagination.page = 1
  fetchUserList()
}

/**
 * 重置
 */
const handleReset = () => {
  searchForm.keyword = ''
  searchForm.status = undefined
  handleSearch()
}

/**
 * 新增用户
 */
const handleCreate = () => {
  currentUser.value = null
  formDialogVisible.value = true
}

/**
 * 编辑用户
 */
const handleEdit = (user: User) => {
  currentUser.value = user
  formDialogVisible.value = true
}

/**
 * 重置密码
 */
const handleResetPassword = (user: User) => {
  currentUser.value = user
  passwordDialogVisible.value = true
}

/**
 * 分配权限
 */
const handleAssignPermission = (user: User) => {
  currentUser.value = user
  permissionDialogVisible.value = true
}

/**
 * 切换状态
 */
const handleToggleStatus = async (user: User) => {
  const newStatus = user.status === 'enable' ? 'disable' : 'enable'
  const action = newStatus === 'enable' ? '启用' : '禁用'
  
  try {
    await ElMessageBox.confirm(
      `确定要${action}用户 "${user.name}" 吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await userApi.updateStatus(user.id, newStatus)
    ElMessage.success(`${action}成功`)
    fetchUserList()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('切换状态失败:', error)
      ElMessage.error(`${action}失败`)
    }
  }
}

/**
 * 删除用户
 */
const handleDelete = async (user: User) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.name}" 吗？此操作不可恢复！`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'error'
      }
    )
    
    await userApi.delete(user.id)
    ElMessage.success('删除成功')
    fetchUserList()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除用户失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

/**
 * 表单提交成功
 */
const handleFormSuccess = () => {
  formDialogVisible.value = false
  fetchUserList()
}

/**
 * 密码重置成功
 */
const handlePasswordSuccess = () => {
  passwordDialogVisible.value = false
}

/**
 * 权限分配成功
 */
const handlePermissionSuccess = () => {
  permissionDialogVisible.value = false
  ElMessage.success('权限分配成功')
}

// 初始化
onMounted(async () => {
  // 确保获取当前用户信息
  if (!authStore.userInfo) {
    try {
      await authStore.getUserInfo()
    } catch (error) {
      console.error('获取当前用户信息失败:', error)
    }
  }
  
  fetchUserList()
})
</script>

<style scoped lang="scss">
.users-container {
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
