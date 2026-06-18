import { get, post } from '@/utils/request'
import type { ChangePasswordBody, SetInitialPasswordBody, UserInfo } from '@/types/user'

export function fetchUserInfo() {
  return get<UserInfo>('/user/info')
}

export function changePassword(body: ChangePasswordBody) {
  return post<void>('/user/changePassword', body)
}

export function setInitialPassword(body: SetInitialPasswordBody) {
  return post<void>('/user/setInitialPassword', body)
}
