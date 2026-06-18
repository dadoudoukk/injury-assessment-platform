import { APP_COPY } from '@/constants/copy'

const TOAST_DURATION = 2000

/** 成功提示 */
export function showSuccess(title: string) {
  uni.showToast({ title, icon: 'success', duration: TOAST_DURATION })
}

/** 错误 / 校验提示（无图标） */
export function showError(title: string) {
  uni.showToast({ title, icon: 'none', duration: TOAST_DURATION })
}

/** 普通信息提示 */
export function showInfo(title: string) {
  uni.showToast({ title, icon: 'none', duration: TOAST_DURATION })
}

/** 从 Error 或字符串提取可展示文案 */
export function getErrorMessage(error: unknown, fallback: string = APP_COPY.requestFailed): string {
  if (error instanceof Error && error.message) return error.message
  if (typeof error === 'string' && error) return error
  return fallback
}

/** 展示接口或业务错误（请求层已 toast 时可传 silent） */
export function showRequestError(error: unknown, fallback?: string) {
  showError(getErrorMessage(error, fallback))
}

export interface ConfirmOptions {
  title?: string
  content: string
  confirmText?: string
  cancelText?: string
  showCancel?: boolean
}

/** 确认弹窗，返回用户是否点击确认 */
export function showConfirm(options: ConfirmOptions): Promise<boolean> {
  return new Promise((resolve) => {
    uni.showModal({
      title: options.title ?? '提示',
      content: options.content,
      confirmText: options.confirmText ?? '确定',
      cancelText: options.cancelText ?? '取消',
      showCancel: options.showCancel ?? true,
      confirmColor: '#2563EB',
      success: (res) => resolve(!!res.confirm),
      fail: () => resolve(false),
    })
  })
}

/** 仅确认按钮的结果弹窗 */
export function showAlert(title: string, content: string): Promise<void> {
  return new Promise((resolve) => {
    uni.showModal({
      title,
      content,
      showCancel: false,
      confirmColor: '#2563EB',
      complete: () => resolve(),
    })
  })
}
