<template>
  <section class="project-nav" aria-label="卡片项目导航" :aria-busy="saving" @dragend="endDrag">
    <button type="button" class="scope-row" :class="{ active: isActive('ungrouped'), 'drop-target': dropTarget === 'ungrouped' }"
      :aria-current="isActive('ungrouped') ? 'page' : undefined" @click="select('ungrouped')"
      @dragover="dragOver($event, 'ungrouped')" @dragleave="dropTarget = undefined" @drop.prevent="drop($event, 'ungrouped')">未分组</button>
    <div class="project-heading"><span>项目 <small>{{ store.projects.length }}</small></span>
      <button type="button" class="icon-button" aria-label="新建项目" title="新建项目" @click="editProject(null)"><el-icon><Plus /></el-icon></button>
    </div>
    <el-input v-model="keyword" size="small" clearable placeholder="搜索全部项目" aria-label="搜索全部项目" :prefix-icon="Search" @keydown.stop />
    <div class="project-page" :style="{ height: `${pageSize * 34}px` }">
      <div v-for="project in store.loadFailed ? [] : pageProjects" :key="project.id" class="project-row"
        :class="{ active: isActive(project.id), 'drop-target': dropTarget === project.id }"
        @dragover="dragOver($event, project.id)" @dragleave="dropTarget = undefined" @drop.prevent="drop($event, project.id)">
        <button type="button" class="drag-handle" :draggable="!saving && !keyword.trim()" :disabled="saving || !!keyword.trim()"
          :aria-label="`拖动排序：${project.name}`" title="拖动排序；跨页排序请使用项目操作菜单" @dragstart="startSort($event, project.id)"><el-icon><Rank /></el-icon></button>
        <button type="button" class="project-name" :data-project-id="project.id" :title="project.name"
          :aria-current="isActive(project.id) ? 'page' : undefined" @click="select(project.id)">{{ project.name }}</button>
        <span class="project-count">{{ project.card_count }}</span>
        <el-dropdown trigger="click" @command="projectCommand($event, project)">
          <button type="button" class="icon-button project-actions" :aria-label="`${project.name}项目操作`"><el-icon><MoreFilled /></el-icon></button>
          <template #dropdown><el-dropdown-menu>
            <el-dropdown-item command="edit">编辑项目</el-dropdown-item>
            <el-dropdown-item command="position" :disabled="saving">移至第几位</el-dropdown-item>
            <el-dropdown-item command="delete">删除项目</el-dropdown-item>
          </el-dropdown-menu></template>
        </el-dropdown>
      </div>
      <div v-if="store.loadFailed" class="empty-state">项目加载失败 <button type="button" @click="store.refresh">重试</button></div>
      <div v-else-if="!pageProjects.length" class="empty-state">{{ !store.loaded ? '正在加载…' : keyword.trim() ? '没有匹配的项目' : '暂无项目，点击 + 新建' }}</div>
    </div>
    <div class="project-pagination" aria-label="项目分页">
      <button type="button" class="icon-button" aria-label="上一页项目" :disabled="page <= 1" @click="turnPage(-1)" @dragover="hoverPage($event, -1)" @dragleave="cancelPageHover" @drop.prevent="endDrag"><el-icon><ArrowLeft /></el-icon></button>
      <span aria-live="polite">{{ page }} / {{ pageCount }}</span>
      <button type="button" class="icon-button" aria-label="下一页项目" :disabled="page >= pageCount" @click="turnPage(1)" @dragover="hoverPage($event, 1)" @dragleave="cancelPageHover" @drop.prevent="endDrag"><el-icon><ArrowRight /></el-icon></button>
    </div>
    <ProjectFormDialog v-model="formVisible" :project="editingProject" @success="projectSaved" />
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMediaQuery } from '@vueuse/core'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Rank, MoreFilled, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { projectApi } from '@/api/modules/project'
import { parseProjectScope, useCardProjectsStore } from '@/stores/modules/cardProjects'
import type { Project, ProjectScope } from '@/types/project'
import ProjectFormDialog from '@/views/projects/components/ProjectFormDialog.vue'

const store = useCardProjectsStore()
const route = useRoute()
const router = useRouter()
const active = computed(() => parseProjectScope(route.query.project))
const isActive = (scope: ProjectScope) => route.path === '/cards/list' && active.value === scope
const keyword = ref('')
const page = ref(1)
const compact = useMediaQuery('(max-height: 800px)')
const pageSize = computed(() => compact.value ? 3 : 5)
const filtered = computed(() => store.projects.filter(p => p.name.toLocaleLowerCase().includes(keyword.value.trim().toLocaleLowerCase())))
const pageCount = computed(() => Math.max(1, Math.ceil(filtered.value.length / pageSize.value)))
const pageProjects = computed(() => filtered.value.slice((page.value - 1) * pageSize.value, page.value * pageSize.value))
const saving = ref(false)
const formVisible = ref(false)
const editingProject = ref<Project | null>(null)
const dropTarget = ref<ProjectScope>()
let hoverTimer: ReturnType<typeof setTimeout> | undefined
const cancelPageHover = () => { clearTimeout(hoverTimer); hoverTimer = undefined }
const endDrag = () => { cancelPageHover(); dropTarget.value = undefined }
const turnPage = (direction: number) => { endDrag(); page.value = Math.max(1, Math.min(pageCount.value, page.value + direction)) }
const select = (scope: ProjectScope) => {
  if (saving.value) return
  router.push({ path: '/cards/list', query: { ...(route.path === '/cards/list' ? route.query : {}), project: scope === 'all' ? undefined : String(scope) } })
}
const locateActive = () => {
  const index = filtered.value.findIndex(p => p.id === active.value)
  if (index >= 0) page.value = Math.floor(index / pageSize.value) + 1
}
watch(keyword, () => { page.value = 1; endDrag() }, { flush: 'sync' })
watch(pageSize, () => { page.value = Math.min(page.value, pageCount.value); locateActive(); endDrag() })
watch(pageCount, count => { page.value = Math.min(page.value, count) })
watch(active, () => { keyword.value = ''; locateActive() }, { flush: 'post' })
watch(() => store.loaded, loaded => { if (loaded) locateActive(); else { keyword.value = ''; page.value = 1 } }, { immediate: true })
watch([active, () => store.projects, () => store.loaded], () => {
  if (route.path === '/cards/list' && store.loaded && typeof active.value === 'number' && !store.projects.some(p => p.id === active.value)) {
    router.replace({ path: route.path, query: { ...route.query, project: undefined } })
  }
}, { immediate: true })
onBeforeUnmount(endDrag)
const editProject = (project: Project | null) => { editingProject.value = project; formVisible.value = true }
const projectSaved = async () => { await store.updated() }
const saveOrder = async (ordered: Project[]) => {
  if (saving.value) return
  saving.value = true
  try {
    await projectApi.reorder(ordered.map(p => p.id))
    await store.refresh()
    ElMessage.success('项目顺序已保存')
  } catch (error) { console.error('保存排序失败:', error); await store.refresh() }
  finally { saving.value = false }
}
const projectCommand = async (command: string, project: Project) => {
  if (command === 'edit') { editProject(project); return }
  try {
    if (command === 'position') {
      const result = await ElMessageBox.prompt(`输入全体项目中的位置（1–${store.projects.length}）`, `调整「${project.name}」的位置`, {
        inputValue: String(store.projects.findIndex(p => p.id === project.id) + 1),
        inputValidator: value => /^\d+$/.test(value || '') && Number(value) >= 1 && Number(value) <= store.projects.length || '请输入有效的位置'
      })
      if (typeof result === 'string') return
      const ordered = store.projects.filter(p => p.id !== project.id)
      ordered.splice(Number(result.value) - 1, 0, project)
      await saveOrder(ordered)
      return
    }
    await ElMessageBox.confirm(`删除「${project.name}」后，其中 ${project.card_count} 张卡片将回到未分组。`, '删除项目', { type: 'warning' })
    await projectApi.delete(project.id)
    await projectSaved()
    ElMessage.success('项目已删除，卡片已移回未分组')
  } catch (error) { if (error !== 'cancel' && error !== 'close') console.error('项目操作失败:', error) }
}
const startSort = (event: DragEvent, id: number) => {
  if (saving.value || keyword.value.trim() || !event.dataTransfer) { event.preventDefault(); return }
  event.dataTransfer.setData('application/x-card-project', String(id))
  event.dataTransfer.effectAllowed = 'move'
}
const dragOver = (event: DragEvent, scope: ProjectScope) => {
  const types = event.dataTransfer?.types || []
  if (saving.value || (!types.includes('application/x-card-iccids') && !(typeof scope === 'number' && !keyword.value.trim() && types.includes('application/x-card-project')))) return
  event.preventDefault()
  cancelPageHover()
  if (event.dataTransfer) event.dataTransfer.dropEffect = 'move'
  dropTarget.value = scope
}
const hoverPage = (event: DragEvent, direction: number) => {
  if (!event.dataTransfer?.types.includes('application/x-card-iccids') || saving.value) return
  event.preventDefault()
  if (!hoverTimer) hoverTimer = setTimeout(() => turnPage(direction), 700)
}
const drop = async (event: DragEvent, scope: ProjectScope) => {
  endDrag()
  if (saving.value) return
  const payload = event.dataTransfer?.getData('application/x-card-iccids')
  if (payload) {
    try {
      const iccids: unknown = JSON.parse(payload)
      if (Array.isArray(iccids) && iccids.length && iccids.length <= 10000 && iccids.every(value => typeof value === 'string')) {
        store.openMove(iccids, typeof scope === 'number' ? scope : 0, active.value)
      }
    } catch { ElMessage.warning('无法识别拖动的卡片，请重新选择') }
    return
  }
  if (keyword.value.trim()) return
  const id = Number(event.dataTransfer?.getData('application/x-card-project'))
  const from = store.projects.findIndex(p => p.id === id)
  const to = store.projects.findIndex(p => p.id === scope)
  if (from < 0 || to < 0 || from === to) return
  const ordered = [...store.projects]
  const item = ordered.splice(from, 1)[0]
  if (!item) return
  ordered.splice(to, 0, item)
  await saveOrder(ordered)
}
</script>

<style scoped>
.project-nav { width: 100%; min-width: 216px; box-sizing: border-box; padding: 0 12px 8px; color: #dce1f3; background: #171e31; }
button { font: inherit; color: inherit; border: 0; background: transparent; cursor: pointer; }
button:focus-visible { outline: 2px solid #a8b5ff; outline-offset: -2px; }
button:disabled { opacity: .35; cursor: default; }
.scope-row { width: 100%; text-align: left; height: 32px; padding: 0 10px; border-radius: 5px; font-size: 13px; }
.scope-row:hover, .project-row:hover { background: #263151; }
.active { color: #c3ccff; background: #303b62; }
.project-heading { display: flex; align-items: center; justify-content: space-between; height: 30px; padding-left: 10px; color: #aeb9d1; }
.project-heading small { margin-left: 4px; }
.icon-button { display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; width: 26px; height: 26px; border-radius: 4px; }
.icon-button:hover:not(:disabled) { background: #3b486d; }
.project-page { margin-top: 6px; overflow: hidden; }
.project-row { display: flex; align-items: center; height: 34px; border-radius: 5px; }
.project-name { min-width: 0; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; text-align: left; height: 100%; padding: 0 3px; font-size: 13px; }
.drag-handle { width: 22px; padding: 0; flex-shrink: 0; cursor: grab; color: #9da9c2; }
.project-count { font-size: 12px; color: #aeb9d1; padding: 0 3px; }
.project-actions { opacity: 0; }
.project-row:hover .project-actions, .project-row:focus-within .project-actions { opacity: 1; }
.drop-target { outline: 2px dashed #a8b5ff; outline-offset: -2px; background: #303b62; }
.project-pagination { display: flex; align-items: center; justify-content: space-between; height: 30px; color: #c3cce2; }
.project-pagination span { font-size: 12px; }
.empty-state { padding-top: 16px; text-align: center; font-size: 12px; color: #b1bdd4; }
.empty-state button { text-decoration: underline; }
:deep(.el-input__wrapper) { background: #232c43; box-shadow: 0 0 0 1px #485370 inset; }
:deep(.el-input__inner) { color: #edf0fa; }
:deep(.el-input__inner::placeholder) { color: #aeb9d1; }
</style>
