/**
 * 路由配置
 */

import type { RouteRecordRaw } from 'vue-router'
import MainLayout from '@/components/layout/MainLayout.vue'

// 路由配置
export const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: {
      title: '登录',
      requiresAuth: false
    }
  },
  {
    path: '/',
    component: MainLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: {
          title: '仪表盘',
          requiresAuth: true
        }
      },
      {
        path: 'cards/list',
        name: 'CardList',
        component: () => import('@/views/cards/list/index.vue'),
        meta: {
          title: '卡片列表',
          requiresAuth: true
        }
      },
      {
        path: 'cards/detail/:id',
        name: 'CardDetail',
        component: () => import('@/views/cards/detail/index.vue'),
        meta: {
          title: '卡片详情',
          requiresAuth: true
        }
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/users/index.vue'),
        meta: {
          title: '客户管理',
          requiresAuth: true
        }
      },
      {
        path: 'packages/supplier',
        name: 'SupplierPackage',
        component: () => import('@/views/packages/supplier/index.vue'),
        meta: {
          title: '底层套餐',
          requiresAuth: true
        }
      },
      {
        path: 'packages/sale',
        name: 'SalePackage',
        component: () => import('@/views/packages/sale/index.vue'),
        meta: {
          title: '销售套餐',
          requiresAuth: true
        }
      },
      {
        path: 'suppliers',
        name: 'Suppliers',
        component: () => import('@/views/suppliers/index.vue'),
        meta: {
          title: '供应商管理',
          requiresAuth: true
        }
      },
      // 出入库管理
      {
        path: 'stock/in',
        name: 'StockIn',
        component: () => import('@/views/stock/in/index.vue'),
        meta: {
          title: '卡片入库',
          requiresAuth: true
        }
      },
      {
        path: 'stock/out',
        name: 'StockOut',
        component: () => import('@/views/stock/out/index.vue'),
        meta: {
          title: '卡片出库',
          requiresAuth: true
        }
      },
      {
        path: 'stock/inventory',
        name: 'Inventory',
        component: () => import('@/views/stock/inventory/index.vue'),
        meta: {
          title: '库存管理',
          requiresAuth: true
        }
      },
      {
        path: 'stock/recycle',
        name: 'StockRecycle',
        component: () => import('@/views/stock/recycle/index.vue'),
        meta: {
          title: '卡片回收',
          requiresAuth: true
        }
      },
      {
        path: 'stock/records',
        name: 'StockRecords',
        component: () => import('@/views/stock/records/index.vue'),
        meta: {
          title: '出入库记录',
          requiresAuth: true
        }
      },
      // 流量池管理
      {
        path: 'pools/list',
        name: 'PoolList',
        component: () => import('@/views/pools/list/index.vue'),
        meta: {
          title: '流量池列表',
          requiresAuth: true
        }
      },
      {
        path: 'pools/detail/:id',
        name: 'PoolDetail',
        component: () => import('@/views/pools/detail/index.vue'),
        meta: {
          title: '流量池详情',
          requiresAuth: true
        }
      },
      // 权限管理
      {
        path: 'permissions',
        name: 'Permissions',
        component: () => import('@/views/permissions/index.vue'),
        meta: {
          title: '权限管理',
          requiresAuth: true
        }
      }
    ]
  }
]


