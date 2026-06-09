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
        <text class="empty-text">暂无相关案件卷宗</text>
      </view>

      <view 
        class="case-card" 
        v-for="item in caseList" 
        :key="item.id"
        @click="goToDetail(item.id)"
      >
        <view class="card-header">
          <text class="report-no">{{ item.reportNumber }}</text>
          <text :class="['status-text', 'status-' + item.status]">
            {{ getStatusText(item.status) }}
          </text>
        </view>
        
        <view class="card-body">
          <view class="info-row" v-if="item.status === 4 && item.reworkRemark">
            <text class="info-label text-red">打回原因</text>
            <text class="info-value text-red font-bold">{{ item.reworkRemark }}</text>
          </view>
          
          <view class="info-row">
            <text class="info-label">伤者姓名</text>
            <text class="info-value font-bold">{{ item.victimName }}</text>
          </view>
          
          <view class="info-row" @click.stop="callPhone(item.victimPhone)">
            <text class="info-label">联系电话</text>
            <text class="info-value text-blue">{{ item.victimPhone }}</text>
          </view>

          <view class="info-row">
            <text class="info-label">出险地点</text>
            <text class="info-value">{{ item.province }}{{ item.city }}{{ item.district }}</text>
          </view>

          <view class="info-row">
            <text class="info-label">事故类型</text>
            <text class="info-value">{{ getDictLabel(item.accidentType, 'biz_accident_type') }}</text>
          </view>

          <view class="info-row">
            <text class="info-label">保险公司</text>
            <text class="info-value">{{ item.insuranceCompany }}</text>
          </view>
        </view>
        
        <view class="card-footer">
          <text class="date-text">{{ item.reportDate }}</text>
          <view class="actions">
            <button class="action-btn danger" v-if="item.status === 1" @click.stop="handleReject(item)">拒单</button>
            <button class="action-btn primary" v-if="item.status === 2">去鉴定</button>
            <button class="action-btn" v-else-if="item.status !== 1">查看卷宗</button>
          </view>
        </view>
      </view>

      <view class="loading-more" v-if="caseList.length > 0">
        <text>{{ loading ? '加载中...' : (hasMore ? '上拉加载更多' : '没有更多数据了') }}</text>
      </view>
    </view>
    
    <!-- 底部导航栏 -->
    <view class="bottom-action-bar">
      <view class="nav-item active">
        <text class="nav-text">工作台</text>
      </view>
      <view class="nav-item" @click="goToMine">
        <text class="nav-text">个人中心</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad, onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app'
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
    confirmColor: '#DC2626',
    success: async (res) => {
      if (res.confirm) {
        uni.showLoading({ title: '处理中...' })
        try {
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

const accidentTypes = ref<any[]>([])

const fetchDicts = async () => {
  try {
    const res = await request('/dict/data/biz_accident_type', 'GET')
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
    uni.stopPullDownRefresh()
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

const goToDetail = (id: string) => {
  uni.navigateTo({
    url: `/pages/detail/index?id=${id}`
  })
}

onLoad(async () => {
  await fetchDicts()
  fetchList(true)
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
  background-color: #FFFFFF;
  padding-bottom: 120rpx;
}

/* Tabs */
.tabs {
  display: flex;
  background-color: #FFFFFF;
  border-bottom: 2rpx solid #E5E7EB;
  position: sticky;
  top: 0;
  z-index: 100;
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 96rpx;
  position: relative;
}

.tab-text {
  font-size: 30rpx;
  color: #6B7280;
  transition: all 0.3s;
}

.tab-item.active .tab-text {
  color: #111827;
  font-weight: 600;
}

.tab-line {
  position: absolute;
  bottom: 0;
  width: 100%;
  height: 4rpx;
  background-color: #111827;
}

/* 列表容器 */
.list-container {
  padding: 40rpx;
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
}

/* 卡片 */
.case-card {
  background-color: #FFFFFF;
  border: 2rpx solid #E5E7EB;
  border-radius: 8rpx;
  padding: 40rpx;
  margin-bottom: 40rpx;
  transition: all 0.3s;
}

.case-card:active {
  background-color: #F9FAFB;
  border-color: #D1D5DB;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 24rpx;
  border-bottom: 2rpx solid #E5E7EB;
  margin-bottom: 30rpx;
}

.report-no {
  font-size: 32rpx;
  font-weight: 600;
  color: #111827;
  font-family: consolas, monospace;
}

.status-text {
  font-size: 26rpx;
  font-weight: 500;
}

.status-1 { color: #D97706; }
.status-2 { color: #2563EB; }
.status-3 { color: #4B5563; }
.status-4 { color: #DC2626; }

.info-row {
  display: flex;
  margin-bottom: 20rpx;
}
.info-row:last-child {
  margin-bottom: 0;
}

.info-label {
  font-size: 28rpx;
  color: #6B7280;
  width: 160rpx;
}

.info-value {
  font-size: 28rpx;
  color: #111827;
  flex: 1;
}

.font-bold {
  font-weight: 500;
}

.text-blue {
  color: #2563EB;
}

.text-red {
  color: #DC2626;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 30rpx;
  padding-top: 24rpx;
  border-top: 2rpx dashed #E5E7EB;
}

.date-text {
  font-size: 26rpx;
  color: #9CA3AF;
}

.actions {
  display: flex;
  gap: 20rpx;
}

.action-btn {
  font-size: 26rpx;
  padding: 0 32rpx;
  height: 60rpx;
  line-height: 60rpx;
  border-radius: 4rpx;
  background: #F3F4F6;
  color: #4B5563;
  margin: 0;
}

.action-btn::after {
  display: none;
}

.action-btn.primary {
  background: #2563EB;
  color: #FFFFFF;
}

.action-btn.danger {
  background: #FFFFFF;
  color: #DC2626;
  border: 2rpx solid #DC2626;
}

.loading-more {
  text-align: center;
  font-size: 26rpx;
  color: #9CA3AF;
  padding: 20rpx 0;
}

/* 底部动作栏 */
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

.nav-item.active .nav-text {
  color: #2563EB;
  font-weight: 600;
}

.nav-text {
  font-size: 30rpx;
  color: #4B5563;
  font-weight: 500;
}
</style>
