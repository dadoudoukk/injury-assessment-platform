import { ROUTES } from '@/constants/routes'
import { fetchAndSetUserInfo } from '@/services/user-session'
import { useUserStore } from '@/store/modules/user'
import type { LoginResponse } from '@/types/auth'
import { isAgencyUser } from './role'

let agencyRedirecting = false

function currentRoute(): string {
  const pages = getCurrentPages()
  return (pages[pages.length - 1] as { route?: string } | undefined)?.route ?? ''
}

function agencyReLaunch(url: string) {
  if (agencyRedirecting) return
  agencyRedirecting = true
  uni.reLaunch({
    url,
    complete: () => {
      agencyRedirecting = false
    },
  })
}

/** 机构工作台页：校验登录、机构身份与是否已设密 */
export async function ensureAgencySession(fetchInfo = true): Promise<boolean> {
  const userStore = useUserStore()
  if (!userStore.token) {
    if (!currentRoute().includes('login/index')) {
      agencyReLaunch(ROUTES.AGENCY_LOGIN)
    }
    return false
  }
  if (fetchInfo) {
    await fetchAndSetUserInfo()
  }
  if (!isAgencyUser(userStore.userInfo)) {
    if (!currentRoute().includes('patient/home')) {
      agencyReLaunch(ROUTES.PATIENT_HOME)
    }
    return false
  }
  if (userStore.userInfo?.mustChangePassword) {
    if (!currentRoute().includes('login/set-password')) {
      agencyReLaunch(ROUTES.SET_PASSWORD)
    }
    return false
  }
  return true
}

/** 机构登录成功后统一跳转；返回 true 表示已触发页面跳转 */
export async function completeAgencyLogin(res: LoginResponse): Promise<boolean> {
  const userStore = useUserStore()
  userStore.setToken(res.access_token)
  userStore.setLastUserType('agency')
  await fetchAndSetUserInfo()

  if (!isAgencyUser(userStore.userInfo)) {
    userStore.logout()
    uni.showToast({ title: '该账号不是机构账号', icon: 'none' })
    return false
  }

  const mustChange =
    res.mustChangePassword === true || userStore.userInfo?.mustChangePassword === true

  uni.showToast({ title: '登录成功', icon: 'success' })

  if (mustChange) {
    agencyReLaunch(ROUTES.SET_PASSWORD)
  } else {
    agencyReLaunch(ROUTES.WORKBENCH)
  }
  return true
}
