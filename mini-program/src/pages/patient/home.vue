<template>
  <view class="container">
    <view class="header-banner">
      <view class="title">人伤鉴定共享中心</view>
      <view class="subtitle">让鉴定更透明 · 让理赔更高效</view>
    </view>

    <view class="action-grid">
      <!-- 已登录用户显示快捷入口 -->
      <view class="action-card patient-card" v-if="userStore.token" @click="goToMyCases">
        <view class="icon-box">
          <text class="iconfont">📋</text>
        </view>
        <text class="card-title">我的案件</text>
        <text class="card-desc">查进度 / 补充资料</text>
      </view>

      <view class="action-card agency-card" v-if="userStore.token" @click="goToMine">
        <view class="icon-box">
          <text class="iconfont">👤</text>
        </view>
        <text class="card-title">个人中心</text>
        <text class="card-desc">账号信息 / 退出登录</text>
      </view>

      <!-- 未登录状态显示原来的入口 -->
      <button 
        v-if="!userStore.token"
        class="action-card patient-card" 
        open-type="getPhoneNumber" 
        @getphonenumber="onGetPhoneNumber"
      >
        <view class="icon-box">
          <text class="iconfont">🏥</text>
        </view>
        <text class="card-title">我是伤者</text>
        <text class="card-desc">我要报案鉴定 / 查进度</text>
      </button>

      <view v-if="!userStore.token" class="action-card agency-card" @click="goToAgencyLogin">
        <view class="icon-box">
          <text class="iconfont">🏢</text>
        </view>
        <text class="card-title">我是鉴定机构</text>
        <text class="card-desc">登录工作台接单处理</text>
      </view>
      
      <view v-if="!userStore.token" class="register-link" @click="goToRegister">
        还没有账号？<text class="link-text">点击申请入驻</text>
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
  background-color: #f5f7fa;
}

.header-banner {
  height: 400rpx;
  background: linear-gradient(135deg, #0ba360 0%, #3cba92 100%);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #fff;
  border-bottom-left-radius: 40rpx;
  border-bottom-right-radius: 40rpx;
  box-shadow: 0 10rpx 20rpx rgba(11, 163, 96, 0.15);
}

.title {
  font-size: 48rpx;
  font-weight: bold;
  letter-spacing: 4rpx;
}

.subtitle {
  font-size: 28rpx;
  margin-top: 20rpx;
  opacity: 0.9;
}

.action-grid {
  padding: 40rpx;
  margin-top: -60rpx;
  position: relative;
  z-index: 10;
}

.action-card {
  background-color: #fff;
  border-radius: 24rpx;
  padding: 40rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin-bottom: 40rpx;
  box-shadow: 0 8rpx 24rpx rgba(0,0,0,0.06);
  border: none;
  line-height: normal;
}
.action-card::after {
  border: none;
}
.action-card:active {
  transform: scale(0.98);
}

.icon-box {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24rpx;
}

.patient-card .icon-box {
  background-color: #e6f6f0;
}
.patient-card .icon-box .iconfont {
  font-size: 60rpx;
}
.patient-card .card-title {
  color: #0ba360;
}

.agency-card .icon-box {
  background-color: #f0f7ff;
}
.agency-card .icon-box .iconfont {
  font-size: 60rpx;
}
.agency-card .card-title {
  color: #1890ff;
}

.card-title {
  font-size: 36rpx;
  font-weight: bold;
  margin-bottom: 12rpx;
}

.card-desc {
  font-size: 26rpx;
  color: #999;
}

.register-link {
  text-align: center;
  font-size: 26rpx;
  color: #888;
  margin-top: 10rpx;
  padding: 20rpx;
}
.register-link .link-text {
  color: #0ba360;
  font-weight: 500;
}
</style>
