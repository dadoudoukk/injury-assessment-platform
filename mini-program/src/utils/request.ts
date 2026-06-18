import { APP_COPY } from '@/constants/copy'
import { STORAGE_KEYS } from '@/constants/storage'
import type { ApiResponse } from '@/types/common'
import { clearSessionCredentials, redirectOnUnauthorized } from '@/utils/auth-redirect'
import { reportError } from '@/utils/logger'

export const BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

/** 将后端返回的文件 URL 转成小程序当前环境可访问的地址 */
export const resolveFileUrl = (fileUrl: string): string => {
  if (!fileUrl) return fileUrl
  if (!/^https?:\/\//i.test(fileUrl)) return fileUrl
  try {
    const apiOrigin = new URL(BASE_URL).origin
    const parsed = new URL(fileUrl)
    return `${apiOrigin}${parsed.pathname}${parsed.search}`
  } catch {
    return fileUrl
  }
}

const LOGIN_URLS = ['/login', '/login/wx', '/login/wx/agency']

const isLoginUrl = (url: string) => LOGIN_URLS.some((p) => url.startsWith(p))

export interface RequestOptions {
  /** 为 true 时不弹出错误 toast */
  silent?: boolean
  /** 为 true 时 401 不自动跳转 */
  skipAuthRedirect?: boolean
  header?: Record<string, string>
}

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE'

/** 去掉 undefined/null/空字符串，避免 GET 查询串出现 status=undefined 等非法值 */
function sanitizeQueryParams(params?: Record<string, unknown>): Record<string, unknown> | undefined {
  if (!params) return undefined

  const cleaned: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === '') continue
    cleaned[key] = value
  }

  return Object.keys(cleaned).length ? cleaned : undefined
}

function buildRequest<T>(
  url: string,
  method: HttpMethod,
  data?: unknown,
  options: RequestOptions = {},
): Promise<T> {
  const { silent = false, skipAuthRedirect = false, header = {} } = options

  return new Promise((resolve, reject) => {
    const token = isLoginUrl(url)
      ? ''
      : uni.getStorageSync(STORAGE_KEYS.TOKEN)

    uni.request({
      url: BASE_URL + url,
      method,
      data: data as UniApp.RequestOptions['data'],
      header: {
        'content-type': 'application/json',
        'x-access-token': token || '',
        ...header,
      },
      success: (res) => {
        const body = (res.data || {}) as ApiResponse<T>
        const { code, data: resData, msg } = body

        if (code === 200) {
          resolve(resData as T)
          return
        }

        if (code === 401) {
          const isLoginRequest = isLoginUrl(url)
          if (!silent) {
            uni.showToast({
              title: isLoginRequest
                ? msg || APP_COPY.loginFailed
                : msg || APP_COPY.sessionExpired,
              icon: 'none',
            })
          }
          if (!isLoginRequest && !skipAuthRedirect) {
            clearSessionCredentials()
            redirectOnUnauthorized()
          }
          reject(new Error(msg || APP_COPY.sessionExpired))
          return
        }

        if (!silent) {
          uni.showToast({ title: msg || APP_COPY.requestFailed, icon: 'none' })
        }
        reportError(new Error(msg || APP_COPY.requestFailed), { url, method, code })
        reject(new Error(msg || APP_COPY.requestFailed))
      },
      fail: (err) => {
        if (!silent) {
          uni.showToast({ title: APP_COPY.networkError, icon: 'none' })
        }
        reportError(err, { url, method, type: 'network' })
        reject(err)
      },
    })
  })
}

export const get = <T>(url: string, params?: Record<string, unknown>, options?: RequestOptions) =>
  buildRequest<T>(url, 'GET', sanitizeQueryParams(params), options)

export const post = <T>(url: string, data?: unknown, options?: RequestOptions) =>
  buildRequest<T>(url, 'POST', data, options)

export const put = <T>(url: string, data?: unknown, options?: RequestOptions) =>
  buildRequest<T>(url, 'PUT', data, options)

export const del = <T>(url: string, data?: unknown, options?: RequestOptions) =>
  buildRequest<T>(url, 'DELETE', data, options)

/** @deprecated 请使用 get/post/put/del，保留兼容旧调用 */
export const request = <T = unknown>(
  url: string,
  method: HttpMethod = 'GET',
  data?: unknown,
  header?: Record<string, string>,
): Promise<T> => buildRequest<T>(url, method, data, { header })
