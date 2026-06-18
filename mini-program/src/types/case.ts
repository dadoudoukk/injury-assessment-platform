import type { CaseStatusValue } from '@/constants/status'

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
}

export interface CaseStats {
  total: number
  pending: number
  accepted: number
  inProgress: number
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
