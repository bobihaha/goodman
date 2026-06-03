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
      <el-button
        v-if="canManageOwnApiCredentials"
        type="success"
        @click="handleManageOwnApiCredentials"
      >
        我的API凭证
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
        <el-table-column label="账户余额" width="120">
          <template #default="{ row }">
            {{ formatMoney(row.quota?.account_balance || 0) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'enable' ? 'success' : 'danger'">
              {{ row.status === 'enable' ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="H5" min-width="220">
          <template #default="{ row }">
            <div v-if="row.h5?.slug" class="h5-cell">
              <el-tag :type="row.h5.status === 'enabled' ? 'success' : 'info'">
                {{ getH5StatusLabel(row.h5.status) }}
              </el-tag>
              <div class="h5-url">{{ buildH5Url(row.h5.slug) }}</div>
            </div>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="72" fixed="right" align="center">
          <template #default="{ row }">
            <el-dropdown trigger="click" @command="handleRowAction($event, row)">
              <el-button
                type="primary"
                link
                class="more-actions-btn"
                title="更多操作"
              >
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit" :icon="Edit">编辑</el-dropdown-item>
                  <el-dropdown-item
                    v-if="canAssignPermission(row)"
                    command="assignPermission"
                    :icon="Setting"
                  >
                    分配权限
                  </el-dropdown-item>
                  <el-dropdown-item
                    v-if="canGrantBalance(row)"
                    command="grantBalance"
                  >
                    分配余额
                  </el-dropdown-item>
                  <el-dropdown-item
                    v-if="canManageApiCredentials(row)"
                    command="apiCredentials"
                  >
                    API凭证
                  </el-dropdown-item>
                  <el-dropdown-item
                    v-if="canManageH5(row) && !row.h5?.slug"
                    command="generateH5"
                  >
                    生成H5
                  </el-dropdown-item>
                  <el-dropdown-item
                    v-if="canManageH5(row) && row.h5?.slug"
                    command="editH5"
                  >
                    H5配置
                  </el-dropdown-item>
                  <el-dropdown-item
                    v-if="canSuperLogin(row)"
                    command="superLogin"
                    :icon="SwitchButton"
                  >
                    超级登录
                  </el-dropdown-item>
                  <el-dropdown-item command="resetPassword" :icon="Key">
                    重置密码
                  </el-dropdown-item>
                  <el-dropdown-item
                    command="toggleStatus"
                    :icon="row.status === 'enable' ? Lock : Unlock"
                  >
                    {{ row.status === 'enable' ? '禁用' : '启用' }}
                  </el-dropdown-item>
                  <el-dropdown-item divided command="delete" :icon="Delete">
                    删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
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
          @size-change="handlePageSizeChange"
          @current-change="fetchUserList"
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

    <GrantBalanceDialog
      v-model="grantBalanceDialogVisible"
      :user="currentUser"
      @success="handleGrantBalanceSuccess"
    />

    <UserH5ConfigDialog
      v-model="h5DialogVisible"
      :user="currentUser"
      @success="handleH5Success"
    />

    <UserApiCredentialDialog
      v-model="apiCredentialDialogVisible"
      :user="currentUser"
      @success="handleApiCredentialSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, Edit, Delete, Key, Lock, Unlock, SwitchButton, Setting, MoreFilled } from '@element-plus/icons-vue'
import { userApi } from '@/api/modules/user'
import { formatDateTime, formatMoney } from '@/utils/formatter'
import type { User, UserListParams } from '@/types/user'
import UserFormDialog from './components/UserFormDialog.vue'
import ResetPasswordDialog from './components/ResetPasswordDialog.vue'
import UserPermissionDialog from './components/UserPermissionDialog.vue'
import GrantBalanceDialog from './components/GrantBalanceDialog.vue'
import UserH5ConfigDialog from './components/UserH5ConfigDialog.vue'
import UserApiCredentialDialog from './components/UserApiCredentialDialog.vue'
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
const grantBalanceDialogVisible = ref(false)
const h5DialogVisible = ref(false)
const apiCredentialDialogVisible = ref(false)
const currentUser = ref<User | null>(null)
const canManageOwnApiCredentials = computed(() => authStore.userInfo?.user_level === 2)

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
 * 超级管理员可以为所有用户分配权限，二级用户可以为自己的子用户分配权限
 */
const canAssignPermission = (user: User): boolean => {
  const currentUser = authStore.userInfo
  if (!currentUser) {
    return false
  }

  // 超级管理员（user_level = 1）可以为所有用户分配权限
  if (currentUser.user_level === 1) {
    return true
  }

  // 二级用户（user_level = 2）可以为自己的子用户（user_level = 3）分配权限
  if (currentUser.user_level === 2 && user.user_level === 3 && user.parent_id === currentUser.id) {
    return true
  }

  return false
}

const canGrantBalance = (user: User): boolean => {
  const currentUser = authStore.userInfo
  if (!currentUser) {
    return false
  }
  if (currentUser.user_level === 1) {
    return user.user_level !== 1
  }
  if (currentUser.user_level === 2 && user.user_level === 3 && user.parent_id === currentUser.id) {
    return true
  }
  return false
}

const canManageH5 = (user: User): boolean => {
  const currentUser = authStore.userInfo
  if (!currentUser) return false
  if (currentUser.user_level === 1) {
    return user.user_level === 2
  }
  if (currentUser.user_level === 2) {
    if (user.user_level === 2) {
      return currentUser.id === user.id
    }
    if (user.user_level === 3) {
      return user.parent_id === currentUser.id
    }
  }
  return false
}

const canManageApiCredentials = (user: User): boolean => {
  const currentUser = authStore.userInfo
  if (!currentUser) return false
  if (currentUser.user_level === 1) {
    return user.user_level === 2
  }
  return currentUser.user_level === 2 && currentUser.id === user.id
}

const getH5StatusLabel = (status?: string) => {
  if (status === 'enabled') return '已启用'
  if (status === 'disabled') return '已停用'
  if (status === 'expired') return '已过期'
  return '未生成'
}

const buildH5Url = (slug?: string) => {
  if (!slug) return ''
  return `${window.location.origin}/h5/${slug}`
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

const handlePageSizeChange = () => {
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

const handleRowAction = (command: string | number | object, user: User) => {
  switch (command) {
    case 'edit':
      handleEdit(user)
      break
    case 'assignPermission':
      handleAssignPermission(user)
      break
    case 'grantBalance':
      handleGrantBalance(user)
      break
    case 'apiCredentials':
      handleManageApiCredentials(user)
      break
    case 'generateH5':
      handleGenerateH5(user)
      break
    case 'editH5':
      handleEditH5(user)
      break
    case 'superLogin':
      handleSuperLogin(user)
      break
    case 'resetPassword':
      handleResetPassword(user)
      break
    case 'toggleStatus':
      handleToggleStatus(user)
      break
    case 'delete':
      handleDelete(user)
      break
  }
}

const handleGrantBalance = (user: User) => {
  currentUser.value = user
  grantBalanceDialogVisible.value = true
}

const handleManageApiCredentials = (user: User) => {
  currentUser.value = user
  apiCredentialDialogVisible.value = true
}

const handleManageOwnApiCredentials = async () => {
  if (!authStore.userInfo?.id) {
    return
  }
  const selfUser = await userApi.getDetail(authStore.userInfo.id)
  currentUser.value = selfUser
  apiCredentialDialogVisible.value = true
}

const handleGenerateH5 = async (user: User) => {
  await userApi.generateH5(user.id)
  ElMessage.success('H5地址已生成')
  fetchUserList()
}

const handleEditH5 = async (user: User) => {
  const h5 = await userApi.getH5Detail(user.id)
  currentUser.value = { ...user, h5 }
  h5DialogVisible.value = true
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

const handleGrantBalanceSuccess = () => {
  grantBalanceDialogVisible.value = false
  fetchUserList()
}

const handleH5Success = () => {
  h5DialogVisible.value = false
  fetchUserList()
}

const handleApiCredentialSuccess = () => {
  fetchUserList()
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

  .h5-cell {
    display: grid;
    gap: 6px;
  }

  .h5-url {
    color: #606266;
    font-size: 12px;
    word-break: break-all;
  }

  .more-actions-btn {
    padding: 4px;
    font-size: 18px;
  }
}
</style>
