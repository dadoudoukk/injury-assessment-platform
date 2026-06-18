import { ref } from 'vue'

/** 页面级 loading 遮罩，支持嵌套调用 */
export function usePageLoading(defaultTitle = '加载中...') {
  let depth = 0

  const isLoading = ref(false)
  const title = ref(defaultTitle)

  function show(loadingTitle?: string) {
    depth++
    if (depth === 1) {
      isLoading.value = true
      title.value = loadingTitle || defaultTitle
      uni.showLoading({ title: title.value, mask: true })
    }
  }

  function hide() {
    depth = Math.max(0, depth - 1)
    if (depth === 0) {
      isLoading.value = false
      uni.hideLoading()
    }
  }

  async function withLoading<T>(task: () => Promise<T>, loadingTitle?: string): Promise<T> {
    show(loadingTitle)
    try {
      return await task()
    } finally {
      hide()
    }
  }

  return {
    isLoading,
    title,
    show,
    hide,
    withLoading,
  }
}
