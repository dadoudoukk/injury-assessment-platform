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
        <view class="info-item" v-if="caseDetail.status === 4 && caseDetail.reworkRemark">
          <text class="info-label text-red">打回原因</text>
          <text class="info-value text-red font-bold">{{ caseDetail.reworkRemark }}</text>
        </view>
        <view class="info-item">
          <text class="info-label">伤者姓名</text>
          <text class="info-value">{{ caseDetail.victimName }}</text>
        </view>
        <view class="info-item">
          <text class="info-label">联系电话</text>
          <text class="info-value text-blue" @click="callPhone(caseDetail.victimPhone)">
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

    <!-- 鉴定工作区 -->
    <view class="section-block" v-if="caseDetail.status === 2 || caseDetail.status === 3 || caseDetail.status === 4">
      <view class="section-title">鉴定文书与结论</view>
      
      <!-- 待接单 -->
      <template v-if="caseDetail.status === 1 && !isPatientMode">
        <view class="action-buttons mt-40">
          <button class="btn-outline-danger" :loading="submitLoading" @click="handleReject">拒绝接单，退回平台</button>
        </view>
      </template>

      <!-- 鉴定中/已打回 (可编辑) -->
      <template v-if="caseDetail.status === 2 || caseDetail.status === 4">
        <view class="form-group">
          <text class="form-label required">预估理赔金额(元)</text>
          <input 
            class="form-input" 
            type="digit" 
            v-model="form.appraisalAmount" 
            placeholder="请输入金额" 
            placeholder-class="ph-color"
          />
        </view>
        
        <view class="form-group">
          <text class="form-label required">鉴定结论</text>
          <textarea 
            class="form-textarea" 
            v-model="form.appraisalConclusion" 
            placeholder="请详细描述伤情和鉴定结论..." 
            maxlength="1000"
            placeholder-class="ph-color"
          ></textarea>
        </view>

        <view class="form-group">
          <text class="form-label required">相关附件(图片/视频)</text>
          <view class="upload-grid">
            <view class="upload-item" v-for="(file, index) in form.reportFiles" :key="index">
              <image class="upload-img" :src="file.url" mode="aspectFill"></image>
              <view class="delete-btn" @click="removeFile(index)">✕</view>
            </view>
            <view class="upload-btn" @click="chooseMedia" v-if="form.reportFiles.length < 9">
              <text class="add-icon">+</text>
              <text class="add-text">上传附件</text>
            </view>
          </view>
        </view>

        <button class="btn-primary mt-60" :loading="submitLoading" @click="submitAppraisal">
          提交鉴定结果
        </button>
      </template>

      <!-- 已完成 (只读) -->
      <template v-if="caseDetail.status === 3">
        <view class="info-list">
          <view class="info-item">
            <text class="info-label">理赔金额</text>
            <text class="info-value highlight">¥{{ caseDetail.appraisalAmount }}</text>
          </view>
          <view class="info-item col-item">
            <text class="info-label mb-16">鉴定结论</text>
            <view class="readonly-box">{{ caseDetail.appraisalConclusion }}</view>
          </view>
          <view class="info-item col-item" v-if="caseDetail.reportFiles && caseDetail.reportFiles.length > 0">
            <text class="info-label mb-16">相关附件</text>
            <view class="preview-grid">
              <image 
                class="preview-img" 
                v-for="(file, index) in caseDetail.reportFiles" 
                :key="index"
                :src="file.url"
                mode="aspectFill"
                @click="previewImage(file.url, caseDetail.reportFiles)"
              ></image>
            </view>
          </view>
        </view>
      </template>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { request, BASE_URL } from '@/utils/request'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()
const caseId = ref('')
const caseDetail = ref<any>(null)
const submitLoading = ref(false)

const isPatientMode = computed(() => {
  const roleName = userStore.userInfo?.roleName || ''
  return !roleName.includes('机构') && !roleName.includes('管理员')
})

const form = reactive({
  appraisalAmount: '',
  appraisalConclusion: '',
  reportFiles: [] as { name: string, url: string }[]
})

onLoad((options) => {
  if (options && options.id) {
    caseId.value = options.id
    fetchDetail()
  }
})

const fetchDetail = async () => {
  uni.showLoading({ title: '加载中' })
  try {
    const res = await request(`/biz/case/${caseId.value}`, 'GET')
    if (res) {
      caseDetail.value = res
    }
  } catch (error) {
    console.error('Fetch detail error:', error)
  } finally {
    uni.hideLoading()
  }
}

const getStatusText = (status: number) => {
  if (status === 4) return '已打回'
  return status === 3 ? '已完成' : (status === 2 ? '鉴定中' : '待接单')
}

const callPhone = (phone: string) => {
  uni.makePhoneCall({ phoneNumber: phone })
}

const chooseMedia = () => {
  uni.chooseMedia({
    count: 9 - form.reportFiles.length,
    mediaType: ['image', 'video'],
    sourceType: ['album', 'camera'],
    sizeType: ['compressed'],
    success: async (res) => {
      const tempFiles = res.tempFiles
      for (const file of tempFiles) {
        if (file.fileType === 'image') {
          try {
            const compressRes = await new Promise<any>((resolve, reject) => {
              uni.compressImage({
                src: file.tempFilePath,
                quality: 80,
                success: resolve,
                fail: reject
              })
            })
            uploadFile(compressRes.tempFilePath)
          } catch (error) {
            console.error('图片压缩失败，使用原图上传', error)
            uploadFile(file.tempFilePath)
          }
        } else {
          uploadFile(file.tempFilePath)
        }
      }
    }
  })
}

const uploadFile = (filePath: string) => {
  uni.showLoading({ title: '上传中...' })
  const token = userStore.token || uni.getStorageSync('token')
  uni.uploadFile({
    url: `${BASE_URL}/file/upload`, 
    filePath: filePath,
    name: 'file',
    header: {
      'x-access-token': token
    },
    success: (uploadRes) => {
      try {
        const resData = JSON.parse(uploadRes.data)
        if (resData.code === 200 && resData.data?.fileUrl) {
          form.reportFiles.push({
            name: '附件',
            url: resData.data.fileUrl
          })
          uni.showToast({ title: '上传成功', icon: 'none' })
        } else {
          uni.showToast({ title: resData.msg || '上传失败', icon: 'none' })
        }
      } catch (e) {
        uni.showToast({ title: '解析失败', icon: 'none' })
      }
    },
    fail: () => {
      uni.showToast({ title: '上传异常', icon: 'none' })
    },
    complete: () => {
      uni.hideLoading()
    }
  })
}

const removeFile = (index: number) => {
  form.reportFiles.splice(index, 1)
}

const submitAppraisal = async () => {
  if (!form.appraisalAmount) return uni.showToast({ title: '请输入金额', icon: 'none' })
  if (!form.appraisalConclusion.trim()) return uni.showToast({ title: '请输入鉴定结论', icon: 'none' })
  if (form.reportFiles.length === 0) return uni.showToast({ title: '请上传至少一份附件', icon: 'none' })

  submitLoading.value = true
  try {
    await request(`/biz/case/${caseId.value}/appraisal`, 'POST', {
      appraisalAmount: Number(form.appraisalAmount),
      appraisalConclusion: form.appraisalConclusion,
      reportFiles: form.reportFiles
    })
    uni.showToast({ title: '提交成功', icon: 'success' })
    fetchDetail()
  } catch (error) {
    console.error('Submit appraisal error:', error)
  } finally {
    submitLoading.value = false
  }
}

const handleAccept = async () => {
  submitLoading.value = true
  try {
    await request(`/biz/case/${caseId.value}/accept`, 'POST')
    uni.showToast({ title: '已接单', icon: 'success' })
    fetchDetail()
  } catch (e) {
    console.error(e)
  } finally {
    submitLoading.value = false
  }
}

const handleReject = () => {
  uni.showModal({
    title: '确认拒单',
    content: '拒单后将把该案件退回平台重新派单，是否确认？',
    confirmColor: '#DC2626',
    success: async (res) => {
      if (res.confirm) {
        submitLoading.value = true
        try {
          await request(`/biz/case/${caseId.value}/reject`, 'POST', { reason: '机构主动拒单' })
          uni.showToast({ title: '已退单并重新分配', icon: 'success' })
          setTimeout(() => {
            uni.navigateBack()
          }, 1500)
        } catch (e) {
          console.error(e)
        } finally {
          submitLoading.value = false
        }
      }
    }
  })
}

const previewImage = (currentUrl: string, files: any[]) => {
  const urls = files.map(item => item.url)
  uni.previewImage({
    current: currentUrl,
    urls: urls
  })
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
.text-status-3 { color: #111827; }
.text-status-4 { color: #DC2626; }

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

.highlight {
  color: #111827;
  font-size: 36rpx;
  font-weight: 600;
}

.mb-16 {
  margin-bottom: 16rpx;
}

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

/* 表单样式 */
.form-group {
  margin-bottom: 60rpx;
}

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
  transition: all 0.3s;
}

.form-textarea {
  width: 100%;
  height: 240rpx;
  font-size: 30rpx;
  color: #111827;
  background-color: #FFFFFF;
  border: 2rpx solid #E5E7EB;
  border-radius: 4rpx;
  padding: 24rpx;
  box-sizing: border-box;
}

.form-input:focus, .form-textarea:focus {
  border-color: #111827;
}

.ph-color {
  color: #9CA3AF;
}

/* 上传区域 */
.upload-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 20rpx;
}

.upload-item, .preview-img, .upload-btn {
  width: 160rpx;
  height: 160rpx;
  border-radius: 4rpx;
}

.upload-item {
  position: relative;
}

.upload-img, .preview-img {
  width: 100%;
  height: 100%;
  border-radius: 4rpx;
}

.delete-btn {
  position: absolute;
  top: -16rpx;
  right: -16rpx;
  width: 40rpx;
  height: 40rpx;
  background-color: #FFFFFF;
  color: #111827;
  border: 2rpx solid #E5E7EB;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  z-index: 2;
  box-shadow: 0 2rpx 4rpx rgba(0,0,0,0.1);
}

.upload-btn {
  background-color: #F9FAFB;
  border: 2rpx dashed #D1D5DB;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.add-icon {
  font-size: 40rpx;
  color: #9CA3AF;
  margin-bottom: 8rpx;
}

.add-text {
  font-size: 24rpx;
  color: #6B7280;
}

.preview-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 20rpx;
}

/* 按钮 */
.btn-primary {
  background-color: #2563EB;
  color: #FFFFFF;
  font-size: 32rpx;
  font-weight: 500;
  height: 96rpx;
  line-height: 96rpx;
  border-radius: 8rpx;
}

.btn-primary::after {
  display: none;
}

.btn-outline-danger {
  background-color: #FFFFFF;
  color: #DC2626;
  font-size: 32rpx;
  font-weight: 500;
  height: 96rpx;
  line-height: 96rpx;
  border: 2rpx solid #DC2626;
  border-radius: 8rpx;
}

.btn-outline-danger::after {
  display: none;
}

.mt-40 { margin-top: 40rpx; }
.mt-60 { margin-top: 60rpx; }
</style>
