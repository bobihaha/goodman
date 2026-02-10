<template>
  <el-dialog
    v-model="visible"
    title="批量查询卡片"
    width="900px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="batch-query-dialog">
      <!-- 输入区域 -->
      <div v-if="!queryResult" class="input-section">
        <el-alert
          title="批量查询说明"
          type="info"
          :closable="false"
          style="margin-bottom: 16px"
        >
          <template #default>
            <div>支持输入多个ICCID，每行一个或用逗号分隔</div>
            <div>一次最多查询 <strong>10000</strong> 个卡号</div>
          </template>
        </el-alert>

        <el-input
          v-model="iccidText"
          type="textarea"
          :rows="12"
          placeholder="请输入ICCID，每行一个或用逗号分隔&#10;例如：&#10;89860123456789012345&#10;89860123456789012346&#10;89860123456789012347"
          @input="handleInput"
        />

        <div class="input-info">
          <span>已输入: <strong>{{ iccidCount }}</strong> 个ICCID</span>
          <span v-if="iccidCount > BATCH_QUERY_MAX_COUNT" class="error-text">
            超出限制！最多支持 {{ BATCH_QUERY_MAX_COUNT }} 个
          </span>
        </div>
      </div>

      <!-- 查询结果 -->
      <div v-else class="result-section">
        <div class="result-summary">
          <el-alert
            :title="`查询完成：找到 ${queryResult.found.length} 张卡片，未找到 ${queryResult.not_found.length} 个ICCID`"
            :type="queryResult.not_found.length > 0 ? 'warning' : 'success'"
            :closable="false"
            style="margin-bottom: 16px"
          />
        </div>

        <!-- 找到的卡片 -->
        <div v-if="queryResult.found.length > 0" class="found-cards">
          <div class="section-title">
            找到的卡片 ({{ queryResult.found.length }})
            <el-button type="text" size="small" @click="handleExportFound">
              <el-icon><Download /></el-icon>
              导出
            </el-button>
          </div>

          <el-table
            :data="queryResult.found"
            max-height="400"
            stripe
          >
            <el-table-column prop="iccid" label="ICCID" width="200" fixed />
            
            <el-table-column prop="msisdn" label="号码" width="130" />

            <el-table-column prop="carrier" label="运营商" width="100">
              <template #default="{ row }">
                {{ CARRIER_MAP[row.carrier] }}
              </template>
            </el-table-column>

            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="CARD_STATUS_MAP[row.status].type" size="small">
                  {{ CARD_STATUS_MAP[row.status].label }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column label="本月用量" width="180">
              <template #default="{ row }">
                <div class="usage-cell">
                  <el-progress
                    :percentage="calculateMonthUsagePercent(row)"
                    :color="getProgressColor(calculateMonthUsagePercent(row))"
                    :stroke-width="8"
                  />
                  <div class="usage-text">
                    {{ formatFlow(row.data_used) }} / {{ formatFlow(row.data_total) }}
                    <span class="usage-percent">({{ calculateMonthUsagePercent(row).toFixed(1) }}%)</span>
                  </div>
                </div>
              </template>
            </el-table-column>

            <el-table-column label="套餐规格" width="120">
              <template #default="{ row }">
                {{ formatFlow(row.flow_size) }}/{{ PERIOD_TYPE_MAP[row.period_type] }}
              </template>
            </el-table-column>

            <el-table-column prop="expired_at" label="到期日期" width="110">
              <template #default="{ row }">
                <span :class="{ 'text-danger': isExpired(row.expired_at) }">
                  {{ formatDateShort(row.expired_at) }}
                </span>
              </template>
            </el-table-column>

            <el-table-column prop="remark" label="备注" min-width="150" show-overflow-tooltip />
          </el-table>
        </div>

        <!-- 未找到的ICCID -->
        <div v-if="queryResult.not_found.length > 0" class="not-found-cards">
          <div class="section-title">
            未找到的ICCID ({{ queryResult.not_found.length }})
            <el-button type="text" size="small" @click="handleCopyNotFound">
              <el-icon><CopyDocument /></el-icon>
              复制
            </el-button>
          </div>

          <div class="not-found-list">
            <el-tag
              v-for="iccid in queryResult.not_found"
              :key="iccid"
              type="danger"
              size="small"
              style="margin: 4px"
            >
              {{ iccid }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div v-if="!queryResult">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          :loading="loading"
          :disabled="iccidCount === 0 || iccidCount > BATCH_QUERY_MAX_COUNT"
          @click="handleQuery"
        >
          查询
        </el-button>
      </div>
      <div v-else>
        <el-button @click="handleReset">重新查询</el-button>
        <el-button type="primary" @click="handleClose">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, CopyDocument } from '@element-plus/icons-vue'
import { cardApi } from '@/api'
import type { Card } from '@/types/card'
import {
  CARRIER_MAP,
  CARD_STATUS_MAP,
  PERIOD_TYPE_MAP,
  BATCH_QUERY_MAX_COUNT
} from '@/constants/card'
import { formatFlow, formatDateShort, isExpired } from '@/utils/formatter'

interface Props {
  modelValue: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 数据
const loading = ref(false)
const iccidText = ref('')
const queryResult = ref<{ found: Card[]; not_found: string[] } | null>(null)

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const iccidCount = computed(() => {
  if (!iccidText.value.trim()) return 0
  
  const iccids = parseICCIDs(iccidText.value)
  return iccids.length
})

// 解析ICCID
const parseICCIDs = (text: string): string[] => {
  if (!text.trim()) return []
  
  // 先按换行分割，再按逗号分割
  const lines = text.split(/[\n,]/)
  
  // 过滤空行和去除空格
  const iccids = lines
    .map(line => line.trim())
    .filter(line => line.length > 0)
  
  // 去重
  return [...new Set(iccids)]
}

// 输入处理
const handleInput = () => {
  // 实时统计数量
}

// 查询
const handleQuery = async () => {
  const iccids = parseICCIDs(iccidText.value)
  
  if (iccids.length === 0) {
    ElMessage.warning('请输入ICCID')
    return
  }
  
  if (iccids.length > BATCH_QUERY_MAX_COUNT) {
    ElMessage.warning(`一次最多查询 ${BATCH_QUERY_MAX_COUNT} 个ICCID`)
    return
  }

  loading.value = true
  try {
    const result = await cardApi.batchQuery({ iccids })
    queryResult.value = result
    
    ElMessage.success(`查询完成：找到 ${result.found.length} 张卡片`)
    emit('success')
  } catch (error) {
    console.error('批量查询失败:', error)
  } finally {
    loading.value = false
  }
}

// 计算本月用量百分比
const calculateMonthUsagePercent = (card: Card): number => {
  if (!card.data_total || card.data_total <= 0) return 0
  
  const percent = (card.data_used / card.data_total) * 100
  return Math.min(Math.max(percent, 0), 100)
}

// 获取进度条颜色
const getProgressColor = (percent: number) => {
  if (percent >= 90) return '#F56C6C'
  if (percent >= 80) return '#E6A23C'
  return '#67C23A'
}

// 导出找到的卡片
const handleExportFound = () => {
  if (!queryResult.value || queryResult.value.found.length === 0) return

  try {
    // 构建CSV内容
    const headers = ['ICCID', '号码', '运营商', '状态', '本月用量(MB)', '总流量(MB)', '使用率(%)', '套餐规格', '到期日期', '备注']
    const rows = queryResult.value.found.map(card => [
      card.iccid,
      card.msisdn || '',
      CARRIER_MAP[card.carrier],
      CARD_STATUS_MAP[card.status].label,
      card.data_used,
      card.data_total,
      calculateMonthUsagePercent(card).toFixed(2),
      `${card.flow_size}MB/${PERIOD_TYPE_MAP[card.period_type]}`,
      card.expired_at || '',
      card.remark || ''
    ])

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n')

    // 添加BOM以支持中文
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `批量查询结果_${new Date().getTime()}.csv`
    link.click()
    window.URL.revokeObjectURL(url)

    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

// 复制未找到的ICCID
const handleCopyNotFound = async () => {
  if (!queryResult.value || queryResult.value.not_found.length === 0) return

  try {
    const text = queryResult.value.not_found.join('\n')
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败')
  }
}

// 重置
const handleReset = () => {
  queryResult.value = null
  iccidText.value = ''
}

// 关闭
const handleClose = () => {
  visible.value = false
}

// 监听对话框关闭，重置数据
watch(visible, (newVal) => {
  if (!newVal) {
    setTimeout(() => {
      handleReset()
    }, 300)
  }
})
</script>

<style scoped lang="scss">
.batch-query-dialog {
  .input-section {
    .input-info {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 12px;
      font-size: 14px;
      color: #606266;

      strong {
        color: #409eff;
        font-size: 16px;
        margin: 0 4px;
      }

      .error-text {
        color: #F56C6C;
        font-weight: 600;
      }
    }
  }

  .result-section {
    .section-title {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 16px;
      font-weight: 600;
      color: #303133;
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 2px solid #DCDFE6;
    }

    .found-cards {
      margin-bottom: 24px;

      .usage-cell {
        .usage-text {
          font-size: 12px;
          color: #606266;
          margin-top: 4px;

          .usage-percent {
            color: #409eff;
            font-weight: 600;
            margin-left: 4px;
          }
        }
      }
    }

    .not-found-cards {
      .not-found-list {
        padding: 12px;
        background: #fef0f0;
        border-radius: 4px;
        max-height: 200px;
        overflow-y: auto;
      }
    }
  }

  .text-danger {
    color: #F56C6C;
  }
}
</style>


