<template>
  <el-dialog
    v-model="visible"
    title="批量查询"
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
            <div>一次最多查询 <strong>10000</strong> 张卡片</div>
          </template>
        </el-alert>

        <el-input
          v-model="iccidText"
          type="textarea"
          :rows="10"
          placeholder="请输入ICCID，每行一个或用逗号分隔&#10;例如：&#10;89860123456789012345&#10;89860123456789012346&#10;89860123456789012347"
          @input="handleInput"
        />

        <div class="input-info">
          <span>已输入: <strong>{{ iccidCount }}</strong> 个ICCID</span>
          <span v-if="iccidCount > BATCH_MAX_COUNT" class="error-text">
            超出限制！最多支持 {{ BATCH_MAX_COUNT }} 个
          </span>
        </div>
      </div>

      <!-- 查询结果 -->
      <div v-else class="result-section">
        <div class="result-summary">
          <el-alert
            :title="`查询完成：找到 ${queryResult.found.length} 张，未找到 ${queryResult.not_found.length} 张`"
            :type="queryResult.not_found.length > 0 ? 'warning' : 'success'"
            :closable="false"
            style="margin-bottom: 16px"
          />
        </div>

        <!-- 找到的卡片 -->
        <div v-if="queryResult.found.length > 0" class="found-cards">
          <div class="section-title">
            找到的卡片 ({{ queryResult.found.length }})
          </div>

          <el-table
            :data="queryResult.found"
            max-height="400"
            stripe
          >
            <el-table-column prop="iccid" label="ICCID" width="200" />
            <el-table-column prop="msisdn" label="号码" width="130" />
            <el-table-column prop="carrier_name" label="运营商" width="100" />
            <el-table-column prop="status_name" label="状态" width="100" />
            <el-table-column label="流量使用" width="180">
              <template #default="{ row }">
                {{ formatFlow(row.data_used) }} / {{ formatFlow(row.data_total) }}
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
              复制ICCID
            </el-button>
          </div>

          <el-table
            :data="notFoundTableData"
            max-height="300"
            stripe
          >
            <el-table-column prop="iccid" label="ICCID" width="200" />
            <el-table-column label="说明" min-width="300">
              <template #default>
                <span class="error-text">卡片不存在或无权查看</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>

    <template #footer>
      <div v-if="!queryResult">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          :loading="loading"
          :disabled="iccidCount === 0 || iccidCount > BATCH_MAX_COUNT"
          @click="handleQuery"
        >
          开始查询
        </el-button>
      </div>
      <div v-else>
        <el-button @click="handleReset">继续查询</el-button>
        <el-button type="primary" @click="handleClose">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { CopyDocument } from '@element-plus/icons-vue'
import { cardApi } from '@/api'
import { formatFlow } from '@/utils/formatter'

const BATCH_MAX_COUNT = 10000

interface Props {
  modelValue: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

interface QueryResult {
  found: any[]
  not_found: string[]
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 数据
const loading = ref(false)
const iccidText = ref('')
const queryResult = ref<QueryResult | null>(null)

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

const notFoundTableData = computed(() => {
  if (!queryResult.value) return []
  return queryResult.value.not_found.map(iccid => ({ iccid }))
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

// 查询操作
const handleQuery = async () => {
  const iccids = parseICCIDs(iccidText.value)
  
  if (iccids.length === 0) {
    ElMessage.warning('请输入ICCID')
    return
  }
  
  if (iccids.length > BATCH_MAX_COUNT) {
    ElMessage.warning(`一次最多查询 ${BATCH_MAX_COUNT} 张卡片`)
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
    ElMessage.error('批量查询操作失败')
  } finally {
    loading.value = false
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
    }

    .not-found-cards {
      .error-text {
        color: #F56C6C;
      }
    }
  }
}
</style>
