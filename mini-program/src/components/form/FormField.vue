<template>
  <view class="form-field">
    <text class="form-field__label" :class="{ 'form-field__label--required': required }">
      {{ label }}
    </text>
    <text v-if="hint" class="form-field__hint">{{ hint }}</text>

    <!-- 自定义控件（picker 等） -->
    <view v-if="$slots.default" class="form-field__control">
      <slot />
    </view>

    <!-- 普通输入框：组件内直接用 v-model，避免小程序端受控 input 不更新 -->
    <input
      v-else
      v-model="modelValue"
      class="form-field__input"
      :class="{ 'form-field__input--error': !!error }"
      :type="inputType"
      :password="password"
      :placeholder="placeholder"
      :maxlength="maxlength"
      :adjust-position="true"
      placeholder-class="form-field__placeholder"
    />

    <text v-if="error" class="form-field__error">{{ error }}</text>
  </view>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    label: string
    placeholder?: string
    required?: boolean
    hint?: string
    error?: string
    inputType?: string
    password?: boolean
    maxlength?: number
  }>(),
  {
    inputType: 'text',
    password: false,
  },
)

const modelValue = defineModel<string>({ default: '' })
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';
@import '@/styles/mixins.scss';

.form-field {
  margin-bottom: $space-lg;

  &:last-child {
    margin-bottom: 0;
  }
}

.form-field__label {
  display: block;
  font-size: $font-size-body;
  color: $color-body;
  font-weight: 500;
  margin-bottom: $space-sm;
}

.form-field__label--required::after {
  content: ' *';
  color: $color-error;
}

.form-field__hint {
  display: block;
  font-size: $font-size-caption;
  color: $color-hint;
  margin: -4rpx 0 $space-sm;
}

.form-field__control {
  @include input-container;
  display: flex;
  align-items: center;
}

.form-field__input {
  @include input-container;
  display: block;
  width: 100%;
  height: 80rpx;
  line-height: 80rpx;
}

.form-field__input--error {
  border-color: $color-error;
}

.form-field__placeholder {
  color: $color-hint;
}

.form-field__error {
  display: block;
  margin-top: $space-xs;
  font-size: $font-size-caption;
  color: $color-error;
}
</style>
