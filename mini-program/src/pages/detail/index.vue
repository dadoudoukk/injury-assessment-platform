<template>
  <view class="detail-container" v-if="caseDetail">
    <view class="header-section">
      <view class="status-wrapper">
        <text :class="['status-title', 'text-status-' + caseDetail.status]">
          {{ getStatusText(caseDetail.status) }}
        </text>
        <text class="report-no">报案号：{{ caseDetail.reportNumber }}</text>
      </view>
    </view>

    <!-- 基础信息区 -->
    <view class="section-block">
      <view class="section-title">案件基础信息</view>
      <view class="info-list">
        <view class="info-item" v-if="caseStatus === 5 && caseDetail.reworkRemark">
          <text class="info-label text-red">打回原因</text>
          <text class="info-value text-red font-bold">{{ caseDetail.reworkRemark }}</text>
        </view>
        <view class="info-item">
          <text class="info-label">伤者姓名</text>
          <text class="info-value">{{ caseDetail.victimName }}</text>
        </view>
        <view class="info-item">
          <text class="info-label">联系电话</text>
          <text
            :class="['info-value', canCallPhone ? 'text-blue' : '']"
            @click="canCallPhone && callPhone(caseDetail.victimPhone)"
          >
            {{ caseDetail.victimPhone }}
          </text>
        </view>
        <view class="info-item">
          <text class="info-label">出险地点</text>
          <text class="info-value">{{ caseDetail.province }}{{ caseDetail.city }}{{ caseDetail.district }}</text>
        </view>
        <view class="info-item">
          <text class="info-label">报案日期</text>
          <text class="info-value">{{ caseDetail.reportDate }}</text>
        </view>
        <view class="info-item">
          <text class="info-label">保险公司</text>
          <text class="info-value">{{ caseDetail.insuranceCompany }}</text>
        </view>
      </view>
    </view>

    <!-- 机构鉴定工作区 -->
    <view class="section-block" v-if="!isPatientMode">
      <view class="section-title">鉴定流转</view>

      <!-- 待确认：确认受理 -->
      <template v-if="caseStatus === 1">
        <view class="hint-text">请核实案件概况后确认受理，受理后可查看完整伤者信息并进行视频取证。</view>
        <button class="btn-primary mt-40" :loading="submitLoading" @click="handleAccept">确认受理</button>
      </template>

      <!-- 已受理 / 已打回：上传视频 -->
      <template v-if="caseStatus === 2 || caseStatus === 5">
        <view class="form-group">
          <text class="form-label required">鉴定取证视频</text>
          <text class="upload-hint">可多次上传，最多 9 个</text>
          <view class="video-list">
            <view
              class="video-cell"
              v-for="(file, index) in form.appraisalVideos"
              :key="file.id"
              @click="previewVideo(file)"
            >
              <image
                v-if="file.thumb && !file.thumbBroken"
                class="video-thumb"
                :src="file.thumb"
                mode="aspectFill"
                @error="onThumbError(file)"
              />
              <view v-else class="video-thumb video-thumb-placeholder" />
              <view class="play-overlay">
                <text class="play-icon">▶</text>
              </view>
              <view class="delete-btn" @click.stop="removeVideo(index)">✕</view>
            </view>
            <view class="upload-btn" @click="chooseVideo" v-if="form.appraisalVideos.length < MAX_VIDEO_COUNT">
              <text class="add-icon">+</text>
              <text class="add-text">上传视频</text>
            </view>
          </view>
        </view>
        <button class="btn-primary mt-60" :loading="submitLoading" @click="submitVideos">提交鉴定视频</button>
      </template>

      <!-- 鉴定中：只读视频 + 填文书编号 -->
      <template v-if="caseStatus === 3">
        <view class="form-group" v-if="caseDetail.appraisalVideos?.length">
          <text class="form-label">已提交视频（只读）</text>
          <view class="readonly-video-list">
            <text class="readonly-video-item" v-for="(v, i) in caseDetail.appraisalVideos" :key="i">
              {{ v.name || '视频' + (i + 1) }}
            </text>
          </view>
        </view>
        <view class="form-group">
          <text class="form-label required">鉴定文书编号</text>
          <input
            class="form-input"
            v-model="form.documentNumber"
            placeholder="请输入鉴定文书编号"
            maxlength="50"
            placeholder-class="ph-color"
          />
        </view>
        <button class="btn-primary mt-60" :loading="submitLoading" @click="submitDocumentNumber">提交文书编号</button>
      </template>

      <!-- 已完成：全只读 -->
      <template v-if="caseStatus === 4">
        <view class="info-list">
          <view class="info-item" v-if="caseDetail.documentNumber">
            <text class="info-label">文书编号</text>
            <text class="info-value highlight">{{ caseDetail.documentNumber }}</text>
          </view>
          <view class="info-item col-item" v-if="caseDetail.appraisalVideos?.length">
            <text class="info-label mb-16">鉴定视频</text>
            <view class="readonly-video-list">
              <text class="readonly-video-item" v-for="(v, i) in caseDetail.appraisalVideos" :key="i">
                {{ v.name || '视频' + (i + 1) }}
              </text>
            </view>
          </view>
          <!-- 历史数据只读 -->
          <view class="info-item" v-if="caseDetail.appraisalAmount">
            <text class="info-label">理赔金额（历史）</text>
            <text class="info-value">¥{{ caseDetail.appraisalAmount }}</text>
          </view>
          <view class="info-item col-item" v-if="caseDetail.appraisalConclusion">
            <text class="info-label mb-16">鉴定结论（历史）</text>
            <view class="readonly-box">{{ caseDetail.appraisalConclusion }}</view>
          </view>
        </view>
      </template>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { request, BASE_URL, resolveFileUrl } from '@/utils/request'
import { isAgencyUser, normalizeCaseStatus } from '@/utils/role'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()
const caseId = ref('')
const caseDetail = ref<any>(null)
const submitLoading = ref(false)

const isPatientMode = computed(() => !isAgencyUser(userStore.userInfo))

const caseStatus = computed(() => normalizeCaseStatus(caseDetail.value?.status))

const canCallPhone = computed(() => {
  if (!caseDetail.value) return false
  if (isPatientMode.value) return true
  return caseStatus.value !== 1
})

const MAX_VIDEO_COUNT = 9

interface AppraisalVideoFormItem {
  id: string
  name: string
  url: string
  localPath?: string
  thumb?: string
  thumbBroken?: boolean
}

const form = reactive({
  appraisalVideos: [] as AppraisalVideoFormItem[],
  documentNumber: ''
})

let uploadPendingCount = 0
let uploadSeq = 0
let loadingDepth = 0
let skipNextDetailRefresh = false

const showPageLoading = (title: string) => {
  loadingDepth++
  if (loadingDepth === 1) {
    uni.showLoading({ title, mask: true })
  }
}

const hidePageLoading = () => {
  loadingDepth = Math.max(0, loadingDepth - 1)
  if (loadingDepth === 0) {
    uni.hideLoading()
  }
}

const beginUploadLoading = () => {
  uploadPendingCount++
  if (uploadPendingCount === 1) {
    showPageLoading('上传中...')
  }
}

const endUploadLoading = () => {
  uploadPendingCount = Math.max(0, uploadPendingCount - 1)
  if (uploadPendingCount === 0) {
    hidePageLoading()
  }
}

const mapServerVideos = (videos: AppraisalVideoFormItem[]) =>
  videos.map((v, i) => ({
    id: v.id || `server-${i}-${v.url}`,
    name: v.name || `视频${i + 1}`,
    url: resolveFileUrl(v.url),
    thumb: v.thumb,
    thumbBroken: false
  }))

const initFormVideos = (status: number, videos?: AppraisalVideoFormItem[]) => {
  if (status === 5 && Array.isArray(videos) && videos.length > 0) {
    form.appraisalVideos = mapServerVideos(videos)
    return
  }
  form.appraisalVideos = []
}

onLoad(async (options) => {
  if (options?.id) {
    caseId.value = options.id
    await fetchDetail()
  }
})

onShow(async () => {
  if (userStore.token) {
    await userStore.fetchUserInfo()
  }
  if (skipNextDetailRefresh) {
    skipNextDetailRefresh = false
    return
  }
  // 已有本地未提交视频时不刷新，避免覆盖用户刚选的内容
  if (caseId.value && form.appraisalVideos.length === 0 && uploadPendingCount === 0) {
    await fetchDetail()
  }
})

const fetchDetail = async (options?: { preserveVideos?: boolean }) => {
  showPageLoading('加载中...')
  try {
    const res = await request(`/biz/case/${caseId.value}`, 'GET')
    if (res) {
      const status = normalizeCaseStatus(res.status)
      caseDetail.value = {
        ...res,
        status
      }
      if (!options?.preserveVideos) {
        initFormVideos(status, res.appraisalVideos)
      }
      form.documentNumber = res.documentNumber || ''
    }
  } catch (error) {
    console.error('Fetch detail error:', error)
  } finally {
    hidePageLoading()
  }
}

const getStatusText = (status: number) => {
  const map: Record<number, string> = {
    1: '待确认',
    2: '已受理',
    3: '鉴定中',
    4: '已完成',
    5: '已打回'
  }
  return map[status] || '未知'
}

const callPhone = (phone: string) => {
  if (!phone || phone.includes('*')) return
  uni.makePhoneCall({ phoneNumber: phone })
}

const onThumbError = (file: AppraisalVideoFormItem) => {
  file.thumbBroken = true
}

const previewVideo = (file: AppraisalVideoFormItem) => {
  const previewUrl = file.localPath || resolveFileUrl(file.url)
  if (!previewUrl) return
  uni.previewMedia({
    sources: [{ url: previewUrl, type: 'video' }],
    fail: () => {
      uni.showToast({ title: '视频预览失败，请检查网络或域名配置', icon: 'none' })
    }
  })
}

const chooseVideo = () => {
  const remain = MAX_VIDEO_COUNT - form.appraisalVideos.length
  if (remain <= 0) {
    return uni.showToast({ title: `最多上传 ${MAX_VIDEO_COUNT} 个视频`, icon: 'none' })
  }
  skipNextDetailRefresh = true
  uni.chooseMedia({
    count: 1,
    mediaType: ['video'],
    sourceType: ['album', 'camera'],
    maxDuration: 300,
    success: (res) => {
      const file = res.tempFiles[0]
      if (!file) return
      if (form.appraisalVideos.length >= MAX_VIDEO_COUNT) {
        return uni.showToast({ title: `最多上传 ${MAX_VIDEO_COUNT} 个视频`, icon: 'none' })
      }
      uploadVideo(file.tempFilePath, file.thumbTempFilePath)
    }
  })
}

const uploadVideo = (filePath: string, thumbPath?: string) => {
  beginUploadLoading()
  const token = userStore.token || uni.getStorageSync('token')
  const videoIndex = ++uploadSeq
  const itemId = `local-${Date.now()}-${videoIndex}`
  uni.uploadFile({
    url: `${BASE_URL}/file/upload/video`,
    filePath,
    name: 'file',
    header: { 'x-access-token': token },
    success: (uploadRes) => {
      try {
        const resData = JSON.parse(uploadRes.data)
        if (resData.code === 200 && resData.data?.fileUrl) {
          form.appraisalVideos.push({
            id: itemId,
            name: `鉴定视频${form.appraisalVideos.length + 1}`,
            url: resolveFileUrl(resData.data.fileUrl),
            localPath: filePath,
            thumb: thumbPath,
            thumbBroken: false
          })
          uni.showToast({ title: '上传成功', icon: 'none' })
        } else {
          uni.showToast({ title: resData.msg || '上传失败', icon: 'none' })
        }
      } catch {
        uni.showToast({ title: '解析失败', icon: 'none' })
      }
    },
    fail: () => uni.showToast({ title: '上传异常', icon: 'none' }),
    complete: () => endUploadLoading()
  })
}

const removeVideo = (index: number) => {
  form.appraisalVideos.splice(index, 1)
}

const handleAccept = async () => {
  submitLoading.value = true
  try {
    await request(`/biz/case/${caseId.value}/accept`, 'POST')
    uni.showToast({ title: '已确认受理', icon: 'success' })
    fetchDetail()
  } catch (e) {
    console.error(e)
  } finally {
    submitLoading.value = false
  }
}

const submitVideos = async () => {
  if (form.appraisalVideos.length === 0) {
    return uni.showToast({ title: '请至少上传一个视频', icon: 'none' })
  }
  submitLoading.value = true
  try {
    await request(`/biz/case/${caseId.value}/appraisal-videos`, 'POST', {
      appraisalVideos: form.appraisalVideos.map(({ name, url }) => ({ name, url }))
    })
    uni.showToast({ title: '提交成功', icon: 'success' })
    fetchDetail()
  } catch (error) {
    console.error(error)
  } finally {
    submitLoading.value = false
  }
}

const submitDocumentNumber = async () => {
  if (!form.documentNumber.trim()) {
    return uni.showToast({ title: '请输入文书编号', icon: 'none' })
  }
  submitLoading.value = true
  try {
    await request(`/biz/case/${caseId.value}/document-number`, 'POST', {
      documentNumber: form.documentNumber.trim()
    })
    uni.showToast({ title: '提交成功', icon: 'success' })
    fetchDetail()
  } catch (error) {
    console.error(error)
  } finally {
    submitLoading.value = false
  }
}
</script>

<style scoped>
.detail-container {
  min-height: 100vh;
  background-color: #F9FAFB;
  padding-bottom: 80rpx;
}

.header-section {
  background-color: #FFFFFF;
  padding: 60rpx 40rpx;
  border-bottom: 2rpx solid #E5E7EB;
}

.status-wrapper {
  display: flex;
  flex-direction: column;
}

.status-title {
  font-size: 56rpx;
  font-weight: 600;
  margin-bottom: 16rpx;
}

.text-status-1 { color: #D97706; }
.text-status-2 { color: #2563EB; }
.text-status-3 { color: #7C3AED; }
.text-status-4 { color: #111827; }
.text-status-5 { color: #DC2626; }

.report-no {
  font-size: 28rpx;
  color: #6B7280;
  font-family: consolas, monospace;
}

.section-block {
  background-color: #FFFFFF;
  margin-top: 24rpx;
  padding: 40rpx;
  border-top: 2rpx solid #E5E7EB;
  border-bottom: 2rpx solid #E5E7EB;
}

.section-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #111827;
  margin-bottom: 40rpx;
  padding-left: 16rpx;
  border-left: 6rpx solid #111827;
}

.hint-text {
  font-size: 28rpx;
  color: #6B7280;
  line-height: 1.6;
}

.info-list {
  display: flex;
  flex-direction: column;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 30rpx 0;
  border-bottom: 2rpx solid #F3F4F6;
}

.info-item:last-child {
  border-bottom: none;
}

.info-item.col-item {
  flex-direction: column;
  align-items: flex-start;
}

.info-label {
  color: #6B7280;
  font-size: 30rpx;
  min-width: 160rpx;
}

.info-value {
  color: #111827;
  font-size: 30rpx;
  text-align: right;
  flex: 1;
}

.text-blue { color: #2563EB; }
.text-red { color: #DC2626; }
.font-bold { font-weight: 500; }
.highlight { font-size: 36rpx; font-weight: 600; }
.mb-16 { margin-bottom: 16rpx; }

.readonly-box {
  background-color: #F9FAFB;
  padding: 30rpx;
  border: 2rpx solid #E5E7EB;
  border-radius: 4rpx;
  width: 100%;
  box-sizing: border-box;
  color: #374151;
  font-size: 28rpx;
  line-height: 1.6;
}

.form-group { margin-bottom: 60rpx; }

.form-label {
  display: block;
  font-size: 28rpx;
  color: #374151;
  font-weight: 500;
  margin-bottom: 20rpx;
}

.form-label.required::after {
  content: " *";
  color: #DC2626;
}

.form-input {
  width: 100%;
  height: 80rpx;
  font-size: 32rpx;
  color: #111827;
  border-bottom: 2rpx solid #E5E7EB;
}

.ph-color { color: #9CA3AF; }

.upload-hint {
  display: block;
  font-size: 24rpx;
  color: #9CA3AF;
  margin: -8rpx 0 16rpx;
}

.video-list {
  display: flex;
  flex-wrap: wrap;
  gap: 20rpx;
}

.video-cell,
.upload-btn {
  position: relative;
  width: 160rpx;
  height: 160rpx;
  border-radius: 4rpx;
  box-sizing: border-box;
  overflow: hidden;
  flex-shrink: 0;
}

.video-cell {
  border: 2rpx solid #E5E7EB;
  background: #F9FAFB;
}

.video-thumb {
  width: 100%;
  height: 100%;
}

.video-thumb-placeholder {
  background: #D1D5DB;
}

.play-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(17, 24, 39, 0.18);
  pointer-events: none;
}

.play-icon {
  font-size: 44rpx;
  color: #FFFFFF;
  line-height: 1;
  text-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.35);
}

.delete-btn {
  position: absolute;
  top: 8rpx;
  right: 8rpx;
  width: 36rpx;
  height: 36rpx;
  background: rgba(255, 255, 255, 0.92);
  border: 2rpx solid #E5E7EB;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22rpx;
  color: #6B7280;
  z-index: 1;
}

.upload-btn {
  background-color: #F9FAFB;
  border: 2rpx dashed #D1D5DB;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.add-icon { font-size: 40rpx; color: #9CA3AF; margin-bottom: 8rpx; }
.add-text { font-size: 24rpx; color: #6B7280; }

.readonly-video-list { width: 100%; }
.readonly-video-item {
  display: block;
  padding: 20rpx 0;
  font-size: 28rpx;
  color: #374151;
  border-bottom: 2rpx solid #F3F4F6;
}

.btn-primary {
  background-color: #2563EB;
  color: #FFFFFF;
  font-size: 32rpx;
  font-weight: 500;
  height: 96rpx;
  line-height: 96rpx;
  border-radius: 8rpx;
}

.btn-primary::after { display: none; }
.mt-40 { margin-top: 40rpx; }
.mt-60 { margin-top: 60rpx; }
</style>
