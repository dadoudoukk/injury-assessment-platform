<template>
  <view class="container">
    <view class="header-section">
      <view class="brand-line"></view>
      <text class="title">人伤鉴定共享中心</text>
      <text class="subtitle">让鉴定更透明 · 让理赔更高效</text>
    </view>

    <view class="action-grid">
      <!-- 已登录用户显示快捷入口 -->
      <view class="action-card patient-card" v-if="userStore.token" @click="goToMyCases">
        <view class="card-content">
          <text class="card-title">我的案件</text>
          <text class="card-desc">查进度 / 补充资料</text>
        </view>
        <view class="arrow"></view>
      </view>

      <view class="action-card agency-card" v-if="userStore.token" @click="goToMine">
        <view class="card-content">
          <text class="card-title">个人中心</text>
          <text class="card-desc">账号信息 / 退出登录</text>
        </view>
        <view class="arrow"></view>
      </view>

      <!-- 未登录状态显示原来的入口 -->
      <button 
        v-if="!userStore.token"
        class="action-card patient-card" 
        open-type="getPhoneNumber" 
        @getphonenumber="onGetPhoneNumber"
      >
        <view class="card-content">
          <text class="card-title">我是伤者</text>
          <text class="card-desc">我要报案鉴定 / 查进度</text>
        </view>
        <view class="arrow"></view>
      </button>

      <view v-if="!userStore.token" class="action-card agency-card" @click="goToAgencyLogin">
        <view class="card-content">
          <text class="card-title">我是鉴定机构</text>
          <text class="card-desc">登录工作台接单处理</text>
        </view>
        <view class="arrow"></view>
      </view>
      
      <view v-if="!userStore.token" class="register-link" @click="goToRegister">
        <text class="text-gray">还没有机构账号？</text>
        <text class="link-text">点击申请入驻</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { request } from '@/utils/request'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()

// 点击跳转机构端登录
const goToAgencyLogin = () => {
  uni.navigateTo({
    url: '/pages/login/index'
  })
}

const goToRegister = () => {
  uni.navigateTo({ url: '/pages/agency/register' })
}

const goToMine = () => {
  uni.navigateTo({ url: '/pages/mine/index' })
}

const goToMyCases = () => {
  // 如果是机构用户，去 index/index，否则去 patient/list
  if (userStore.userInfo?.roleName?.includes('机构') || userStore.userInfo?.roleName?.includes('管理员')) {
    uni.navigateTo({ url: '/pages/index/index' })
  } else {
    uni.navigateTo({ url: '/pages/patient/list' })
  }
}

// 伤者端：获取手机号授权
const onGetPhoneNumber = async (e: any) => {
  if (e.detail.errMsg !== 'getPhoneNumber:ok') {
    uni.showToast({ title: '需要授权手机号才能使用', icon: 'none' })
    return
  }
  
  uni.showLoading({ title: '登录中...' })
  try {
    // 清除过期 token，避免登录请求携带无效凭证
    userStore.logout()
    // 真实项目中，后端拿着 e.detail.code 去微信服务器换取真实的手机号
    const res = await request('/login/wx', 'POST', {
      code: e.detail.code,
      phone: '13800000000' // 临时降级参数：如果你的后端还没有配置微信 AppID，后端会默认取这个号码
    })
    
    if (res && res.access_token) {
      userStore.setToken(res.access_token)
      uni.showToast({ title: '登录成功', icon: 'success' })
      
      // 伤者登录成功，跳转到伤者的列表页/报案页
      setTimeout(() => {
        uni.navigateTo({ url: '/pages/patient/list' })
      }, 1000)
    }
  } catch (error) {
    console.error('Wx login error:', error)
  } finally {
    uni.hideLoading()
  }
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #FFFFFF;
  display: flex;
  flex-direction: column;
}

.header-section {
  padding: 120rpx 60rpx 80rpx;
  background-color: #FFFFFF;
  position: relative;
}

.brand-line {
  width: 60rpx;
  height: 8rpx;
  background-color: #2563EB;
  margin-bottom: 30rpx;
}

.title {
  display: block;
  font-size: 56rpx;
  font-weight: 600;
  color: #111827;
  letter-spacing: 2rpx;
  margin-bottom: 20rpx;
}

.subtitle {
  display: block;
  font-size: 28rpx;
  color: #6B7280;
  letter-spacing: 2rpx;
}

.action-grid {
  padding: 0 60rpx;
  flex: 1;
}

.action-card {
  background-color: #FFFFFF;
  border: 2rpx solid #E5E7EB;
  border-radius: 8rpx;
  padding: 40rpx 40rpx;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 40rpx;
  box-shadow: none;
  line-height: normal;
  text-align: left;
  transition: all 0.3s;
}

.action-card::after {
  border: none;
}

.action-card:active {
  background-color: #F9FAFB;
  border-color: #D1D5DB;
}

.patient-card {
  border-left: 8rpx solid #2563EB;
}

.agency-card {
  border-left: 8rpx solid #4B5563;
}

.card-content {
  display: flex;
  flex-direction: column;
}

.card-title {
  font-size: 36rpx;
  font-weight: 600;
  color: #111827;
  margin-bottom: 12rpx;
}

.card-desc {
  font-size: 26rpx;
  color: #6B7280;
}

.arrow {
  width: 16rpx;
  height: 16rpx;
  border-top: 4rpx solid #9CA3AF;
  border-right: 4rpx solid #9CA3AF;
  transform: rotate(45deg);
}

.register-link {
  text-align: center;
  margin-top: 60rpx;
  padding: 30rpx 0;
}

.text-gray {
  font-size: 28rpx;
  color: #6B7280;
}

.link-text {
  font-size: 28rpx;
  color: #2563EB;
  font-weight: 500;
  margin-left: 10rpx;
}
</style>
