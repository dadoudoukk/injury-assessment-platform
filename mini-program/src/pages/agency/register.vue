<template>
  <view class="container">
    <view class="header-banner">
      <view class="title">机构入驻申请</view>
      <view class="subtitle">请填写真实的鉴定机构信息，平台审核通过后即可入驻接单</view>
    </view>

    <view class="form-card">
      <view class="form-item">
        <text class="form-label required">机构名称</text>
        <input v-model="form.agencyName" class="form-input" placeholder="请输入机构完整名称" maxlength="100" />
      </view>

      <view class="form-item">
        <text class="form-label required">联系人</text>
        <input v-model="form.contactPerson" class="form-input" placeholder="请输入联系人姓名" maxlength="50" />
      </view>

      <view class="form-item">
        <text class="form-label required">联系电话</text>
        <input v-model="form.contactPhone" class="form-input" type="number" placeholder="请输入手机号" maxlength="20" />
      </view>

      <view class="form-item">
        <text class="form-label required">所在省份</text>
        <input v-model="form.province" class="form-input" placeholder="例如：浙江省" />
      </view>
      <view class="form-item">
        <text class="form-label required">所在城市</text>
        <input v-model="form.city" class="form-input" placeholder="例如：杭州市" />
      </view>
      <view class="form-item">
        <text class="form-label required">所在区县</text>
        <input v-model="form.district" class="form-input" placeholder="例如：西湖区" />
      </view>

      <view class="form-item">
        <text class="form-label required">详细地址</text>
        <textarea v-model="form.address" class="form-textarea" placeholder="请输入详细的办公地址" maxlength="255"></textarea>
      </view>

      <button class="submit-btn" :loading="loading" @click="submitForm">提交申请</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { request } from '@/utils/request'

const loading = ref(false)

const form = reactive({
  agencyName: '',
  contactPerson: '',
  contactPhone: '',
  province: '',
  city: '',
  district: '',
  address: ''
})

const submitForm = async () => {
  if (!form.agencyName.trim()) return uni.showToast({ title: '请输入机构名称', icon: 'none' })
  if (!form.contactPerson.trim()) return uni.showToast({ title: '请输入联系人', icon: 'none' })
  if (!form.contactPhone.trim()) return uni.showToast({ title: '请输入联系电话', icon: 'none' })
  if (!form.province.trim()) return uni.showToast({ title: '请输入省份', icon: 'none' })
  if (!form.city.trim()) return uni.showToast({ title: '请输入城市', icon: 'none' })
  if (!form.district.trim()) return uni.showToast({ title: '请输入区县', icon: 'none' })
  if (!form.address.trim()) return uni.showToast({ title: '请输入详细地址', icon: 'none' })

  loading.value = true
  try {
    const res = await request('/biz/agency/register', 'POST', form)
    // res 只有成功的时候才有返回值或者在 request 拦截中抛出
    uni.showModal({
      title: '提交成功',
      content: '您的入驻申请已提交，请耐心等待平台审核。审核通过后将通过短信告知您登录账号。',
      showCancel: false,
      success: () => {
        uni.navigateBack()
      }
    })
  } catch (error) {
    // 报错已在 request 中拦截并显示 toast
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f4f7f6;
  padding-bottom: 60rpx;
}

.header-banner {
  background: linear-gradient(135deg, #0ba360 0%, #3cba92 100%);
  padding: 60rpx 40rpx 80rpx;
  color: #fff;
}

.title {
  font-size: 48rpx;
  font-weight: bold;
  margin-bottom: 16rpx;
}

.subtitle {
  font-size: 28rpx;
  opacity: 0.9;
}

.form-card {
  margin: -40rpx 30rpx 0;
  background-color: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
  box-shadow: 0 10rpx 30rpx rgba(0, 0, 0, 0.05);
}

.form-item {
  margin-bottom: 30rpx;
}

.form-label {
  display: block;
  font-size: 28rpx;
  color: #333;
  margin-bottom: 16rpx;
  font-weight: 500;
}

.required::after {
  content: "*";
  color: #ff4d4f;
  margin-left: 8rpx;
}

.form-input {
  width: 100%;
  height: 80rpx;
  background-color: #f8f9fa;
  border-radius: 12rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  box-sizing: border-box;
}

.form-textarea {
  width: 100%;
  height: 160rpx;
  background-color: #f8f9fa;
  border-radius: 12rpx;
  padding: 24rpx;
  font-size: 28rpx;
  box-sizing: border-box;
}

.submit-btn {
  margin-top: 60rpx;
  background-color: #0ba360;
  color: #fff;
  border-radius: 40rpx;
  font-size: 32rpx;
  height: 88rpx;
  line-height: 88rpx;
}

.submit-btn::after {
  border: none;
}
</style>