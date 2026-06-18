<template>
  <view class="empty-state">
    <view class="empty-state__icon" :class="`empty-state__icon--${resolvedVariant}`">
      <text class="empty-state__icon-text">{{ resolvedIcon }}</text>
    </view>
    <text class="empty-state__title">{{ resolvedTitle }}</text>
    <text v-if="resolvedDescription" class="empty-state__desc">{{ resolvedDescription }}</text>
    <button
      v-if="actionText"
      class="empty-state__action"
      @click="$emit('action')"
    >
      {{ actionText }}
    </button>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { EMPTY_STATE_COPY } from '@/constants/copy'

export type EmptyStateVariant = 'default' | 'list' | 'search' | 'error'

const props = withDefaults(
  defineProps<{
    title?: string
    description?: string
    actionText?: string
    icon?: string
    variant?: EmptyStateVariant
  }>(),
  {
    variant: 'default',
  },
)

defineEmits<{
  action: []
}>()

const VARIANT_PRESETS: Record<
  EmptyStateVariant,
  { icon: string; title: string; description?: string }
> = {
  default: { icon: '📋', title: EMPTY_STATE_COPY.defaultTitle },
  list: { icon: '📋', title: EMPTY_STATE_COPY.defaultTitle },
  search: { icon: '🔍', title: EMPTY_STATE_COPY.agencyListTitle, description: EMPTY_STATE_COPY.agencyListDesc },
  error: {
    icon: '⚠️',
    title: EMPTY_STATE_COPY.loadErrorTitle,
    description: EMPTY_STATE_COPY.loadErrorDesc,
  },
}

const resolvedVariant = computed(() => props.variant)
const preset = computed(() => VARIANT_PRESETS[props.variant])
const resolvedIcon = computed(() => props.icon ?? preset.value.icon)
const resolvedTitle = computed(() => props.title ?? preset.value.title)
const resolvedDescription = computed(() => props.description ?? preset.value.description)
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';
@import '@/styles/mixins.scss';

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 160rpx $space-xl $space-2xl;
}

.empty-state__icon {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background-color: $color-page-bg;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: $space-lg;

  &--error {
    background-color: #fef2f2;
  }
}

.empty-state__icon-text {
  font-size: 56rpx;
  line-height: 1;
}

.empty-state__title {
  font-size: 32rpx;
  font-weight: 500;
  color: $color-body;
  margin-bottom: $space-sm;
}

.empty-state__desc {
  font-size: $font-size-body;
  color: $color-secondary;
  text-align: center;
  line-height: 1.6;
  margin-bottom: $space-3xl;
  max-width: 560rpx;
}

.empty-state__action {
  @include primary-button;
  padding: 0 80rpx;
  height: 88rpx;
  line-height: 88rpx;
}
</style>
