<template>
  <view class="container">
    <view class="header-section">
      <text class="page-title">设置登录密码</text>
      <text class="page-subtitle">首次登录须设置密码，设置后可使用「手机号 + 密码」登录机构端</text>
    </view>

    <view class="form-section">
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

      <button class="submit-btn" :loading="loading" @click="handleSubmit">确认设置</button>
      <view class="logout-link" @click="handleLogout">退出登录</view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import { request } from "@/utils/request";
import { useUserStore } from "@/store/modules/user";
import { isAgencyUser } from "@/utils/role";

const userStore = useUserStore();
const loading = ref(false);
const form = reactive({
  newPassword: "",
  confirmPassword: "",
});

onShow(async () => {
  if (!userStore.token) {
    uni.reLaunch({ url: "/pages/login/index" });
    return;
  }
  await userStore.fetchUserInfo();
  if (!isAgencyUser(userStore.userInfo)) {
    uni.reLaunch({ url: "/pages/patient/home" });
    return;
  }
  if (!userStore.userInfo?.mustChangePassword) {
    uni.reLaunch({ url: "/pages/index/index" });
  }
});

const handleSubmit = async () => {
  const pwd = form.newPassword.trim();
  const confirm = form.confirmPassword.trim();
  if (pwd.length < 6) {
    return uni.showToast({ title: "密码至少 6 位", icon: "none" });
  }
  if (pwd === "123456" || pwd === "wx123456") {
    return uni.showToast({ title: "不能使用系统占位密码", icon: "none" });
  }
  if (pwd !== confirm) {
    return uni.showToast({ title: "两次密码不一致", icon: "none" });
  }

  loading.value = true;
  try {
    await request("/user/setInitialPassword", "POST", { newPassword: pwd });
    await userStore.fetchUserInfo();
    uni.showToast({ title: "设置成功", icon: "success" });
    setTimeout(() => {
      uni.reLaunch({ url: "/pages/index/index" });
    }, 800);
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
};

const handleLogout = () => {
  uni.showModal({
    title: "提示",
    content: "确定退出登录吗？",
    confirmColor: "#2563EB",
    success: (res) => {
      if (res.confirm) {
        userStore.logout();
        uni.reLaunch({ url: "/pages/patient/home" });
      }
    },
  });
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
  line-height: 1.6;
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

.logout-link {
  margin-top: 40rpx;
  text-align: center;
  font-size: 28rpx;
  color: #6b7280;
}
</style>
