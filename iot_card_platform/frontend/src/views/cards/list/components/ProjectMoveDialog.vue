<template>
  <el-dialog v-model="visible" title="项目转移" width="680px" :close-on-click-modal="false"
    :close-on-press-escape="!loading" :show-close="!loading" @closed="reset">
    <template v-if="!result">
      <el-alert type="info" :closable="false" :title="`操作范围：${sourceLabel}。仅可调整自己账号的卡片。`" />
      <p v-if="initialIccids.length">已选择 {{ initialIccids.length }} 张卡片</p>
      <el-input v-else v-model="text" type="textarea" :rows="7" :disabled="loading"
        placeholder="粘贴 ICCID，支持换行、逗号、空格、Excel 制表符；每批最多 10000 个" class="input-area" />
      <p>格式有效 {{ parsed.valid.length }} 个 · 重复 {{ parsed.duplicates }} 个 · 格式异常 {{ parsed.invalid.length }} 个</p>
      <el-alert v-if="parsed.valid.length > 10000" type="warning" :closable="false" title="每批最多 10000 个 ICCID，请分批操作" />
      <el-alert v-if="parsed.invalid.length" type="warning" :closable="false" title="请修正格式异常的卡号后再提交">
        <div class="invalid-list">{{ parsed.invalid.slice(0, 20).join('、') }}{{ parsed.invalid.length > 20 ? '…' : '' }}</div>
      </el-alert>
      <el-form label-width="90px" class="input-area">
        <el-form-item label="目标位置" required>
          <el-select v-model="target" filterable placeholder="选择目标项目或未分组" :disabled="loading" style="width: 100%">
            <el-option :value="0" label="未分组（移出项目）" />
            <el-option v-for="project in projects" :key="project.id" :value="project.id" :label="project.name" />
          </el-select>
        </el-form-item>
      </el-form>
      <p v-if="target !== undefined">将 {{ parsed.valid.length }} 张卡片移至「{{ targetName }}」，仅改变项目分组。</p>
    </template>
    <template v-else>
      <el-alert :type="result.failed_count ? 'warning' : 'success'" :closable="false"
        :title="`成功 ${result.success_count} 张，无需变更 ${result.skipped_count} 张，失败 ${result.failed_count} 张`" />
      <template v-if="result.failed_count">
        <el-button link type="primary" class="input-area" @click="copyFailed">复制失败卡号</el-button>
        <el-table :data="result.failed_list.slice((failedPage - 1) * 100, failedPage * 100)" max-height="300">
          <el-table-column prop="iccid" label="ICCID" width="235" />
          <el-table-column prop="error" label="失败原因" />
        </el-table>
        <el-pagination v-if="result.failed_count > 100" v-model:current-page="failedPage" :page-size="100"
          :total="result.failed_count" layout="prev, pager, next" class="input-area" />
      </template>
    </template>
    <template #footer>
      <el-button :disabled="loading" @click="visible = false">{{ result ? '关闭' : '取消' }}</el-button>
      <el-button v-if="!result" type="primary" :loading="loading" :disabled="!canSubmit" @click="submit">确认转移</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { projectApi } from '@/api/modules/project'
import type { Project, ProjectMoveResult, ProjectScope } from '@/types/project'

const props = defineProps<{
  modelValue: boolean
  projects: Project[]
  initialIccids: string[]
  initialTarget?: number
  source: ProjectScope
}>()
const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}>()
const visible = computed({ get: () => props.modelValue, set: value => emit('update:modelValue', value) })
const text = ref('')
const target = ref<number>()
const loading = ref(false)
const result = ref<ProjectMoveResult>()
const failedPage = ref(1)
const parsed = computed(() => {
  const tokens = props.initialIccids.length ? props.initialIccids : text.value.trim().split(/[\s,，;；]+/).filter(Boolean)
  const unique = [...new Set(tokens.map(value => value.trim()))]
  return {
    valid: unique.filter(value => /^[0-9A-Za-z]{10,30}$/.test(value)),
    invalid: unique.filter(value => !/^[0-9A-Za-z]{10,30}$/.test(value)),
    duplicates: tokens.length - unique.length
  }
})
const canSubmit = computed(() => target.value !== undefined && parsed.value.valid.length > 0 && parsed.value.valid.length <= 10000 && !parsed.value.invalid.length)
const targetName = computed(() => target.value === 0 ? '未分组' : props.projects.find(p => p.id === target.value)?.name || '所选项目')
const sourceLabel = computed(() => props.source === 'all' ? '本人卡片' : props.source === 'ungrouped' ? '本人未分组卡片' : props.projects.find(p => p.id === props.source)?.name || '当前项目')
const reset = () => { text.value = ''; result.value = undefined; target.value = undefined; failedPage.value = 1 }
watch(() => props.modelValue, value => { if (value) { reset(); target.value = props.initialTarget } })
const submit = async () => {
  if (!canSubmit.value || loading.value) return
  loading.value = true
  try {
    result.value = await projectApi.moveCards({
      iccids: parsed.value.valid,
      project_id: target.value || null,
      source_project_id: typeof props.source === 'number' ? props.source : undefined,
      source_ungrouped: props.source === 'ungrouped'
    })
    emit('success')
  } catch (error) {
    console.error('项目转移失败:', error)
  } finally { loading.value = false }
}
const copyFailed = async () => {
  try {
    await navigator.clipboard.writeText(result.value?.failed_list.map(item => item.iccid).join('\n') || '')
    ElMessage.success('失败卡号已复制')
  } catch { ElMessage.error('复制失败，请手动复制卡号') }
}
</script>

<style scoped>
.input-area { margin-top: 16px; }
.invalid-list { max-height: 100px; overflow: auto; overflow-wrap: anywhere; }
</style>
