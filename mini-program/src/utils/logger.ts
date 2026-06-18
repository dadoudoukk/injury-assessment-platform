type TrackPayload = Record<string, unknown>

const isDev = import.meta.env.DEV

function safeStringify(value: unknown): string {
  try {
    return JSON.stringify(value)
  } catch {
    return String(value)
  }
}

/** 业务埋点（当前本地记录，预留后端上报接口） */
export function trackEvent(event: string, payload?: TrackPayload) {
  const record = { event, payload, ts: Date.now() }
  if (isDev) {
    console.log('[track]', record)
  }
  // 后续可接入：post('/analytics/event', record, { silent: true })
}

/** 页面浏览埋点 */
export function trackPageView(page: string, extra?: TrackPayload) {
  trackEvent('page_view', { page, ...extra })
}

/** 异常记录（配合 request 层与页面 catch 使用） */
export function reportError(error: unknown, context?: TrackPayload) {
  const message = error instanceof Error ? error.message : String(error)
  const stack = error instanceof Error ? error.stack : undefined

  console.error('[error]', message, context, error)

  trackEvent('error', {
    message,
    stack,
    ...context,
  })
}

/** 开发调试日志 */
export function logDebug(tag: string, ...args: unknown[]) {
  if (!isDev) return
  console.log(`[${tag}]`, ...args.map((a) => (typeof a === 'object' ? safeStringify(a) : a)))
}
