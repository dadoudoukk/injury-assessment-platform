import { resolveFileUrl } from '@/utils/request'

/** 打开远程 PDF 文档 */
export function openRemotePdf(url: string): void {
  if (!url) return
  uni.showLoading({ title: '打开中...', mask: true })
  uni.downloadFile({
    url: resolveFileUrl(url),
    success: (res) => {
      if (res.statusCode === 200) {
        uni.openDocument({
          filePath: res.tempFilePath,
          showMenu: true,
          fail: () => uni.showToast({ title: '无法打开 PDF', icon: 'none' }),
        })
      } else {
        uni.showToast({ title: '下载失败', icon: 'none' })
      }
    },
    fail: () => uni.showToast({ title: '下载失败', icon: 'none' }),
    complete: () => uni.hideLoading(),
  })
}

/** 预览本地或远程视频 */
export function previewVideo(url: string): void {
  if (!url) return
  uni.previewMedia({
    sources: [{ url: resolveFileUrl(url), type: 'video' }],
    fail: () => {
      uni.showToast({ title: '视频预览失败，请检查网络或域名配置', icon: 'none' })
    },
  })
}
