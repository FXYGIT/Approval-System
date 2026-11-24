import { request } from './http'

import type { LoginInput, RegisterInput, TokenResponse, UserPublic } from '@/types/user'

export function register(data: RegisterInput): Promise<UserPublic> {
  return request.post<UserPublic>('/auth/register', data)
}

export function login(data: LoginInput): Promise<TokenResponse> {
  return request.post<TokenResponse>('/auth/login', data)
}

export function fetchMe(): Promise<UserPublic> {
  return request.get<UserPublic>('/users/me')
}
