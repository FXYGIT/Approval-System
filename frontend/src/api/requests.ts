import { request } from './http'

import type { Page } from '@/types/api'
import type { HistoryEntry } from '@/types/history'
import type { DraftInput, DraftUpdate, RequestPublic, RequestStatus } from '@/types/request'

export interface RequestQuery {
  page?: number
  pageSize?: number
  scope?: 'mine' | 'pending'
  status?: RequestStatus
  keyword?: string
}

export interface ApproveInput {
  comment?: string | null
  version?: number
}

export interface RejectInput {
  comment: string
  version?: number
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

export function submitRequest(id: string): Promise<RequestPublic> {
  return request.post<RequestPublic>(`/requests/${id}/submit`)
}

export function approveRequest(id: string, data: ApproveInput = {}): Promise<RequestPublic> {
  return request.post<RequestPublic>(`/requests/${id}/approve`, data)
}

export function rejectRequest(id: string, data: RejectInput): Promise<RequestPublic> {
  return request.post<RequestPublic>(`/requests/${id}/reject`, data)
}

export function getHistory(id: string): Promise<HistoryEntry[]> {
  return request.get<HistoryEntry[]>(`/requests/${id}/history`)
}
