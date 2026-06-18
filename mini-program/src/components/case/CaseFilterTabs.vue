<template>
  <scroll-view class="case-filter-tabs" scroll-x :show-scrollbar="false">
    <view class="case-filter-tabs__inner">
      <view
        v-for="(tab, index) in tabs"
        :key="tab.key ?? index"
        :class="['case-filter-tabs__item', { 'case-filter-tabs__item--active': currentIndex === index }]"
        @click="$emit('change', index)"
      >
        <text class="case-filter-tabs__text">{{ tab.name }}</text>
        <view v-if="currentIndex === index" class="case-filter-tabs__line" />
      </view>
    </view>
  </scroll-view>
</template>

<script setup lang="ts">
export interface CaseFilterTab {
  name: string
  key?: string | number
  value?: unknown
}

defineProps<{
  tabs: CaseFilterTab[]
  currentIndex: number
}>()

defineEmits<{
  change: [index: number]
}>()
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';

.case-filter-tabs {
  background-color: $color-card-bg;
  border-bottom: 2rpx solid $color-border;
  position: sticky;
  top: 0;
  z-index: 100;
  white-space: nowrap;
}

.case-filter-tabs__inner {
  display: inline-flex;
  min-width: 100%;
}

.case-filter-tabs__item {
  flex-shrink: 0;
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 96rpx;
  padding: 0 28rpx;
  position: relative;
}

.case-filter-tabs__text {
  font-size: 30rpx;
  color: $color-secondary;
  transition: color 0.2s;
}

.case-filter-tabs__item--active .case-filter-tabs__text {
  color: $color-title;
  font-weight: 600;
}

.case-filter-tabs__line {
  position: absolute;
  bottom: 0;
  left: 16rpx;
  right: 16rpx;
  height: 4rpx;
  background-color: $color-primary;
  border-radius: 2rpx;
}
</style>
