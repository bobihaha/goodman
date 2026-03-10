<template>
  <el-dialog
    v-model="visible"
    title="导出历史用量"
    width="500px"
    @close="handleClose"
  >
    <el-form :model="form" label-width="100px">
      <el-form-item label="月份范围" required>
        <el-date-picker
          v-model="form.dateRange"
          type="monthrange"
          range-separator="至"
          start-placeholder="开始月份"
          end-placeholder="结束月份"
          style="width: 100%"
        />
      </el-form-item>
      <el-form-item label="卡片数量">
        <span>{{ cardIds.length }} 张</span>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleExport">
        导出
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { cardApi } from '@/api'
import * as XLSX from 'xlsx'

interface Props {
  modelValue: boolean
  cardIds: number[]
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue'])

const visible = ref(false)
const loading = ref(false)
const form = ref({
  dateRange: [] as Date[]
})

watch(() => props.modelValue, (val) => {
  visible.value = val
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

const handleClose = () => {
  visible.value = false
  form.value.dateRange = []
}

const handleExport = async () => {
  if (!form.value.dateRange || form.value.dateRange.length !== 2) {
    ElMessage.warning('请选择日期范围')
    return
  }

  loading.value = true
  try {
    const startDate = formatDate(form.value.dateRange[0])
    const endDate = formatDate(form.value.dateRange[1])

    const data = await cardApi.exportHistory(props.cardIds, startDate, endDate)

    if (data.length === 0) {
      ElMessage.warning('没有数据可导出')
      return
    }

    const ws = XLSX.utils.json_to_sheet(data)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, '历史用量')
    XLSX.writeFile(wb, `卡片历史用量_${startDate}_${endDate}.xlsx`)

    ElMessage.success('导出成功')
    handleClose()
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  } finally {
    loading.value = false
  }
}

const formatDate = (date: Date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
</script>
