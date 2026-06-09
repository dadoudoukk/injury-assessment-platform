<template>
  <view class="container">
    <!-- 顶部状态切换 Tabs -->
    <view class="tabs">
      <view 
        v-for="(tab, index) in tabs" 
        :key="index"
        :class="['tab-item', currentTab === index ? 'active' : '']"
        @click="switchTab(index)"
      >
        <text class="tab-text">{{ tab.name }}</text>
        <view v-if="currentTab === index" class="tab-line"></view>
      </view>
    </view>

    <!-- 列表区域 -->
    <view class="list-container">
      <view v-if="caseList.length === 0 && !loading" class="empty-state">
        <text class="empty-icon">📭</text>
        <text class="empty-text">暂无相关案件数据</text>
      </view>

      <view 
        class="case-card" 
        v-for="item in caseList" 
        :key="item.id"
        @click="goToDetail(item.id)"
      >
        <view class="card-header">
          <view class="header-left">
            <text class="report-label">报案号：</text>
            <text class="report-no">{{ item.reportNumber }}</text>
          </view>
          <view :class="['status-tag', 'status-' + item.status]">
            {{ getStatusText(item.status) }}
          </view>
        </view>
        
        <view class="card-body">
          <view class="info-row" v-if="item.status === 4 && item.reworkRemark">
            <text class="info-icon">⚠️</text>
            <text class="info-label" style="color: #ff4d4f">打回原因：</text>
            <text class="info-value" style="color: #ff4d4f">{{ item.reworkRemark }}</text>
          </view>
          
          <view class="info-row">
            <text class="info-icon">👤</text>
            <text class="info-label">伤者姓名：</text>
            <text class="info-value strong">{{ item.victimName }}</text>
          </view>
          
          <view class="info-row" @click.stop="callPhone(item.victimPhone)">
            <text class="info-icon">📱</text>
            <text class="info-label">联系电话：</text>
            <text class="info-value phone">{{ item.victimPhone }}</text>
            <text class="call-btn">拨打</text>
          </view>

          <view class="info-row">
            <text class="info-icon">📍</text>
            <text class="info-label">出险地点：</text>
            <text class="info-value">{{ item.province }}{{ item.city }}{{ item.district }}</text>
          </view>

          <view class="info-row">
            <text class="info-icon">🚑</text>
            <text class="info-label">事故类型：</text>
            <text class="info-value">{{ getDictLabel(item.accidentType, 'biz_accident_type') }}</text>
          </view>

          <view class="info-row">
            <text class="info-icon">🏢</text>
            <text class="info-label">保险公司：</text>
            <text class="info-value">{{ item.insuranceCompany }}</text>
          </view>
        </view>
        
        <!-- 底部操作栏 -->
        <view class="card-footer">
          <text class="date-text">报案时间：{{ item.reportDate }}</text>
          <view class="actions">
            <view class="action-btn danger-btn" v-if="item.status === 1" @click.stop="handleReject(item)">拒单</view>
            <view class="action-btn" v-if="item.status === 2">去鉴定</view>
            <view class="action-btn view-btn" v-else>查看详情</view>
          </view>
        </view>
      </view>

      <!-- 加载状态提示 -->
      <view class="loading-more" v-if="caseList.length > 0">
        <text>{{ loading ? '加载中...' : (hasMore ? '上拉加载更多' : '没有更多数据了') }}</text>
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
import { onLoad, onPullDownRefresh, onReachBottom, onShow } from '@dcloudio/uni-app'
import { request } from '@/utils/request'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()

const goToMine = () => {
  uni.navigateTo({ url: '/pages/mine/index' })
}

const handleReject = (item: any) => {
  uni.showModal({
    title: '确认拒单',
    content: '拒单后将把该案件退回平台重新派单，是否确认？',
    success: async (res) => {
      if (res.confirm) {
        uni.showLoading({ title: '处理中...' })
        try {
          // 由于 request 已经包含了 msg 提示，这里如果想用它的 msg 可以让 request 抛出完整的对象，或者就默认成功了
          await request(`/biz/case/${item.id}/reject`, 'POST', { reason: '机构主动拒单' })
          uni.showToast({ title: '已退单并重新分配', icon: 'success' })
          fetchList(true)
        } catch (e) {
          console.error(e)
        } finally {
          uni.hideLoading()
        }
      }
    }
  })
}

// Tabs配置
const tabs = [
  { name: '全部', value: null },
  { name: '鉴定中', value: 2 },
  { name: '已打回', value: 4 },
  { name: '已完成', value: 3 }
]
const currentTab = ref(0)

// 列表数据与分页
const caseList = ref<any[]>([])
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)
const loading = ref(false)
const hasMore = ref(true)

// 字典缓存 (本地简单缓存处理展示)
// 实际项目中可以统一封装 dict store
const accidentTypes = ref<any[]>([])

const fetchDicts = async () => {
  try {
    const res = await request('/dict/data/type/biz_accident_type', 'GET')
    if (res) {
      accidentTypes.value = res
    }
  } catch (error) {
    console.error('Fetch dict error:', error)
  }
}

const getDictLabel = (value: string, _type: string) => {
  const dict = accidentTypes.value.find(item => item.dictValue === value)
  return dict ? dict.dictLabel : value
}

const getStatusText = (status: number) => {
  const map: Record<number, string> = {
    1: '待接单',
    2: '鉴定中',
    3: '已完成',
    4: '已打回'
  }
  return map[status] || '未知'
}

// 获取案件列表
const fetchList = async (isRefresh = false) => {
  if (loading.value) return
  loading.value = true

  if (isRefresh) {
    pageNum.value = 1
    hasMore.value = true
  }

  try {
    const status = tabs[currentTab.value].value
    const params: any = {
      pageNum: pageNum.value,
      pageSize: pageSize.value
    }
    if (status) params.status = status

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
    uni.stopPullDownRefresh() // 停止下拉刷新动画
  }
}

// 切换Tab
const switchTab = (index: number) => {
  if (currentTab.value === index) return
  currentTab.value = index
  fetchList(true)
}

// 拨打电话
const callPhone = (phone: string) => {
  uni.makePhoneCall({
    phoneNumber: phone
  })
}

// 跳转详情页 (下步开发)
const goToDetail = (id: string) => {
  uni.navigateTo({
    url: `/pages/detail/index?id=${id}`
  })
}

// 生命周期与事件
onLoad(async () => {
  await fetchDicts()
  fetchList(true)
})

// 下拉刷新
onPullDownRefresh(() => {
  fetchList(true)
})

// 上拉加载更多
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
  padding-bottom: 40rpx;
}

/* Tabs */
.tabs {
  display: flex;
  background-color: #ffffff;
  padding: 0 20rpx;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.02);
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 88rpx;
  position: relative;
}

.tab-text {
  font-size: 30rpx;
  color: #666666;
  transition: all 0.3s;
}

.tab-item.active .tab-text {
  color: #0ba360;
  font-weight: 600;
}

.tab-line {
  position: absolute;
  bottom: 0;
  width: 40rpx;
  height: 6rpx;
  background-color: #0ba360;
  border-radius: 6rpx;
}

/* 列表容器 */
.list-container {
  padding: 24rpx;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding-top: 200rpx;
}
.empty-icon {
  font-size: 100rpx;
  margin-bottom: 20rpx;
}
.empty-text {
  color: #999;
  font-size: 28rpx;
}

/* 卡片 */
.case-card {
  background-color: #ffffff;
  border-radius: 20rpx;
  padding: 24rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 6rpx 20rpx rgba(0,0,0,0.03);
  position: relative;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 20rpx;
  border-bottom: 1rpx dashed #eeeeee;
}

.header-left {
  display: flex;
  align-items: center;
}

.report-label {
  font-size: 26rpx;
  color: #999999;
}

.report-no {
  font-size: 28rpx;
  font-weight: 600;
  color: #333333;
}

.status-tag {
  font-size: 24rpx;
  padding: 4rpx 16rpx;
  border-radius: 10rpx;
  font-weight: 500;
}
.status-1 {
  background-color: #fff8e6;
  color: #f59a23;
}
.status-2 {
  background-color: #e6f6f0;
  color: #0ba360;
}
.status-3 {
  background-color: #f2f3f5;
  color: #666666;
}
.status-4 {
  background-color: #fff1f0;
  color: #ff4d4f;
}

.card-body {
  padding: 20rpx 0;
}

.info-row {
  display: flex;
  align-items: center;
  margin-bottom: 16rpx;
}
.info-row:last-child {
  margin-bottom: 0;
}

.info-icon {
  font-size: 28rpx;
  margin-right: 12rpx;
}

.info-label {
  font-size: 28rpx;
  color: #666666;
  width: 150rpx;
}

.info-value {
  font-size: 28rpx;
  color: #333333;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.info-value.strong {
  font-weight: bold;
  font-size: 30rpx;
}

.info-value.phone {
  color: #007aff;
}

.call-btn {
  font-size: 24rpx;
  color: #0ba360;
  border: 1rpx solid #0ba360;
  padding: 4rpx 16rpx;
  border-radius: 20rpx;
  margin-left: 10rpx;
}
.call-btn:active {
  background-color: #0ba360;
  color: #ffffff;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 20rpx;
  border-top: 1rpx solid #f5f5f5;
}

.date-text {
  font-size: 24rpx;
  color: #999999;
}

.actions {
  display: flex;
  gap: 20rpx;
}

.action-btn {
  background: linear-gradient(90deg, #0ba360 0%, #3cba92 100%);
  color: #ffffff;
  font-size: 26rpx;
  padding: 10rpx 30rpx;
  border-radius: 30rpx;
  font-weight: 500;
  box-shadow: 0 4rpx 10rpx rgba(11, 163, 96, 0.2);
}

.danger-btn {
  background: #fff;
  color: #ff4d4f;
  border: 1rpx solid #ff4d4f;
  padding: 8rpx 28rpx;
  box-shadow: none;
}
.action-btn:active {
  transform: scale(0.95);
}

.action-btn.view-btn {
  background: #f0f2f5;
  color: #666666;
  box-shadow: none;
}

.loading-more {
  text-align: center;
  font-size: 24rpx;
  color: #999999;
  padding: 20rpx 0;
}

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
