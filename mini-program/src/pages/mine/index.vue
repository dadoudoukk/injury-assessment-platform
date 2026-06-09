<template>
  <view class="container">
    <view class="header-section">
      <view class="user-info">
        <view class="avatar-placeholder"></view>
        <view class="info-content">
          <view class="nickname">{{ userInfo?.name || '未知用户' }}</view>
          <view class="role-text" v-if="userInfo?.roleName">{{ userInfo?.roleName }}</view>
        </view>
      </view>
    </view>

    <view class="info-section">
      <view class="section-title">账户信息</view>
      
      <view class="info-list">
        <view class="info-item" v-if="userInfo?.phone">
          <text class="info-label">绑定手机号</text>
          <text class="info-value">{{ userInfo.phone }}</text>
        </view>
        <view class="info-item" v-if="userInfo?.agencyName">
          <text class="info-label">所属机构</text>
          <text class="info-value">{{ userInfo.agencyName }}</text>
        </view>
      </view>
    </view>

    <view class="action-section">
      <button class="logout-btn" @click="handleLogout">退出登录</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()

const userInfo = computed(() => userStore.userInfo)

onShow(() => {
  if (userStore.token) {
    userStore.fetchUserInfo()
  }
})

const handleLogout = () => {
  uni.showModal({
    title: '提示',
    content: '确定要退出登录吗？',
    confirmColor: '#2563EB',
    success: (res) => {
      if (res.confirm) {
        userStore.logout()
        uni.reLaunch({ url: '/pages/patient/home' })
      }
    }
  })
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #FFFFFF;
  padding: 60rpx;
  display: flex;
  flex-direction: column;
}

.header-section {
  padding-top: 40rpx;
  margin-bottom: 80rpx;
}

.user-info {
  display: flex;
  align-items: center;
}

.avatar-placeholder {
  width: 120rpx;
  height: 120rpx;
  background-color: #F3F4F6;
  border-radius: 8rpx;
  margin-right: 40rpx;
}

.info-content {
  display: flex;
  flex-direction: column;
}

.nickname {
  font-size: 48rpx;
  font-weight: 600;
  color: #111827;
  margin-bottom: 12rpx;
}

.role-text {
  font-size: 26rpx;
  color: #6B7280;
}

.info-section {
  margin-bottom: 80rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #111827;
  margin-bottom: 40rpx;
  border-left: 6rpx solid #2563EB;
  padding-left: 16rpx;
}

.info-list {
  border-top: 2rpx solid #E5E7EB;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 40rpx 0;
  border-bottom: 2rpx solid #E5E7EB;
}

.info-label {
  font-size: 30rpx;
  color: #4B5563;
  font-weight: 500;
}

.info-value {
  font-size: 30rpx;
  color: #111827;
}

.action-section {
  margin-top: auto;
  padding-bottom: 40rpx;
}

.logout-btn {
  background-color: #FFFFFF;
  color: #EF4444;
  font-size: 32rpx;
  font-weight: 500;
  height: 96rpx;
  line-height: 96rpx;
  border: 2rpx solid #EF4444;
  border-radius: 8rpx;
  letter-spacing: 2rpx;
}

.logout-btn::after {
  display: none;
}

.logout-btn:active {
  background-color: #FEF2F2;
}
</style>
