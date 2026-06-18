<template>
  <view class="case-stat-bar">
    <view
      v-for="item in items"
      :key="item.key"
      class="case-stat-bar__item"
      :class="{
        'case-stat-bar__item--active': activeKey === item.key,
        'case-stat-bar__item--static': item.clickable === false,
      }"
      @click="onItemClick(item)"
    >
      <text class="case-stat-bar__value">{{ item.value }}</text>
      <text class="case-stat-bar__label">{{ item.label }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
export interface CaseStatItem {
  key: string
  label: string
  value: number
  /** 为 false 时仅展示数字，不参与筛选联动 */
  clickable?: boolean
}

defineProps<{
  items: CaseStatItem[]
  activeKey?: string
}>()

const emit = defineEmits<{
  select: [key: string]
}>()

function onItemClick(item: CaseStatItem) {
  if (item.clickable === false) return
  emit('select', item.key)
}
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';
@import '@/styles/mixins.scss';

.case-stat-bar {
  @include card-base;
  display: flex;
  margin: $space-lg $space-xl;
  padding: $space-lg 0;
}

.case-stat-bar__item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $space-xs;
  position: relative;

  &:not(:last-child)::after {
    content: '';
    position: absolute;
    right: 0;
    top: 20%;
    height: 60%;
    width: 2rpx;
    background-color: $color-border;
  }
}

.case-stat-bar__value {
  font-size: 44rpx;
  font-weight: 600;
  color: $color-title;
  line-height: 1.2;
}

.case-stat-bar__label {
  font-size: $font-size-caption;
  color: $color-secondary;
}

.case-stat-bar__item--active .case-stat-bar__value {
  color: $color-primary;
}

.case-stat-bar__item--static {
  cursor: default;
}
</style>
