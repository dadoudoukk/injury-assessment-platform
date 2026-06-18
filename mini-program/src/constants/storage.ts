/** 本地存储 key 统一管理 */
export const STORAGE_KEYS = {
  TOKEN: 'token',
  USER_INFO: 'userInfo',
  LAST_USER_TYPE: 'lastUserType',
} as const

export type UserType = 'patient' | 'agency'
