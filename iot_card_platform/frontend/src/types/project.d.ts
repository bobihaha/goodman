export interface Project {
  id: number
  name: string
  user_id: number
  remark?: string
  card_count: number
  created_at?: string
  updated_at?: string
}

export interface ProjectCreateRequest {
  name: string
  remark?: string
}

export interface ProjectUpdateRequest {
  name?: string
  remark?: string
}

export interface ProjectListParams {
  page?: number
  page_size?: number
  keyword?: string
}

export type ProjectScope = 'all' | 'ungrouped' | number

export interface ProjectMoveRequest {
  iccids: string[]
  project_id: number | null
  source_project_id?: number
  source_ungrouped?: boolean
}

export interface ProjectMoveResult {
  success_count: number
  skipped_count: number
  failed_count: number
  duplicate_count: number
  success_list: { iccid: string }[]
  skipped_list: { iccid: string; message: string }[]
  failed_list: { iccid: string; error: string }[]
}
