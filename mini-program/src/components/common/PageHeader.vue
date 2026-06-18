<template>
  <view class="page-header" :class="{ 'page-header--compact': compact }">
    <view v-if="showBrandLine" class="page-header__brand-line" />
    <text class="page-header__title">{{ title }}</text>
    <text v-if="subtitle" class="page-header__subtitle">{{ subtitle }}</text>
  </view>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    title: string
    subtitle?: string
    showBrandLine?: boolean
    compact?: boolean
  }>(),
  {
    showBrandLine: true,
    compact: false,
  },
)
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';

.page-header {
  padding: $space-3xl $space-3xl $space-2xl;
  background-color: $color-card-bg;

  &--compact {
    padding: $space-xl;
  }
}

.page-header__brand-line {
  width: 40rpx;
  height: 6rpx;
  background-color: $color-primary;
  margin-bottom: $space-md;
}

.page-header__title {
  display: block;
  font-size: $font-size-page-title;
  font-weight: 600;
  color: $color-title;
  letter-spacing: 1rpx;
}

.page-header__subtitle {
  display: block;
  margin-top: $space-sm;
  font-size: $font-size-body;
  color: $color-secondary;
  line-height: 1.6;
}
</style>
