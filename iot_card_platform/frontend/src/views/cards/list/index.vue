<template>
  <div class="card-list-page">
    <!-- 统计卡片 -->
    <div class="stats-row">
      <el-row :gutter="16">
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon total">
              <el-icon><CreditCard /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total }}</div>
              <div class="stat-label">总卡片数</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon activated">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.activated }}</div>
              <div class="stat-label">已激活</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon silent">
              <el-icon><Clock /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.silent }}</div>
              <div class="stat-label">沉默期</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon suspended">
              <el-icon><WarningFilled /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.suspended }}</div>
              <div class="stat-label">已停机</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 搜索和筛选 -->
    <el-card class="search-card" shadow="never">
      <el-form :model="searchForm" inline class="search-form">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="ICCID / MSISDN / 移动后6位 / 联通电信后2-7位"
            clearable
            style="width: 293px"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="状态">
          <el-select
            v-model="searchForm.status"
            placeholder="全部状态"
            clearable
            style="width: 213px"
          >
            <el-option
              v-for="item in CARD_STATUS_OPTIONS"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="运营商">
          <el-select
            v-model="searchForm.carrier"
            placeholder="全部运营商"
            clearable
            style="width: 213px"
          >
            <el-option
              v-for="item in CARRIER_OPTIONS"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="周期">
          <el-select
            v-model="searchForm.period_type"
            placeholder="全部周期"
            clearable
            style="width: 187px"
          >
            <el-option
              v-for="item in PERIOD_TYPE_OPTIONS"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="流量池">
          <el-select
            v-model="searchForm.is_pool_member"
            placeholder="全部"
            clearable
            style="width: 187px"
          >
            <el-option label="在池中" :value="true" />
            <el-option label="不在池中" :value="false" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><RefreshLeft /></el-icon>
            重置
          </el-button>
          <el-button link type="primary" @click="showAdvanced = !showAdvanced">
            <el-icon><ArrowDown v-if="!showAdvanced" /><ArrowUp v-else /></el-icon>
            {{ showAdvanced ? '收起' : '高级搜索' }}
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 高级搜索 -->
      <el-form v-if="showAdvanced" :model="searchForm" inline class="search-form advanced-form">
        <el-form-item label="关联客户">
          <el-select
            v-model="searchForm.customer_id"
            placeholder="全部客户"
            filterable
            remote
            clearable
            :remote-method="searchCustomers"
            :loading="customerLoading"
            style="width: 213px"
          >
            <el-option
              v-for="item in customerList"
              :key="item.id"
              :label="`${item.account} (${item.name})`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="备注">
          <el-input
            v-model="searchForm.remark"
            placeholder="备注关键词"
            clearable
            style="width: 187px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>

        <el-form-item label="出库单号">
          <el-input
            v-model="searchForm.batch_id"
            placeholder="请输入出库单号或批次ID"
            clearable
            style="width: 160px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>

        <el-form-item label="出库时间">
          <el-date-picker
            v-model="stockOutRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 280px"
          />
        </el-form-item>

        <el-form-item label="激活时间">
          <el-date-picker
            v-model="activatedRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 280px"
          />
        </el-form-item>

        <el-form-item label="到期时间">
          <el-date-picker
            v-model="expiredRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 280px"
          />
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作栏 -->
    <el-card class="toolbar-card" shadow="never">
      <div class="toolbar">
        <div class="toolbar-left">
          <el-button type="primary" @click="showBatchQueryDialog">
            <el-icon><Search /></el-icon>
            批量查询
          </el-button>
          <el-button
            type="success"
            @click="showBatchTransferDialog"
          >
            <el-icon><Connection /></el-icon>
            批量划拨
          </el-button>
          <el-button
            type="warning"
            @click="showBatchRemarkDialog"
          >
            <el-icon><Edit /></el-icon>
            批量备注
          </el-button>
          <el-button
            type="primary"
            @click="showBatchRenewDialog"
          >
            <el-icon><Refresh /></el-icon>
            批量续费
          </el-button>
          <el-button
            type="warning"
            @click="showBatchAddFlowDialog"
          >
            <el-icon><Plus /></el-icon>
            批量补量
          </el-button>
          <el-button
            type="danger"
            @click="showBatchSuspendDialog"
          >
            <el-icon><CircleClose /></el-icon>
            批量停机
          </el-button>
          <el-button
            type="success"
            @click="showBatchResumeDialog"
          >
            <el-icon><CircleCheck /></el-icon>
            批量复机
          </el-button>
        </div>
        <div class="toolbar-right">
          <el-button @click="handleExport">
            <el-icon><Download /></el-icon>
            导出
          </el-button>
          <el-button @click="goPurchaseRecords">
            购买记录
          </el-button>
          <el-button
            @click="showExportHistoryDialog"
          >
            <el-icon><Download /></el-icon>
            导出历史用量
          </el-button>
          <el-popover
            placement="bottom-end"
            :width="300"
            trigger="click"
            popper-class="column-settings-popover"
          >
            <template #reference>
              <el-button>
                <el-icon><Setting /></el-icon>
                设置列
              </el-button>
            </template>
            <div class="column-settings">
              <div class="column-settings-header">
                <span class="column-settings-title">卡片列表显示列</span>
                <el-button link type="primary" @click="resetVisibleColumns">
                  恢复默认
                </el-button>
              </div>
              <div class="column-settings-tip">
                ICCID 和操作列固定显示，其他列可自由勾选
              </div>
              <el-checkbox-group
                v-model="visibleColumnKeys"
                class="column-checkbox-group"
                @change="handleVisibleColumnsChange"
              >
                <el-checkbox
                  v-for="column in allDraggableColumns"
                  :key="column.key"
                  :label="column.key"
                >
                  {{ column.label }}
                </el-checkbox>
              </el-checkbox-group>
            </div>
          </el-popover>
          <el-button @click="fetchCardList">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
      <div v-if="selectedCards.length > 0" class="selection-info">
        已选择 <span class="selection-count">{{ selectedCards.length }}</span> 张卡片
        <el-button type="primary" link @click="showBatchAddFlowDialog">批量补量</el-button>
        <el-button type="text" @click="clearSelection">清空选择</el-button>
      </div>
    </el-card>

    <!-- 批量查询筛选提示 -->
    <div v-if="isBatchQueryMode" class="batch-query-bar">
      <el-icon><Filter /></el-icon>
      <span>批量查询结果：共 <strong>{{ cardList.length }}</strong> 张卡片</span>
      <span v-if="batchQueryNotFound.length > 0" class="not-found-info">
        ，未找到 <strong>{{ batchQueryNotFound.length }}</strong> 张
      </span>
      <el-button type="primary" link @click="clearBatchQuery">清除筛选</el-button>
    </div>

    <!-- 卡片列表 -->
    <el-card class="table-card" shadow="never">
      <el-table
        v-loading="loading"
        :data="cardList"
        border
        stripe
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column prop="iccid" width="200" fixed>
          <template #header>
            <div class="sortable-header">
              <span>ICCID</span>
              <span class="sort-buttons">
                <el-icon class="sort-icon" :class="{ active: isSortActive('iccid', 'asc') }" @click="handleColumnSort('iccid', 'asc')"><ArrowUp /></el-icon>
                <el-icon class="sort-icon" :class="{ active: isSortActive('iccid', 'desc') }" @click="handleColumnSort('iccid', 'desc')"><ArrowDown /></el-icon>
              </span>
            </div>
          </template>
          <template #default="{ row }">
            <el-link type="primary" @click="viewDetail(row.id)">
              {{ row.iccid }}
            </el-link>
          </template>
        </el-table-column>

        <template v-for="column in orderedColumns" :key="column.key">
          <el-table-column
            :prop="column.prop"
            :label="column.label"
            :width="column.width"
            :min-width="column.minWidth"
            :align="column.align"
            :show-overflow-tooltip="column.showOverflowTooltip"
          >
            <template #header>
              <div
                class="draggable-header"
                :class="{
                  dragging: dragState.draggingKey === column.key,
                  'drag-over-before': dragState.overKey === column.key && dragState.dropPosition === 'before',
                  'drag-over-after': dragState.overKey === column.key && dragState.dropPosition === 'after'
                }"
                draggable="true"
                @dragstart="handleColumnDragStart(column.key, $event)"
                @dragover="handleColumnDragOver(column.key, $event)"
                @drop="handleColumnDrop(column.key, $event)"
                @dragend="handleColumnDragEnd"
              >
                <div class="sortable-header">
                  <span class="drag-handle" title="拖动调整列顺序">⋮⋮</span>
                  <span>{{ column.label }}</span>
                  <span v-if="column.sortField" class="sort-buttons">
                    <el-icon class="sort-icon" :class="{ active: isSortActive(column.sortField, 'asc') }" @click.stop="handleColumnSort(column.sortField, 'asc')"><ArrowUp /></el-icon>
                    <el-icon class="sort-icon" :class="{ active: isSortActive(column.sortField, 'desc') }" @click.stop="handleColumnSort(column.sortField, 'desc')"><ArrowDown /></el-icon>
                  </span>
                </div>
              </div>
            </template>

            <template #default="{ row }">
              <template v-if="column.key === 'imsi'">
                {{ row.imsi || '-' }}
              </template>
              <template v-else-if="column.key === 'msisdn'">
                {{ row.msisdn || '-' }}
              </template>
              <template v-else-if="column.key === 'material'">
                {{ row.material_name || CARD_MATERIAL_MAP[row.material as keyof typeof CARD_MATERIAL_MAP] || '-' }}
              </template>
              <template v-else-if="column.key === 'diagnostic'">
                <el-button type="primary" link @click="showDiagnosticsDialog(row)">
                  诊断
                </el-button>
              </template>
              <template v-else-if="column.key === 'refresh'">
                <el-button
                  type="primary"
                  link
                  :loading="refreshingMap[row.id]"
                  @click="handleRowRefresh(row)"
                >
                  刷新
                </el-button>
              </template>
              <template v-else-if="column.key === 'card_type'">
                <el-tag v-if="row.card_type === 'pool'" type="success" size="small">
                  流量池卡
                </el-tag>
                <el-tag v-else type="info" size="small">
                  单卡
                </el-tag>
              </template>
              <template v-else-if="column.key === 'carrier'">
                {{ getCarrierLabel(row.carrier) }}
              </template>
              <template v-else-if="column.key === 'status'">
                <el-tag :type="getStatusMeta(row.status).type">
                  {{ getStatusMeta(row.status).label }}
                </el-tag>
              </template>
              <template v-else-if="column.key === 'data_used_month'">
                {{ formatFlowValue(row.data_used_month) }}
              </template>
              <template v-else-if="column.key === 'data_total'">
                {{ formatFlowValue(getDisplayTotal(row)) }}
              </template>
              <template v-else-if="column.key === 'data_used'">
                {{ formatFlowValue(row.data_used) }}
              </template>
              <template v-else-if="column.key === 'flow_usage'">
                <div class="flow-usage">
                  <div class="flow-progress-row">
                    <el-progress
                      :percentage="Math.min(formatUsagePercent(row.data_used, getDisplayTotal(row)), 100)"
                      :color="getProgressColor(formatUsagePercent(row.data_used, getDisplayTotal(row)))"
                      :show-text="false"
                    />
                    <span class="flow-percent">{{ formatUsagePercent(row.data_used, getDisplayTotal(row)).toFixed(2) }}%</span>
                  </div>
                  <div class="flow-text">
                    {{ formatFlowValue(row.data_used) }} / {{ formatFlowValue(getDisplayTotal(row)) }}
                  </div>
                </div>
              </template>
              <template v-else-if="column.key === 'flow_size'">
                {{ formatFlow(row.flow_size) }}/{{ getPeriodLabel(row.period_type) }}
              </template>
              <template v-else-if="column.key === 'test_expire_date'">
                <span v-if="row.test_expire_date">{{ formatDate(row.test_expire_date) }}</span>
                <span v-else class="text-muted">-</span>
              </template>
              <template v-else-if="column.key === 'silent_expire_date'">
                <span v-if="row.silent_expire_date">{{ formatDate(row.silent_expire_date) }}</span>
                <span v-else class="text-muted">-</span>
              </template>
              <template v-else-if="column.key === 'activated_at'">
                <span v-if="row.activated_at">{{ formatDate(row.activated_at) }}</span>
                <span v-else class="text-muted">-</span>
              </template>
              <template v-else-if="column.key === 'stock_out_date'">
                <span v-if="row.stock_out_date || row.stock_out_at">{{ formatDate(row.stock_out_date || row.stock_out_at) }}</span>
                <span v-else class="text-muted">-</span>
              </template>
              <template v-else-if="column.key === 'expired_at'">
                <span :class="{ 'text-danger': isExpired(row.expired_at) }">
                  {{ formatDate(row.expired_at) }}
                </span>
              </template>
              <template v-else-if="column.key === 'is_pool_member'">
                <el-tag v-if="row.is_pool_member" type="success" size="small">
                  在池中
                </el-tag>
                <el-tag v-else type="info" size="small">
                  未入池
                </el-tag>
              </template>
              <template v-else-if="column.key === 'related_user_name'">
                <span>{{ row.related_user_name || '-' }}</span>
              </template>
              <template v-else-if="column.key === 'remark'">
                <span>{{ row.remark || '-' }}</span>
              </template>
            </template>
          </el-table-column>
        </template>

        <el-table-column label="操作" width="64" fixed="right" align="center">
          <template #default="{ row }">
            <div class="row-actions">
              <el-dropdown
                trigger="click"
                @command="handleRowAction($event, row)"
              >
                <el-button
                  type="text"
                  size="small"
                  class="more-actions-btn"
                  title="操作"
                >
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="detail">详情</el-dropdown-item>
                    <el-dropdown-item command="transfer">划拨</el-dropdown-item>
                    <el-dropdown-item command="remark">备注</el-dropdown-item>
                    <el-dropdown-item command="renew">续费</el-dropdown-item>
                    <el-dropdown-item
                      command="addFlow"
                      :disabled="row.card_type !== 'single'"
                    >
                      补量
                    </el-dropdown-item>
                    <el-dropdown-item
                      command="resume"
                      :disabled="row.status !== 'suspended'"
                    >
                      复机
                    </el-dropdown-item>
                    <el-dropdown-item
                      command="restart"
                      :disabled="!['activated', 'testing', 'silent', 'suspended'].includes(row.status)"
                    >
                      重启
                    </el-dropdown-item>
                    <el-dropdown-item
                      v-if="isSuperAdmin"
                      command="forceResume"
                      :disabled="row.status !== 'suspended'"
                    >
                      强制复机
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div v-if="!isBatchQueryMode" class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[20, 50, 100, 200]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 批量查询对话框 -->
    <BatchQueryDialog
      v-model="batchQueryVisible"
      @success="handleBatchQuerySuccess"
    />

    <!-- 批量划拨对话框 -->
    <BatchTransferDialog
      v-model="batchTransferVisible"
      @success="handleBatchTransferSuccess"
    />

    <!-- 批量备注对话框 -->
    <BatchRemarkDialog
      v-model="batchRemarkVisible"
      @success="handleBatchRemarkSuccess"
    />

    <!-- 导出历史用量对话框 -->
    <ExportHistoryDialog
      v-model="exportHistoryVisible"
      :card-ids="exportHistoryCardIds"
      :export-count="exportHistoryCount"
      :export-scope-label="exportHistoryScopeLabel"
      :filter-params="exportHistoryFilterParams"
    />

    <!-- 批量续费对话框 -->
    <BatchRenewDialog
      v-model="batchRenewVisible"
      @success="handleBatchRenewSuccess"
    />

    <!-- 批量补量对话框 -->
    <BatchAddFlowDialog
      v-model="batchAddFlowVisible"
      @success="handleBatchAddFlowSuccess"
    />

    <!-- 批量停机对话框 -->
    <BatchSuspendDialog
      v-model="batchSuspendVisible"
      @success="handleBatchSuspendSuccess"
    />

    <!-- 批量复机对话框 -->
    <BatchResumeDialog
      v-model="batchResumeVisible"
      @success="handleBatchResumeSuccess"
    />

    <!-- 单卡划拨对话框 -->
    <TransferDialog
      v-model="transferVisible"
      :card="currentCard"
      @success="handleTransferSuccess"
    />

    <!-- 单卡备注对话框 -->
    <RemarkDialog
      v-model="remarkVisible"
      :card="currentCard"
      @success="handleRemarkSuccess"
    />

    <SingleAddFlowDialog
      v-model="singleAddFlowVisible"
      :card="currentCard"
      @success="handleSingleAddFlowSuccess"
    />

    <SingleRenewDialog
      v-model="singleRenewVisible"
      :card="currentCard"
      @success="handleSingleRenewSuccess"
    />

    <CardDiagnosticsDialog
      v-model="diagnosticsVisible"
      :card="currentCard"
    />

    <el-dialog
      v-model="actionDialogVisible"
      :title="actionDialogTitle"
      width="300px"
      :close-on-click-modal="false"
      :close-on-press-escape="!actionDialogProcessing"
      :show-close="!actionDialogProcessing"
      :before-close="handleActionDialogClose"
    >
      <div class="action-dialog">
        <el-icon
          class="action-dialog__icon"
          :class="{
            'is-spinning': actionDialogProcessing,
            'is-success': actionDialogState === 'success',
            'is-danger': actionDialogState === 'failed'
          }"
        >
          <RefreshRight v-if="actionDialogProcessing" />
          <CircleCheckFilled v-else-if="actionDialogState === 'success'" />
          <WarningFilled v-else />
        </el-icon>
        <div class="action-dialog__message">{{ actionDialogMessage }}</div>
      </div>
      <template #footer>
        <el-button v-if="!actionDialogProcessing" type="primary" @click="actionDialogVisible = false">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { CheckboxValueType } from 'element-plus'
import {
  CreditCard,
  CircleCheck,
  Clock,
  WarningFilled,
  Search,
  RefreshLeft,
  Connection,
  Edit,
  Refresh,
  Plus,
  CircleClose,
  Download,
  Filter,
  ArrowDown,
  ArrowUp,
  MoreFilled,
  Setting,
  RefreshRight,
  CircleCheckFilled
} from '@element-plus/icons-vue'
import { cardApi } from '@/api'
import { userApi } from '@/api'
import { useAuthStore } from '@/stores/modules/auth'
import type { Card, CardListParams, CardStats, SortOrder } from '@/types/card'
import type { User } from '@/types/user'
import {
  CARRIER_MAP,
  CARRIER_OPTIONS,
  CARD_MATERIAL_MAP,
  CARD_STATUS_MAP,
  CARD_STATUS_OPTIONS,
  PERIOD_TYPE_MAP,
  PERIOD_TYPE_OPTIONS
} from '@/constants/card'
import { formatFlow, formatFlowValue, formatDate, formatUsagePercent, isExpired } from '@/utils/formatter'
import BatchQueryDialog from './components/BatchQueryDialog.vue'
import BatchTransferDialog from './components/BatchTransferDialog.vue'
import BatchRemarkDialog from './components/BatchRemarkDialog.vue'
import BatchRenewDialog from './components/BatchRenewDialog.vue'
import BatchAddFlowDialog from './components/BatchAddFlowDialog.vue'
import BatchSuspendDialog from './components/BatchSuspendDialog.vue'
import BatchResumeDialog from './components/BatchResumeDialog.vue'
import SingleAddFlowDialog from './components/SingleAddFlowDialog.vue'
import SingleRenewDialog from './components/SingleRenewDialog.vue'
import TransferDialog from './components/TransferDialog.vue'
import RemarkDialog from './components/RemarkDialog.vue'
import ExportHistoryDialog from './components/ExportHistoryDialog.vue'
import CardDiagnosticsDialog from './components/CardDiagnosticsDialog.vue'

type DraggableColumnKey =
  | 'imsi'
  | 'msisdn'
  | 'material'
  | 'diagnostic'
  | 'refresh'
  | 'card_type'
  | 'carrier'
  | 'status'
  | 'data_used_month'
  | 'data_total'
  | 'data_used'
  | 'flow_usage'
  | 'flow_size'
  | 'test_expire_date'
  | 'silent_expire_date'
  | 'activated_at'
  | 'stock_out_date'
  | 'expired_at'
  | 'is_pool_member'
  | 'related_user_name'
  | 'remark'

interface DraggableColumnConfig {
  key: DraggableColumnKey
  label: string
  prop?: string
  width?: number
  minWidth?: number
  align?: 'left' | 'center' | 'right'
  showOverflowTooltip?: boolean
  sortField?: string
}

const COLUMN_ORDER_STORAGE_KEY = 'card-list-column-order'
const COLUMN_VISIBILITY_STORAGE_KEY = 'card-list-visible-columns'
const DEFAULT_DRAGGABLE_COLUMN_ORDER: DraggableColumnKey[] = [
  'imsi',
  'msisdn',
  'material',
  'diagnostic',
  'refresh',
  'card_type',
  'carrier',
  'status',
  'data_used_month',
  'data_total',
  'data_used',
  'flow_usage',
  'flow_size',
  'test_expire_date',
  'silent_expire_date',
  'activated_at',
  'stock_out_date',
  'expired_at',
  'is_pool_member',
  'related_user_name',
  'remark'
]

const DRAGGABLE_COLUMN_MAP: Record<DraggableColumnKey, DraggableColumnConfig> = {
  imsi: { key: 'imsi', label: 'IMSI', prop: 'imsi', width: 180, sortField: 'imsi' },
  msisdn: { key: 'msisdn', label: '号码', prop: 'msisdn', width: 130, sortField: 'msisdn' },
  material: { key: 'material', label: '材质', prop: 'material_name', width: 160, sortField: 'material' },
  diagnostic: { key: 'diagnostic', label: '诊断', width: 90, align: 'center' },
  refresh: { key: 'refresh', label: '刷新', width: 90, align: 'center' },
  card_type: { key: 'card_type', label: '卡片类型', prop: 'card_type', width: 110, sortField: 'card_type' },
  carrier: { key: 'carrier', label: '运营商', prop: 'carrier', width: 100, sortField: 'carrier' },
  status: { key: 'status', label: '状态', prop: 'status', width: 100, sortField: 'status' },
  data_used_month: { key: 'data_used_month', label: '本月用量', width: 120, sortField: 'data_used_month' },
  data_total: { key: 'data_total', label: '套餐总量', width: 120, sortField: 'data_total' },
  data_used: { key: 'data_used', label: '已用量', width: 120, sortField: 'data_used' },
  flow_usage: { key: 'flow_usage', label: '流量使用', width: 200 },
  flow_size: { key: 'flow_size', label: '套餐规格', width: 120, sortField: 'flow_size' },
  test_expire_date: { key: 'test_expire_date', label: '测试期', prop: 'test_expire_date', width: 110, sortField: 'test_expire_date' },
  silent_expire_date: { key: 'silent_expire_date', label: '沉默期', prop: 'silent_expire_date', width: 110, sortField: 'silent_expire_date' },
  activated_at: { key: 'activated_at', label: '激活日期', prop: 'activated_at', width: 110, sortField: 'activated_at' },
  stock_out_date: { key: 'stock_out_date', label: '出库日期', prop: 'stock_out_at', width: 110, sortField: 'stock_out_date' },
  expired_at: { key: 'expired_at', label: '到期日期', prop: 'expired_at', width: 110, sortField: 'expired_at' },
  is_pool_member: { key: 'is_pool_member', label: '流量池', width: 100, sortField: 'is_pool_member' },
  related_user_name: { key: 'related_user_name', label: '关联用户', prop: 'related_user_name', width: 140, showOverflowTooltip: true },
  remark: { key: 'remark', label: '备注', prop: 'remark', minWidth: 150, showOverflowTooltip: true, sortField: 'remark' }
}

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// 数据
const loading = ref(false)
const cardList = ref<Card[]>([])
const selectedCards = ref<Card[]>([])
const currentCard = ref<Card | null>(null)
const refreshingMap = ref<Record<number, boolean>>({})
const isBatchQueryMode = ref(false)
const batchQueryIccids = ref<string[]>([])
const batchQueryNotFound = ref<string[]>([])
const actionDialogVisible = ref(false)
const actionDialogState = ref<'processing' | 'success' | 'failed'>('processing')
const actionDialogTitle = ref('正在操作')
const actionDialogMessage = ref('正在处理，请稍候')
const showAdvanced = ref(false)
const customerLoading = ref(false)
const customerList = ref<User[]>([])
const stockOutRange = ref<string[]>([])
const activatedRange = ref<string[]>([])
const expiredRange = ref<string[]>([])
const columnOrder = ref<DraggableColumnKey[]>([...DEFAULT_DRAGGABLE_COLUMN_ORDER])
const visibleColumnKeys = ref<DraggableColumnKey[]>([...DEFAULT_DRAGGABLE_COLUMN_ORDER])
const sortState = reactive<{
  sort_by?: string
  sort_order: SortOrder
}>({
  sort_by: undefined,
  sort_order: 'desc'
})
const dragState = reactive<{
  draggingKey: DraggableColumnKey | ''
  overKey: DraggableColumnKey | ''
  dropPosition: 'before' | 'after'
}>({
  draggingKey: '',
  overKey: '',
  dropPosition: 'before'
})

// 统计数据
const stats = ref<CardStats>({
  total: 0,
  stock: 0,
  testing: 0,
  silent: 0,
  activated: 0,
  expired: 0,
  suspended: 0,
  cancelled: 0,
  by_carrier: {
    cmcc: 0,
    cucc: 0,
    ctcc: 0
  }
})

const actionDialogProcessing = computed(() => actionDialogState.value === 'processing')
const restartPollIntervalMs = 5000
const restartMaxPollAttempts = 72

const openActionDialog = (title: string, message: string) => {
  actionDialogTitle.value = title
  actionDialogMessage.value = message
  actionDialogState.value = 'processing'
  actionDialogVisible.value = true
}

const finishActionDialog = (success: boolean, message: string, title?: string) => {
  actionDialogState.value = success ? 'success' : 'failed'
  actionDialogTitle.value = title || '操作结果'
  actionDialogMessage.value = message
}

const getRestartFailureMessage = (error: unknown) => {
  const rawMessage = error instanceof Error ? error.message : String(error || '')
  const message = rawMessage.trim()
  if (!message) return '重启失败，请手动复机'
  if (message.includes('timeout') || message.includes('exceeded') || message.includes('Network Error')) {
    return '重启失败，请手动复机'
  }
  return message
}
const getCarrierLimitNotice = (carrier?: string) => carrier === 'cmcc' ? '移动卡单日不可超2次停复机操作' : ''

const handleActionDialogClose = (done: () => void) => {
  if (actionDialogProcessing.value) return
  done()
}

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

const waitForRestartCompletion = async (cardId: number, initialStatus?: string) => {
  let seenSuspended = initialStatus === 'suspended'

  for (let attempt = 0; attempt < restartMaxPollAttempts; attempt += 1) {
    await sleep(restartPollIntervalMs)
    const latestCard = await cardApi.getDetail(cardId)
    const currentStatus = String(latestCard?.status || '')

    if (currentStatus === 'suspended') {
      seenSuspended = true
      continue
    }

    if (seenSuspended && currentStatus) {
      return true
    }
  }

  return false
}

// 搜索表单
const searchForm = reactive<CardListParams>({
  keyword: '',
  status: undefined,
  carrier: undefined,
  period_type: undefined,
  is_pool_member: undefined,
  over_usage: undefined,
  remark: undefined,
  customer_id: undefined,
  batch_id: undefined
})

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 对话框显示状态
const batchQueryVisible = ref(false)
const batchTransferVisible = ref(false)
const batchRemarkVisible = ref(false)
const batchRenewVisible = ref(false)
const batchAddFlowVisible = ref(false)
const batchSuspendVisible = ref(false)
const batchResumeVisible = ref(false)
const transferVisible = ref(false)
const remarkVisible = ref(false)
const singleAddFlowVisible = ref(false)
const singleRenewVisible = ref(false)
const exportHistoryVisible = ref(false)
const diagnosticsVisible = ref(false)

// 计算属性
const isSuperAdmin = computed(() => authStore.userInfo?.user_level === 1)
const getCarrierLabel = (carrier: any) => CARRIER_MAP[carrier as keyof typeof CARRIER_MAP] || '-'
const getStatusMeta = (status: any) => CARD_STATUS_MAP[status as keyof typeof CARD_STATUS_MAP] || CARD_STATUS_MAP.stock
const getPeriodLabel = (periodType: any) => PERIOD_TYPE_MAP[periodType as keyof typeof PERIOD_TYPE_MAP] || '-'
const exportHistoryCardIds = computed(() => {
  if (selectedCards.value.length > 0) {
    return selectedCards.value.map(card => card.id)
  }
  if (isBatchQueryMode.value) {
    return cardList.value.map(card => card.id)
  }
  return []
})
const exportHistoryCount = computed(() => {
  if (selectedCards.value.length > 0) {
    return selectedCards.value.length
  }
  if (isBatchQueryMode.value) {
    return cardList.value.length
  }
  return pagination.total
})
const exportHistoryScopeLabel = computed(() => {
  if (selectedCards.value.length > 0) {
    return '已勾选卡片'
  }
  if (isBatchQueryMode.value) {
    return '当前批量查询结果'
  }
  return '当前筛选结果'
})
const exportHistoryFilterParams = computed(() => ({
  ...searchForm,
  stock_out_start: stockOutRange.value?.[0] || undefined,
  stock_out_end: stockOutRange.value?.[1] || undefined,
  activated_start: activatedRange.value?.[0] || undefined,
  activated_end: activatedRange.value?.[1] || undefined,
  expired_start: expiredRange.value?.[0] || undefined,
  expired_end: expiredRange.value?.[1] || undefined
}))
const allDraggableColumns = computed(() =>
  columnOrder.value
    .map(key => DRAGGABLE_COLUMN_MAP[key])
    .filter(Boolean)
)
const orderedColumns = computed(() =>
  allDraggableColumns.value.filter(column => visibleColumnKeys.value.includes(column.key))
)

const getDisplayTotal = (card: Card) => {
  const total = Number(card.data_total || 0)
  const specTotal = Number(card.flow_size || 0)
  if (card.period_type === 'monthly' && specTotal > total) {
    return specTotal
  }
  return total
}

const normalizeCardList = (cards: Card[]) =>
  cards.map((card: Card) => ({
    ...card,
    usage_percent: formatUsagePercent(card.data_used, getDisplayTotal(card))
  }))

const getSortComparableValue = (card: Card, sortBy: string) => {
  switch (sortBy) {
    case 'data_total':
      return getDisplayTotal(card)
    case 'stock_out_date':
      return card.stock_out_at || card.stock_out_date || ''
    case 'is_pool_member':
      return card.is_pool_member ? 1 : 0
    default:
      return (card as Record<string, any>)[sortBy]
  }
}

const sortBatchQueryList = () => {
  if (!isBatchQueryMode.value || !sortState.sort_by) {
    return
  }

  const sortBy = sortState.sort_by
  const order = sortState.sort_order
  const multiplier = order === 'asc' ? 1 : -1

  cardList.value = [...cardList.value].sort((a, b) => {
    const aValue = getSortComparableValue(a, sortBy)
    const bValue = getSortComparableValue(b, sortBy)

    if (aValue == null || aValue === '') {
      return bValue == null || bValue === '' ? 0 : 1
    }
    if (bValue == null || bValue === '') {
      return -1
    }

    if (typeof aValue === 'number' && typeof bValue === 'number') {
      return (aValue - bValue) * multiplier
    }

    return String(aValue).localeCompare(String(bValue), 'zh-CN', { numeric: true }) * multiplier
  })
}

const isSortActive = (field: string, order: SortOrder) => (
  sortState.sort_by === field && sortState.sort_order === order
)

const saveColumnOrder = () => {
  localStorage.setItem(COLUMN_ORDER_STORAGE_KEY, JSON.stringify(columnOrder.value))
}

const saveVisibleColumns = () => {
  localStorage.setItem(COLUMN_VISIBILITY_STORAGE_KEY, JSON.stringify(visibleColumnKeys.value))
}

const loadColumnOrder = () => {
  const saved = localStorage.getItem(COLUMN_ORDER_STORAGE_KEY)
  if (!saved) {
    return
  }

  try {
    const parsed = JSON.parse(saved)
    if (!Array.isArray(parsed)) {
      return
    }

    const valid = parsed.filter((key): key is DraggableColumnKey =>
      DEFAULT_DRAGGABLE_COLUMN_ORDER.includes(key as DraggableColumnKey)
    )

    if (!valid.length) {
      return
    }

    const missing = DEFAULT_DRAGGABLE_COLUMN_ORDER.filter(key => !valid.includes(key))
    columnOrder.value = [...valid, ...missing]
  } catch (error) {
    console.error('加载列顺序失败:', error)
  }
}

const loadVisibleColumns = () => {
  const saved = localStorage.getItem(COLUMN_VISIBILITY_STORAGE_KEY)
  if (!saved) {
    return
  }

  try {
    const parsed = JSON.parse(saved)
    if (!Array.isArray(parsed)) {
      return
    }

    const valid = parsed.filter((key): key is DraggableColumnKey =>
      DEFAULT_DRAGGABLE_COLUMN_ORDER.includes(key as DraggableColumnKey)
    )

    const missing = DEFAULT_DRAGGABLE_COLUMN_ORDER.filter(key => !valid.includes(key))
    visibleColumnKeys.value = [...valid, ...missing]
  } catch (error) {
    console.error('加载显示列配置失败:', error)
  }
}

const handleVisibleColumnsChange = (value: CheckboxValueType[]) => {
  visibleColumnKeys.value = value.filter((key): key is DraggableColumnKey =>
    DEFAULT_DRAGGABLE_COLUMN_ORDER.includes(key as DraggableColumnKey)
  )
  saveVisibleColumns()
}

const resetVisibleColumns = () => {
  visibleColumnKeys.value = [...DEFAULT_DRAGGABLE_COLUMN_ORDER]
  saveVisibleColumns()
}

const handleColumnDragStart = (key: DraggableColumnKey, event: DragEvent) => {
  dragState.draggingKey = key
  dragState.overKey = ''
  dragState.dropPosition = 'before'
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', key)
  }
}

const handleColumnDragOver = (targetKey: DraggableColumnKey, event: DragEvent) => {
  if (!dragState.draggingKey || dragState.draggingKey === targetKey) {
    return
  }

  event.preventDefault()
  const target = event.currentTarget as HTMLElement | null
  if (!target) {
    return
  }

  const rect = target.getBoundingClientRect()
  const midpoint = rect.left + rect.width / 2
  dragState.overKey = targetKey
  dragState.dropPosition = event.clientX < midpoint ? 'before' : 'after'
}

const handleColumnDrop = (targetKey: DraggableColumnKey, event: DragEvent) => {
  event.preventDefault()
  const draggingKey = dragState.draggingKey
  if (!draggingKey || draggingKey === targetKey) {
    handleColumnDragEnd()
    return
  }

  const currentOrder = [...columnOrder.value]
  const fromIndex = currentOrder.indexOf(draggingKey)
  const targetIndex = currentOrder.indexOf(targetKey)

  if (fromIndex === -1 || targetIndex === -1) {
    handleColumnDragEnd()
    return
  }

  currentOrder.splice(fromIndex, 1)
  let insertIndex = currentOrder.indexOf(targetKey)
  if (dragState.dropPosition === 'after') {
    insertIndex += 1
  }
  currentOrder.splice(insertIndex, 0, draggingKey)
  columnOrder.value = currentOrder
  saveColumnOrder()
  handleColumnDragEnd()
}

const handleColumnDragEnd = () => {
  dragState.draggingKey = ''
  dragState.overKey = ''
  dragState.dropPosition = 'before'
}

const handleColumnSort = (field: string, order: SortOrder) => {
  sortState.sort_by = field
  sortState.sort_order = order
  pagination.page = 1

  if (isBatchQueryMode.value) {
    sortBatchQueryList()
    return
  }

  fetchCardList()
}

// 获取卡片列表
const fetchCardList = async () => {
  loading.value = true
  try {
    const params: CardListParams = {
      page: pagination.page,
      page_size: pagination.page_size,
      ...searchForm,
      stock_out_start: stockOutRange.value?.[0] || undefined,
      stock_out_end: stockOutRange.value?.[1] || undefined,
      activated_start: activatedRange.value?.[0] || undefined,
      activated_end: activatedRange.value?.[1] || undefined,
      expired_start: expiredRange.value?.[0] || undefined,
      expired_end: expiredRange.value?.[1] || undefined,
      sort_by: sortState.sort_by,
      sort_order: sortState.sort_order
    }
    
    const response: any = await cardApi.getList(params)
    
    cardList.value = normalizeCardList(response.items || [])
    
    pagination.total = response.total
  } catch (error) {
    console.error('获取卡片列表失败:', error)
  } finally {
    loading.value = false
  }
}

const refreshCurrentList = async () => {
  if (isBatchQueryMode.value && batchQueryIccids.value.length > 0) {
    const result = await cardApi.batchQuery({ iccids: batchQueryIccids.value })
    batchQueryNotFound.value = result.not_found
    cardList.value = normalizeCardList(result.found)
    pagination.total = result.found.length
    pagination.page = 1
    sortBatchQueryList()
    return
  }

  await fetchCardList()
}

// 获取统计数据
const fetchStats = async () => {
  try {
    stats.value = await cardApi.getStats()
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

// 搜索客户
const searchCustomers = async (query: string) => {
  customerLoading.value = true
  try {
    const response = await userApi.getList({
      keyword: query || undefined,
      page: 1,
      page_size: 50
    })
    customerList.value = response.list
  } catch (error) {
    console.error('搜索客户失败:', error)
  } finally {
    customerLoading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchCardList()
}

// 重置
const handleReset = () => {
  Object.assign(searchForm, {
    keyword: '',
    status: undefined,
    carrier: undefined,
    period_type: undefined,
    is_pool_member: undefined,
    remark: undefined,
    customer_id: undefined,
    batch_id: undefined
  })
  stockOutRange.value = []
  activatedRange.value = []
  expiredRange.value = []
  handleSearch()
}

// 分页变化
const handlePageChange = (page: number) => {
  pagination.page = page
  fetchCardList()
}

const handleSizeChange = (size: number) => {
  pagination.page_size = size
  pagination.page = 1
  fetchCardList()
}

// 选择变化
const handleSelectionChange = (selection: Card[]) => {
  selectedCards.value = selection
}

// 清空选择
const clearSelection = () => {
  selectedCards.value = []
}

// 查看详情
const viewDetail = (id: number) => {
  router.push(`/cards/detail/${id}`)
}

// 显示批量查询对话框
const showBatchQueryDialog = () => {
  batchQueryVisible.value = true
}

// 显示批量划拨对话框
const showBatchTransferDialog = () => {
  batchTransferVisible.value = true
}

// 显示导出历史用量对话框
const showExportHistoryDialog = () => {
  if (exportHistoryCount.value === 0) {
    ElMessage.warning('当前没有可导出的卡片')
    return
  }
  exportHistoryVisible.value = true
}

// 显示批量备注对话框
const showBatchRemarkDialog = () => {
  batchRemarkVisible.value = true
}

// 显示批量续费对话框
const showBatchRenewDialog = () => {
  batchRenewVisible.value = true
}

// 显示批量补量对话框
const showBatchAddFlowDialog = () => {
  batchAddFlowVisible.value = true
}

// 显示批量停机对话框
const showBatchSuspendDialog = () => {
  batchSuspendVisible.value = true
}

// 显示批量复机对话框
const showBatchResumeDialog = () => {
  batchResumeVisible.value = true
}

// 导出
const handleExport = async () => {
  try {
    const params = {
      ...exportHistoryFilterParams.value,
      card_ids: exportHistoryCardIds.value.length > 0 ? exportHistoryCardIds.value : undefined
    }

    const blob = await cardApi.export(params)

    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `卡片列表_${new Date().getTime()}.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)

    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
  }
}

const goPurchaseRecords = () => {
  router.push('/records/purchases')
}

// 显示单卡划拨对话框
const showTransferDialog = (card: Card) => {
  currentCard.value = card
  transferVisible.value = true
}

// 显示单卡备注对话框
const showRemarkDialog = (card: Card) => {
  currentCard.value = card
  remarkVisible.value = true
}

// 单行补量
const handleRowAddFlow = (card: Card) => {
  currentCard.value = card
  singleAddFlowVisible.value = true
}

const handleRowRenew = (card: Card) => {
  currentCard.value = card
  singleRenewVisible.value = true
}

const showDiagnosticsDialog = (card: Card) => {
  currentCard.value = card
  diagnosticsVisible.value = true
}

const handleRowRefresh = async (card: Card) => {
  if (!card.iccid) {
    ElMessage.warning('当前卡片缺少 ICCID，无法刷新')
    return
  }

  refreshingMap.value = {
    ...refreshingMap.value,
    [card.id]: true
  }

  try {
    const result = await cardApi.syncSingleCard(card.iccid)
    const changedFields = result.changed_fields || []
    if (result.changed) {
      ElMessage.success(
        changedFields.length
          ? `卡片 ${card.iccid} 已同步，更新字段：${changedFields.join('、')}`
          : `卡片 ${card.iccid} 已同步并更新`
      )
    } else {
      ElMessage.info(`卡片 ${card.iccid} 已同步，供应商数据无变化`)
    }

    await Promise.all([
      refreshCurrentList(),
      fetchStats()
    ])
  } catch (error) {
    console.error('单卡刷新失败:', error)
    ElMessage.error('刷新失败，请稍后重试')
  } finally {
    refreshingMap.value = {
      ...refreshingMap.value,
      [card.id]: false
    }
  }
}

const handleRowAction = (command: string, card: Card) => {
  switch (command) {
    case 'detail':
      viewDetail(card.id)
      break
    case 'transfer':
      showTransferDialog(card)
      break
    case 'remark':
      showRemarkDialog(card)
      break
    case 'renew':
      handleRowRenew(card)
      break
    case 'addFlow':
      if (card.card_type === 'single') {
        handleRowAddFlow(card)
      }
      break
    case 'resume':
      if (card.status === 'suspended') {
        handleRowResume(card)
      }
      break
    case 'restart':
      if (['activated', 'testing', 'silent', 'suspended'].includes(card.status)) {
        handleRowRestart(card)
      }
      break
    case 'forceResume':
      if (card.status === 'suspended' && isSuperAdmin.value) {
        handleRowForceResume(card)
      }
      break
    default:
      break
  }
}

// 单行复机
const handleRowResume = async (card: Card) => {
  try {
    await ElMessageBox.confirm(
      getCarrierLimitNotice(card.carrier)
        ? `确定要复机卡片 ${card.iccid} 吗？\n\n提示：${getCarrierLimitNotice(card.carrier)}`
        : `确定要复机卡片 ${card.iccid} 吗？`,
      '复机确认',
      {
        confirmButtonText: '确定复机',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    openActionDialog('正在复机', '正在提交复机操作，请稍候')
    const result = await cardApi.batchResumeByIccids({
      iccids: [card.iccid]
    })

    if (result.success > 0) {
      await Promise.all([refreshCurrentList(), fetchStats()])
      finishActionDialog(true, '复机成功', '复机结果')
    } else {
      const firstError = result.failed_list?.[0]?.error || '复机失败'
      finishActionDialog(
        false,
        firstError.includes('超级管理员手动停卡') ? '该卡由超级管理员手动停卡，请联系管理员处理' : firstError,
        '复机结果'
      )
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('单行复机失败:', error)
      finishActionDialog(false, error?.message || '复机失败，请稍后重试', '复机结果')
    }
  }
}

const handleRowRestart = async (card: Card) => {
  try {
    await ElMessageBox.confirm(
      getCarrierLimitNotice(card.carrier)
        ? `确定要重启卡片 ${card.iccid} 吗？系统会执行停机后再复机。\n\n提示：${getCarrierLimitNotice(card.carrier)}`
        : `确定要重启卡片 ${card.iccid} 吗？系统会执行停机后再复机。`,
      '重启确认',
      {
        confirmButtonText: '确定重启',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    openActionDialog('正在重启', '正在操作，请稍候')
    const result = await cardApi.restartCard(card.id)
    if (result.status === 'processing') {
      const success = await waitForRestartCompletion(card.id, card.status)
      await Promise.all([refreshCurrentList(), fetchStats()])
      finishActionDialog(success, success ? '重启成功' : '重启失败，请手动复机', '重启结果')
    } else {
      await Promise.all([refreshCurrentList(), fetchStats()])
      finishActionDialog(true, result.message || '重启成功', '重启结果')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('单行重启失败:', error)
      finishActionDialog(false, getRestartFailureMessage(error), '重启结果')
    }
  }
}

// 单行强制复机
const handleRowForceResume = async (card: Card) => {
  try {
    await ElMessageBox.confirm(
      `确定要强制复机卡片 ${card.iccid} 吗？该操作会绕过人工停卡与超限限制。`,
      '强制复机确认',
      {
        confirmButtonText: '确认强制复机',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const result = await cardApi.batchForceResumeByIccids({
      iccids: [card.iccid]
    })

    if (result.success > 0) {
      ElMessage.success('强制复机成功')
      refreshCurrentList()
      fetchStats()
    } else {
      ElMessage.error(result.failed_list?.[0]?.error || '强制复机失败')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('单行强制复机失败:', error)
    }
  }
}

// 批量查询成功回调
const handleBatchQuerySuccess = (data: { found: Card[]; not_found: string[]; iccids: string[] }) => {
  isBatchQueryMode.value = true
  batchQueryIccids.value = data.iccids
  batchQueryNotFound.value = data.not_found
  cardList.value = normalizeCardList(data.found)
  pagination.total = data.found.length
  pagination.page = 1
  sortBatchQueryList()
}

// 清除批量查询筛选
const clearBatchQuery = () => {
  isBatchQueryMode.value = false
  batchQueryIccids.value = []
  batchQueryNotFound.value = []
  fetchCardList()
}

// 批量划拨成功回调
const handleBatchTransferSuccess = () => {
  clearSelection()
  refreshCurrentList()
  fetchStats()
}

// 批量备注成功回调
const handleBatchRemarkSuccess = () => {
  clearSelection()
  refreshCurrentList()
}

// 批量续费成功回调
const handleBatchRenewSuccess = () => {
  clearSelection()
  refreshCurrentList()
}

// 批量补量成功回调
const handleBatchAddFlowSuccess = () => {
  clearSelection()
  refreshCurrentList()
  fetchStats()
}

// 批量停机成功回调
const handleBatchSuspendSuccess = () => {
  clearSelection()
  refreshCurrentList()
  fetchStats()
}

// 批量复机成功回调
const handleBatchResumeSuccess = () => {
  clearSelection()
  refreshCurrentList()
  fetchStats()
}

// 单卡划拨成功回调
const handleTransferSuccess = () => {
  refreshCurrentList()
  fetchStats()
}

// 单卡备注成功回调
const handleRemarkSuccess = () => {
  refreshCurrentList()
}

const handleSingleAddFlowSuccess = () => {
  refreshCurrentList()
  fetchStats()
}

const handleSingleRenewSuccess = () => {
  refreshCurrentList()
  fetchStats()
}

// 获取进度条颜色
const getProgressColor = (percent: number) => {
  if (percent >= 90) return '#F56C6C'
  if (percent >= 80) return '#E6A23C'
  return '#67C23A'
}

// 初始化
onMounted(() => {
  loadColumnOrder()
  loadVisibleColumns()

  // 读取 URL 参数
  const carrierParam = route.query.carrier as string
  if (carrierParam) {
    searchForm.carrier = carrierParam as any
  }

  // 到期卡筛选
  const expiringParam = route.query.expiring as string
  if (expiringParam === 'true') {
    const today = new Date()
    const monthStart = new Date(today.getFullYear(), today.getMonth(), 1)
    const monthEnd = new Date(today.getFullYear(), today.getMonth() + 1, 0)
    expiredRange.value = [
      monthStart.toISOString().split('T')[0] || '',
      monthEnd.toISOString().split('T')[0] || ''
    ]
  }

  // 超量卡筛选
  const overUsageParam = route.query.over_usage as string
  if (overUsageParam === 'true') {
    searchForm.over_usage = true
  }

  fetchCardList()
  fetchStats()
})
</script>

<style scoped lang="scss">
.card-list-page {
  padding: 16px 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
  font-size: 14px;
  color: #1d2129;
}

.stats-row {
  margin-bottom: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  transition: all 0.3s;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .stat-icon {
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 10px;
    font-size: 22px;
    margin-right: 14px;

    &.total {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: #fff;
    }

    &.activated {
      background: linear-gradient(135deg, #67C23A 0%, #85ce61 100%);
      color: #fff;
    }

    &.silent {
      background: linear-gradient(135deg, #E6A23C 0%, #f0c78a 100%);
      color: #fff;
    }

    &.suspended {
      background: linear-gradient(135deg, #F56C6C 0%, #f89898 100%);
      color: #fff;
    }
  }

  .stat-content {
    flex: 1;

    .stat-value {
      font-size: 24px;
      font-weight: 600;
      color: #1d2129;
      line-height: 1.2;
      margin-bottom: 4px;
    }

    .stat-label {
      font-size: 13px;
      color: #86909c;
    }
  }
}

.search-card,
.toolbar-card,
.table-card {
  margin-bottom: 12px;
}

.search-card {
  :deep(.el-card__body) {
    padding: 16px 20px 8px;
  }
}

.search-form {
  :deep(.el-form-item) {
    margin-bottom: 10px;
    margin-right: 16px;
  }

  :deep(.el-form-item__label) {
    font-size: 13px;
    color: #4e5969;
    font-weight: 500;
  }

  :deep(.el-input__wrapper),
  :deep(.el-select .el-input__wrapper) {
    height: 36px;
    font-size: 13px;
  }

  &.advanced-form {
    border-top: 1px dashed #e5e6eb;
    padding-top: 12px;
    margin-top: 4px;
  }
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 12px;

  .toolbar-left,
  .toolbar-right {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  :deep(.el-button) {
    font-size: 13px;
    padding: 8px 14px;
  }
}

.column-settings {
  .column-settings-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
  }

  .column-settings-title {
    font-size: 14px;
    font-weight: 600;
    color: #1d2129;
  }

  .column-settings-tip {
    margin-bottom: 12px;
    font-size: 12px;
    color: #86909c;
  }

  .column-checkbox-group {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px 12px;
  }

  :deep(.el-checkbox) {
    margin-right: 0;
  }
}

.selection-info {
  padding: 10px 14px;
  background: #e8f3ff;
  border-radius: 4px;
  color: #165dff;
  font-size: 13px;

  .selection-count {
    font-weight: 600;
    font-size: 14px;
    margin: 0 4px;
  }
}

.row-actions {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;

  :deep(.el-button) {
    margin-left: 0;
    margin-right: 0;
  }

  .more-actions-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 24px;
    padding: 0;
  }
}

.flow-usage {
  .flow-progress-row {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .flow-percent {
    flex-shrink: 0;
    min-width: 54px;
    font-size: 12px;
    color: #4e5969;
    text-align: right;
  }

  :deep(.el-progress) {
    flex: 1;
  }

  .flow-text {
    font-size: 12px;
    color: #86909c;
    margin-top: 2px;
  }
}

.batch-query-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  margin-bottom: 12px;
  background: #fff7e6;
  border: 1px solid #ffe4b5;
  border-radius: 6px;
  font-size: 13px;
  color: #d46b08;

  strong {
    font-size: 14px;
    margin: 0 2px;
  }

  .not-found-info {
    color: #F56C6C;
  }
}

.text-danger {
  color: #F56C6C;
}

.text-muted {
  color: #c9cdd4;
}

.table-card {
  :deep(.el-table) {
    font-size: 13px;

    th.el-table__cell {
      background: #f7f8fa;
      color: #4e5969;
      font-weight: 500;
      font-size: 13px;
      padding: 10px 0;
    }

    td.el-table__cell {
      padding: 8px 0;
      color: #1d2129;
    }

    .el-tag {
      font-size: 12px;
    }
  }

  .sortable-header {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    line-height: 1;
  }

  .draggable-header {
    display: inline-flex;
    align-items: center;
    width: 100%;
    cursor: move;
    user-select: none;
    position: relative;

    &.dragging {
      opacity: 0.45;
    }

    &.drag-over-before::before,
    &.drag-over-after::after {
      content: '';
      position: absolute;
      top: -8px;
      bottom: -8px;
      width: 2px;
      background: #409eff;
    }

    &.drag-over-before::before {
      left: -6px;
    }

    &.drag-over-after::after {
      right: -6px;
    }
  }

  .drag-handle {
    color: #c0c4cc;
    font-size: 12px;
    letter-spacing: -1px;
  }

  .sort-buttons {
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin-top: 1px;
  }

  .sort-icon {
    font-size: 12px;
    color: #c0c4cc;
    cursor: pointer;
    transition: color 0.2s ease;

    &:hover {
      color: #409eff;
    }

    &.active {
      color: #409eff;
    }
  }

  :deep(.el-card__body) {
    padding: 16px 20px;
  }
}

.toolbar-card {
  :deep(.el-card__body) {
    padding: 14px 20px;
  }
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;

  :deep(.el-pagination) {
    font-size: 13px;
  }
}

.action-dialog {
  display: grid;
  justify-items: center;
  gap: 12px;
  padding: 2px 0 6px;
  text-align: center;
}

.action-dialog__icon {
  font-size: 28px;
  color: #2563eb;
}

.action-dialog__icon.is-success {
  color: #16a34a;
}

.action-dialog__icon.is-danger {
  color: #ef4444;
}

.action-dialog__message {
  color: #111827;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.6;
}
</style>
