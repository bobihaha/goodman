/**
 * H5 自助服务 API
 */

import { get, post, put } from '@/utils/request'
import type { Card, CardDiagnostics } from '@/types/card'

export interface H5PortalConfig {
  user_id: number
  user_name: string
  title?: string
  logo?: string
  banner?: string
  notice?: string
  contact_phone?: string
  contact_wechat?: string
  theme?: Record<string, any>
  allow_suspend: boolean
  allow_resume: boolean
  allow_remark: boolean
  require_verify: boolean
  status: 'enabled' | 'disabled' | 'expired'
}

export interface H5CardCandidate {
  id: number
  iccid_masked: string
  msisdn_masked?: string
  status?: string
  status_name?: string
  spec_name?: string
  activated_at?: string
  expired_at?: string
}

export interface H5CardActions {
  allow_suspend: boolean
  allow_resume: boolean
  allow_remark: boolean
}

export interface H5CardDetail {
  card: Card
  diagnostics?: CardDiagnostics | null
  actions: H5CardActions
}

export interface H5CardQueryResponse {
  match_type: 'exact' | 'fuzzy_single' | 'fuzzy_multiple' | 'none'
  items: Array<H5CardDetail | H5CardCandidate>
}

export interface H5CardActionResult {
  card_id: number
  iccid: string
  action: 'suspend' | 'resume' | 'refresh' | 'device_separation'
  status: 'processing' | 'success' | 'failed' | 'unsupported'
  callback_no?: string
  suspend_callback_no?: string
  resume_callback_no?: string
  device_separation_detection_status?: 'detected' | 'clear' | 'pending' | 'unsupported'
  device_separation_detection_message?: string
  message?: string
}

export const h5Api = {
  getConfig(slug: string): Promise<H5PortalConfig> {
    return get<H5PortalConfig>(`/h5/${slug}/config`)
  },

  queryCard(slug: string, keyword: string): Promise<H5CardQueryResponse> {
    return post<H5CardQueryResponse>(`/h5/${slug}/card/query`, { keyword })
  },

  getCardDetail(slug: string, cardId: number): Promise<H5CardDetail> {
    return get<H5CardDetail>(`/h5/${slug}/card/${cardId}`)
  },

  suspendCard(slug: string, cardId: number, reason?: string): Promise<H5CardActionResult> {
    return post<H5CardActionResult>(`/h5/${slug}/card/${cardId}/suspend`, { reason })
  },

  resumeCard(slug: string, cardId: number): Promise<H5CardActionResult> {
    return post<H5CardActionResult>(`/h5/${slug}/card/${cardId}/resume`, {})
  },

  refreshCard(slug: string, cardId: number): Promise<H5CardActionResult> {
    return post<H5CardActionResult>(`/h5/${slug}/card/${cardId}/refresh`, {}, {
      timeout: 180000
    })
  },

  detectDeviceSeparation(slug: string, cardId: number): Promise<H5CardActionResult> {
    return post<H5CardActionResult>(`/h5/${slug}/card/${cardId}/device-separation`, {})
  },

  updateRemark(slug: string, cardId: number, remark: string, operatorName?: string, operatorPhone?: string): Promise<Card> {
    return put<Card>(`/h5/${slug}/card/${cardId}/remark`, {
      remark,
      operator_name: operatorName,
      operator_phone: operatorPhone
    })
  }
}
