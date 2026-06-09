<template>
  <view class="container">
    <view class="list-container">
      <view v-if="caseList.length === 0 && !loading" class="empty-state">
        <text class="empty-icon">📭</text>
        <text class="empty-text">您暂未提交过案件信息</text>
      </view>

      <view 
        class="case-card" 
        v-for="item in caseList" 
        :key="item.id"
      >
        <view class="card-header">
          <text class="report-no">报案号：{{ item.reportNumber }}</text>
          <view :class="['status-tag', 'status-' + item.status]">
            {{ getStatusText(item.status) }}
          </view>
        </view>
        
        <view class="card-body">
          <view class="progress-bar">
            <!-- 简单模拟进度条 -->
            <view class="step" :class="{ active: true }">
              <text class="step-dot"></text>
              <text class="step-text">已报案</text>
            </view>
            <view class="step-line" :class="{ active: item.status >= 2 }"></view>
            <view class="step" :class="{ active: item.status >= 2 }">
              <text class="step-dot"></text>
              <text class="step-text">{{ item.status === 1 ? '匹配机构中' : '鉴定中' }}</text>
            </view>
            <view class="step-line" :class="{ active: item.status === 3 }"></view>
            <view class="step" :class="{ active: item.status === 3 }">
              <text class="step-dot"></text>
              <text class="step-text">已出报告</text>
            </view>
          </view>

          <!-- 如果已分配机构，显示机构信息 -->
          <view class="agency-info" v-if="item.status >= 2 && item.agencyName">
            <view class="info-title">为您服务的鉴定机构：</view>
            <view class="info-content">{{ item.agencyName }}</view>
            <view class="info-tip">法医人员将与您取得联系，请保持电话畅通。</view>
          </view>
          
          <view class="agency-info warning" v-else-if="item.status === 1">
            <view class="info-title">进度提示：</view>
            <view class="info-tip">系统正在为您就近匹配鉴定机构，请耐心等待。</view>
          </view>
        </view>
      </view>

      <view class="loading-more" v-if="caseList.length > 0">
        <text>{{ loading ? '加载中...' : (hasMore ? '上拉加载更多' : '没有更多记录了') }}</text>
      </view>
    </view>
    
    <!-- 悬浮个人中心按钮 -->
    <view class="float-mine-btn" @click="goToMine">
      <text class="iconfont">👤</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad, onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app'
import { request } from '@/utils/request'

const goToMine = () => {
  uni.navigateTo({ url: '/pages/mine/index' })
}

const caseList = ref<any[]>([])
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)
const loading = ref(false)
const hasMore = ref(true)

const getStatusText = (status: number) => {
  const map: Record<number, string> = { 1: '待接单', 2: '鉴定中', 3: '已完成', 4: '复议中' }
  return map[status] || '未知'
}

const fetchList = async (isRefresh = false) => {
  if (loading.value) return
  loading.value = true

  if (isRefresh) {
    pageNum.value = 1
    hasMore.value = true
  }

  try {
    const params: any = {
      pageNum: pageNum.value,
      pageSize: pageSize.value
    }

    const res = await request('/biz/case', 'GET', params)
    
    if (res && res.list) {
      if (isRefresh) {
        caseList.value = res.list
      } else {
        caseList.value = [...caseList.value, ...res.list]
      }
      total.value = res.total || 0
      
      if (caseList.value.length >= total.value) {
        hasMore.value = false
      } else {
        hasMore.value = true
      }
    }
  } catch (error) {
    console.error('Fetch case list error:', error)
  } finally {
    loading.value = false
    uni.stopPullDownRefresh()
  }
}

onLoad(() => {
  fetchList(true)
  uni.$on('refreshList', () => {
    fetchList(true)
  })
})

onPullDownRefresh(() => {
  fetchList(true)
})

onReachBottom(() => {
  if (hasMore.value && !loading.value) {
    pageNum.value += 1
    fetchList()
  }
})
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f4f7f6;
  padding: 24rpx;
}
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 200rpx;
}
.empty-icon { font-size: 100rpx; margin-bottom: 20rpx; }
.empty-text { color: #999; font-size: 28rpx; }

.case-card {
  background-color: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 6rpx 20rpx rgba(0,0,0,0.03);
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 24rpx;
  border-bottom: 1rpx solid #f0f0f0;
}
.report-no { font-size: 28rpx; font-weight: bold; color: #333; }
.status-tag { font-size: 24rpx; padding: 4rpx 16rpx; border-radius: 10rpx; }
.status-1 { background-color: #fff8e6; color: #f59a23; }
.status-2 { background-color: #e6f6f0; color: #0ba360; }
.status-3 { background-color: #f2f3f5; color: #666; }

.card-body { padding-top: 30rpx; }

/* 进度条 */
.progress-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 40rpx;
  padding: 0 20rpx;
}
.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 2;
}
.step-dot {
  width: 20rpx;
  height: 20rpx;
  border-radius: 50%;
  background-color: #ddd;
  margin-bottom: 10rpx;
}
.step.active .step-dot {
  background-color: #0ba360;
  box-shadow: 0 0 0 6rpx rgba(11, 163, 96, 0.2);
}
.step-text {
  font-size: 24rpx;
  color: #999;
}
.step.active .step-text {
  color: #333;
  font-weight: bold;
}
.step-line {
  flex: 1;
  height: 4rpx;
  background-color: #ddd;
  margin: 0 10rpx;
  margin-top: -30rpx;
}
.step-line.active {
  background-color: #0ba360;
}

/* 机构提示信息 */
.agency-info {
  background-color: #f8f9fa;
  border-radius: 12rpx;
  padding: 24rpx;
  border-left: 6rpx solid #0ba360;
}
.agency-info.warning {
  border-left-color: #f59a23;
  background-color: #fff8e6;
}
.info-title { font-size: 26rpx; color: #666; margin-bottom: 10rpx; }
.info-content { font-size: 30rpx; font-weight: bold; color: #333; margin-bottom: 10rpx; }
.info-tip { font-size: 24rpx; color: #999; }

.loading-more { text-align: center; font-size: 24rpx; color: #999; padding: 20rpx 0; }

/* 悬浮按钮 */
.float-mine-btn {
  position: fixed;
  right: 40rpx;
  bottom: 100rpx;
  width: 100rpx;
  height: 100rpx;
  background: linear-gradient(135deg, #0ba360 0%, #3cba92 100%);
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 8rpx 20rpx rgba(11, 163, 96, 0.4);
  z-index: 99;
}

.float-mine-btn .iconfont {
  color: #ffffff;
  font-size: 48rpx;
}
</style>
