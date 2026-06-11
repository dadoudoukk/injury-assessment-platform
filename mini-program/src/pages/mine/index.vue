<template>
  <view class="mine-container">
    <view class="header-section"></view>

    <view class="content-card">
      <!-- 伤者：仅展示脱敏手机号 -->
      <view v-if="!isAgency" class="patient-view">
        <text class="phone-number">{{ maskedPhone || "未绑定手机号" }}</text>
      </view>

      <!-- 机构：展示机构信息 -->
      <view v-else class="agency-view">
        <text class="agency-title">{{ userInfo?.agencyName || "未知鉴定机构" }}</text>
        <view class="info-list">
          <view class="info-row">
            <text class="info-label">联系人</text>
            <text class="info-value">{{ userInfo?.contactPerson || "暂无" }}</text>
          </view>
          <view class="info-row">
            <text class="info-label">联系电话</text>
            <text class="info-value">{{ userInfo?.contactPhone || "暂无" }}</text>
          </view>
          <view class="info-row">
            <text class="info-label">省市区</text>
            <text class="info-value">{{ regionText || "暂无" }}</text>
          </view>
          <view class="info-row">
            <text class="info-label">详细地址</text>
            <text class="info-value address-text">{{ userInfo?.address || "暂无" }}</text>
          </view>
        </view>
      </view>
    </view>

    <view v-if="isAgency && !mustChangePassword" class="action-btn" @click="goChangePassword">
      修改密码
    </view>

    <view class="logout-btn" @click="handleLogout">退出登录</view>
  </view>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { onShow } from "@dcloudio/uni-app";
import { useUserStore } from "@/store/modules/user";
import { isAgencyUser } from "@/utils/role";
import { ensureAgencySession } from "@/utils/agency-auth";

const userStore = useUserStore();

const userInfo = computed(() => userStore.userInfo);
const isAgency = computed(() => isAgencyUser(userInfo.value));
const mustChangePassword = computed(() => userInfo.value?.mustChangePassword === true);

const maskedPhone = computed(() => {
  const phone = userInfo.value?.phone || "";
  if (!phone) return "";
  return phone.replace(/(\d{3})\d{4}(\d{4})/, "$1****$2");
});

const regionText = computed(() => {
  const info = userInfo.value;
  if (!info) return "";
  const parts = [info.province, info.city, info.district].filter(Boolean);
  return parts.join("");
});

onShow(async () => {
  if (!userStore.token) {
    uni.reLaunch({ url: "/pages/patient/home" });
    return;
  }
  await userStore.fetchUserInfo();
  if (isAgency.value) {
    await ensureAgencySession(false);
  }
});

const goChangePassword = () => {
  uni.navigateTo({ url: "/pages/login/change-password" });
};

const handleLogout = () => {
  uni.showModal({
    title: "提示",
    content: "确定要退出登录吗？",
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

<style scoped lang="scss">
.mine-container {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding-bottom: 40rpx;
}

.header-section {
  height: 280rpx;
  background: linear-gradient(135deg, #2b85e4 0%, #5cadff 100%);
  border-radius: 0 0 40rpx 40rpx;
}

.content-card {
  margin: -80rpx 30rpx 0;
  background-color: #ffffff;
  border-radius: 16rpx;
  padding: 48rpx 36rpx;
  box-shadow: 0 8rpx 20rpx rgba(0, 0, 0, 0.05);
  position: relative;
  z-index: 2;
}

.patient-view {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 120rpx;
}

.phone-number {
  font-size: 48rpx;
  font-weight: 600;
  color: #111827;
  letter-spacing: 2rpx;
}

.agency-view {
  display: flex;
  flex-direction: column;
}

.agency-title {
  font-size: 36rpx;
  font-weight: 600;
  color: #111827;
  line-height: 1.4;
  margin-bottom: 36rpx;
  padding-bottom: 28rpx;
  border-bottom: 2rpx solid #f0f0f0;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 28rpx;
}

.info-row {
  display: flex;
  align-items: flex-start;
  font-size: 28rpx;
  line-height: 1.5;
}

.info-label {
  width: 140rpx;
  flex-shrink: 0;
  color: #6b7280;
}

.info-value {
  flex: 1;
  color: #111827;
}

.address-text {
  word-break: break-all;
}

.action-btn {
  margin: 40rpx 30rpx 0;
  background-color: #ffffff;
  color: #2563eb;
  font-size: 32rpx;
  text-align: center;
  padding: 28rpx 0;
  border-radius: 16rpx;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.02);
}

.logout-btn {
  margin: 24rpx 30rpx 0;
  background-color: #ffffff;
  color: #ef4444;
  font-size: 32rpx;
  text-align: center;
  padding: 28rpx 0;
  border-radius: 16rpx;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.02);
}
</style>
