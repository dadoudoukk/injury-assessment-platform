import type {
  AppraisalVideosSubmitBody,
  CaseCreateBody,
  CaseDetail,
  CaseItem,
  CaseListQuery,
  CaseStats,
  CaseStatsSummary,
  DocumentNumberSubmitBody,
} from '@/types/case'
import type { PageResult } from '@/types/common'
import { get, post } from '@/utils/request'

export function fetchCaseList(params: CaseListQuery) {
  return get<PageResult<CaseItem>>('/biz/case', params as Record<string, unknown>)
}

export function fetchCaseDetail(caseId: string | number) {
  return get<CaseDetail>(`/biz/case/${caseId}`)
}

export function fetchCaseStats() {
  return get<CaseStats>('/biz/case/stats')
}

/** 工作台顶部三项聚合：待处理 / 处理中 / 已完成 */
export function fetchCaseStatsSummary(): Promise<CaseStatsSummary> {
  return fetchCaseStats().then((stats) => ({
    pending: stats.pending,
    processing: stats.accepted + stats.inProgress + stats.rework,
    completed: stats.completed,
  }))
}

export function acceptCase(caseId: string | number) {
  return post<void>(`/biz/case/${caseId}/accept`)
}

export function createPatientCase(body: CaseCreateBody) {
  return post<void>('/biz/case/patient', body)
}

export function submitAppraisalVideos(
  caseId: string | number,
  body: AppraisalVideosSubmitBody,
) {
  return post<void>(`/biz/case/${caseId}/appraisal-videos`, body)
}

export function submitDocumentNumber(
  caseId: string | number,
  body: DocumentNumberSubmitBody,
) {
  return post<void>(`/biz/case/${caseId}/document-number`, body)
}
