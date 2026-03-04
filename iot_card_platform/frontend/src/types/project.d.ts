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
