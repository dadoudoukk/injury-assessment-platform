<template>
  <view class="image-thumb-grid">
    <view
      v-for="(file, index) in files"
      :key="file.id || `${file.url}-${index}`"
      class="image-thumb-grid__cell"
      @click="onPreview(index)"
    >
      <image
        class="image-thumb-grid__thumb"
        :src="resolveSrc(file)"
        mode="aspectFill"
      />
      <view
        v-if="!readonly"
        class="image-thumb-grid__delete"
        @click.stop="emit('remove', index)"
      >
        ✕
      </view>
    </view>

    <view
      v-if="!readonly && files.length < maxCount"
      class="image-thumb-grid__add"
      @click="emit('add')"
    >
      <text class="image-thumb-grid__add-icon">+</text>
      <text class="image-thumb-grid__add-text">{{ addText }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { resolveFileUrl } from '@/utils/request'

export interface ImageThumbItem {
  id?: string
  url: string
  localPath?: string
}

const props = withDefaults(
  defineProps<{
    files: ImageThumbItem[]
    maxCount?: number
    readonly?: boolean
    addText?: string
  }>(),
  {
    maxCount: 9,
    readonly: false,
    addText: '添加图片',
  },
)

const emit = defineEmits<{
  add: []
  remove: [index: number]
}>()

function resolveSrc(file: ImageThumbItem): string {
  return file.localPath || resolveFileUrl(file.url)
}

function onPreview(index: number) {
  const urls = props.files.map(resolveSrc).filter(Boolean)
  if (!urls.length) return
  const current = resolveSrc(props.files[index])
  uni.previewImage({
    urls,
    current,
  })
}
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';

.image-thumb-grid {
  display: flex;
  flex-wrap: wrap;
  gap: $space-md;
}

.image-thumb-grid__cell,
.image-thumb-grid__add {
  position: relative;
  width: 160rpx;
  height: 160rpx;
  border-radius: $radius-sm;
  box-sizing: border-box;
  overflow: hidden;
  flex-shrink: 0;
}

.image-thumb-grid__cell {
  border: 2rpx solid $color-border;
  background: $color-page-bg;
}

.image-thumb-grid__thumb {
  width: 100%;
  height: 100%;
}

.image-thumb-grid__delete {
  position: absolute;
  top: 8rpx;
  right: 8rpx;
  width: 36rpx;
  height: 36rpx;
  background: rgba(255, 255, 255, 0.92);
  border: 2rpx solid $color-border;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22rpx;
  color: $color-secondary;
  z-index: 1;
}

.image-thumb-grid__add {
  background-color: $color-page-bg;
  border: 2rpx dashed #d1d5db;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.image-thumb-grid__add-icon {
  font-size: 40rpx;
  color: $color-hint;
  margin-bottom: 8rpx;
  line-height: 1;
}

.image-thumb-grid__add-text {
  font-size: $font-size-caption;
  color: $color-secondary;
  text-align: center;
  padding: 0 $space-xs;
}
</style>
