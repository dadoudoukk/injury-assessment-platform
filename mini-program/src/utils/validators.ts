import type { AgencyRegisterBody, CaseCreateBody } from '@/types/case'
import type { UploadedFileItem } from '@/composables/useFileUpload'
import { PASSWORD_COPY } from '@/constants/copy'
import { buildMaterialAttachments } from '@/utils/attachment'

export interface ValidationResult<T extends string = keyof CaseCreateBody> {
  valid: boolean
  message?: string
  field?: T
}

const PHONE_PATTERN = /^1[3-9]\d{9}$/

export function validatePhone(phone: string): ValidationResult {
  const trimmed = phone.trim()
  if (!trimmed) {
    return { valid: false, message: '请输入联系电话', field: 'victimPhone' }
  }
  if (!PHONE_PATTERN.test(trimmed)) {
    return { valid: false, message: '请输入正确的手机号', field: 'victimPhone' }
  }
  return { valid: true }
}

export function validateCaseForm(form: CaseCreateBody): ValidationResult {
  if (!form.victimName.trim()) {
    return { valid: false, message: '请输入伤者姓名', field: 'victimName' }
  }

  const phoneResult = validatePhone(form.victimPhone)
  if (!phoneResult.valid) return phoneResult

  if (!form.reportDate) {
    return { valid: false, message: '请选择出险日期', field: 'reportDate' }
  }

  if (!form.province || !form.city || !form.district) {
    return { valid: false, message: '请选择出险地点', field: 'province' }
  }

  if (!form.accidentType) {
    return { valid: false, message: '请选择事故类型', field: 'accidentType' }
  }

  if (!form.injuryType) {
    return { valid: false, message: '请选择伤情类型', field: 'injuryType' }
  }

  if (!form.reportNumber.trim()) {
    return { valid: false, message: '请输入出险报案号', field: 'reportNumber' }
  }

  if (!form.insuranceCompany.trim()) {
    return { valid: false, message: '请输入承保保险公司', field: 'insuranceCompany' }
  }

  const policyCount = form.policyImages?.length || 0
  if (policyCount < 1) {
    return { valid: false, message: '请至少上传 1 张保单图片', field: 'policyImages' as keyof CaseCreateBody }
  }

  return { valid: true }
}

export function validateCaseMaterials(
  policyImages: UploadedFileItem[],
  accidentDecisionImages: UploadedFileItem[] = [],
): ValidationResult {
  if (policyImages.length < 1) {
    return { valid: false, message: '请至少上传 1 张保单图片' }
  }
  const all = [...policyImages, ...accidentDecisionImages]
  for (const file of all) {
    if (file.kind && file.kind !== 'image') {
      return { valid: false, message: '案件材料仅支持图片' }
    }
  }
  return { valid: true }
}

export function buildCaseCreatePayload(form: CaseCreateBody) {
  const policyImages = (form.policyImages || []).map(({ name, url, kind }) => ({
    name,
    url,
    kind: kind || 'image',
    category: 'policy' as const,
  }))
  const accidentDecisionImages = (form.accidentDecisionImages || []).map(({ name, url, kind }) => ({
    name,
    url,
    kind: kind || 'image',
    category: 'accident_decision' as const,
  }))
  return {
    ...form,
    policyImages,
    accidentDecisionImages,
    attachments: buildMaterialAttachments(policyImages, accidentDecisionImages),
  }
}

export function validateAgencyRegisterForm(
  form: AgencyRegisterBody,
): ValidationResult<keyof AgencyRegisterBody> {
  if (!form.agencyName.trim()) {
    return { valid: false, message: '请输入机构名称', field: 'agencyName' }
  }
  if (!form.contactPerson.trim()) {
    return { valid: false, message: '请输入联系人', field: 'contactPerson' }
  }

  const phone = form.contactPhone.trim()
  if (!phone) {
    return { valid: false, message: '请输入联系电话', field: 'contactPhone' }
  }
  if (!PHONE_PATTERN.test(phone)) {
    return { valid: false, message: '请输入正确的手机号', field: 'contactPhone' }
  }

  if (!form.province || !form.city || !form.district) {
    return { valid: false, message: '请选择所在地区', field: 'province' }
  }
  if (!form.address.trim()) {
    return { valid: false, message: '请输入详细地址', field: 'address' }
  }

  return { valid: true }
}

export type ChangePasswordField = 'oldPassword' | 'newPassword' | 'confirmPassword'
export type SetPasswordField = 'newPassword' | 'confirmPassword'

const FORBIDDEN_PLACEHOLDER_PASSWORDS = new Set(['123456', 'wx123456'])

export function validateChangePasswordForm(form: {
  oldPassword: string
  newPassword: string
  confirmPassword: string
}): ValidationResult<ChangePasswordField> {
  const oldPwd = form.oldPassword.trim()
  const pwd = form.newPassword.trim()
  const confirm = form.confirmPassword.trim()

  if (!oldPwd) {
    return { valid: false, message: PASSWORD_COPY.oldPasswordRequired, field: 'oldPassword' }
  }
  if (pwd.length < 6) {
    return { valid: false, message: PASSWORD_COPY.newPasswordMinLength, field: 'newPassword' }
  }
  if (pwd !== confirm) {
    return { valid: false, message: PASSWORD_COPY.passwordMismatch, field: 'confirmPassword' }
  }

  return { valid: true }
}

export function validateSetPasswordForm(form: {
  newPassword: string
  confirmPassword: string
}): ValidationResult<SetPasswordField> {
  const pwd = form.newPassword.trim()
  const confirm = form.confirmPassword.trim()

  if (pwd.length < 6) {
    return { valid: false, message: PASSWORD_COPY.passwordMinLength, field: 'newPassword' }
  }
  if (FORBIDDEN_PLACEHOLDER_PASSWORDS.has(pwd)) {
    return {
      valid: false,
      message: PASSWORD_COPY.forbiddenPlaceholderPassword,
      field: 'newPassword',
    }
  }
  if (pwd !== confirm) {
    return { valid: false, message: PASSWORD_COPY.passwordMismatch, field: 'confirmPassword' }
  }

  return { valid: true }
}
