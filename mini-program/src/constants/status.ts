/**
 * 案件状态枚举 — 与后端 biz_case.py CASE_STATUS_LABELS 保持一致
 */
export const CASE_STATUS = {
  PENDING_CONFIRM: 1,
  ACCEPTED: 2,
  APPRAISING: 3,
  COMPLETED: 4,
  REWORK: 5,
  REPORT_PENDING_AUDIT: 6,
} as const

export type CaseStatusValue = (typeof CASE_STATUS)[keyof typeof CASE_STATUS]

export const CASE_STATUS_LABELS: Record<number, string> = {
  [CASE_STATUS.PENDING_CONFIRM]: '待确认',
  [CASE_STATUS.ACCEPTED]: '已受理',
  [CASE_STATUS.APPRAISING]: '鉴定中',
  [CASE_STATUS.COMPLETED]: '已完成',
  [CASE_STATUS.REWORK]: '已打回',
  [CASE_STATUS.REPORT_PENDING_AUDIT]: '报告待平台审核',
}

/** 状态标签颜色语义（供 StatusTag、列表标签等使用） */
export const CASE_STATUS_COLORS: Record<number, string> = {
  [CASE_STATUS.PENDING_CONFIRM]: '#D97706',
  [CASE_STATUS.ACCEPTED]: '#2563EB',
  [CASE_STATUS.APPRAISING]: '#2563EB',
  [CASE_STATUS.COMPLETED]: '#16A34A',
  [CASE_STATUS.REWORK]: '#DC2626',
  [CASE_STATUS.REPORT_PENDING_AUDIT]: '#7C3AED',
}

/** 伤者报案申请单状态 — 与后端 biz_case_application.app_status 一致 */
export const APP_STATUS = {
  PENDING_AUDIT: 'pending_audit',
  REJECTED: 'rejected',
  APPROVED: 'approved',
} as const

export type AppStatusValue = (typeof APP_STATUS)[keyof typeof APP_STATUS]

export const APP_STATUS_LABELS: Record<string, string> = {
  [APP_STATUS.PENDING_AUDIT]: '审核中',
  [APP_STATUS.REJECTED]: '已驳回',
  [APP_STATUS.APPROVED]: '已通过',
}

export const APP_STATUS_COLORS: Record<string, string> = {
  [APP_STATUS.PENDING_AUDIT]: '#D97706',
  [APP_STATUS.REJECTED]: '#DC2626',
  [APP_STATUS.APPROVED]: '#16A34A',
}

/** 审核记录状态 — 与后端 biz_audit_record.status 一致 */
export const AUDIT_STATUS = {
  PENDING: 'pending',
  APPROVED: 'approved',
  REJECTED: 'rejected',
} as const

export type AuditStatusValue = (typeof AUDIT_STATUS)[keyof typeof AUDIT_STATUS]

export const AUDIT_STATUS_LABELS: Record<string, string> = {
  [AUDIT_STATUS.PENDING]: '待审核',
  [AUDIT_STATUS.APPROVED]: '已通过',
  [AUDIT_STATUS.REJECTED]: '已驳回',
}

export const AUDIT_STATUS_COLORS: Record<string, string> = {
  [AUDIT_STATUS.PENDING]: '#D97706',
  [AUDIT_STATUS.APPROVED]: '#16A34A',
  [AUDIT_STATUS.REJECTED]: '#DC2626',
}

const FALLBACK_STATUS_COLOR = '#6B7280'

export function normalizeCaseStatusValue(status: unknown): number {
  const n = Number(status)
  return Number.isFinite(n) ? n : 0
}

export function getCaseStatusLabel(status: unknown): string {
  const n = normalizeCaseStatusValue(status)
  if (!n) return '未知'
  return CASE_STATUS_LABELS[n] ?? '未知'
}

export function getCaseStatusColor(status: unknown): string {
  const n = normalizeCaseStatusValue(status)
  return CASE_STATUS_COLORS[n] ?? FALLBACK_STATUS_COLOR
}

/** 患者端：是否处于机构匹配中 */
export function isPatientMatching(status: unknown): boolean {
  return normalizeCaseStatusValue(status) === CASE_STATUS.PENDING_CONFIRM
}

export function getAppStatusLabel(status: unknown): string {
  const key = String(status || '').trim()
  if (!key) return '未知'
  return APP_STATUS_LABELS[key] ?? '未知'
}

export function getAppStatusColor(status: unknown): string {
  const key = String(status || '').trim()
  return APP_STATUS_COLORS[key] ?? FALLBACK_STATUS_COLOR
}

export function getAuditStatusLabel(status: unknown): string {
  const key = String(status || '').trim()
  if (!key) return '未知'
  return AUDIT_STATUS_LABELS[key] ?? '未知'
}

export function getAuditStatusColor(status: unknown): string {
  const key = String(status || '').trim()
  return AUDIT_STATUS_COLORS[key] ?? FALLBACK_STATUS_COLOR
}

/**
 * 工作台 / 患者端「处理中」统计口径：
 * 已受理 + 鉴定中 + 报告待平台审核；不含已打回（与 isPatientAppraisalActive 一致）。
 */
export function summarizeCaseStatsProcessing(stats: {
  accepted: number
  inProgress: number
}): number {
  return stats.accepted + stats.inProgress
}

/** 患者端：是否处于鉴定流程中（含已受理、鉴定中、报告待审；不含已打回） */
export function isPatientInAppraisalFlow(status: unknown): boolean {
  const s = normalizeCaseStatusValue(status)
  return s >= CASE_STATUS.ACCEPTED && s !== CASE_STATUS.REWORK
}

/** 患者端：鉴定流程中且尚未完成 */
export function isPatientAppraisalActive(status: unknown): boolean {
  const s = normalizeCaseStatusValue(status)
  return (
    s >= CASE_STATUS.ACCEPTED &&
    s < CASE_STATUS.COMPLETED &&
    s !== CASE_STATUS.REWORK
  )
}

/** 患者端：是否已出报告 */
export function isPatientReportCompleted(status: unknown): boolean {
  return normalizeCaseStatusValue(status) === CASE_STATUS.COMPLETED
}

/** 患者端：是否报告待平台审核 */
export function isPatientReportPendingAudit(status: unknown): boolean {
  return normalizeCaseStatusValue(status) === CASE_STATUS.REPORT_PENDING_AUDIT
}

/** 患者端：是否已打回 */
export function isPatientRework(status: unknown): boolean {
  return normalizeCaseStatusValue(status) === CASE_STATUS.REWORK
}

/** 患者端：进度条中间步骤文案 */
export function getPatientProgressMiddleLabel(status: unknown): string {
  const s = normalizeCaseStatusValue(status)
  if (isPatientMatching(status)) return '匹配中'
  if (s === CASE_STATUS.REPORT_PENDING_AUDIT) return '报告审核中'
  return '鉴定中'
}

/** 患者端：是否展示服务机构信息 */
export function shouldShowPatientAgencyInfo(
  status: unknown,
  agencyName?: string | null,
): boolean {
  return normalizeCaseStatusValue(status) >= CASE_STATUS.ACCEPTED && !!agencyName
}
