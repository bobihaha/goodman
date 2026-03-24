<template>
  <el-dialog
    :model-value="modelValue"
    title="分配菜单权限"
    width="800px"
    @close="handleClose"
  >
    <div v-loading="loading" class="permission-assign-container">
      <el-alert
        title="提示"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 20px"
      >
        <template #default>
          为用户 <strong>{{ userName }}</strong> 分配菜单权限，勾选后点击确定保存
        </template>
      </el-alert>

      <el-input
        v-model="searchKeyword"
        placeholder="搜索菜单名称"
        clearable
        style="margin-bottom: 20px"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <div class="menu-tree-container">
        <el-tree
          ref="treeRef"
          :data="filteredMenuTree"
          :props="treeProps"
          show-checkbox
          node-key="id"
          :default-checked-keys="selectedMenuIds"
          :default-expand-all="true"
          @check="handleTreeCheck"
        >
          <template #default="{ data }">
            <div class="menu-node">
              <span class="menu-name">{{ data.name }}</span>
              <span class="menu-path">{{ data.path || '' }}</span>
            </div>
          </template>
        </el-tree>
      </div>

      <div class="selected-summary">
        已选择 <strong>{{ selectedMenuIds.length }}</strong> 个菜单
      </div>
    </div>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { menuApi } from '@/api'
import type { Menu } from '@/types/user'

interface Props {
  modelValue: boolean
  userId: number | null
  userName: string
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue', 'success'])

const loading = ref(false)
const submitting = ref(false)
const searchKeyword = ref('')
const treeRef = ref()
const allMenus = ref<Menu[]>([])
const menuTree = ref<Menu[]>([])
const selectedMenuIds = ref<number[]>([])

const treeProps = {
  children: 'children',
  label: 'name'
}

// 构建菜单树
const buildMenuTree = (menus: Menu[]): Menu[] => {
  const menuMap = new Map<number, Menu>()
  const rootMenus: Menu[] = []

  // 先将所有菜单放入Map
  menus.forEach(menu => {
    menuMap.set(menu.id, { ...menu, children: [] })
  })

  // 构建树形结构
  menus.forEach(menu => {
    const menuItem = menuMap.get(menu.id)
    if (!menuItem) return

    if (menu.parent_id === 0) {
      rootMenus.push(menuItem)
    } else {
      const parent = menuMap.get(menu.parent_id)
      if (parent) {
        if (!parent.children) parent.children = []
        parent.children.push(menuItem)
      }
    }
  })

  return rootMenus
}

// 过滤菜单树（根据搜索关键词）
const filteredMenuTree = computed(() => {
  if (!searchKeyword.value) return menuTree.value

  const keyword = searchKeyword.value.toLowerCase()
  
  const filterMenu = (menu: Menu): Menu | null => {
    const matches = menu.name.toLowerCase().includes(keyword)
    
    if (menu.children && menu.children.length > 0) {
      const filteredChildren = menu.children
        .map(child => filterMenu(child))
        .filter(child => child !== null) as Menu[]
      
      if (filteredChildren.length > 0 || matches) {
        return { ...menu, children: filteredChildren }
      }
    }
    
    return matches ? { ...menu } : null
  }

  return menuTree.value
    .map(menu => filterMenu(menu))
    .filter(menu => menu !== null) as Menu[]
})

// 加载所有菜单
const loadMenus = async () => {
  loading.value = true
  try {
    allMenus.value = await menuApi.getAllMenus()
    
    // 只保留 menu 和 directory 类型，过滤掉 button 类型
    const menuAndDirOnly = allMenus.value.filter(menu => {
      const type = typeof menu.type === 'object' ? (menu.type as any)?.value : menu.type
      return type === 'menu' || type === 'directory'
    })
    
    menuTree.value = buildMenuTree(menuAndDirOnly)
  } catch (error) {
    ElMessage.error('加载菜单列表失败')
  } finally {
    loading.value = false
  }
}

// 加载用户已有菜单权限
const loadUserMenus = async () => {
  if (!props.userId) return

  loading.value = true
  try {
    selectedMenuIds.value = await menuApi.getUserMenuIds(props.userId)
  } catch (error) {
    ElMessage.error('加载用户菜单权限失败')
  } finally {
    loading.value = false
  }
}

// 树节点选中变化
const handleTreeCheck = () => {
  if (treeRef.value) {
    selectedMenuIds.value = treeRef.value.getCheckedKeys()
  }
}

// 监听对话框打开
watch(() => props.modelValue, async (val) => {
  if (val) {
    await loadMenus()
    await loadUserMenus()
  }
})

const handleClose = () => {
  emit('update:modelValue', false)
  searchKeyword.value = ''
  selectedMenuIds.value = []
}

const handleSubmit = async () => {
  if (!props.userId) return

  submitting.value = true
  try {
    // 获取选中的菜单ID（包括半选中的父节点）
    const checkedKeys = treeRef.value.getCheckedKeys()
    const halfCheckedKeys = treeRef.value.getHalfCheckedKeys()
    const allSelectedIds = [...checkedKeys, ...halfCheckedKeys]
    
    await menuApi.setUserMenus(props.userId, allSelectedIds)
    ElMessage.success('菜单权限分配成功')
    emit('success')
    handleClose()
  } catch (error: any) {
    ElMessage.error(error.message || '菜单权限分配失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped lang="scss">
.permission-assign-container {
  min-height: 400px;
  max-height: 600px;
  overflow-y: auto;

  .menu-tree-container {
    border: 1px solid #dcdfe6;
    border-radius: 4px;
    padding: 16px;
    background-color: #f5f7fa;
    max-height: 400px;
    overflow-y: auto;

    :deep(.el-tree) {
      background-color: transparent;

      .el-tree-node__content {
        height: 40px;
        padding: 4px 0;

        &:hover {
          background-color: #f0f9ff;
        }
      }

      .menu-node {
        display: flex;
        align-items: center;
        gap: 12px;
        flex: 1;

        .menu-name {
          font-size: 14px;
          color: #303133;
          font-weight: 500;
        }

        .menu-path {
          font-size: 12px;
          color: #909399;
          font-family: 'Courier New', monospace;
        }
      }
    }
  }

  .selected-summary {
    margin-top: 16px;
    padding: 12px;
    background-color: #f0f9ff;
    border-radius: 4px;
    text-align: center;
    color: #606266;

    strong {
      color: #409eff;
      font-size: 16px;
    }
  }
}
</style>
