<template>
  <view class="loading-state" :class="{ 'loading-state--fullscreen': fullscreen }">
    <wd-loading v-if="useWot" :color="color" />
    <view v-else class="loading-state__spinner" />
    <text v-if="text" class="loading-state__text">{{ text }}</text>
  </view>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    text?: string
    fullscreen?: boolean
    useWot?: boolean
    color?: string
  }>(),
  {
    text: '加载中...',
    fullscreen: false,
    useWot: true,
    color: '#2563EB',
  },
)
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: $space-3xl;
  gap: $space-md;
}

.loading-state--fullscreen {
  min-height: 60vh;
}

.loading-state__spinner {
  width: 48rpx;
  height: 48rpx;
  border: 4rpx solid $color-border;
  border-top-color: $color-primary;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.loading-state__text {
  font-size: $font-size-body;
  color: $color-hint;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
