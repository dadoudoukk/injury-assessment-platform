<template>
  <view class="form-section">
    <view class="form-section__header">
      <text class="form-section__title">{{ title }}</text>
      <text v-if="description" class="form-section__desc">{{ description }}</text>
    </view>
    <view class="form-section__body">
      <slot />
    </view>
  </view>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  description?: string
}>()
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';
@import '@/styles/mixins.scss';

.form-section {
  margin-bottom: $space-3xl;
}

.form-section__header {
  margin-bottom: $space-lg;
}

.form-section__title {
  @include section-title;
  display: block;
  padding-left: $space-sm;
  border-left: 6rpx solid $color-title;
}

.form-section__desc {
  display: block;
  margin-top: $space-xs;
  padding-left: $space-sm + 6rpx;
  font-size: $font-size-caption;
  color: $color-secondary;
  line-height: 1.6;
}

.form-section__body {
  @include card-base;
  padding: $space-lg $space-xl;
}
</style>
