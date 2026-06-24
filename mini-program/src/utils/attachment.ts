import type {
  ApplicationBatchHistory,
  AttachmentCategory,
  AttachmentItem,
  AttachmentKind,
} from '@/types/case'
import { openRemotePdf } from '@/utils/file'
import { resolveFileUrl } from '@/utils/request'

export function inferAttachmentKind(url: string, name?: string): AttachmentKind {
  const probe = `${name || ''} ${url}`.toLowerCase()
  if (/\.pdf($|\?)/i.test(probe)) return 'pdf'
  if (/\.(png|jpe?g|gif|webp|bmp)($|\?)/i.test(probe)) return 'image'
  return 'file'
}

export function normalizeAttachment(
  raw: Record<string, unknown>,
): AttachmentItem | null {
  const url = String(raw.url || '').trim()
  if (!url) return null
  const name = String(raw.name || '').trim() || undefined
  const kind =
    raw.kind === 'image' || raw.kind === 'pdf' || raw.kind === 'file'
      ? raw.kind
      : inferAttachmentKind(url, name)
  const category =
    raw.category === 'policy' || raw.category === 'accident_decision'
      ? raw.category
      : undefined
  return { name, url, kind, category }
}

export function attachmentKey(file: Pick<AttachmentItem, 'url' | 'name'>): string {
  return `${file.url}|${file.name || ''}`
}

export function dedupeAttachments(items: AttachmentItem[]): AttachmentItem[] {
  const seen = new Set<string>()
  const result: AttachmentItem[] = []
  for (const item of items) {
    const key = attachmentKey(item)
    if (seen.has(key)) continue
    seen.add(key)
    result.push(item)
  }
  return result
}

export function extractAttachmentsFromPayload(
  payload?: Record<string, unknown>,
): AttachmentItem[] {
  const list = payload?.attachments
  if (!Array.isArray(list)) return []
  return list
    .filter((item): item is Record<string, unknown> => !!item && typeof item === 'object')
    .map(normalizeAttachment)
    .filter((item): item is AttachmentItem => item !== null)
}

export function extractCategorizedFromPayload(
  payload: Record<string, unknown> | undefined,
  category: AttachmentCategory,
  structuredField: 'policyImages' | 'accidentDecisionImages',
): AttachmentItem[] {
  if (!payload) return []
  const structured = payload[structuredField]
  const fromStructured = Array.isArray(structured)
    ? structured
        .filter((item): item is Record<string, unknown> => !!item && typeof item === 'object')
        .map(normalizeAttachment)
        .filter((item): item is AttachmentItem => item !== null)
    : []
  const fromAttachments = extractAttachmentsFromPayload(payload).filter(
    (item) => item.category === category,
  )
  return dedupeAttachments([...fromStructured, ...fromAttachments])
}

export function extractBatchAttachments(
  batch: ApplicationBatchHistory,
): AttachmentItem[] {
  return extractAttachmentsFromPayload(batch.submitPayload)
}

export function extractBatchPolicyImages(batch: ApplicationBatchHistory): AttachmentItem[] {
  return extractCategorizedFromPayload(batch.submitPayload, 'policy', 'policyImages')
}

export function extractBatchAccidentImages(batch: ApplicationBatchHistory): AttachmentItem[] {
  return extractCategorizedFromPayload(
    batch.submitPayload,
    'accident_decision',
    'accidentDecisionImages',
  )
}

export function buildMaterialAttachments(
  policyImages: AttachmentItem[],
  accidentDecisionImages: AttachmentItem[],
): AttachmentItem[] {
  const policy = policyImages.map((item) => ({
    ...item,
    kind: 'image' as const,
    category: 'policy' as const,
  }))
  const accident = accidentDecisionImages.map((item) => ({
    ...item,
    kind: 'image' as const,
    category: 'accident_decision' as const,
  }))
  return dedupeAttachments([...policy, ...accident])
}

export function openAttachment(file: AttachmentItem): void {
  if (!file.url) return
  const url = resolveFileUrl(file.url)
  const kind = file.kind || inferAttachmentKind(url, file.name)
  if (kind === 'pdf') {
    openRemotePdf(url)
    return
  }
  if (kind === 'image') {
    uni.previewImage({ urls: [url] })
    return
  }
  if (/\.pdf($|\?)/i.test(url)) {
    openRemotePdf(url)
    return
  }
  if (/\.(png|jpe?g|gif|webp|bmp)($|\?)/i.test(url)) {
    uni.previewImage({ urls: [url] })
    return
  }
  uni.showToast({ title: '暂不支持预览该文件类型', icon: 'none' })
}
