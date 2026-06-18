import { defineStore } from 'pinia'
import { ref } from 'vue'
import { STORAGE_KEYS, type UserType } from '@/constants/storage'
import type { UserInfo } from '@/types/user'
import { clearAllSessionStorage, clearSessionStorage } from '@/utils/session'

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(uni.getStorageSync(STORAGE_KEYS.TOKEN) || '')
  const userInfo = ref<UserInfo | null>(
    uni.getStorageSync(STORAGE_KEYS.USER_INFO) || null,
  )

  const setToken = (newToken: string) => {
    token.value = newToken
    uni.setStorageSync(STORAGE_KEYS.TOKEN, newToken)
  }

  const setUserInfo = (info: UserInfo | null) => {
    userInfo.value = info
    if (info) {
      uni.setStorageSync(STORAGE_KEYS.USER_INFO, info)
    } else {
      uni.removeStorageSync(STORAGE_KEYS.USER_INFO)
    }
  }

  const setLastUserType = (type: UserType) => {
    uni.setStorageSync(STORAGE_KEYS.LAST_USER_TYPE, type)
  }

  const getLastUserType = (): UserType | '' => {
    return uni.getStorageSync(STORAGE_KEYS.LAST_USER_TYPE) || ''
  }

  /** 清理登录凭证，保留 lastUserType（用于 401 跳转、换号重登等场景） */
  const clearSession = () => {
    clearSessionStorage()
    token.value = ''
    userInfo.value = null
  }

  /** 主动退出：清理全部会话信息，含 lastUserType */
  const logout = () => {
    clearAllSessionStorage()
    token.value = ''
    userInfo.value = null
  }

  return {
    token,
    userInfo,
    setToken,
    setUserInfo,
    setLastUserType,
    getLastUserType,
    clearSession,
    logout,
  }
})
