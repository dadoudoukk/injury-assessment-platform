/** 是否为鉴定机构/平台机构账号（优先 agencyId，兼容 roleName） */
export function isAgencyUser(userInfo: Record<string, unknown> | null | undefined): boolean {
  if (!userInfo) return false
  const agencyId = userInfo.agencyId
  if (agencyId != null && agencyId !== '') return true
  const roleName = String(userInfo.roleName || '')
  return roleName.includes('机构') || roleName.includes('管理员')
}

export function normalizeCaseStatus(status: unknown): number {
  const n = Number(status)
  return Number.isFinite(n) ? n : 0
}
