<template>
  <div class="pools-list-container">
    <!-- 搜索栏 -->
    <el-card class="search-card" shadow="never">
      <el-form :model="searchForm" inline>
        <el-form-item label="流量池名称">
          <el-input
            v-model="searchForm.name"
            placeholder="请输入流量池名称"
            clearable
            style="width: 200px"
            @clear="handleSearch"
          />
        </el-form-item>
        <el-form-item label="运营商">
          <el-select
            v-model="searchForm.carrier"
            placeholder="请选择运营商"
            clearable
            style="width: 150px"
            @change="handleSearch"
          >
            <el-option
              v-for="item in CARRIER_OPTIONS"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="销售套餐">
          <el-input
            v-model="searchForm.sale_package_id"
            placeholder="请输入销售套餐ID"
            clearable
            style="width: 150px"
            @clear="handleSearch"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="searchForm.status"
            placeholder="请选择状态"
            clearable
            style="width: 120px"
            @change="handleSearch"
          >
            <el-option
              v-for="item in POOL_STATUS_OPTIONS"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">
            搜索
          </el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 流量池卡片列表 -->
    <div class="pools-grid">
      <el-card
        v-for="pool in poolList"
        :key="pool.id"
        class="pool-card"
        shadow="hover"
        @click="handleViewDetail(pool)"
      >
        <!-- 流量池标题 -->
        <div class="pool-header">
          <div class="pool-title">
            <h3>{{ pool.name }}</h3>
            <el-tag :type="POOL_STATUS_MAP[pool.status].type" size="small">
              {{ POOL_STATUS_MAP[pool.status].label }}
            </el-tag>
          </div>
          <el-button
            link
            type="primary"
            @click.stop="handleViewDetail(pool)"
          >
            查看详情 <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>

        <!-- 流量使用情况 -->
        <div class="pool-usage">
          <div class="usage-title">流量使用情况：</div>
          <div class="usage-stats">
            <span class="total">共{{ formatFlow(pool.data_total) }}</span>
            <span class="remaining">剩余<span class="value">{{ formatFlow(pool.data_remaining) }}</span></span>
          </div>
          <el-progress
            :percentage="pool.usage_percent"
            :color="getProgressColor(pool.usage_percent, pool.alert_threshold)"
            :stroke-width="8"
            :show-text="false"
          />
          <div class="usage-percent-text">{{ pool.usage_percent }}%</div>
        </div>

        <!-- 卡片激活情况 -->
        <div class="pool-cards">
          <div class="cards-title">卡片激活情况：</div>
          <div class="cards-stats">
            <div class="stat-item">
              <span class="label">已激活</span>
              <span class="value activated">{{ pool.card_stats?.activated || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="label">已停卡</span>
              <span class="value suspended">{{ pool.card_stats?.suspended || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="label">库存</span>
              <span class="value stock">{{ pool.card_stats?.stock || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="label">测试期</span>
              <span class="value testing">{{ pool.card_stats?.testing || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="label">已销卡</span>
              <span class="value cancelled">{{ pool.card_stats?.cancelled || 0 }}</span>
            </div>
          </div>
          <el-progress
            :percentage="getCardActivatedPercent(pool)"
            :stroke-width="6"
            :show-text="false"
            :color="'#FFA500'"
          />
        </div>

        <!-- 最近同步时间 -->
        <div class="pool-footer">
          <span class="sync-time">最近同步时间：{{ pool.last_sync_at || '-' }}</span>
        </div>

        <!-- 操作按钮 -->
        <div class="pool-actions" @click.stop>
          <el-button size="small" @click="handleEdit(pool)">告警设置</el-button>
          <el-button size="small" type="primary" @click="handleAddCards(pool)">添加卡片</el-button>
          <el-button size="small" type="warning" @click="handleRecharge(pool)">充值</el-button>
        </div>
      </el-card>

      <!-- 空状态 -->
      <el-empty
        v-if="!loading && poolList.length === 0"
        description="暂无流量池数据"
        style="grid-column: 1 / -1"
      />

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-container" style="grid-column: 1 / -1">
        <el-skeleton :rows="3" animated />
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[12, 24, 48, 96]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSearch"
        @current-change="handleSearch"
      />
    </div>

    <!-- 流量池表单对话框 -->
    <PoolFormDialog
      v-model="formDialogVisible"
      :pool="currentPool"
      @success="handleSearch"
    />

    <!-- 添加卡片对话框 -->
    <AddCardsDialog
      v-model="addCardsDialogVisible"
      :pool="currentPool"
      @success="handleSearch"
    />

    <!-- 充值加油包对话框 -->
    <RechargeDialog
      v-model="rechargeDialogVisible"
      :pool="currentPool"
      @success="handleSearch"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, ArrowRight } from '@element-plus/icons-vue'
import { getPoolList, togglePoolStatus } from '@/api/modules/pool'
import { formatFlow } from '@/utils/formatter'
import { CARRIER_MAP, CARRIER_OPTIONS } from '@/constants/card'
import { POOL_STATUS_MAP, POOL_STATUS_OPTIONS } from '@/constants/pool'
import type { Pool, PoolListParams } from '@/types/pool'
import PoolFormDialog from './components/PoolFormDialog.vue'
import AddCardsDialog from './components/AddCardsDialog.vue'
import RechargeDialog from './components/RechargeDialog.vue'

const router = useRouter()

// 搜索表单
const searchForm = reactive<PoolListParams>({
  name: '',
  carrier: undefined,
  sale_package_id: undefined,
  status: undefined
})

// 分页
const pagination = reactive({
  page: 1,
  page_size: 12,
  total: 0
})

// 流量池列表
const poolList = ref<Pool[]>([])
const loading = ref(false)

// 对话框
const formDialogVisible = ref(false)
const addCardsDialogVisible = ref(false)
const rechargeDialogVisible = ref(false)
const currentPool = ref<Pool | null>(null)

/**
 * 获取流量池列表
 */
const fetchPoolList = async () => {
  loading.value = true
  try {
    const params = {
      ...searchForm,
      page: pagination.page,
      page_size: pagination.page_size
    }
    const response = await getPoolList(params)
    poolList.value = response.list || []
    pagination.total = response.total || 0
  } catch (error) {
    console.error('获取流量池列表失败:', error)
    ElMessage.error('获取流量池列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 计算卡片激活百分比
 */
const getCardActivatedPercent = (pool: Pool) => {
  if (!pool.card_count || pool.card_count === 0) return 0
  const activated = pool.card_stats?.activated || 0
  return Math.round((activated / pool.card_count) * 100)
}

/**
 * 搜索
 */
const handleSearch = () => {
  pagination.page = 1
  fetchPoolList()
}

/**
 * 重置
 */
const handleReset = () => {
  Object.assign(searchForm, {
    name: '',
    carrier: undefined,
    sale_package_id: undefined,
    status: undefined
  })
  handleSearch()
}

/**
 * 编辑流量池
 */
const handleEdit = (pool: Pool) => {
  currentPool.value = pool
  formDialogVisible.value = true
}

/**
 * 查看详情
 */
const handleViewDetail = (pool: Pool) => {
  router.push(`/pools/detail/${pool.id}`)
}

/**
 * 添加卡片
 */
const handleAddCards = (pool: Pool) => {
  currentPool.value = pool
  addCardsDialogVisible.value = true
}

/**
 * 充值加油包
 */
const handleRecharge = (pool: Pool) => {
  currentPool.value = pool
  rechargeDialogVisible.value = true
}

/**
 * 启用/禁用流量池
 */
const handleToggleStatus = async (pool: Pool) => {
  const action = pool.status === 'enable' ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(
      `确定要${action}流量池"${pool.name}"吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const newStatus = pool.status === 'enable' ? 'disable' : 'enable'
    await togglePoolStatus(pool.id, newStatus)
    ElMessage.success(`${action}成功`)
    fetchPoolList()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error(`${action}流量池失败:`, error)
      ElMessage.error(`${action}失败`)
    }
  }
}



/**
 * 获取进度条颜色
 */
const getProgressColor = (percent: number, threshold?: number) => {
  if (threshold && percent >= threshold) {
    return '#f56c6c'
  }
  if (percent >= 80) {
    return '#e6a23c'
  }
  return '#67c23a'
}

onMounted(() => {
  fetchPoolList()
})
</script>

<style scoped lang="scss">
.pools-list-container {
  padding: 20px;

  .search-card {
    margin-bottom: 20px;
  }

  .pools-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
    gap: 20px;
    margin-bottom: 20px;

    .pool-card {
      cursor: pointer;
      transition: all 0.3s;
      border-radius: 8px;

      &:hover {
        transform: translateY(-4px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      }

      :deep(.el-card__body) {
        padding: 20px;
      }

      .pool-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 20px;
        padding-bottom: 16px;
        border-bottom: 1px solid #f0f0f0;

        .pool-title {
          flex: 1;

          h3 {
            margin: 0 0 8px 0;
            font-size: 18px;
            font-weight: 600;
            color: #303133;
          }
        }
      }

      .pool-usage {
        margin-bottom: 20px;

        .usage-title {
          font-size: 14px;
          color: #606266;
          margin-bottom: 12px;
        }

        .usage-stats {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;
          font-size: 14px;

          .total {
            color: #606266;
          }

          .remaining {
            color: #909399;

            .value {
              color: #409eff;
              font-weight: 600;
              font-size: 16px;
            }
          }
        }

        .usage-percent-text {
          text-align: right;
          font-size: 12px;
          color: #909399;
          margin-top: 4px;
        }
      }

      .pool-cards {
        margin-bottom: 16px;

        .cards-title {
          font-size: 14px;
          color: #606266;
          margin-bottom: 12px;
        }

        .cards-stats {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;

          .stat-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;

            .label {
              font-size: 12px;
              color: #909399;
            }

            .value {
              font-size: 16px;
              font-weight: 600;

              &.activated {
                color: #FFA500;
              }

              &.suspended {
                color: #909399;
              }

              &.stock {
                color: #909399;
              }

              &.testing {
                color: #909399;
              }

              &.cancelled {
                color: #909399;
              }
            }
          }
        }
      }

      .pool-footer {
        padding-top: 12px;
        border-top: 1px solid #f0f0f0;
        margin-bottom: 16px;

        .sync-time {
          font-size: 12px;
          color: #909399;
        }
      }

      .pool-actions {
        display: flex;
        gap: 8px;
        justify-content: flex-end;
      }
    }

    .loading-container {
      padding: 40px;
    }
  }

  .pagination-container {
    display: flex;
    justify-content: center;
    padding: 20px 0;
  }
}
</style>

