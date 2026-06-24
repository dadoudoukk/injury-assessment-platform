<template>
  <view class="application-card" hover-class="application-card--hover" @click="$emit('click')">
    <view class="application-card__header">
      <text class="application-card__report-no">报案号：{{ item.reportNumber }}</text>
      <StatusTag
        :label="getAppStatusLabel(item.appStatus)"
        :color="getAppStatusColor(item.appStatus)"
      />
    </view>

    <view class="application-card__body">
      <view class="application-card__row">
        <text class="application-card__label">伤者姓名</text>
        <text class="application-card__value">{{ item.victimName }}</text>
      </view>
      <view class="application-card__row">
        <text class="application-card__label">出险日期</text>
        <text class="application-card__value">{{ item.reportDate }}</text>
      </view>
      <view class="application-card__row">
        <text class="application-card__label">保险公司</text>
        <text class="application-card__value">{{ item.insuranceCompany }}</text>
      </view>
    </view>

    <view class="application-card__hint">
      <template v-if="item.appStatus === APP_STATUS.PENDING_AUDIT">
        <text class="application-card__hint-title">进度提示</text>
        <text class="application-card__hint-content application-card__hint-content--muted">
          {{ APPLICATION_COPY.pendingHint }}
        </text>
      </template>
      <template v-else-if="item.appStatus === APP_STATUS.REJECTED">
        <text class="application-card__hint-title">{{ APPLICATION_COPY.rejectReason }}</text>
        <text class="application-card__hint-content application-card__hint-content--danger">
          {{ item.rejectRemark || '平台未填写具体原因，请联系客服' }}
        </text>
      </template>
    </view>
  </view>
</template>

<script setup lang="ts">
import StatusTag from '@/components/common/StatusTag.vue'
import { APPLICATION_COPY } from '@/constants/copy'
import { APP_STATUS, getAppStatusColor, getAppStatusLabel } from '@/constants/status'
import type { ApplicationItem } from '@/types/case'

defineProps<{
  item: ApplicationItem
}>()

defineEmits<{
  click: []
}>()
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';
@import '@/styles/mixins.scss';

.application-card {
  @include card-base;
  margin-bottom: $space-xl;
}

.application-card--hover {
  background-color: #f9fafb;
  border-color: #d1d5db;
}

.application-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: $space-md;
  border-bottom: 2rpx solid $color-border;
  margin-bottom: $space-lg;
}

.application-card__report-no {
  font-size: 32rpx;
  font-weight: 600;
  color: $color-title;
  font-family: consolas, monospace;
}

.application-card__body {
  display: flex;
  flex-direction: column;
  gap: $space-sm;
  margin-bottom: $space-lg;
}

.application-card__row {
  display: flex;
}

.application-card__label {
  width: 160rpx;
  font-size: $font-size-body;
  color: $color-secondary;
  flex-shrink: 0;
}

.application-card__value {
  flex: 1;
  font-size: $font-size-body;
  color: $color-title;
}

.application-card__hint {
  background-color: $color-page-bg;
  border: 2rpx solid $color-border;
  border-radius: $radius-sm;
  padding: $space-lg;
}

.application-card__hint-title {
  display: block;
  font-size: $font-size-caption;
  color: $color-secondary;
  margin-bottom: $space-xs;
}

.application-card__hint-content {
  display: block;
  font-size: 30rpx;
  font-weight: 500;
  color: $color-title;
}

.application-card__hint-content--muted {
  color: $color-secondary;
  font-weight: 400;
}

.application-card__hint-content--danger {
  color: $color-error;
}
</style>
