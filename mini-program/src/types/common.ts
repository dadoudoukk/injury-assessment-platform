export interface ApiResponse<T = unknown> {
  code: number
  data: T
  msg: string
}

export interface PageResult<T> {
  list: T[]
  total: number
  pageNum?: number
  pageSize?: number
}
