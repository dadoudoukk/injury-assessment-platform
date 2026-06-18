<template>
  <view
    class="load-more-footer"
    :class="{ 'load-more-footer--retry': !!error }"
    @click="onClick"
  >
    <wd-loading v-if="loading" size="32rpx" color="#9CA3AF" />
    <text
      class="load-more-footer__text"
      :class="{ 'load-more-footer__text--error': !!error }"
    >
      {{ text }}
    </text>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { LIST_COPY } from '@/constants/copy'

const props = withDefaults(
  defineProps<{
    loading?: boolean
    hasMore?: boolean
    error?: string
    noMoreText?: string
    loadMoreText?: string
    loadingText?: string
    retryText?: string
  }>(),
  {
    loading: false,
    hasMore: true,
    error: '',
    noMoreText: LIST_COPY.noMorePatient,
    loadMoreText: LIST_COPY.loadMore,
    loadingText: LIST_COPY.loading,
    retryText: LIST_COPY.loadMoreFailed,
  },
)

const emit = defineEmits<{
  retry: []
}>()

const text = computed(() => {
  if (props.error) return props.retryText
  if (props.loading) return props.loadingText
  if (props.hasMore) return props.loadMoreText
  return props.noMoreText
})

const onClick = () => {
  if (props.error && !props.loading) {
    emit('retry')
  }
}
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';

.load-more-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $space-sm;
  padding: $space-xl 0;
}

.load-more-footer--retry {
  cursor: pointer;
}

.load-more-footer__text {
  font-size: $font-size-caption;
  color: $color-hint;

  &--error {
    color: $color-error;
  }
}
</style>
