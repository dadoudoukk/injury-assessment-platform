<template>
  <view class="container">
    <view class="header-section">
      <view class="brand-line"></view>
      <text class="page-title">案件列表</text>
    </view>

    <view class="list-container">
      <view v-if="caseList.length === 0 && !loading" class="empty-state">
        <text class="empty-text">暂无理赔案件</text>
        <button class="empty-btn" @click="goToCreate">快速报案</button>
      </view>

      <view class="case-card" hover-class="card-hover" v-for="item in caseList" :key="item.id" @click="goToDetail(item.id)">
        <view class="card-header">
          <text class="report-no">报案号：{{ item.reportNumber }}</text>
          <text :class="['status-text', 'status-' + item.status]">
            {{ getStatusText(item.status) }}
          </text>
        </view>

        <view class="card-body">
          <view class="progress-bar">
            <view class="step" :class="{ active: true }">
              <view class="step-dot"></view>
              <text class="step-label">已报案</text>
            </view>
            <view class="step-line" :class="{ active: item.status >= 2 }"></view>
            <view class="step" :class="{ active: item.status >= 2 && item.status !== 5 }">
              <view class="step-dot" :class="{ current: item.status >= 2 && item.status < 4 }"></view>
              <text class="step-label">{{ item.status === 1 ? '匹配中' : '鉴定中' }}</text>
            </view>
            <view class="step-line" :class="{ active: item.status === 4 }"></view>
            <view class="step" :class="{ active: item.status === 4 }">
              <view class="step-dot" :class="{ current: item.status === 4 }"></view>
              <text class="step-label">已出报告</text>
            </view>
          </view>

          <!-- 如果已分配机构，显示机构信息 -->
          <view class="agency-info" v-if="item.status >= 2 && item.agencyName">
            <view class="info-title">服务机构</view>
            <view class="info-content">{{ item.agencyName }}</view>
          </view>

          <view class="agency-info" v-else-if="item.status === 1">
            <view class="info-title">进度提示</view>
            <view class="info-content text-gray">系统正在匹配机构，请耐心等待。</view>
          </view>
        </view>
      </view>

      <view class="loading-more" v-if="caseList.length > 0">
        <text>{{ loading ? "加载中..." : hasMore ? "上拉加载更多" : "没有更多记录了" }}</text>
      </view>
    </view>

    <!-- 底部固定栏用于跳转个人中心和报案 -->
    <view class="bottom-action-bar">
      <view class="nav-item" @click="goToMine">
        <text class="nav-text">个人中心</text>
      </view>
      <view class="nav-item primary" @click="goToCreate">
        <text class="nav-text">我要报案</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { onLoad, onPullDownRefresh, onReachBottom } from "@dcloudio/uni-app";
import { request } from "@/utils/request";

const goToMine = () => {
  uni.navigateTo({ url: "/pages/mine/index" });
};

const goToCreate = () => {
  uni.navigateTo({ url: "/pages/patient/create" });
};

const goToDetail = (id: string | number) => {
  uni.navigateTo({ url: `/pages/detail/index?id=${id}` });
};

const caseList = ref<any[]>([]);
const pageNum = ref(1);
const pageSize = ref(10);
const total = ref(0);
const loading = ref(false);
const hasMore = ref(true);

const getStatusText = (status: number) => {
  const map: Record<number, string> = {
    1: "待确认",
    2: "已受理",
    3: "鉴定中",
    4: "已完成",
    5: "已打回"
  };
  return map[status] || "未知";
};

const fetchList = async (isRefresh = false) => {
  if (loading.value) return;
  loading.value = true;

  if (isRefresh) {
    pageNum.value = 1;
    hasMore.value = true;
  }

  try {
    const params: any = {
      pageNum: pageNum.value,
      pageSize: pageSize.value,
    };

    const res = await request("/biz/case", "GET", params);

    if (res && res.list) {
      if (isRefresh) {
        caseList.value = res.list;
      } else {
        caseList.value = [...caseList.value, ...res.list];
      }
      total.value = res.total || 0;

      if (caseList.value.length >= total.value) {
        hasMore.value = false;
      } else {
        hasMore.value = true;
      }
    }
  } catch (error) {
    console.error("Fetch case list error:", error);
  } finally {
    loading.value = false;
    uni.stopPullDownRefresh();
  }
};

onLoad(() => {
  fetchList(true);
  uni.$on("refreshList", () => {
    fetchList(true);
  });
});

onPullDownRefresh(() => {
  fetchList(true);
});

onReachBottom(() => {
  if (hasMore.value && !loading.value) {
    pageNum.value += 1;
    fetchList();
  }
});
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #FFFFFF;
  padding-bottom: 120rpx; /* 留出底部导航栏空间 */
}

.header-section {
  padding: 40rpx 40rpx;
  background-color: #FFFFFF;
}

.brand-line {
  width: 40rpx;
  height: 6rpx;
  background-color: #2563EB;
  margin-bottom: 20rpx;
}

.page-title {
  font-size: 44rpx;
  font-weight: 600;
  color: #111827;
}

.list-container {
  padding: 0 40rpx;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 160rpx;
}

.empty-text {
  color: #6B7280;
  font-size: 32rpx;
  margin-bottom: 60rpx;
}

.empty-btn {
  background-color: #2563EB;
  color: #FFFFFF;
  font-size: 32rpx;
  padding: 0 80rpx;
  height: 88rpx;
  line-height: 88rpx;
  border-radius: 8rpx;
  font-weight: 500;
}
.empty-btn::after {
  border: none;
}

.case-card {
  background-color: #FFFFFF;
  border: 2rpx solid #E5E7EB;
  border-radius: 8rpx;
  padding: 40rpx;
  margin-bottom: 40rpx;
  transition: all 0.3s;
}

.card-hover {
  background-color: #F9FAFB;
  border-color: #D1D5DB;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 30rpx;
  border-bottom: 2rpx solid #E5E7EB;
}

.report-no {
  font-size: 32rpx;
  font-weight: 600;
  color: #111827;
}

.status-text {
  font-size: 26rpx;
  font-weight: 500;
}

.status-1 { color: #2563EB; }
.status-2 { color: #059669; }
.status-3 { color: #4B5563; }
.status-4 { color: #DC2626; }

.card-body {
  padding-top: 40rpx;
}

/* 极简进度条 */
.progress-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 40rpx;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 2;
  background: #FFF;
}

.step-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background-color: #E5E7EB;
  margin-bottom: 16rpx;
}

.step.active .step-dot {
  background-color: #111827;
}

.step-dot.current {
  background-color: #2563EB;
  box-shadow: 0 0 0 4rpx rgba(37, 99, 235, 0.2);
}

.step-label {
  font-size: 24rpx;
  color: #9CA3AF;
}

.step.active .step-label {
  color: #111827;
  font-weight: 500;
}

.step-line {
  flex: 1;
  height: 2rpx;
  background-color: #E5E7EB;
  margin: 0 10rpx;
  margin-top: -36rpx; /* 对齐点 */
}

.step-line.active {
  background-color: #111827;
}

/* 机构提示信息 */
.agency-info {
  background-color: #F9FAFB;
  border: 2rpx solid #E5E7EB;
  border-radius: 4rpx;
  padding: 30rpx;
}

.info-title {
  font-size: 24rpx;
  color: #6B7280;
  margin-bottom: 12rpx;
}

.info-content {
  font-size: 30rpx;
  font-weight: 500;
  color: #111827;
}

.text-gray {
  color: #6B7280;
  font-weight: 400;
}

.loading-more {
  text-align: center;
  font-size: 26rpx;
  color: #9CA3AF;
  padding: 40rpx 0;
}

/* 底部固定动作栏 */
.bottom-action-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 110rpx;
  background-color: #FFFFFF;
  border-top: 2rpx solid #E5E7EB;
  display: flex;
  z-index: 100;
}

.nav-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-item:active {
  background-color: #F9FAFB;
}

.nav-item.primary {
  background-color: #2563EB;
}

.nav-item.primary:active {
  background-color: #1D4ED8;
}

.nav-text {
  font-size: 30rpx;
  color: #4B5563;
  font-weight: 500;
}

.nav-item.primary .nav-text {
  color: #FFFFFF;
}
</style>
