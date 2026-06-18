<template>
  <view class="bottom-nav">
    <view
      v-for="item in items"
      :key="item.key"
      :class="[
        'bottom-nav__item',
        `bottom-nav__item--${item.variant || 'default'}`,
        { 'bottom-nav__item--active': item.active },
      ]"
      @click="emit('select', item.key)"
    >
      <text class="bottom-nav__text">{{ item.label }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
export interface BottomNavItem {
  key: string
  label: string
  active?: boolean
  variant?: 'default' | 'primary' | 'danger'
}

defineProps<{
  items: BottomNavItem[]
}>()

const emit = defineEmits<{
  select: [key: string]
}>()
</script>

<style scoped lang="scss">
@use '@/styles/tokens.scss' as *;

.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 110rpx;
  padding-bottom: env(safe-area-inset-bottom);
  background-color: $color-card-bg;
  border-top: 2rpx solid $color-border;
  display: flex;
  z-index: 100;
}

.bottom-nav__item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;

  &:active {
    opacity: 0.85;
  }
}

.bottom-nav__text {
  font-size: 30rpx;
  color: #4b5563;
  font-weight: 500;
}

.bottom-nav__item--active .bottom-nav__text {
  color: $color-primary;
  font-weight: 600;
}

.bottom-nav__item--primary {
  background-color: $color-primary;

  .bottom-nav__text {
    color: #ffffff;
  }

  &:active {
    background-color: $color-primary-dark;
  }
}

.bottom-nav__item--danger .bottom-nav__text {
  color: #ef4444;
}
</style>
