import { request } from './http'

import type { Page } from '@/types/api'
import type { DraftInput, DraftUpdate, RequestPublic, RequestStatus } from '@/types/request'

export interface RequestQuery {
  page?: number
  pageSize?: number
  status?: RequestStatus
  keyword?: string
}

export function listRequests(params: RequestQuery = {}): Promise<Page<RequestPublic>> {
  return request.get<Page<RequestPublic>>('/requests', { params })
}

export function getRequest(id: string): Promise<RequestPublic> {
  return request.get<RequestPublic>(`/requests/${id}`)
}

export function createRequest(data: DraftInput): Promise<RequestPublic> {
  return request.post<RequestPublic>('/requests', data)
}

export function updateRequest(id: string, data: DraftUpdate): Promise<RequestPublic> {
  return request.put<RequestPublic>(`/requests/${id}`, data)
}

export function deleteRequest(id: string): Promise<void> {
  return request.delete<void>(`/requests/${id}`)
}
