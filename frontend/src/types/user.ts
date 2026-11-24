export interface UserSummary {
  id: string
  username: string
  displayName: string
}

export interface UserPublic extends UserSummary {
  createdAt: string
}

export interface TokenResponse {
  accessToken: string
  tokenType: string
  expiresIn: number
}

export interface LoginInput {
  username: string
  password: string
}

export interface RegisterInput {
  username: string
  password: string
  displayName: string
}
