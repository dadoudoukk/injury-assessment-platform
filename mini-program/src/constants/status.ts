/**
 * 案件状态枚举 — 与后端 biz_case.py CASE_STATUS_LABELS 保持一致
 */
export const CASE_STATUS = {
  PENDING_CONFIRM: 1,
  ACCEPTED: 2,
  APPRAISING: 3,
  COMPLETED: 4,
  REWORK: 5,
} as const

export type CaseStatusValue = (typeof CASE_STATUS)[keyof typeof CASE_STATUS]

export const CASE_STATUS_LABELS: Record<number, string> = {
  [CASE_STATUS.PENDING_CONFIRM]: '待确认',
  [CASE_STATUS.ACCEPTED]: '已受理',
  [CASE_STATUS.APPRAISING]: '鉴定中',
  [CASE_STATUS.COMPLETED]: '已完成',
  [CASE_STATUS.REWORK]: '已打回',
}

/** 状态标签颜色语义（供 StatusTag、列表标签等使用） */
export const CASE_STATUS_COLORS: Record<number, string> = {
  [CASE_STATUS.PENDING_CONFIRM]: '#D97706',
  [CASE_STATUS.ACCEPTED]: '#2563EB',
  [CASE_STATUS.APPRAISING]: '#2563EB',
  [CASE_STATUS.COMPLETED]: '#16A34A',
  [CASE_STATUS.REWORK]: '#DC2626',
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

/** 患者端：是否处于鉴定流程中（含已受理、鉴定中；不含已打回） */
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

/** 患者端：是否已打回 */
export function isPatientRework(status: unknown): boolean {
  return normalizeCaseStatusValue(status) === CASE_STATUS.REWORK
}

/** 患者端：进度条中间步骤文案 */
export function getPatientProgressMiddleLabel(status: unknown): string {
  return isPatientMatching(status) ? '匹配中' : '鉴定中'
}

/** 患者端：是否展示服务机构信息 */
export function shouldShowPatientAgencyInfo(
  status: unknown,
  agencyName?: string | null,
): boolean {
  return normalizeCaseStatusValue(status) >= CASE_STATUS.ACCEPTED && !!agencyName
}
