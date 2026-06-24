<template>
  <view class="batch-history">
    <view
      v-for="batch in sortedBatches"
      :key="batch.id"
      class="batch-history__item"
    >
      <view class="batch-history__header">
        <text class="batch-history__title">第 {{ batch.submitBatch }} 次提交</text>
        <StatusTag
          :label="getAuditStatusLabel(batch.status)"
          :color="getAuditStatusColor(batch.status)"
        />
      </view>

      <text v-if="batch.createdAt" class="batch-history__time">
        提交时间：{{ batch.createdAt }}
      </text>

      <text
        v-if="batch.status === AUDIT_STATUS.REJECTED && batch.auditRemark"
        class="batch-history__remark"
      >
        驳回原因：{{ batch.auditRemark }}
      </text>

      <view v-if="getBatchPolicyImages(batch).length" class="batch-history__group">
        <text class="batch-history__group-title">保单图片</text>
        <ImageThumbGrid :files="getBatchPolicyImages(batch)" readonly />
      </view>

      <view v-if="getBatchAccidentImages(batch).length" class="batch-history__group">
        <text class="batch-history__group-title">事故认定书</text>
        <ImageThumbGrid :files="getBatchAccidentImages(batch)" readonly />
      </view>

      <view
        v-if="!getBatchPolicyImages(batch).length && !getBatchAccidentImages(batch).length && legacyAttachments(batch).length"
        class="batch-history__group"
      >
        <text class="batch-history__group-title">附件</text>
        <view
          v-for="(file, index) in legacyAttachments(batch)"
          :key="`${batch.id}-legacy-${index}`"
          class="batch-history__attachment"
          @click="openAttachment(file)"
        >
          <text class="batch-history__attachment-name">
            {{ file.name || `附件 ${index + 1}` }}
          </text>
        </view>
      </view>

      <text
        v-if="!hasBatchMaterials(batch)"
        class="batch-history__empty"
      >
        本批次未上传材料
      </text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import StatusTag from '@/components/common/StatusTag.vue'
import ImageThumbGrid from '@/components/upload/ImageThumbGrid.vue'
import { AUDIT_STATUS, getAuditStatusColor, getAuditStatusLabel } from '@/constants/status'
import type { ApplicationBatchHistory } from '@/types/case'
import {
  extractBatchAccidentImages,
  extractBatchAttachments,
  extractBatchPolicyImages,
  openAttachment,
} from '@/utils/attachment'

const props = defineProps<{
  batches?: ApplicationBatchHistory[]
}>()

const sortedBatches = computed(() =>
  [...(props.batches || [])].sort((a, b) => b.submitBatch - a.submitBatch),
)

function getBatchPolicyImages(batch: ApplicationBatchHistory) {
  return extractBatchPolicyImages(batch)
}

function getBatchAccidentImages(batch: ApplicationBatchHistory) {
  return extractBatchAccidentImages(batch)
}

function legacyAttachments(batch: ApplicationBatchHistory) {
  return extractBatchAttachments(batch).filter((item) => !item.category)
}

function hasBatchMaterials(batch: ApplicationBatchHistory) {
  return (
    getBatchPolicyImages(batch).length > 0 ||
    getBatchAccidentImages(batch).length > 0 ||
    legacyAttachments(batch).length > 0
  )
}
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';

.batch-history {
  display: flex;
  flex-direction: column;
  gap: $space-lg;
}

.batch-history__item {
  padding: $space-lg;
  background-color: $color-page-bg;
  border: 2rpx solid $color-border;
  border-radius: $radius-sm;
}

.batch-history__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $space-sm;
}

.batch-history__title {
  font-size: $font-size-body;
  font-weight: 600;
  color: $color-title;
}

.batch-history__time {
  display: block;
  font-size: $font-size-caption;
  color: $color-hint;
  margin-bottom: $space-sm;
}

.batch-history__remark {
  display: block;
  font-size: $font-size-caption;
  color: $color-error;
  line-height: 1.5;
  margin-bottom: $space-sm;
}

.batch-history__group {
  margin-top: $space-sm;
}

.batch-history__group-title {
  display: block;
  font-size: $font-size-caption;
  color: $color-secondary;
  margin-bottom: $space-xs;
}

.batch-history__attachment {
  padding: $space-sm $space-md;
  background-color: $color-card-bg;
  border-radius: $radius-sm;
  margin-bottom: $space-xs;
}

.batch-history__attachment-name {
  font-size: $font-size-body;
  color: $color-primary;
}

.batch-history__empty {
  font-size: $font-size-caption;
  color: $color-hint;
}
</style>
