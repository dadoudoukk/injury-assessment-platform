<template>
  <view class="status-tag" :class="[`status-tag--${variant}`]" :style="tagStyle">
    <text class="status-tag__text">{{ displayLabel }}</text>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { getCaseStatusColor, getCaseStatusLabel } from '@/constants/status'

const props = withDefaults(
  defineProps<{
    status?: unknown
    label?: string
    color?: string
    variant?: 'solid' | 'outline' | 'text'
  }>(),
  {
    variant: 'text',
  },
)

const displayLabel = computed(() => {
  if (props.label) return props.label
  if (props.status != null) return getCaseStatusLabel(props.status)
  return '未知'
})

const resolvedColor = computed(() => {
  if (props.color) return props.color
  if (props.status != null) return getCaseStatusColor(props.status)
  return '#6B7280'
})

const tagStyle = computed(() => {
  const color = resolvedColor.value
  if (props.variant === 'solid') {
    return {
      backgroundColor: `${color}1A`,
      borderColor: `${color}33`,
      color,
    }
  }
  if (props.variant === 'outline') {
    return {
      backgroundColor: 'transparent',
      borderColor: `${color}66`,
      color,
    }
  }
  return { color }
})
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';

.status-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.status-tag--text {
  font-size: $font-size-caption;
  font-weight: 500;
}

.status-tag--solid,
.status-tag--outline {
  padding: 4rpx 16rpx;
  border-radius: $radius-sm;
  border-width: 2rpx;
  border-style: solid;
}

.status-tag__text {
  font-size: $font-size-caption;
  font-weight: 500;
  line-height: 1.4;
}
</style>
