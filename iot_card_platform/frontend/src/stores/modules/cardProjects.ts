import { defineStore } from 'pinia'
import { ref } from 'vue'
import { projectApi } from '@/api/modules/project'
import type { Project, ProjectScope } from '@/types/project'

export const parseProjectScope = (value: unknown): ProjectScope => {
  if (value === 'ungrouped') return value
  const id = typeof value === 'string' && /^\d+$/.test(value) ? Number(value) : 0
  return Number.isSafeInteger(id) && id > 0 ? id : 'all'
}

export const useCardProjectsStore = defineStore('cardProjects', () => {
  const projects = ref<Project[]>([])
  const loaded = ref(false)
  const loadFailed = ref(false)
  const revision = ref(0)
  const moveVisible = ref(false)
  const moveIccids = ref<string[]>([])
  const moveTarget = ref<number>()
  const moveSource = ref<ProjectScope>('all')
  let requestId = 0

  const refresh = async () => {
    const id = ++requestId
    try {
      const data = await projectApi.getAll()
      if (id !== requestId) return
      projects.value = data
      loaded.value = true
      loadFailed.value = false
    } catch (error) {
      if (id === requestId) loadFailed.value = true
      console.error('加载项目失败:', error)
    }
  }
  const reset = () => {
    ++requestId
    projects.value = []
    loaded.value = false
    loadFailed.value = false
    moveVisible.value = false
    moveIccids.value = []
    moveTarget.value = undefined
    moveSource.value = 'all'
  }
  const updated = async () => { await refresh(); revision.value++ }
  const openMove = (iccids: string[] = [], target?: number, source: ProjectScope = 'all') => {
    moveIccids.value = iccids
    moveTarget.value = target
    moveSource.value = source
    moveVisible.value = true
  }
  return { projects, loaded, loadFailed, revision, moveVisible, moveIccids, moveTarget, moveSource, refresh, reset, updated, openMove }
})
