/**
 * 项目管理 API
 */

import request from '@/utils/request'
import type { Project, ProjectCreateRequest, ProjectUpdateRequest, ProjectListParams, ProjectMoveRequest, ProjectMoveResult } from '@/types/project'
import type { PaginationResponse } from '@/types/common'

export const projectApi = {
  reorder(projectIds: number[]): Promise<void> {
    return request.put('/projects/order', { project_ids: projectIds })
  },
  moveCards(data: ProjectMoveRequest): Promise<ProjectMoveResult> {
    return request.post('/projects/move-cards', data)
  },
  /**
   * 获取项目列表
   */
  getList(params: ProjectListParams): Promise<PaginationResponse<Project>> {
    return request.get<PaginationResponse<Project>>('/projects', { params })
  },

  /**
   * 获取所有项目（下拉选择用）
   */
  getAll(): Promise<Project[]> {
    return request.get('/projects/all')
  },

  /**
   * 获取项目详情
   */
  getDetail(id: number): Promise<Project> {
    return request.get<Project>(`/projects/${id}`)
  },

  /**
   * 创建项目
   */
  create(data: ProjectCreateRequest): Promise<Project> {
    return request.post<Project>('/projects', data)
  },

  /**
   * 更新项目
   */
  update(id: number, data: ProjectUpdateRequest): Promise<Project> {
    return request.put<Project>(`/projects/${id}`, data)
  },

  /**
   * 删除项目
   */
  delete(id: number): Promise<void> {
    return request.delete<void>(`/projects/${id}`)
  }
}
