<template>
  <view class="container">
    <view class="header-bg">
      <view class="user-info-card">
        <image class="avatar" :src="userInfo?.avatar || '/static/default-avatar.png'" mode="aspectFill" />
        <view class="info-content">
          <view class="nickname">{{ userInfo?.name || '未知用户' }}</view>
          <view class="role-tag" v-if="userInfo?.roleName">{{ userInfo?.roleName }}</view>
        </view>
      </view>
    </view>

    <view class="menu-list">
      <view class="menu-item" v-if="userInfo?.phone">
        <text class="menu-label">绑定手机号</text>
        <text class="menu-value">{{ userInfo.phone }}</text>
      </view>
      <view class="menu-item" v-if="userInfo?.agencyName">
        <text class="menu-label">所属机构</text>
        <text class="menu-value">{{ userInfo.agencyName }}</text>
      </view>
    </view>

    <view class="logout-box">
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
  background-color: #f4f7f6;
}

.header-bg {
  height: 360rpx;
  background: linear-gradient(135deg, #0ba360 0%, #3cba92 100%);
  border-bottom-left-radius: 40rpx;
  border-bottom-right-radius: 40rpx;
  padding: 40rpx;
  box-sizing: border-box;
}

.user-info-card {
  margin-top: 40rpx;
  display: flex;
  align-items: center;
}

.avatar {
  width: 140rpx;
  height: 140rpx;
  border-radius: 50%;
  background-color: #fff;
  border: 4rpx solid rgba(255, 255, 255, 0.5);
  margin-right: 30rpx;
}

.info-content {
  color: #fff;
}

.nickname {
  font-size: 40rpx;
  font-weight: 600;
  margin-bottom: 16rpx;
}

.role-tag {
  font-size: 24rpx;
  background-color: rgba(255, 255, 255, 0.2);
  padding: 6rpx 20rpx;
  border-radius: 30rpx;
  display: inline-block;
}

.menu-list {
  margin: -60rpx 30rpx 40rpx;
  background-color: #fff;
  border-radius: 20rpx;
  padding: 0 30rpx;
  box-shadow: 0 10rpx 30rpx rgba(0, 0, 0, 0.05);
  position: relative;
  z-index: 2;
}

.menu-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30rpx 0;
  border-bottom: 2rpx solid #f0f0f0;
}

.menu-item:last-child {
  border-bottom: none;
}

.menu-label {
  font-size: 30rpx;
  color: #333;
}

.menu-value {
  font-size: 30rpx;
  color: #888;
}

.logout-box {
  padding: 40rpx 30rpx;
}

.logout-btn {
  background-color: #fff;
  color: #ff4d4f;
  font-size: 32rpx;
  border-radius: 40rpx;
  border: 2rpx solid #ff4d4f;
  box-shadow: 0 8rpx 16rpx rgba(255, 77, 79, 0.1);
}

.logout-btn::after {
  display: none;
}
</style>