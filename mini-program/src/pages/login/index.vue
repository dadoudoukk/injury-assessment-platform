<template>
  <view class="container">
    <view class="header-section">
      <text class="page-title">机构账号登录</text>
      <text class="page-subtitle">审核通过后，可使用入驻手机号微信登录；已设密码的同事可用账号密码登录</text>
    </view>

    <view class="form-section">
      <button
        class="wx-btn"
        open-type="getPhoneNumber"
        :loading="wxLoading"
        @getphonenumber="onWxLogin"
      >
        微信授权登录
      </button>

      <view class="divider">
        <view class="divider-line"></view>
        <text class="divider-text">或使用账号密码</text>
        <view class="divider-line"></view>
      </view>

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

      <button class="submit-btn" :loading="loading" @click="handleLogin">登 录</button>

      <view class="form-footer">
        <text class="footer-text">忘记密码？请使用上方微信授权登录后重设密码</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { request } from "@/utils/request";
import { useUserStore } from "@/store/modules/user";
import { completeAgencyLogin } from "@/utils/agency-auth";

const userStore = useUserStore();
const loading = ref(false);
const wxLoading = ref(false);

const form = reactive({
  username: "",
  password: "",
});

const onWxLogin = async (e: any) => {
  if (e.detail.errMsg !== "getPhoneNumber:ok") {
    uni.showToast({ title: "需要授权手机号才能登录", icon: "none" });
    return;
  }

  wxLoading.value = true;
  try {
    userStore.logout();
    const res = await request("/login/wx/agency", "POST", {
      code: e.detail.code,
      phone: "13800000000",
    });
    if (res?.access_token) {
      uni.showToast({ title: "登录成功", icon: "success" });
      setTimeout(() => {
        completeAgencyLogin(res);
      }, 500);
    }
  } catch (error) {
    console.error("Wx agency login error:", error);
  } finally {
    wxLoading.value = false;
  }
};

const handleLogin = async () => {
  if (!form.username.trim()) {
    return uni.showToast({ title: "请输入账号", icon: "none" });
  }
  if (!form.password.trim()) {
    return uni.showToast({ title: "请输入密码", icon: "none" });
  }

  loading.value = true;
  try {
    userStore.logout();
    const res = await request("/login", "POST", form);
    if (res?.access_token) {
      uni.showToast({ title: "登录成功", icon: "success" });
      setTimeout(() => {
        completeAgencyLogin(res);
      }, 500);
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
  margin-bottom: 60rpx;
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
  line-height: 1.6;
}

.form-section {
  width: 100%;
}

.wx-btn {
  background-color: #07c160;
  color: #ffffff;
  font-size: 32rpx;
  font-weight: 500;
  height: 96rpx;
  line-height: 96rpx;
  border-radius: 8rpx;
}

.wx-btn::after {
  border: none;
}

.divider {
  display: flex;
  align-items: center;
  margin: 48rpx 0;
  gap: 20rpx;
}

.divider-line {
  flex: 1;
  height: 2rpx;
  background-color: #e5e7eb;
}

.divider-text {
  font-size: 24rpx;
  color: #9ca3af;
  flex-shrink: 0;
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
}

.ph-color {
  color: #9ca3af;
  font-size: 30rpx;
}

.submit-btn {
  margin-top: 20rpx;
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

.form-footer {
  margin-top: 40rpx;
  text-align: center;
}

.footer-text {
  font-size: 26rpx;
  color: #9ca3af;
  line-height: 1.5;
}
</style>
