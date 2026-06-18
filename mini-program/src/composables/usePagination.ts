import { computed, ref } from 'vue'
import type { PageResult } from '@/types/common'
import { getErrorMessage } from '@/utils/feedback'
import { reportError } from '@/utils/logger'

export interface PaginationOptions {
  pageSize?: number
  immediate?: boolean
}

export function usePagination<T>(
  fetchFn: (params: { pageNum: number; pageSize: number }) => Promise<PageResult<T>>,
  options: PaginationOptions = {},
) {
  const pageSize = ref(options.pageSize ?? 10)
  const pageNum = ref(1)
  const total = ref(0)
  const list = ref([] as T[])
  const loading = ref(false)
  /** 是否已完成首次加载（用于区分首屏 loading 与空列表） */
  const initialized = ref(false)
  /** 首屏 / 整页刷新失败（仅当列表为空时展示全页错误态） */
  const initialError = ref('')
  /** 翻页加载失败（保留已加载数据，支持重试） */
  const loadMoreError = ref('')
  const hasMore = computed(() => list.value.length < total.value)

  async function fetchList(isRefresh = false) {
    if (loading.value) return

    loading.value = true
    if (isRefresh) {
      pageNum.value = 1
      initialError.value = ''
      loadMoreError.value = ''
    }

    try {
      const res = await fetchFn({
        pageNum: pageNum.value,
        pageSize: pageSize.value,
      })

      const items = res?.list || []
      total.value = res?.total || 0

      if (isRefresh) {
        list.value = items
      } else {
        list.value = [...list.value, ...items] as T[]
      }
      loadMoreError.value = ''
    } catch (err) {
      const message = getErrorMessage(err)
      reportError(err, { scope: 'pagination', pageNum: pageNum.value, isRefresh })

      if (isRefresh) {
        if (list.value.length === 0) {
          initialError.value = message
        }
      } else {
        loadMoreError.value = message
        pageNum.value = Math.max(1, pageNum.value - 1)
      }
    } finally {
      loading.value = false
      initialized.value = true
      uni.stopPullDownRefresh()
    }
  }

  function refresh() {
    return fetchList(true)
  }

  /** 触底加载；若上次翻页失败则自动重试同一页 */
  function loadMore() {
    if (!hasMore.value || loading.value) return

    if (loadMoreError.value) {
      loadMoreError.value = ''
      return fetchList(false)
    }

    pageNum.value += 1
    return fetchList(false)
  }

  function retryLoadMore() {
    if (!loadMoreError.value || loading.value || !hasMore.value) return
    loadMoreError.value = ''
    return fetchList(false)
  }

  function reset() {
    pageNum.value = 1
    total.value = 0
    list.value = []
    loading.value = false
    initialized.value = false
    initialError.value = ''
    loadMoreError.value = ''
  }

  return {
    list,
    pageNum,
    pageSize,
    total,
    loading,
    initialized,
    initialError,
    loadMoreError,
    hasMore,
    fetchList,
    refresh,
    loadMore,
    retryLoadMore,
    reset,
  }
}
