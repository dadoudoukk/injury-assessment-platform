import { post } from '@/utils/request'
import type { LoginResponse, PasswordLoginBody, WxLoginBody } from '@/types/auth'

export function loginWithPassword(body: PasswordLoginBody) {
  return post<LoginResponse>('/login', body)
}

export function wxLoginPatient(body: WxLoginBody) {
  return post<LoginResponse>('/login/wx', body)
}

export function wxLoginAgency(body: WxLoginBody) {
  return post<LoginResponse>('/login/wx/agency', body)
}
