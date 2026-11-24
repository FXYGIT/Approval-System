export interface Page<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

export interface ErrorBody {
  error?: {
    code?: string
    message?: string
  }
}
