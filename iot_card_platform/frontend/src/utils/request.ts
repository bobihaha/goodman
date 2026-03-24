/**
 * Axios 请求封装
 * 统一处理请求和响应，包含错误处理、Token管理等
 */

import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import { storage } from './storage'

let isRedirectingToLogin = false

const redirectToLogin = () => {
  if (isRedirectingToLogin) {
    return
  }

  isRedirectingToLogin = true
  storage.remove('access_token')
  storage.remove('refresh_token')
  storage.remove('original_user_info')
  storage.remove('original_access_token')
  storage.remove('original_refresh_token')

  const currentPath = window.location.pathname + window.location.search
  const loginUrl = currentPath && currentPath !== '/login'
    ? `/login?redirect=${encodeURIComponent(currentPath)}`
    : '/login'

  window.location.replace(loginUrl)
}

// 创建 axios 实例
const axiosInstance: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 60000, // 增加到60秒，避免入库操作超时
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
axiosInstance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 使用 storage 工具获取 token（会自动添加前缀）
    const token = storage.get<string>('access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
axiosInstance.interceptors.response.use(
  (response: AxiosResponse) => {
    const { data } = response

    // 如果响应数据有 code 字段，按照标准格式处理
    if (data && typeof data === 'object' && 'code' in data) {
      // 业务成功
      if (data.code === 200 || data.code === 0) {
        return data.data
      }
      if (data.code === 401) {
        redirectToLogin()
        return Promise.reject(new Error('登录已失效'))
      }
      // 业务失败（后端返回的是 msg 字段，不是 message）
      const errorMsg = data.msg || data.message || '操作失败'
      ElMessage.error(errorMsg)
      return Promise.reject(new Error(errorMsg))
    }

    // 如果没有 code 字段，直接返回 data（后端可能直接返回数据）
    return data
  },
  (error) => {
    // HTTP 错误处理
    if (!error.response) {
      ElMessage.error('网络连接失败，请检查网络')
      return Promise.reject(error)
    }

    const { status, data } = error.response

    // 统一错误处理（后端返回的是 msg 字段）
    const errorMsg = data?.msg || data?.message
    
    switch (status) {
      case 400:
        ElMessage.error(errorMsg || '请求参数错误')
        break
      case 401:
        redirectToLogin()
        break
      case 403:
        ElMessage.error(errorMsg || '没有权限访问')
        break
      case 404:
        ElMessage.error(errorMsg || '请求的资源不存在')
        break
      case 500:
        ElMessage.error(errorMsg || '服务器错误，请稍后重试')
        break
      case 502:
        ElMessage.error('网关错误')
        break
      case 503:
        ElMessage.error('服务暂时不可用')
        break
      default:
        ElMessage.error(errorMsg || `请求失败(${status})`)
    }

    return Promise.reject(error)
  }
)

// 导出请求方法
type RequestInstance = Omit<AxiosInstance, 'get' | 'post' | 'put' | 'delete'> & {
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T>
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>
  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>
  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T>
}

const request = axiosInstance as RequestInstance

export default request

// 导出类型化的请求方法
export const get = <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
  return request.get<T>(url, config)
}

export const post = <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
  return request.post<T>(url, data, config)
}

export const put = <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
  return request.put<T>(url, data, config)
}

export const del = <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
  return request.delete<T>(url, config)
}
