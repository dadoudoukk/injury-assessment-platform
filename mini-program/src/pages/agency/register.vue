<template>
  <view class="container">
    <view class="header-section">
      <text class="page-title">机构入驻申请</text>
      <text class="page-subtitle">请填写真实的鉴定机构信息，审核通过后请使用入驻手机号在机构端微信登录</text>
    </view>

    <view class="form-section">
      <view class="input-group">
        <text class="label required">机构名称</text>
        <input v-model="form.agencyName" class="input-field" placeholder="请输入机构完整名称" maxlength="100" placeholder-class="ph-color" />
      </view>

      <view class="input-group">
        <text class="label required">联系人</text>
        <input v-model="form.contactPerson" class="input-field" placeholder="请输入联系人姓名" maxlength="50" placeholder-class="ph-color" />
      </view>

      <view class="input-group">
        <text class="label required">联系电话</text>
        <input v-model="form.contactPhone" class="input-field" type="number" placeholder="请输入手机号" maxlength="20" placeholder-class="ph-color" />
      </view>

      <view class="input-group">
        <text class="label required">所在地区</text>
        <picker mode="region" @change="onRegionChange">
          <view class="picker-field">
            <text :class="form.province ? 'text-black' : 'ph-color'">
              {{ form.province ? `${form.province} ${form.city} ${form.district}` : '请选择省/市/区' }}
            </text>
            <view class="arrow"></view>
          </view>
        </picker>
      </view>

      <view class="input-group">
        <view class="label-row">
          <text class="label required" style="margin-bottom: 0;">详细地址</text>
          <view class="location-btn" @click="chooseLocation">
            <text class="location-icon">📍</text>
            <text>地图选择</text>
          </view>
        </view>
        <textarea v-model="form.address" class="textarea-field" placeholder="请输入详细的办公地址" maxlength="255" placeholder-class="ph-color"></textarea>
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

const onRegionChange = (e: any) => {
  const [province, city, district] = e.detail.value;
  form.province = province;
  form.city = city;
  form.district = district;
}

const chooseLocation = () => {
  uni.chooseLocation({
    success: (res) => {
      if (res.address || res.name) {
        let fullAddress = res.address || '';
        if (res.name && !fullAddress.includes(res.name)) {
          fullAddress += ` ${res.name}`;
        }
        form.address = fullAddress.trim();
      }
    },
    fail: (err) => {
      console.log('chooseLocation err:', err)
      const errMsg = err?.errMsg || ''
      if (errMsg.includes('auth deny') || errMsg.includes('authorize')) {
        uni.showModal({
          title: '需要位置权限',
          content: '请在设置中允许小程序使用位置信息，以便选择机构地址',
          confirmText: '去设置',
          success: (res) => {
            if (res.confirm) uni.openSetting({})
          }
        })
      } else if (errMsg.includes('requiredPrivateInfos')) {
        uni.showToast({ title: '地图功能未配置，请联系管理员', icon: 'none' })
      } else if (errMsg.includes('cancel')) {
        // 用户取消选择，无需提示
      } else {
        uni.showToast({ title: '无法打开地图，请手动输入地址', icon: 'none' })
      }
    }
  })
}

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
    uni.showModal({
      title: '提交成功',
      content: '您的入驻申请已提交，请耐心等待平台审核。审核通过后，请返回首页点击「我是鉴定机构」并使用入驻手机号微信登录。',
      showCancel: false,
      confirmColor: '#2563EB',
      success: () => {
        uni.navigateBack()
      }
    })
  } catch (error) {
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #FFFFFF;
  padding: 60rpx;
}

.header-section {
  margin-bottom: 80rpx;
}

.page-title {
  display: block;
  font-size: 48rpx;
  font-weight: 600;
  color: #111827;
  margin-bottom: 16rpx;
}

.page-subtitle {
  display: block;
  font-size: 28rpx;
  color: #6B7280;
}

.form-section {
  width: 100%;
}

.input-group {
  margin-bottom: 60rpx;
}

.label {
  display: block;
  font-size: 28rpx;
  color: #374151;
  font-weight: 500;
  margin-bottom: 20rpx;
}

.label.required::after {
  content: " *";
  color: #DC2626;
}

.label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.location-btn {
  display: flex;
  align-items: center;
  font-size: 26rpx;
  color: #2563EB;
  background-color: #EFF6FF;
  padding: 6rpx 16rpx;
  border-radius: 20rpx;
}

.location-icon {
  margin-right: 6rpx;
  font-size: 24rpx;
}

.input-field {
  width: 100%;
  height: 80rpx;
  font-size: 32rpx;
  color: #111827;
  border-bottom: 2rpx solid #E5E7EB;
  transition: all 0.3s;
}

.picker-field {
  width: 100%;
  height: 80rpx;
  font-size: 32rpx;
  color: #111827;
  border-bottom: 2rpx solid #E5E7EB;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.3s;
}

.arrow {
  width: 16rpx;
  height: 16rpx;
  border-top: 4rpx solid #9CA3AF;
  border-right: 4rpx solid #9CA3AF;
  transform: rotate(45deg);
}

.text-black {
  color: #111827;
}

.textarea-field {
  width: 100%;
  height: 160rpx;
  font-size: 32rpx;
  color: #111827;
  border-bottom: 2rpx solid #E5E7EB;
  transition: all 0.3s;
  padding: 20rpx 0;
  box-sizing: border-box;
}

.input-field:focus, .textarea-field:focus {
  border-bottom-color: #111827;
}

.ph-color {
  color: #9CA3AF;
  font-size: 30rpx;
}

.submit-btn {
  margin-top: 80rpx;
  background-color: #2563EB;
  color: #FFFFFF;
  font-size: 32rpx;
  font-weight: 500;
  height: 96rpx;
  line-height: 96rpx;
  border-radius: 8rpx;
  letter-spacing: 2rpx;
}

.submit-btn::after {
  border: none;
}

.submit-btn:active {
  background-color: #1D4ED8;
}
</style>
