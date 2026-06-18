import { fetchUserInfo as apiFetchUserInfo } from '@/api/user'
import { useUserStore } from '@/store/modules/user'
import type { UserInfo } from '@/types/user'

/** 拉取用户信息并写入 store（请求层与 store 之间的桥接，避免 store 直接依赖 api） */
export async function fetchAndSetUserInfo(): Promise<UserInfo | null> {
  const userStore = useUserStore()
  try {
    const res = await apiFetchUserInfo()
    if (res) {
      userStore.setUserInfo(res)
      return res
    }
  } catch (e) {
    console.error('Failed to fetch user info', e)
  }
  return userStore.userInfo
}
