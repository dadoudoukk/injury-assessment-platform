import { ref } from 'vue'
import { STORAGE_KEYS } from '@/constants/storage'
import { BASE_URL, resolveFileUrl } from '@/utils/request'
import { useUserStore } from '@/store/modules/user'

export interface UploadedFileItem {
  id: string
  name: string
  url: string
  localPath?: string
  thumb?: string
  thumbBroken?: boolean
}

export interface FileUploadOptions {
  maxCount?: number
  loadingTitle?: string
}

interface PickedFile {
  path?: string
  tempFilePath?: string
  name?: string
}

interface ChooseFileResult {
  tempFiles?: PickedFile[]
}

interface ChooseFileOptions {
  count: number
  type: 'file'
  extension?: string[]
  success: (res: ChooseFileResult) => void
  fail: () => void
}

interface FilePickerApi {
  chooseFile?: (options: ChooseFileOptions) => void
}

/** 视频 / PDF 上传封装，供案件详情等页面复用 */
export function useFileUpload(options: FileUploadOptions = {}) {
  const userStore = useUserStore()
  const loadingTitle = options.loadingTitle ?? '上传中...'

  let pendingCount = 0
  let uploadSeq = 0
  const isUploading = ref(false)

  function beginLoading() {
    pendingCount++
    if (pendingCount === 1) {
      isUploading.value = true
      uni.showLoading({ title: loadingTitle, mask: true })
    }
  }

  function endLoading() {
    pendingCount = Math.max(0, pendingCount - 1)
    if (pendingCount === 0) {
      isUploading.value = false
      uni.hideLoading()
    }
  }

  function getToken() {
    return userStore.token || uni.getStorageSync(STORAGE_KEYS.TOKEN)
  }

  function uploadFile(filePath: string, endpoint: string): Promise<string> {
    return new Promise((resolve, reject) => {
      beginLoading()
      uni.uploadFile({
        url: `${BASE_URL}${endpoint}`,
        filePath,
        name: 'file',
        header: { 'x-access-token': getToken() },
        success: (uploadRes) => {
          try {
            const resData = JSON.parse(uploadRes.data)
            if (resData.code === 200 && resData.data?.fileUrl) {
              resolve(resolveFileUrl(resData.data.fileUrl))
            } else {
              uni.showToast({ title: resData.msg || '上传失败', icon: 'none' })
              reject(new Error(resData.msg || '上传失败'))
            }
          } catch {
            uni.showToast({ title: '解析失败', icon: 'none' })
            reject(new Error('解析失败'))
          }
        },
        fail: () => {
          uni.showToast({ title: '上传异常', icon: 'none' })
          reject(new Error('上传异常'))
        },
        complete: () => endLoading(),
      })
    })
  }

  function uploadVideo(filePath: string, thumbPath?: string, name?: string): Promise<UploadedFileItem> {
    const itemId = `local-${Date.now()}-${++uploadSeq}`
    return uploadFile(filePath, '/file/upload/video').then((url) => ({
      id: itemId,
      name: name || '鉴定视频',
      url,
      localPath: filePath,
      thumb: thumbPath,
      thumbBroken: false,
    }))
  }

  function uploadPdf(filePath: string, fileName: string): Promise<UploadedFileItem> {
    return uploadFile(filePath, '/file/upload/pdf').then((url) => ({
      id: `pdf-${Date.now()}`,
      name: fileName,
      url,
      localPath: filePath,
    }))
  }

  function getLocalFilePicker(): FilePickerApi['chooseFile'] | undefined {
    const uniApi = uni as unknown as FilePickerApi
    if (typeof uniApi.chooseFile === 'function') return uniApi.chooseFile.bind(uniApi)

    const wxApi = (globalThis as { wx?: FilePickerApi }).wx
    if (typeof wxApi?.chooseFile === 'function') return wxApi.chooseFile.bind(wxApi)

    return undefined
  }

  function resolvePickedFile(file?: PickedFile): { path: string; name: string } | null {
    const filePath = file?.path || file?.tempFilePath
    if (!filePath) return null
    return {
      path: filePath,
      name: file.name || '电子证书.pdf',
    }
  }

  async function uploadPickedPdf(file?: PickedFile): Promise<UploadedFileItem | null> {
    const picked = resolvePickedFile(file)
    if (!picked) return null

    try {
      const item = await uploadPdf(picked.path, picked.name)
      uni.showToast({ title: '上传成功', icon: 'none' })
      return item
    } catch {
      return null
    }
  }

  function chooseMessagePdfFile(): Promise<UploadedFileItem | null> {
    return new Promise((resolve) => {
      uni.chooseMessageFile({
        count: 1,
        type: 'file',
        extension: ['pdf'],
        success: async (res) => {
          resolve(await uploadPickedPdf(res.tempFiles[0]))
        },
        fail: () => {
          uni.showToast({ title: '请选择 PDF 文件', icon: 'none' })
          resolve(null)
        },
      })
    })
  }

  function chooseAndUploadVideo(
    currentCount: number,
    maxCount = options.maxCount ?? 9,
  ): Promise<UploadedFileItem | null> {
    const remain = maxCount - currentCount
    if (remain <= 0) {
      uni.showToast({ title: `最多上传 ${maxCount} 个视频`, icon: 'none' })
      return Promise.resolve(null)
    }

    return new Promise((resolve) => {
      uni.chooseMedia({
        count: 1,
        mediaType: ['video'],
        sourceType: ['album', 'camera'],
        maxDuration: 300,
        success: async (res) => {
          const file = res.tempFiles[0]
          if (!file) {
            resolve(null)
            return
          }
          try {
            const item = await uploadVideo(
              file.tempFilePath,
              file.thumbTempFilePath,
              `鉴定视频${currentCount + 1}`,
            )
            uni.showToast({ title: '上传成功', icon: 'none' })
            resolve(item)
          } catch {
            resolve(null)
          }
        },
        fail: () => resolve(null),
      })
    })
  }

  function chooseAndUploadPdf(): Promise<UploadedFileItem | null> {
    const chooseFile = getLocalFilePicker()
    if (chooseFile) {
      return new Promise((resolve) => {
        chooseFile({
          count: 1,
          type: 'file',
          extension: ['pdf'],
          success: async (res) => {
            resolve(await uploadPickedPdf(res.tempFiles?.[0]))
          },
          fail: () => resolve(null),
        })
      })
    }

    uni.showToast({ title: '当前微信版本不支持本地文件选择，请从聊天文件选择 PDF', icon: 'none' })
    return new Promise((resolve) => {
      setTimeout(() => {
        chooseMessagePdfFile().then(resolve)
      }, 1200)
    })
  }

  return {
    isUploading,
    uploadVideo,
    uploadPdf,
    chooseAndUploadVideo,
    chooseAndUploadPdf,
  }
}
