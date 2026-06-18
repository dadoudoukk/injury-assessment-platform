import { wxLoginPatient } from '@/api/auth'
import { ROUTES } from '@/constants/routes'
import { fetchAndSetUserInfo } from '@/services/user-session'
import type { LoginResponse } from '@/types/auth'
import { completeAgencyLogin, ensureAgencySession } from '@/utils/agency-auth'
import { isAgencyUser } from '@/utils/role'
import { useUserStore } from '@/store/modules/user'

/** 登录守卫与会话跳转逻辑统一入口 */
export function useAuthGuard() {
  const userStore = useUserStore()

  /** 机构端页面：校验 token、机构身份、强制改密 */
  async function ensureAgencySessionGuard(fetchInfo = true) {
    return ensureAgencySession(fetchInfo)
  }

  /** 患者端页面：校验 token，未登录跳转门户首页 */
  async function ensurePatientSession(fetchInfo = true): Promise<boolean> {
    if (!userStore.token) {
      uni.reLaunch({ url: ROUTES.PATIENT_HOME })
      return false
    }
    if (fetchInfo) {
      await fetchAndSetUserInfo()
    }
    if (isAgencyUser(userStore.userInfo)) {
      uni.reLaunch({ url: ROUTES.WORKBENCH })
      return false
    }
    return true
  }

  /** 门户首页：伤者已登录则跳转案件列表；机构已登录则展示快捷入口 */
  async function redirectIfPatientLoggedIn() {
    if (!userStore.token) return false

    await fetchAndSetUserInfo()
    if (isAgencyUser(userStore.userInfo)) {
      await ensureAgencySession(false)
      return false
    }

    uni.reLaunch({ url: ROUTES.PATIENT_LIST })
    return true
  }

  /** 机构登录页：已登录机构用户直接进工作台 */
  async function redirectIfAgencyLoggedIn() {
    if (!userStore.token) return false

    await fetchAndSetUserInfo()
    if (!isAgencyUser(userStore.userInfo)) return false

    if (userStore.userInfo?.mustChangePassword) {
      uni.reLaunch({ url: ROUTES.SET_PASSWORD })
    } else {
      uni.reLaunch({ url: ROUTES.WORKBENCH })
    }
    return true
  }

  /** 患者微信登录成功后跳转 */
  async function completePatientLogin(res: LoginResponse) {
    if (!res?.access_token) return

    userStore.setToken(res.access_token)
    userStore.setLastUserType('patient')
    await fetchAndSetUserInfo()

    if (isAgencyUser(userStore.userInfo)) {
      uni.showToast({ title: '该手机号为机构账号，请使用机构入口登录', icon: 'none' })
      userStore.logout()
      return
    }

    uni.showToast({ title: '登录成功', icon: 'success' })
    setTimeout(() => {
      uni.reLaunch({ url: ROUTES.PATIENT_LIST })
    }, 500)
  }

  /** 机构登录成功后跳转（复用 agency-auth） */
  async function completeAgencyLoginGuard(res: LoginResponse) {
    return completeAgencyLogin(res)
  }

  /** 患者端微信授权登录 */
  async function loginPatientWithWxCode(code: string) {
    userStore.clearSession()
    const res = await wxLoginPatient({ code })
    await completePatientLogin(res)
    return res
  }

  return {
    ensureAgencySession: ensureAgencySessionGuard,
    ensurePatientSession,
    redirectIfPatientLoggedIn,
    redirectIfAgencyLoggedIn,
    completePatientLogin,
    completeAgencyLogin: completeAgencyLoginGuard,
    loginPatientWithWxCode,
  }
}
