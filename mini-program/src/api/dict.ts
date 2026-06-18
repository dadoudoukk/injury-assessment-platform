import { get } from '@/utils/request'
import type { DictOption } from '@/types/dict'

export function fetchDictByCode(dictCode: string) {
  return get<DictOption[]>(`/dict/data/${dictCode}`)
}

export function fetchAccidentTypes() {
  return fetchDictByCode('biz_accident_type')
}

export function fetchInjuryTypes() {
  return fetchDictByCode('biz_injury_type')
}
