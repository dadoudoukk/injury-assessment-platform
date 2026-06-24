import { computed, ref } from 'vue'
import { fetchCaseList, fetchMyApplications } from '@/api/case'
import { APP_STATUS } from '@/constants/status'
import type { ApplicationItem, CaseItem, PatientListEntry } from '@/types/case'
import { getErrorMessage } from '@/utils/feedback'
import { parseDateTimeToMs } from '@/utils/format'
import { reportError } from '@/utils/logger'

const PAGE_SIZE = 10

function resolveSortAt(...candidates: Array<string | undefined | null>): number {
  for (const value of candidates) {
    const ms = parseDateTimeToMs(value)
    if (ms > 0) return ms
  }
  return 0
}

function toApplicationEntry(item: ApplicationItem): PatientListEntry {
  return {
    kind: 'application',
    data: item,
    sortAt: resolveSortAt(item.updatedAt, item.createdAt),
  }
}

function toCaseEntry(item: CaseItem): PatientListEntry {
  return {
    kind: 'case',
    data: item,
    sortAt: resolveSortAt(item.updatedAt, item.createdAt),
  }
}

/** 患者端：合并「我的申请」与「我的案件」列表 */
export function usePatientMergedList() {
  const applications = ref<ApplicationItem[]>([])
  const cases = ref<CaseItem[]>([])
  const caseTotal = ref(0)
  const casePageNum = ref(1)
  const loading = ref(false)
  const initialized = ref(false)
  const initialError = ref('')
  const loadMoreError = ref('')

  const visibleApplications = computed(() =>
    applications.value.filter(
      (item) =>
        item.appStatus !== APP_STATUS.APPROVED || !item.caseId,
    ),
  )

  const mergedList = computed<PatientListEntry[]>(() => {
    const entries: PatientListEntry[] = [
      ...visibleApplications.value.map(toApplicationEntry),
      ...cases.value.map(toCaseEntry),
    ]
    return entries.sort((a, b) => b.sortAt - a.sortAt)
  })

  const hasMore = computed(() => cases.value.length < caseTotal.value)

  async function loadApplications() {
    const res = await fetchMyApplications()
    applications.value = res?.list || []
  }

  async function loadCases(isRefresh: boolean) {
    const pageNum = isRefresh ? 1 : casePageNum.value
    const res = await fetchCaseList({ pageNum, pageSize: PAGE_SIZE })
    const items = res?.list || []
    caseTotal.value = res?.total || 0
    if (isRefresh) {
      cases.value = items
      casePageNum.value = 1
    } else {
      cases.value = [...cases.value, ...items]
    }
  }

  async function refresh() {
    if (loading.value) return
    loading.value = true
    initialError.value = ''
    loadMoreError.value = ''
    casePageNum.value = 1

    try {
      await Promise.all([loadApplications(), loadCases(true)])
    } catch (err) {
      const message = getErrorMessage(err)
      reportError(err, { scope: 'patient_merged_list', action: 'refresh' })
      if (mergedList.value.length === 0) {
        initialError.value = message
      }
    } finally {
      loading.value = false
      initialized.value = true
      uni.stopPullDownRefresh()
    }
  }

  async function loadMore() {
    if (!hasMore.value || loading.value) return

    if (loadMoreError.value) {
      loadMoreError.value = ''
    } else {
      casePageNum.value += 1
    }

    loading.value = true
    try {
      await loadCases(false)
      loadMoreError.value = ''
    } catch (err) {
      const message = getErrorMessage(err)
      reportError(err, { scope: 'patient_merged_list', action: 'loadMore' })
      loadMoreError.value = message
      casePageNum.value = Math.max(1, casePageNum.value - 1)
    } finally {
      loading.value = false
    }
  }

  function retryLoadMore() {
    if (!loadMoreError.value || loading.value || !hasMore.value) return
    loadMoreError.value = ''
    return loadMore()
  }

  return {
    mergedList,
    loading,
    initialized,
    initialError,
    loadMoreError,
    hasMore,
    refresh,
    loadMore,
    retryLoadMore,
  }
}
