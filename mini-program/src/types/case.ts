import type { CaseStatusValue, AppStatusValue, AuditStatusValue } from '@/constants/status'

export interface CaseListQuery {
  pageNum?: number
  pageSize?: number
  status?: CaseStatusValue | null
  reportNumber?: string
  victimName?: string
}

export interface CaseItem {
  id: string
  reportNumber: string
  victimName: string
  victimPhone: string
  reportDate: string
  province: string
  city: string
  district: string
  accidentType: string
  injuryType?: string
  insuranceCompany: string
  status: CaseStatusValue
  agencyId?: number | null
  agencyName?: string | null
  reworkRemark?: string | null
  createdAt?: string
  updatedAt?: string
}

export interface AppraisalVideoItem {
  id?: string
  name: string
  url: string
  thumb?: string
}

export interface ElectronicCertificateItem {
  name: string
  url: string
}

export interface CaseDetail extends CaseItem {
  injuryType: string
  appraisalAmount?: string | null
  appraisalConclusion?: string | null
  reportFiles?: unknown[]
  appraisalVideos?: AppraisalVideoItem[]
  documentNumber?: string | null
  electronicCertificate?: ElectronicCertificateItem | null
  appraisalSubmittedAt?: string | null
  appraisalSubmittedBy?: string | null
  pendingAgencySubmitAuditId?: string | null
  documentFieldsSource?: string | null
  latestAgencySubmitRejectRemark?: string | null
  agencySubmitBatchHistory?: ApplicationBatchHistory[]
}

export type AttachmentKind = 'image' | 'pdf' | 'file'

export type AttachmentCategory = 'policy' | 'accident_decision'

export interface AttachmentItem {
  name?: string
  url: string
  kind?: AttachmentKind
  category?: AttachmentCategory
}

export interface ApplicationItem {
  id: string
  reportNumber: string
  victimName: string
  victimPhone: string
  reportDate: string
  province: string
  city: string
  district: string
  accidentType: string
  injuryType: string
  insuranceCompany: string
  appStatus: AppStatusValue
  caseId?: string | null
  rejectRemark?: string
  pendingAuditId?: string | null
  createdAt?: string
  updatedAt?: string
}

export interface ApplicationBatchHistory {
  id: string
  submitBatch: number
  status: AuditStatusValue
  submitPayload?: Record<string, unknown>
  auditRemark?: string
  auditedAt?: string | null
  createdAt?: string
}

export interface ApplicationDetail extends ApplicationItem {
  attachments: AttachmentItem[]
  policyImages?: AttachmentItem[]
  accidentDecisionImages?: AttachmentItem[]
  batchHistory?: ApplicationBatchHistory[]
}

export interface ApplicationResubmitBody {
  victimName?: string
  victimPhone?: string
  province?: string
  city?: string
  district?: string
  accidentType?: string
  injuryType?: string
  policyImages?: AttachmentItem[]
  accidentDecisionImages?: AttachmentItem[]
  attachments?: AttachmentItem[]
}

/** 患者端合并列表项 */
export type PatientListEntry =
  | { kind: 'application'; data: ApplicationItem; sortAt: number }
  | { kind: 'case'; data: CaseItem; sortAt: number }

export interface CaseStats {
  total: number
  pending: number
  accepted: number
  inProgress: number
  reportPendingAudit?: number
  completed: number
  rework: number
}

/** 工作台顶部三项聚合统计 */
export interface CaseStatsSummary {
  pending: number
  processing: number
  completed: number
}

export interface CaseCreateBody {
  victimName: string
  victimPhone: string
  reportDate: string
  province: string
  city: string
  district: string
  accidentType: string
  injuryType: string
  reportNumber: string
  insuranceCompany: string
  policyImages?: AttachmentItem[]
  accidentDecisionImages?: AttachmentItem[]
  attachments?: AttachmentItem[]
}

export interface AppraisalVideosSubmitBody {
  appraisalVideos: Array<{ name: string; url: string }>
}

export interface DocumentNumberSubmitBody {
  documentNumber: string
  electronicCertificate: { name: string; url: string }
}

export interface AgencyRegisterBody {
  agencyName: string
  contactPerson: string
  contactPhone: string
  province: string
  city: string
  district: string
  address: string
}
