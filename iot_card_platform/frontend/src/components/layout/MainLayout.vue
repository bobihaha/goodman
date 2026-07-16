<template>
  <div class="main-layout">
    <el-container>
      <!-- 侧边栏 -->
      <el-aside :width="isCollapse ? '64px' : '240px'" class="sidebar">
        <div class="logo-container">
          <transition name="fade">
            <h1 v-if="!isCollapse" class="logo-title">IoT 管理平台</h1>
            <h1 v-else class="logo-title-mini">IoT</h1>
          </transition>
        </div>

        <el-scrollbar class="menu-scrollbar">
          <el-menu
            :default-active="activeMenu"
            :collapse="isCollapse"
            :unique-opened="true"
            router
            class="sidebar-menu"
          >
            <template v-for="item in menuList" :key="item.path">
              <!-- 有子菜单 -->
              <el-sub-menu v-if="item.children && item.children.length > 0" :index="item.path">
                <template #title>
                  <el-icon><component :is="item.icon" /></el-icon>
                  <span>{{ item.name }}</span>
                </template>
                <el-menu-item
                  v-for="child in item.children"
                  :key="child.path"
                  :index="child.path"
                >
                  <template #default>
                    <el-icon><component :is="child.icon" /></el-icon>
                    <span>{{ child.name }}</span>
                  </template>
                </el-menu-item>
              </el-sub-menu>

              <!-- 无子菜单 -->
              <el-menu-item v-else :index="item.path">
                <template #default>
                  <el-icon><component :is="item.icon" /></el-icon>
                  <span>{{ item.name }}</span>
                </template>
              </el-menu-item>
            </template>
          </el-menu>
        </el-scrollbar>
      </el-aside>

      <!-- 主内容区 -->
      <el-container class="main-container">
        <!-- 超级登录横幅 -->
        <SuperLoginBanner />

        <!-- 顶部导航栏 -->
        <el-header class="header">
          <div class="header-left">
            <el-icon class="collapse-icon" @click="toggleCollapse">
              <Fold v-if="!isCollapse" />
              <Expand v-else />
            </el-icon>

            <!-- 面包屑 -->
            <el-breadcrumb separator="/" class="breadcrumb">
              <el-breadcrumb-item
                v-for="(item, index) in breadcrumbs"
                :key="index"
                :to="index === breadcrumbs.length - 1 ? undefined : item.path"
              >
                {{ item.name }}
              </el-breadcrumb-item>
            </el-breadcrumb>
          </div>

          <div class="header-right">
            <!-- 全屏按钮 -->
            <el-tooltip content="全屏" placement="bottom">
              <el-icon class="header-icon" @click="toggleFullscreen">
                <FullScreen />
              </el-icon>
            </el-tooltip>

            <!-- 用户信息 -->
            <el-dropdown class="user-dropdown" @command="handleCommand">
              <div class="user-info">
                <el-avatar :size="32" :src="userInfo?.avatar">
                  <el-icon><User /></el-icon>
                </el-avatar>
                <span class="username">{{ userInfo?.name || '用户' }}</span>
                <el-icon class="arrow-icon"><ArrowDown /></el-icon>
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">
                    <el-icon><User /></el-icon>
                    个人中心
                  </el-dropdown-item>
                  <el-dropdown-item command="settings">
                    <el-icon><Setting /></el-icon>
                    系统设置
                  </el-dropdown-item>
                  <el-dropdown-item divided command="logout">
                    <el-icon><SwitchButton /></el-icon>
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>

        <!-- 主内容 -->
        <el-main class="main-content">
          <router-view v-slot="{ Component }">
            <transition name="fade-transform" mode="out-in">
              <keep-alive :include="cachedViews">
                <component :is="Component" />
              </keep-alive>
            </transition>
          </router-view>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Fold,
  Expand,
  FullScreen,
  User,
  ArrowDown,
  Setting,
  SwitchButton,
  DataBoard,
  CreditCard,
  Box,
  Connection,
  UserFilled,
  OfficeBuilding,
  Setting as SettingIcon,
  WarningFilled,
  Money,
  Calendar
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores'
import SuperLoginBanner from '@/components/common/SuperLoginBanner.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// 侧边栏折叠状态
const isCollapse = ref(false)

// 缓存的视图
const cachedViews = ref<string[]>([])

// 用户信息
const userInfo = computed(() => authStore.userInfo)

// 当前激活的菜单
const activeMenu = computed(() => route.path)

// 图标映射（根据菜单code或path匹配图标）
const iconMap: Record<string, any> = {
  'dashboard': DataBoard,
  'supplier_traffic_pools': Connection,
  'supplier-traffic-pools': Connection,
  'cards': CreditCard,
  'card': CreditCard,
  'packages': Box,
  'package': Box,
  'stock': Box,
  'pools': Connection,
  'pool': Connection,
  'users': UserFilled,
  'user': UserFilled,
  'suppliers': OfficeBuilding,
  'supplier': OfficeBuilding,
  'suspend': WarningFilled,
  'suspend_policy': SettingIcon,
  'suspend_logs': CreditCard,
  'suspend_alerts': WarningFilled,
  'system': SettingIcon,
  'system_config': SettingIcon,
  'permissions': SettingIcon,
  'renewal': Money,
  'channel_points': Money,
  'channels': Money,
  'package_period': Calendar,
  'package_period_force_activate': Calendar
}

// 从后端菜单数据转换为前端菜单格式
const convertMenus = (menus: any[]) => {
  return menus
    .filter(menu => {
      // 只显示 menu 和 directory 类型，过滤掉 button 类型
      const type = menu.type?.value || menu.type
      return type === 'menu' || type === 'directory'
    })
    .map(menu => {
      // 根据菜单code或path匹配图标
      const iconKey = menu.code || menu.path?.split('/')[1] || ''
      const icon = iconMap[iconKey] || DataBoard

      const converted: any = {
        path: menu.path || `/${menu.code}`,
        name: menu.name,
        icon: icon
      }

      // 递归处理子菜单
      if (menu.children && menu.children.length > 0) {
        const childMenus = convertMenus(menu.children)
        if (childMenus.length > 0) {
          converted.children = childMenus
        }
      }

      return converted
    })
}

// 菜单列表（根据用户权限动态生成）
const menuList = computed(() => {
  const userMenus = authStore.menus || []
  return convertMenus(userMenus)
})

// 面包屑
const breadcrumbs = computed(() => {
  const matched = route.matched.filter(item => item.meta && item.meta.title)
  const breadcrumbList = matched.map(item => ({
    name: item.meta.title as string,
    path: item.path
  }))

  // 如果不是首页，添加首页到面包屑
  if (route.path !== '/dashboard') {
    breadcrumbList.unshift({ name: '首页', path: '/dashboard' })
  }

  return breadcrumbList
})

// 切换侧边栏折叠
const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

// 切换全屏
const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

// 处理用户下拉菜单命令
const handleCommand = async (command: string) => {
  switch (command) {
    case 'profile':
      router.push('/system/config?tab=profile')
      break
    case 'settings':
      router.push('/system/config')
      break
    case 'logout':
      try {
        await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        await authStore.logout()
        ElMessage.success('退出成功')
        router.push('/login')
      } catch (error) {
        // 用户取消
      }
      break
  }
}

// 监听路由变化，更新面包屑
watch(
  () => route.path,
  () => {
    // 可以在这里添加页面缓存逻辑
  }
)
</script>

<style scoped lang="scss">
.main-layout {
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

.el-container {
  height: 100%;
}

// 侧边栏样式
.sidebar {
  background: linear-gradient(180deg, #1a1f3a 0%, #0f1419 100%);
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
  transition: width 0.3s;
  overflow: hidden;

  .logo-container {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding: 0 20px;

    .logo-title {
      font-size: 20px;
      font-weight: 700;
      color: #fff;
      margin: 0;
      letter-spacing: 1px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .logo-title-mini {
      font-size: 24px;
      font-weight: 700;
      color: #fff;
      margin: 0;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
  }

  .menu-scrollbar {
    height: calc(100vh - 60px);
  }

  .sidebar-menu {
    border: none;
    background: transparent;

    :deep(.el-menu-item),
    :deep(.el-sub-menu__title) {
      color: rgba(255, 255, 255, 0.85);
      font-weight: 500;
      transition: all 0.3s;
      margin: 4px 8px;
      border-radius: 8px;

      &:hover {
        background: rgba(102, 126, 234, 0.15) !important;
        color: #fff;
      }

      &.is-active {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.3) 0%, rgba(118, 75, 162, 0.2) 100%) !important;
        color: #fff;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);

        &::before {
          content: '';
          position: absolute;
          left: 0;
          top: 50%;
          transform: translateY(-50%);
          width: 4px;
          height: 24px;
          background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
          border-radius: 0 4px 4px 0;
        }
      }
    }

    :deep(.el-sub-menu__title:hover) {
      background: rgba(102, 126, 234, 0.15) !important;
      color: #fff;
    }

    :deep(.el-sub-menu.is-opened > .el-sub-menu__title) {
      color: #fff;
      font-weight: 600;
    }

    :deep(.el-menu--inline) {
      background: rgba(0, 0, 0, 0.2);

      .el-menu-item {
        padding-left: 48px !important;

        &.is-active {
          background: rgba(102, 126, 234, 0.25) !important;
          color: #a8b5ff;

          &::before {
            left: 8px;
            width: 3px;
            height: 20px;
          }
        }
      }
    }

    :deep(.el-icon) {
      color: inherit;
      font-size: 18px;
    }

    :deep(span) {
      font-size: 14px;
    }
  }
}

// 主容器
.main-container {
  background: #f5f7fa;
}

// 顶部导航栏
.header {
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  z-index: 10;

  .header-left {
    display: flex;
    align-items: center;
    gap: 24px;

    .collapse-icon {
      font-size: 20px;
      cursor: pointer;
      color: #606266;
      transition: all 0.3s;

      &:hover {
        color: #409eff;
        transform: scale(1.1);
      }
    }

    .breadcrumb {
      font-size: 14px;
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 20px;

    .header-icon {
      font-size: 20px;
      cursor: pointer;
      color: #606266;
      transition: all 0.3s;

      &:hover {
        color: #409eff;
        transform: scale(1.1);
      }
    }

    .user-dropdown {
      cursor: pointer;

      .user-info {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 4px 12px;
        border-radius: 20px;
        transition: all 0.3s;

        &:hover {
          background: #f5f7fa;
        }

        .username {
          font-size: 14px;
          color: #303133;
          font-weight: 500;
        }

        .arrow-icon {
          font-size: 12px;
          color: #909399;
        }
      }
    }
  }
}

// 主内容区
.main-content {
  padding: 20px;
  overflow-y: auto;
  background: #f5f7fa;
}

// 过渡动画
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: all 0.3s;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>
