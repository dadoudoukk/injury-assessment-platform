<template>
  <view class="form-field">
    <text class="form-field__label" :class="{ 'form-field__label--required': required }">
      {{ label }}
    </text>
    <text v-if="hint" class="form-field__hint">{{ hint }}</text>

    <!-- 自定义控件（picker 等） -->
    <view v-if="custom" class="form-field__control">
      <slot />
    </view>

    <!-- 普通输入框：显式 v-if 避免 v-else 编译异常，本地值先行更新避免输入被父级旧值回刷 -->
    <input
      v-if="!custom"
      :value="innerValue"
      class="form-field__input"
      :class="{ 'form-field__input--error': !!error }"
      :type="inputType"
      :password="password"
      :placeholder="placeholder"
      :maxlength="maxlength"
      :adjust-position="true"
      :hold-keyboard="true"
      placeholder-class="form-field__placeholder"
      @input="onInput"
    />

    <text v-if="error" class="form-field__error">{{ error }}</text>
  </view>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue?: string
    label: string
    placeholder?: string
    required?: boolean
    hint?: string
    error?: string
    inputType?: string
    password?: boolean
    maxlength?: number
    custom?: boolean
  }>(),
  {
    inputType: 'text',
    password: false,
    maxlength: 140,
    custom: false,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const innerValue = ref(props.modelValue ?? '')

watch(
  () => props.modelValue,
  (value) => {
    const next = value ?? ''
    if (next !== innerValue.value) {
      innerValue.value = next
    }
  },
)

function onInput(event: InputEvent) {
  const next = (event as InputEvent & { detail: { value: string } }).detail.value
  innerValue.value = next
  emit('update:modelValue', next)
  return next
}
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
