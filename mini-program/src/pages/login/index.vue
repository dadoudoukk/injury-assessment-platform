<template>
  <view class="login-container">
    <!-- 顶部背景与 Logo 区域 -->
    <view class="header-bg">
      <view class="logo-box">
        <image class="logo-icon" src="/static/logo.png" mode="aspectFit" v-if="false"></image>
        <view class="logo-text-box" v-else>
          <text class="logo-text-icon">鉴</text>
        </view>
      </view>
      <text class="title">人伤鉴定共享中心</text>
      <text class="subtitle">鉴定机构端 · 高效协作</text>
    </view>

    <!-- 登录表单区域 -->
    <view class="form-box">
      <view class="form-header">
        <text class="form-title">欢迎登录</text>
      </view>
      
      <view class="input-group">
        <view class="input-item">
          <text class="iconfont icon-user label-icon">👤</text>
          <input 
            v-model="form.username" 
            class="input" 
            type="text" 
            placeholder="请输入手机号/账号" 
            placeholder-class="input-placeholder"
          />
        </view>
        <view class="input-item">
          <text class="iconfont icon-lock label-icon">🔒</text>
          <input 
            v-model="form.password" 
            class="input" 
            type="password" 
            placeholder="请输入密码" 
            placeholder-class="input-placeholder"
          />
        </view>
      </view>

      <button class="login-btn" :loading="loading" @click="handleLogin">
        登 录
      </button>
      
      <view class="form-footer">
        <text class="footer-text">遇到问题？请联系平台客服</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { request } from '@/utils/request'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const handleLogin = async () => {
  if (!form.username.trim()) {
    return uni.showToast({ title: '请输入账号', icon: 'none' })
  }
  if (!form.password.trim()) {
    return uni.showToast({ title: '请输入密码', icon: 'none' })
  }
  
  loading.value = true
  try {
    const res = await request('/login', 'POST', form)
    if (res && res.access_token) {
      userStore.setToken(res.access_token)
      uni.showToast({ title: '登录成功', icon: 'success' })
      setTimeout(() => {
        uni.reLaunch({ url: '/pages/index/index' })
      }, 1000)
    }
  } catch (error) {
    console.error('Login error:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  background-color: #f4f7f6; /* 浅灰绿色背景 */
  display: flex;
  flex-direction: column;
  position: relative;
}

/* 顶部背景 */
.header-bg {
  height: 450rpx;
  background: linear-gradient(135deg, #0ba360 0%, #3cba92 100%);
  border-bottom-left-radius: 100rpx;
  border-bottom-right-radius: 100rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 100rpx;
  box-shadow: 0 10rpx 30rpx rgba(11, 163, 96, 0.2);
}

.logo-box {
  width: 120rpx;
  height: 120rpx;
  background-color: #ffffff;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 24rpx;
  box-shadow: 0 8rpx 16rpx rgba(0,0,0,0.1);
}

.logo-text-icon {
  font-size: 60rpx;
  font-weight: bold;
  color: #0ba360;
}

.title {
  font-size: 44rpx;
  font-weight: bold;
  color: #ffffff;
  letter-spacing: 2rpx;
  text-shadow: 0 2rpx 4rpx rgba(0,0,0,0.1);
}

.subtitle {
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.9);
  margin-top: 12rpx;
}

/* 表单卡片 */
.form-box {
  background-color: #ffffff;
  margin: -60rpx 40rpx 0;
  border-radius: 30rpx;
  padding: 60rpx 40rpx;
  box-shadow: 0 15rpx 40rpx rgba(0,0,0,0.06);
  position: relative;
  z-index: 10;
}

.form-header {
  margin-bottom: 50rpx;
}

.form-title {
  font-size: 40rpx;
  font-weight: 600;
  color: #333333;
}

.input-group {
  margin-bottom: 60rpx;
}

.input-item {
  display: flex;
  align-items: center;
  background-color: #f8f9fa;
  border-radius: 20rpx;
  padding: 0 30rpx;
  height: 100rpx;
  margin-bottom: 30rpx;
  border: 2rpx solid transparent;
  transition: all 0.3s;
}

.input-item:focus-within {
  border-color: #3cba92;
  background-color: #ffffff;
  box-shadow: 0 0 0 4rpx rgba(60, 186, 146, 0.1);
}

.label-icon {
  font-size: 36rpx;
  color: #999999;
  margin-right: 20rpx;
}

.input {
  flex: 1;
  font-size: 32rpx;
  color: #333333;
  height: 100%;
}

.input-placeholder {
  color: #c0c4cc;
}

.login-btn {
  background: linear-gradient(90deg, #0ba360 0%, #3cba92 100%);
  color: #ffffff;
  border-radius: 50rpx;
  font-size: 36rpx;
  font-weight: 500;
  height: 96rpx;
  line-height: 96rpx;
  box-shadow: 0 10rpx 20rpx rgba(11, 163, 96, 0.3);
  transition: all 0.3s;
}

.login-btn:active {
  transform: scale(0.98);
  box-shadow: 0 5rpx 10rpx rgba(11, 163, 96, 0.2);
}

.login-btn::after {
  border: none;
}

.form-footer {
  margin-top: 40rpx;
  text-align: center;
}

.footer-text {
  font-size: 26rpx;
  color: #999999;
}
</style>

