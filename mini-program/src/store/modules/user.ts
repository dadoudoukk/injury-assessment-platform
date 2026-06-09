import { defineStore } from 'pinia'
import { ref } from 'vue'
import { request } from '@/utils/request'

export const useUserStore = defineStore('user', () => {
  const token = ref(uni.getStorageSync('token') || '')
  const userInfo = ref<any>(uni.getStorageSync('userInfo') || null)

  const setToken = (newToken: string) => {
    token.value = newToken
    uni.setStorageSync('token', newToken)
  }

  const setUserInfo = (info: any) => {
    userInfo.value = info
    uni.setStorageSync('userInfo', info)
  }

  const fetchUserInfo = async () => {
    try {
      const res = await request('/user/info', 'GET')
      if (res) {
        setUserInfo(res)
      }
    } catch (e) {
      console.error('Failed to fetch user info', e)
    }
  }

  const logout = () => {
    token.value = ''
    userInfo.value = null
    uni.removeStorageSync('token')
    uni.removeStorageSync('userInfo')
  }

  return {
    token,
    userInfo,
    setToken,
    setUserInfo,
    fetchUserInfo,
    logout
  }
})
