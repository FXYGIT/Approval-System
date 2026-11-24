import axios, { AxiosError, type AxiosRequestConfig } from 'axios'

import type { ErrorBody } from '@/types/api'

export const TOKEN_KEY = 'approval.token'

export class ApiError extends Error {
  status: number
  code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

const http = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

type UnauthorizedHandler = () => void

let onUnauthorized: UnauthorizedHandler = () => {}

export function setUnauthorizedHandler(handler: UnauthorizedHandler): void {
  onUnauthorized = handler
}

function fallbackMessage(status: number): string {
  switch (status) {
    case 400:
      return '请求参数错误'
    case 401:
      return '请先登录'
    case 403:
      return '无权访问'
    case 404:
      return '资源不存在'
    case 409:
      return '操作冲突，请刷新后重试'
    case 422:
      return '输入不合法'
    default:
      return status >= 500 ? '服务器异常，请稍后重试' : '请求失败'
  }
}

http.interceptors.response.use(
  (response) => response.data,
  (error: AxiosError<ErrorBody>) => {
    const status = error.response?.status ?? 0
    const body = error.response?.data
    const code = body?.error?.code ?? (status === 401 ? 'AUTHENTICATION_REQUIRED' : 'UNKNOWN_ERROR')
    const message = body?.error?.message ?? fallbackMessage(status)
    if (status === 401) {
      onUnauthorized()
    }
    return Promise.reject(new ApiError(status, code, message))
  },
)

export const request = {
  get: <T>(url: string, config?: AxiosRequestConfig) => http.get<T, T>(url, config),
  post: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    http.post<T, T>(url, data, config),
  put: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    http.put<T, T>(url, data, config),
  delete: <T>(url: string, config?: AxiosRequestConfig) => http.delete<T, T>(url, config),
}

export default http
