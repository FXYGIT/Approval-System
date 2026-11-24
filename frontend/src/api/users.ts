import { request } from './http'

import type { Page } from '@/types/api'
import type { UserSummary } from '@/types/user'

export interface UserQuery {
  page?: number
  pageSize?: number
  keyword?: string
}

export function listUsers(params: UserQuery = {}): Promise<Page<UserSummary>> {
  return request.get<Page<UserSummary>>('/users', { params })
}
