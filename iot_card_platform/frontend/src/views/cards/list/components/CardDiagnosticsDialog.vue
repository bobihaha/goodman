<template>
  <el-dialog
    v-model="visible"
    title="卡片诊断"
    width="420px"
    :close-on-click-modal="false"
    @open="fetchDiagnostics"
  >
    <div v-loading="loading" class="diagnostics-dialog">
      <template v-if="diagnostics">
        <div class="diag-row">
          <span class="diag-label">ICCID</span>
          <span class="diag-value">{{ diagnostics.iccid || '-' }}</span>
        </div>
        <div class="diag-row">
          <span class="diag-label">号码</span>
          <span class="diag-value">{{ diagnostics.msisdn || '-' }}</span>
        </div>
        <div class="diag-row">
          <span class="diag-label">开机状态</span>
          <el-tag :type="getPowerTagType(diagnostics.power_status_msg)">
            {{ diagnostics.power_status_msg || '未知' }}
          </el-tag>
        </div>
        <div class="diag-row">
          <span class="diag-label">工作状态</span>
          <el-tag :type="getWorkTagType(diagnostics.work_status_msg)">
            {{ diagnostics.work_status_msg || '未知' }}
          </el-tag>
        </div>
      </template>
      <el-empty v-else description="暂无诊断数据" :image-size="72" />
    </div>

    <template #footer>
      <el-button @click="visible = false">关闭</el-button>
      <el-button type="primary" :loading="loading" @click="fetchDiagnostics">刷新诊断</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { cardApi } from '@/api'
import type { Card, CardDiagnostics } from '@/types/card'

interface Props {
  modelValue: boolean
  card: Card | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const loading = ref(false)
const diagnostics = ref<CardDiagnostics | null>(null)

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const fetchDiagnostics = async () => {
  if (!props.card?.id) return

  loading.value = true
  try {
    diagnostics.value = await cardApi.getDiagnostics(props.card.id)
  } catch (error) {
    console.error('获取卡片诊断失败:', error)
    diagnostics.value = null
  } finally {
    loading.value = false
  }
}

const getPowerTagType = (status?: string) => {
  if (status === '开机') return 'success'
  if (status === '关机') return 'info'
  return 'warning'
}

const getWorkTagType = (status?: string) => {
  if (status === '在线') return 'success'
  if (status === '离线') return 'danger'
  return 'warning'
}

watch(
  () => props.modelValue,
  (value) => {
    if (!value) {
      diagnostics.value = null
    }
  }
)
</script>

<style scoped lang="scss">
.diagnostics-dialog {
  min-height: 180px;
}

.diag-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.diag-row:last-child {
  border-bottom: none;
}

.diag-label {
  color: #606266;
}

.diag-value {
  color: #303133;
  font-weight: 500;
  word-break: break-all;
  text-align: right;
}
</style>
