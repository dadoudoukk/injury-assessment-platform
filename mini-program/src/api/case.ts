import { summarizeCaseStatsProcessing } from '@/constants/status'
import type {
  AppraisalVideosSubmitBody,
  ApplicationDetail,
  ApplicationItem,
  ApplicationResubmitBody,
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

export function fetchMyApplications() {
  return get<{ list: ApplicationItem[] }>('/biz/case/application/mine')
}

export function fetchApplicationDetail(applicationId: string | number) {
  return get<ApplicationDetail>(`/biz/case/application/${applicationId}`)
}

export function resubmitApplication(
  applicationId: string | number,
  body: ApplicationResubmitBody,
) {
  return post<void>(`/biz/case/application/${applicationId}/resubmit`, {
    bizType: 'case_submit',
    bizId: applicationId,
    ...body,
  })
}

export function fetchCaseDetail(caseId: string | number) {
  return get<CaseDetail>(`/biz/case/${caseId}`)
}

export function fetchCaseStats() {
  return get<CaseStats>('/biz/case/stats')
}

/** 工作台顶部三项聚合：待处理 / 处理中 / 已完成（处理中不含已打回） */
export function fetchCaseStatsSummary(): Promise<CaseStatsSummary> {
  return fetchCaseStats().then((stats) => ({
    pending: stats.pending,
    processing: summarizeCaseStatsProcessing(stats),
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
