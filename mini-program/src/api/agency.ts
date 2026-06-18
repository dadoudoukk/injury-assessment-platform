import type { AgencyRegisterBody } from '@/types/case'
import { post } from '@/utils/request'

export function registerAgency(body: AgencyRegisterBody) {
  return post<{ id?: string }>('/biz/agency/register', body)
}
