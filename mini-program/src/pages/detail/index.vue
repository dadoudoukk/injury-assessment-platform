<template>
  <view class="detail-container" v-if="caseDetail">
    <!-- 顶部状态栏 -->
    <view class="status-header" :class="'bg-status-' + caseDetail.status">
      <view class="status-text">
        <text class="icon" v-if="caseDetail.status === 3">✅</text>
        <text class="icon" v-else-if="caseDetail.status === 4">⚠️</text>
        <text class="icon" v-else-if="caseDetail.status === 2">⏳</text>
        <text class="icon" v-else>📝</text>
        <text>{{ getStatusText(caseDetail.status) }}</text>
      </view>
      <text class="report-no">报案号：{{ caseDetail.reportNumber }}</text>
    </view>

    <!-- 基础信息卡片 (只读) -->
    <view class="card-box">
      <view class="card-title">案件基础信息</view>
      <view class="info-list">
        <view class="info-item" v-if="caseDetail.status === 4 && caseDetail.reworkRemark">
          <text class="label" style="color: #ff4d4f">打回原因</text>
          <text class="value" style="color: #ff4d4f; font-weight: bold">{{ caseDetail.reworkRemark }}</text>
        </view>
        <view class="info-item">
          <text class="label">伤者姓名</text>
          <text class="value">{{ caseDetail.victimName }}</text>
        </view>
        <view class="info-item">
          <text class="label">联系电话</text>
          <text class="value phone" @click="callPhone(caseDetail.victimPhone)">
            {{ caseDetail.victimPhone }} <text class="iconfont">📞</text>
          </text>
        </view>
        <view class="info-item">
          <text class="label">出险地点</text>
          <text class="value">{{ caseDetail.province }}{{ caseDetail.city }}{{ caseDetail.district }}</text>
        </view>
        <view class="info-item">
          <text class="label">报案日期</text>
          <text class="value">{{ caseDetail.reportDate }}</text>
        </view>
        <view class="info-item">
          <text class="label">保险公司</text>
          <text class="value">{{ caseDetail.insuranceCompany }}</text>
        </view>
      </view>
    </view>

    <!-- 鉴定工作区 (填表与传图) -->
    <view class="card-box" v-if="caseDetail.status === 2 || caseDetail.status === 3 || caseDetail.status === 4">
      <view class="card-title">鉴定文书与结论</view>
      
      <!-- 待接单 (显示拒单按钮) -->
      <template v-if="caseDetail.status === 1 && !isPatientMode">
        <view class="action-buttons">
          <button class="action-btn reject" :loading="submitLoading" @click="handleReject">拒绝接单，退回平台</button>
        </view>
      </template>

      <!-- 鉴定中/已打回 (可编辑) -->
      <template v-if="caseDetail.status === 2 || caseDetail.status === 4">
        <view class="form-item">
          <text class="form-label required">预估理赔金额(元)</text>
          <input 
            class="form-input" 
            type="digit" 
            v-model="form.appraisalAmount" 
            placeholder="请输入金额" 
          />
        </view>
        
        <view class="form-item">
          <text class="form-label required">鉴定结论</text>
          <textarea 
            class="form-textarea" 
            v-model="form.appraisalConclusion" 
            placeholder="请详细描述伤情和鉴定结论..." 
            maxlength="1000"
          ></textarea>
        </view>

        <view class="form-item">
          <text class="form-label required">相关附件(图片/视频)</text>
          <view class="upload-grid">
            <view class="upload-item" v-for="(file, index) in form.reportFiles" :key="index">
              <image class="upload-img" :src="file.url" mode="aspectFill"></image>
              <view class="delete-btn" @click="removeFile(index)">✖</view>
            </view>
            <view class="upload-btn" @click="chooseMedia" v-if="form.reportFiles.length < 9">
              <text class="add-icon">+</text>
              <text class="add-text">上传</text>
            </view>
          </view>
        </view>

        <button class="submit-btn" :loading="submitLoading" @click="submitAppraisal">
          提交鉴定结果
        </button>
      </template>

      <!-- 已完成 (只读) -->
      <template v-if="caseDetail.status === 3">
        <view class="info-list">
          <view class="info-item">
            <text class="label">理赔金额</text>
            <text class="value highlight">￥{{ caseDetail.appraisalAmount }}</text>
          </view>
          <view class="info-item col-item">
            <text class="label">鉴定结论</text>
            <text class="value desc-box">{{ caseDetail.appraisalConclusion }}</text>
          </view>
          <view class="info-item col-item" v-if="caseDetail.reportFiles && caseDetail.reportFiles.length > 0">
            <text class="label">相关附件</text>
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
import { ref, reactive } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { request } from '@/utils/request'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()
const caseId = ref('')
const caseDetail = ref<any>(null)
const submitLoading = ref(false)

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

// 选择图片/视频上传
const chooseMedia = () => {
  uni.chooseMedia({
    count: 9 - form.reportFiles.length,
    mediaType: ['image', 'video'],
    sourceType: ['album', 'camera'],
    sizeType: ['compressed'], // 优先使用系统压缩
    success: async (res) => {
      const tempFiles = res.tempFiles
      for (const file of tempFiles) {
        if (file.fileType === 'image') {
          // 对图片进行二次压缩，防止过大
          try {
            const compressRes = await new Promise<any>((resolve, reject) => {
              uni.compressImage({
                src: file.tempFilePath,
                quality: 80, // 压缩质量，0-100
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
          // 视频直接上传
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
    url: 'http://127.0.0.1:8000/api/file/upload', 
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
    // 重新获取详情展示最新状态
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
    // 假设更新状态到 2（鉴定中）
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
  background-color: #f4f7f6;
  padding-bottom: 60rpx;
}

.status-header {
  padding: 40rpx 40rpx 60rpx;
  color: #fff;
  display: flex;
  flex-direction: column;
}
.bg-status-1 {
  background: linear-gradient(135deg, #f59a23 0%, #f7b733 100%);
}
.bg-status-2 {
  background: linear-gradient(135deg, #0ba360 0%, #3cba92 100%);
}
.bg-status-3 {
  background: linear-gradient(135deg, #8ba89f 0%, #a4babb 100%);
}
.bg-status-4 {
  background: linear-gradient(135deg, #ff4d4f 0%, #ff7875 100%);
}
.status-text {
  font-size: 40rpx;
  font-weight: bold;
  display: flex;
  align-items: center;
}
.status-text .icon {
  margin-right: 16rpx;
}
.report-no {
  font-size: 26rpx;
  margin-top: 16rpx;
  opacity: 0.9;
}

/* 卡片公共样式 */
.card-box {
  background-color: #ffffff;
  border-radius: 24rpx;
  margin: -30rpx 30rpx 30rpx;
  padding: 30rpx;
  box-shadow: 0 8rpx 20rpx rgba(0,0,0,0.04);
  position: relative;
  z-index: 10;
}
.card-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 30rpx;
  padding-left: 16rpx;
  border-left: 8rpx solid #0ba360;
}

/* 信息列表 */
.info-list {
  display: flex;
  flex-direction: column;
}
.info-item {
  display: flex;
  justify-content: space-between;
  padding: 20rpx 0;
  border-bottom: 1rpx solid #f5f5f5;
}
.info-item:last-child {
  border-bottom: none;
}
.info-item.col-item {
  flex-direction: column;
  justify-content: flex-start;
  align-items: flex-start;
}
.label {
  color: #999;
  font-size: 28rpx;
  min-width: 140rpx;
}
.value {
  color: #333;
  font-size: 28rpx;
  text-align: right;
  flex: 1;
}
.value.phone {
  color: #0ba360;
  font-weight: bold;
}
.value.highlight {
  color: #f5222d;
  font-size: 32rpx;
  font-weight: bold;
}
.desc-box {
  text-align: left;
  margin-top: 16rpx;
  background-color: #f9f9f9;
  padding: 20rpx;
  border-radius: 12rpx;
  width: 100%;
  box-sizing: border-box;
}

/* 表单样式 */
.form-item {
  margin-bottom: 40rpx;
}
.form-label {
  font-size: 28rpx;
  color: #333;
  margin-bottom: 20rpx;
  display: block;
}
.form-label.required::after {
  content: '*';
  color: red;
  margin-left: 8rpx;
}
.form-input {
  background-color: #f8f9fa;
  height: 80rpx;
  border-radius: 12rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
}
.form-textarea {
  background-color: #f8f9fa;
  width: 100%;
  height: 200rpx;
  border-radius: 12rpx;
  padding: 24rpx;
  font-size: 28rpx;
  box-sizing: border-box;
}

/* 上传图片区 */
.upload-grid, .preview-grid {
  display: flex;
  flex-wrap: wrap;
  margin-top: 16rpx;
}
.upload-item, .preview-img, .upload-btn {
  width: 180rpx;
  height: 180rpx;
  border-radius: 12rpx;
  margin-right: 20rpx;
  margin-bottom: 20rpx;
}
.upload-item {
  position: relative;
}
.upload-img, .preview-img {
  width: 100%;
  height: 100%;
  border-radius: 12rpx;
}
.delete-btn {
  position: absolute;
  top: -10rpx;
  right: -10rpx;
  width: 40rpx;
  height: 40rpx;
  background-color: rgba(0,0,0,0.5);
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20rpx;
  z-index: 2;
}
.upload-btn {
  background-color: #f5f5f5;
  border: 2rpx dashed #ddd;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
}
.add-icon {
  font-size: 60rpx;
  font-weight: 300;
  margin-bottom: 10rpx;
  line-height: 1;
}
.add-text {
  font-size: 24rpx;
}

.submit-btn {
  background: linear-gradient(90deg, #0ba360 0%, #3cba92 100%);
  color: #ffffff;
  border-radius: 50rpx;
  height: 90rpx;
  line-height: 90rpx;
  font-size: 32rpx;
  margin-top: 60rpx;
}
.action-buttons {
  display: flex;
  justify-content: space-between;
  margin-top: 40rpx;
}
.action-buttons .action-btn {
  width: 48%;
  font-size: 30rpx;
  border-radius: 40rpx;
}
.action-buttons .accept {
  background-color: #0ba360;
  color: #fff;
}
.action-buttons .reject {
  background-color: #fff;
  color: #ff4d4f;
  border: 2rpx solid #ff4d4f;
}
</style>
