<template>
  <el-dialog
    v-model="visible"
    title="选择卡片"
    width="1200px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-alert
      v-if="pool"
      :title="`只能选择符合流量池规格的卡片：${CARRIER_MAP[pool.carrier]} | ${formatFlow(pool.flow_size)}/${PERIOD_TYPE_MAP[pool.period_type]} | 卡类型：流量池卡 | 状态：已激活且未加入其他流量池`"
      type="info"
      :closable="false"
      style="margin-bottom: 16px"
    />

    <!-- 搜索栏 -->
    <el-form :model="searchForm" inline style="margin-bottom: 16px">
      <el-form-item label="ICCID/号码">
        <el-input
          v-model="searchForm.keyword"
          placeholder="请输入ICCID或号码"
          clearable
          style="width: 200px"
          @clear="handleSearch"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :icon="Search" @click="handleSearch">
          搜索
        </el-button>
      </el-form-item>
    </el-form>

    <!-- 卡片列表 -->
    <el-table
      ref="tableRef"
      v-loading="loading"
      :data="cardList"
      border
      stripe
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" :reserve-selection="true" />
      <el-table-column prop="iccid" label="ICCID" width="200" />
      <el-table-column prop="msisdn" label="号码" width="130" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusMeta(row.status as CardStatus).type">
            {{ getStatusMeta(row.status as CardStatus).label }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="流量使用" min-width="200">
        <template #default="{ row }">
          {{ formatFlow(row.data_used) }} / {{ formatFlow(row.data_total) }}
          ({{ row.usage_percent }}%)
        </template>
      </el-table-column>
      <el-table-column prop="activated_at" label="激活日期" width="110" />
      <el-table-column prop="expired_at" label="到期日期" width="110" />
    </el-table>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.page_size"
      :total="pagination.total"
      :page-sizes="[10, 20, 50, 100]"
      layout="total, sizes, prev, pager, next, jumper"
      style="margin-top: 16px"
      @size-change="handleSearch"
      @current-change="handleSearch"
    />

    <template #footer>
      <div style="display: flex; justify-content: space-between; align-items: center">
        <span>已选择 {{ selectedCardIds.length }} 张卡片</span>
        <div>
          <el-button @click="handleClose">取消</el-button>
          <el-button type="primary" @click="handleConfirm">
            确定
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage, type ElTable } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { cardApi } from '@/api/modules/card'
import { formatFlow } from '@/utils/formatter'
import { CARRIER_MAP, PERIOD_TYPE_MAP, CARD_STATUS_MAP } from '@/constants/card'
import type { Pool } from '@/types/pool'
import type { Card } from '@/types/card'
import type { CardStatus, CardType } from '@/types/common'

interface Props {
  modelValue: boolean
  pool?: Pool | null
  selectedCards?: any[]
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm', cards: any[]): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const tableRef = ref<InstanceType<typeof ElTable>>()
const loading = ref(false)

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const getStatusMeta = (status: CardStatus) => CARD_STATUS_MAP[status]

// 搜索表单
const searchForm = reactive({
  keyword: ''
})

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 卡片列表
const cardList = ref<Card[]>([])

// 已选择的卡片ID
const selectedCardIds = ref<number[]>([])

// 已选择的卡片
const selectedCardList = ref<Card[]>([])

/**
 * 获取卡片列表
 */
const fetchCardList = async () => {
  if (!props.pool) return

  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      carrier: props.pool.carrier,
      flow_size: props.pool.flow_size,
      period_type: props.pool.period_type,
      status: 'activated' as CardStatus,
      is_pool_member: false,
      card_type: 'pool' as CardType,  // 只查询流量池卡
      keyword: searchForm.keyword || undefined
    }

    const response = await cardApi.getList(params)
    cardList.value = response.list || []
    pagination.total = response.total || 0

    // 恢复已选择的卡片
    if (selectedCardIds.value.length > 0) {
      setTimeout(() => {
        cardList.value.forEach(card => {
          if (selectedCardIds.value.includes(card.id)) {
            tableRef.value?.toggleRowSelection(card, true)
          }
        })
      }, 0)
    }
  } catch (error) {
    console.error('获取卡片列表失败:', error)
    ElMessage.error('获取卡片列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 搜索
 */
const handleSearch = () => {
  pagination.page = 1
  fetchCardList()
}

/**
 * 选择变化
 */
const handleSelectionChange = (selection: Card[]) => {
  selectedCardList.value = selection
  selectedCardIds.value = selection.map(c => c.id)
}

/**
 * 确认选择
 */
const handleConfirm = () => {
  if (selectedCardList.value.length === 0) {
    ElMessage.warning('请至少选择一张卡片')
    return
  }
  emit('confirm', selectedCardList.value)
  handleClose()
}

/**
 * 关闭对话框
 */
const handleClose = () => {
  searchForm.keyword = ''
  pagination.page = 1
  selectedCardIds.value = []
  selectedCardList.value = []
  visible.value = false
}

// 监听对话框打开
watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      // 初始化已选择的卡片
      if (props.selectedCards && props.selectedCards.length > 0) {
        selectedCardIds.value = props.selectedCards.map(c => c.id)
        selectedCardList.value = [...props.selectedCards]
      } else {
        selectedCardIds.value = []
        selectedCardList.value = []
      }
      fetchCardList()
    }
  }
)
</script>

<style scoped lang="scss">
:deep(.el-pagination) {
  justify-content: flex-end;
}
</style>
