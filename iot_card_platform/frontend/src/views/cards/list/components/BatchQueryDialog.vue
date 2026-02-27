<template>
  <el-dialog
    v-model="visible"
    title="批量查询"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="batch-query-dialog">
      <el-alert
        title="批量查询说明"
        type="info"
        :closable="false"
        style="margin-bottom: 16px"
      >
        <template #default>
          <div>支持输入多个ICCID，每行一个或用逗号分隔</div>
          <div>一次最多查询 <strong>10000</strong> 张卡片</div>
          <div>查询结果将直接显示在卡片列表中</div>
        </template>
      </el-alert>

      <el-input
        v-model="iccidText"
        type="textarea"
        :rows="10"
        placeholder="请输入ICCID，每行一个或用逗号分隔&#10;例如：&#10;89860123456789012345&#10;89860123456789012346&#10;89860123456789012347"
      />

      <div class="input-info">
        <span>已输入: <strong>{{ iccidCount }}</strong> 个ICCID</span>
        <span v-if="iccidCount > BATCH_MAX_COUNT" class="error-text">
          超出限制！最多支持 {{ BATCH_MAX_COUNT }} 个
        </span>
      </div>
    </div>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button
        type="primary"
        :loading="loading"
        :disabled="iccidCount === 0 || iccidCount > BATCH_MAX_COUNT"
        @click="handleQuery"
      >
        开始查询
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { cardApi } from '@/api'
import type { Card } from '@/types/card'

const BATCH_MAX_COUNT = 10000

interface Props {
  modelValue: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success', data: { found: Card[]; not_found: string[] }): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const loading = ref(false)
const iccidText = ref('')

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const iccidCount = computed(() => {
  if (!iccidText.value.trim()) return 0
  return parseICCIDs(iccidText.value).length
})

const parseICCIDs = (text: string): string[] => {
  if (!text.trim()) return []
  const lines = text.split(/[\n,]/)
  const iccids = lines.map(line => line.trim()).filter(line => line.length > 0)
  return [...new Set(iccids)]
}

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

    if (result.not_found.length > 0) {
      ElMessage.warning(`查询完成：找到 ${result.found.length} 张，未找到 ${result.not_found.length} 张`)
    } else {
      ElMessage.success(`查询完成：找到 ${result.found.length} 张卡片`)
    }

    emit('success', result)
    handleClose()
  } catch (error) {
    console.error('批量查询失败:', error)
    ElMessage.error('批量查询操作失败')
  } finally {
    loading.value = false
  }
}

const handleClose = () => {
  visible.value = false
}

watch(visible, (newVal) => {
  if (!newVal) {
    setTimeout(() => {
      iccidText.value = ''
    }, 300)
  }
})
</script>

<style scoped lang="scss">
.batch-query-dialog {
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
</style>
