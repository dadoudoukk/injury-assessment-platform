<template>
  <view class="submit-bar" :class="{ 'submit-bar--fixed': fixed }">
    <button
      class="submit-bar__btn"
      :class="{ 'submit-bar__btn--disabled': disabled }"
      :loading="loading"
      :disabled="disabled || loading"
      @click="$emit('submit')"
    >
      {{ text }}
    </button>
    <text v-if="hint" class="submit-bar__hint">{{ hint }}</text>
  </view>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    text?: string
    hint?: string
    loading?: boolean
    disabled?: boolean
    fixed?: boolean
  }>(),
  {
    text: '提交',
    loading: false,
    disabled: false,
    fixed: false,
  },
)

defineEmits<{
  submit: []
}>()
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';
@import '@/styles/mixins.scss';

.submit-bar {
  padding: $space-lg 0;
}

.submit-bar--fixed {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  padding: $space-md $space-xl calc($space-md + env(safe-area-inset-bottom));
  background-color: $color-card-bg;
  border-top: 2rpx solid $color-border;
  z-index: 100;
}

.submit-bar__btn {
  @include primary-button;
  width: 100%;
}

.submit-bar__btn--disabled {
  opacity: 0.5;
}

.submit-bar__hint {
  display: block;
  margin-top: $space-sm;
  text-align: center;
  font-size: $font-size-caption;
  color: $color-hint;
}
</style>
