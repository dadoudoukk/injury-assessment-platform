import { AGENCY_ROUTE_PREFIXES, ROUTES } from '@/constants/routes'
import { STORAGE_KEYS, type UserType } from '@/constants/storage'
import { useUserStore } from '@/store/modules/user'
import { clearSessionStorage } from '@/utils/session'

function isAgencyRoute(route: string): boolean {
  return AGENCY_ROUTE_PREFIXES.some((prefix) => route.includes(prefix))
}

/** 401 后按 lastUserType + 路由兜底跳转 */
export function redirectOnUnauthorized(): void {
  const lastUserType = uni.getStorageSync(STORAGE_KEYS.LAST_USER_TYPE) as UserType | ''

  if (lastUserType === 'agency') {
    uni.reLaunch({ url: ROUTES.AGENCY_LOGIN })
    return
  }
  if (lastUserType === 'patient') {
    uni.reLaunch({ url: ROUTES.PATIENT_HOME })
    return
  }

  const pages = getCurrentPages()
  const current = pages[pages.length - 1]
  const route = (current as { route?: string } | undefined)?.route ?? ''

  if (isAgencyRoute(route)) {
    uni.reLaunch({ url: ROUTES.AGENCY_LOGIN })
    return
  }

  uni.reLaunch({ url: ROUTES.PATIENT_HOME })
}

/** 清理会话凭证，保留 lastUserType 供跳转推断；同步清空 store，避免 401 后页面来回跳转闪屏 */
export function clearSessionCredentials(): void {
  clearSessionStorage()
  useUserStore().clearSession()
}
