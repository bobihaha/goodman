import axios from 'axios'
import request from '@/utils/request'
import type { ChannelCustomerItem, ChannelPartner, ChannelPointItem, ChannelPointSummary } from '@/types/channel'

const compactParams = (params?: Record<string, any>) => Object.fromEntries(
  Object.entries(params || {}).filter(([, value]) => value !== '' && value !== undefined && value !== null)
)

const channelRequest = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' }
})

channelRequest.interceptors.request.use(config => {
  const token = localStorage.getItem('channel_access_token')
  if (token && config.headers) config.headers.Authorization = `Bearer ${token}`
  return config
})

channelRequest.interceptors.response.use(response => {
  const data = response.data
  if (data?.code === 200 || data?.code === 0) return data.data
  return Promise.reject(new Error(data?.msg || '操作失败'))
}, error => {
  const data = error.response?.data
  const detail = Array.isArray(data?.detail)
    ? data.detail.map((item: any) => item?.msg).filter(Boolean).join('；')
    : data?.detail
  return Promise.reject(new Error(data?.msg || data?.message || detail || error.message || '网络请求失败'))
})

export const channelAdminApi = {
  getSettings: () => request.get<{ default_stock_out_rate: number; default_renewal_rate: number }>('/channels/admin/settings'),
  updateSettings: (data: { default_stock_out_rate: number; default_renewal_rate: number }) => request.put('/channels/admin/settings', data),
  getPartners: (params?: { keyword?: string; status?: string }) => request.get<{ items: ChannelPartner[]; total: number }>('/channels/admin/partners', { params: compactParams(params) }),
  createPartner: (data: Record<string, any>) => request.post<ChannelPartner>('/channels/admin/partners', data),
  updatePartner: (id: number, data: Record<string, any>) => request.put<ChannelPartner>(`/channels/admin/partners/${id}`, data),
  resetPassword: (id: number, new_password: string) => request.post(`/channels/admin/partners/${id}/reset-password`, { new_password }),
  getPoints: (params: Record<string, any>) => request.get<{ items: ChannelPointItem[]; total: number; page: number; page_size: number }>('/channels/admin/points', { params: compactParams(params) }),
  settlePoints: (point_ids: number[]) => request.post<{ settled_count: number }>('/channels/admin/points/settle', { point_ids })
}

export const channelPortalApi = {
  getPublicConfig: (slug: string): Promise<{ channel_name: string }> => channelRequest.get(`/channels/public/${slug}`) as any,
  register: (slug: string, data: { customer_name: string; customer_phone: string; customer_profile: string; consent: boolean }): Promise<{ success: boolean; message: string }> => channelRequest.post(`/channels/public/${slug}/register`, data) as any,
  login: (data: { account: string; password: string }): Promise<{ access_token: string; partner: { id: number; name: string; contact_name: string; account: string } }> => channelRequest.post('/channels/auth/login', data) as any,
  me: (): Promise<{ id: number; name: string; contact_name: string; account: string; phone: string; h5_path: string }> => channelRequest.get('/channels/me') as any,
  summary: (): Promise<ChannelPointSummary> => channelRequest.get('/channels/me/summary') as any,
  customers: (params: Record<string, any>): Promise<{ items: ChannelCustomerItem[]; total: number; page: number; page_size: number }> => channelRequest.get('/channels/me/customers', { params: compactParams(params) }) as any,
  points: (params: Record<string, any>): Promise<{ items: ChannelPointItem[]; total: number; page: number; page_size: number }> => channelRequest.get('/channels/me/points', { params: compactParams(params) }) as any
}
