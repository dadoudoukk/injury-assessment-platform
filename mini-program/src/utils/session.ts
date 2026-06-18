import { STORAGE_KEYS } from '@/constants/storage'

/** 清理登录凭证 storage，不含 lastUserType */
export function clearSessionStorage(): void {
  uni.removeStorageSync(STORAGE_KEYS.TOKEN)
  uni.removeStorageSync(STORAGE_KEYS.USER_INFO)
}

/** 主动退出：清理全部会话 storage */
export function clearAllSessionStorage(): void {
  clearSessionStorage()
  uni.removeStorageSync(STORAGE_KEYS.LAST_USER_TYPE)
}
