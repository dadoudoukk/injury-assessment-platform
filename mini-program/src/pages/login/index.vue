<template>
  <view class="container">
    <view class="header-section">
      <text class="page-title">机构账号登录</text>
      <text class="page-subtitle">欢迎回来，请登录您的工作台</text>
    </view>

    <view class="form-section">
      <view class="input-group">
        <text class="label">账号</text>
        <input
          v-model="form.username"
          class="input-field"
          type="text"
          placeholder="请输入手机号/账号"
          placeholder-class="ph-color"
        />
      </view>
      <view class="input-group">
        <text class="label">密码</text>
        <input
          v-model="form.password"
          class="input-field"
          type="password"
          placeholder="请输入密码"
          placeholder-class="ph-color"
        />
      </view>

      <button class="submit-btn" :loading="loading" @click="handleLogin">
        登 录
      </button>

      <view class="form-footer">
        <text class="footer-text">遇到问题？请联系平台客服</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { request } from "@/utils/request";
import { useUserStore } from "@/store/modules/user";

const userStore = useUserStore();
const loading = ref(false);

const form = reactive({
  username: "",
  password: "",
});

const handleLogin = async () => {
  if (!form.username.trim()) {
    return uni.showToast({ title: "请输入账号", icon: "none" });
  }
  if (!form.password.trim()) {
    return uni.showToast({ title: "请输入密码", icon: "none" });
  }

  loading.value = true;
  try {
    const res = await request("/login", "POST", form);
    if (res && res.access_token) {
      userStore.setToken(res.access_token);
      uni.showToast({ title: "登录成功", icon: "success" });
      setTimeout(() => {
        uni.reLaunch({ url: "/pages/index/index" });
      }, 1000);
    }
  } catch (error) {
    console.error("Login error:", error);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #ffffff;
  padding: 60rpx;
}

.header-section {
  margin-top: 40rpx;
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
  color: #6b7280;
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

.input-field {
  width: 100%;
  height: 80rpx;
  font-size: 32rpx;
  color: #111827;
  border-bottom: 2rpx solid #e5e7eb;
  transition: all 0.3s;
}

.input-field:focus {
  border-bottom-color: #111827;
}

.ph-color {
  color: #9ca3af;
  font-size: 30rpx;
}

.submit-btn {
  margin-top: 80rpx;
  background-color: #2563eb;
  color: #ffffff;
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
  background-color: #1d4ed8;
}

.form-footer {
  margin-top: 40rpx;
  text-align: center;
}

.footer-text {
  font-size: 26rpx;
  color: #9ca3af;
}
</style>
