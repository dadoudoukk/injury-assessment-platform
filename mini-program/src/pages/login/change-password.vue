<template>
  <view class="container">
    <view class="header-section">
      <text class="page-title">修改密码</text>
      <text class="page-subtitle">修改后请使用新密码登录</text>
    </view>

    <view class="form-section">
      <view class="input-group">
        <text class="label">原密码</text>
        <input
          v-model="form.oldPassword"
          class="input-field"
          type="password"
          placeholder="请输入原密码"
          placeholder-class="ph-color"
        />
      </view>
      <view class="input-group">
        <text class="label">新密码</text>
        <input
          v-model="form.newPassword"
          class="input-field"
          type="password"
          placeholder="至少 6 位"
          placeholder-class="ph-color"
        />
      </view>
      <view class="input-group">
        <text class="label">确认密码</text>
        <input
          v-model="form.confirmPassword"
          class="input-field"
          type="password"
          placeholder="再次输入新密码"
          placeholder-class="ph-color"
        />
      </view>

      <button class="submit-btn" :loading="loading" @click="handleSubmit">确认修改</button>
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
  oldPassword: "",
  newPassword: "",
  confirmPassword: "",
});

const handleSubmit = async () => {
  const oldPwd = form.oldPassword.trim();
  const pwd = form.newPassword.trim();
  const confirm = form.confirmPassword.trim();
  if (!oldPwd) {
    return uni.showToast({ title: "请输入原密码", icon: "none" });
  }
  if (pwd.length < 6) {
    return uni.showToast({ title: "新密码至少 6 位", icon: "none" });
  }
  if (pwd !== confirm) {
    return uni.showToast({ title: "两次密码不一致", icon: "none" });
  }

  loading.value = true;
  try {
    await request("/user/changePassword", "POST", {
      oldPassword: oldPwd,
      newPassword: pwd,
    });
    userStore.logout();
    uni.showModal({
      title: "修改成功",
      content: "密码已更新，请重新登录",
      showCancel: false,
      confirmColor: "#2563EB",
      success: () => {
        uni.reLaunch({ url: "/pages/login/index" });
      },
    });
  } catch (e) {
    console.error(e);
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
}

.submit-btn::after {
  border: none;
}
</style>
