import { computed, reactive, ref } from 'vue'
import {
  acceptCase,
  fetchCaseDetail,
  submitAppraisalVideos as apiSubmitAppraisalVideos,
  submitDocumentNumber as apiSubmitDocumentNumber,
} from '@/api/case'
import { useFileUpload, type UploadedFileItem } from '@/composables/useFileUpload'
import { usePageLoading } from '@/composables/usePageLoading'
import type { CaseStatusValue } from '@/constants/status'
import { CASE_STATUS, getCaseStatusLabel } from '@/constants/status'
import { FEEDBACK_COPY } from '@/constants/copy'
import { fetchAndSetUserInfo } from '@/services/user-session'
import type { CaseDetail } from '@/types/case'
import { ensureAgencySession } from '@/utils/agency-auth'
import { showError, showSuccess } from '@/utils/feedback'
import { reportError } from '@/utils/logger'
import { resolveFileUrl } from '@/utils/request'
import { isAgencyUser, normalizeCaseStatus } from '@/utils/role'
import { useUserStore } from '@/store/modules/user'

const MAX_VIDEO_COUNT = 9

export function useCaseDetail() {
  const userStore = useUserStore()
  const pageLoading = usePageLoading('加载中...')
  const fileUpload = useFileUpload({ maxCount: MAX_VIDEO_COUNT })

  const caseId = ref('')
  const caseDetail = ref<CaseDetail | null>(null)
  const submitLoading = ref(false)
  const loadError = ref('')
  let skipNextDetailRefresh = false

  const form = reactive({
    appraisalVideos: [] as UploadedFileItem[],
    documentNumber: '',
    electronicCertificate: null as UploadedFileItem | null,
  })

  const isPatientMode = computed(() => !isAgencyUser(userStore.userInfo))

  const caseStatus = computed(() => normalizeCaseStatus(caseDetail.value?.status))

  const canCallPhone = computed(() => {
    if (!caseDetail.value) return false
    if (isPatientMode.value) return true
    return caseStatus.value !== CASE_STATUS.PENDING_CONFIRM
  })

  const getStatusText = getCaseStatusLabel

  const mapServerVideos = (videos: UploadedFileItem[]) =>
    videos.map((v, i) => ({
      id: v.id || `server-${i}-${v.url}`,
      name: v.name || `视频${i + 1}`,
      url: resolveFileUrl(v.url),
      thumb: v.thumb,
      thumbBroken: false,
    }))

  const initFormVideos = (status: number, videos?: UploadedFileItem[]) => {
    if (status === CASE_STATUS.REWORK && Array.isArray(videos) && videos.length > 0) {
      form.appraisalVideos = mapServerVideos(videos)
      return
    }
    form.appraisalVideos = []
  }

  const fetchDetail = async (options?: { preserveVideos?: boolean }) => {
    loadError.value = ''
    try {
      await pageLoading.withLoading(async () => {
        const res = await fetchCaseDetail(caseId.value)
        if (res) {
          const status = normalizeCaseStatus(res.status)
          caseDetail.value = {
            ...res,
            status: status as CaseStatusValue,
          }
          if (!options?.preserveVideos) {
            initFormVideos(status, res.appraisalVideos as UploadedFileItem[] | undefined)
          }
          form.documentNumber = res.documentNumber || ''
          form.electronicCertificate = res.electronicCertificate?.url
            ? {
                id: 'server-cert',
                name: res.electronicCertificate.name || '电子证书.pdf',
                url: resolveFileUrl(res.electronicCertificate.url),
              }
            : null
        } else {
          caseDetail.value = null
          loadError.value = 'not_found'
        }
      })
    } catch (error) {
      loadError.value = 'fetch_failed'
      reportError(error, { scope: 'case_detail', caseId: caseId.value })
    }
  }

  const initFromOptions = async (id?: string) => {
    if (!id) return
    caseId.value = id
    await fetchDetail()
  }

  const handleShow = async () => {
    if (userStore.token) {
      await fetchAndSetUserInfo()
    }
    if (isAgencyUser(userStore.userInfo)) {
      const ok = await ensureAgencySession(false)
      if (!ok) return
    }
    if (skipNextDetailRefresh) {
      skipNextDetailRefresh = false
      return
    }
    if (
      caseId.value &&
      form.appraisalVideos.length === 0 &&
      !form.electronicCertificate &&
      !fileUpload.isUploading.value
    ) {
      await fetchDetail()
    }
  }

  const callPhone = (phone: string) => {
    if (!phone || phone.includes('*')) return
    uni.makePhoneCall({ phoneNumber: phone })
  }

  const onThumbError = (file: UploadedFileItem) => {
    file.thumbBroken = true
  }

  const previewVideo = (file: UploadedFileItem) => {
    const previewUrl = file.localPath || resolveFileUrl(file.url)
    if (!previewUrl) return
    uni.previewMedia({
      sources: [{ url: previewUrl, type: 'video' }],
      fail: () => showError('视频预览失败，请检查网络或域名配置'),
    })
  }

  const chooseVideo = async () => {
    skipNextDetailRefresh = true
    const item = await fileUpload.chooseAndUploadVideo(form.appraisalVideos.length, MAX_VIDEO_COUNT)
    if (item) {
      form.appraisalVideos.push(item)
    }
  }

  const removeVideo = (index: number) => {
    form.appraisalVideos.splice(index, 1)
  }

  const chooseCertificate = async () => {
    skipNextDetailRefresh = true
    const item = await fileUpload.chooseAndUploadPdf()
    if (item) {
      form.electronicCertificate = item
    }
  }

  const removeCertificate = () => {
    form.electronicCertificate = null
  }

  const openPdfDocument = (url: string) => {
    if (!url) return
    uni.showLoading({ title: '打开中...', mask: true })
    uni.downloadFile({
      url,
      success: (res) => {
        if (res.statusCode === 200) {
          uni.openDocument({
            filePath: res.tempFilePath,
            showMenu: true,
            fail: () => showError('无法打开 PDF'),
          })
        } else {
          showError('下载失败')
        }
      },
      fail: () => showError('下载失败'),
      complete: () => uni.hideLoading(),
    })
  }

  const previewCertificate = () => {
    const cert = form.electronicCertificate
    if (!cert) return
    openPdfDocument(cert.localPath || cert.url)
  }

  const previewServerCertificate = () => {
    const cert = caseDetail.value?.electronicCertificate
    if (!cert?.url) return
    openPdfDocument(resolveFileUrl(cert.url))
  }

  const handleAccept = async () => {
    submitLoading.value = true
    try {
      await acceptCase(caseId.value)
      showSuccess(FEEDBACK_COPY.acceptSuccess)
      await fetchDetail()
    } catch (error) {
      reportError(error, { scope: 'accept_case', caseId: caseId.value })
    } finally {
      submitLoading.value = false
    }
  }

  const submitVideos = async () => {
    if (form.appraisalVideos.length === 0) {
      return showError('请至少上传一个视频')
    }
    submitLoading.value = true
    try {
      await apiSubmitAppraisalVideos(caseId.value, {
        appraisalVideos: form.appraisalVideos.map(({ name, url }) => ({ name, url })),
      })
      showSuccess(FEEDBACK_COPY.submitSuccess)
      await fetchDetail()
    } catch (error) {
      reportError(error, { scope: 'submit_videos', caseId: caseId.value })
    } finally {
      submitLoading.value = false
    }
  }

  const submitDocumentNumber = async () => {
    if (!form.documentNumber.trim()) {
      return showError('请输入文书编号')
    }
    if (!form.electronicCertificate?.url) {
      return showError('请上传电子证书')
    }
    submitLoading.value = true
    try {
      await apiSubmitDocumentNumber(caseId.value, {
        documentNumber: form.documentNumber.trim(),
        electronicCertificate: {
          name: form.electronicCertificate.name,
          url: form.electronicCertificate.url,
        },
      })
      showSuccess(FEEDBACK_COPY.submitSuccess)
      await fetchDetail()
    } catch (error) {
      reportError(error, { scope: 'submit_document', caseId: caseId.value })
    } finally {
      submitLoading.value = false
    }
  }

  return {
    MAX_VIDEO_COUNT,
    caseId,
    caseDetail,
    form,
    submitLoading,
    detailLoading: pageLoading.isLoading,
    loadError,
    isPatientMode,
    caseStatus,
    canCallPhone,
    getStatusText,
    initFromOptions,
    handleShow,
    fetchDetail,
    callPhone,
    onThumbError,
    previewVideo,
    chooseVideo,
    removeVideo,
    chooseCertificate,
    removeCertificate,
    previewCertificate,
    previewServerCertificate,
    handleAccept,
    submitVideos,
    submitDocumentNumber,
  }
}
