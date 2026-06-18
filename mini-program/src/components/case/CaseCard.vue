<template>
  <view class="case-card" hover-class="case-card--hover" @click="$emit('click')">
    <view class="case-card__header">
      <text class="case-card__report-no">{{ reportNoLabel }}</text>
      <StatusTag :status="item.status" />
    </view>

    <!-- 患者端：进度条 -->
    <view v-if="mode === 'patient'" class="case-card__progress">
      <view class="case-card__step" :class="{ 'case-card__step--active': true }">
        <view class="case-card__dot" />
        <text class="case-card__step-label">已报案</text>
      </view>
      <view
        class="case-card__line"
        :class="{ 'case-card__line--active': isPatientInAppraisalFlow(item.status) }"
      />
      <view
        class="case-card__step"
        :class="{
          'case-card__step--active':
            isPatientInAppraisalFlow(item.status) || isPatientRework(item.status),
        }"
      >
        <view
          class="case-card__dot"
          :class="{
            'case-card__dot--current':
              isPatientAppraisalActive(item.status) || isPatientRework(item.status),
          }"
        />
        <text class="case-card__step-label">{{ getPatientProgressMiddleLabel(item.status) }}</text>
      </view>
      <view
        class="case-card__line"
        :class="{ 'case-card__line--active': isPatientReportCompleted(item.status) }"
      />
      <view
        class="case-card__step"
        :class="{ 'case-card__step--active': isPatientReportCompleted(item.status) }"
      >
        <view
          class="case-card__dot"
          :class="{ 'case-card__dot--current': isPatientReportCompleted(item.status) }"
        />
        <text class="case-card__step-label">已出报告</text>
      </view>
    </view>

    <!-- 机构端：信息行 -->
    <view v-else class="case-card__body">
      <view
        v-if="normalizeStatus(item.status) === CASE_STATUS.REWORK && item.reworkRemark"
        class="case-card__row"
      >
        <text class="case-card__label case-card__label--danger">打回原因</text>
        <text class="case-card__value case-card__value--danger">{{ item.reworkRemark }}</text>
      </view>
      <view class="case-card__row">
        <text class="case-card__label">伤者姓名</text>
        <text class="case-card__value case-card__value--bold">{{ item.victimName }}</text>
      </view>
      <view class="case-card__row">
        <text class="case-card__label">联系电话</text>
        <text
          :class="[
            'case-card__value',
            normalizeStatus(item.status) !== CASE_STATUS.PENDING_CONFIRM ? 'case-card__value--link' : '',
          ]"
          @click.stop="onPhoneClick"
        >
          {{ item.victimPhone }}
        </text>
      </view>
      <view class="case-card__row">
        <text class="case-card__label">出险地点</text>
        <text class="case-card__value">{{ locationText }}</text>
      </view>
      <view v-if="accidentTypeLabel" class="case-card__row">
        <text class="case-card__label">事故类型</text>
        <text class="case-card__value">{{ accidentTypeLabel }}</text>
      </view>
      <view class="case-card__row">
        <text class="case-card__label">保险公司</text>
        <text class="case-card__value">{{ item.insuranceCompany }}</text>
      </view>
    </view>

    <!-- 患者端：机构/进度提示 -->
    <view v-if="mode === 'patient'" class="case-card__hint">
      <template v-if="shouldShowPatientAgencyInfo(item.status, item.agencyName)">
        <text class="case-card__hint-title">服务机构</text>
        <text class="case-card__hint-content">{{ item.agencyName }}</text>
      </template>
      <template v-else-if="isPatientMatching(item.status)">
        <text class="case-card__hint-title">进度提示</text>
        <text class="case-card__hint-content case-card__hint-content--muted">
          系统正在匹配机构，请耐心等待。
        </text>
      </template>
      <template v-else-if="isPatientRework(item.status)">
        <text class="case-card__hint-title">进度提示</text>
        <text class="case-card__hint-content case-card__hint-content--danger">
          案件已打回，请等待机构重新处理。
        </text>
      </template>
    </view>

    <!-- 机构端：底部操作区 -->
    <view v-if="mode === 'agency'" class="case-card__footer">
      <text class="case-card__date">{{ item.reportDate }}</text>
      <view class="case-card__actions" @click.stop>
        <button
          v-if="normalizeStatus(item.status) === CASE_STATUS.PENDING_CONFIRM"
          class="case-card__btn case-card__btn--primary"
          :loading="acceptLoading"
          @click="$emit('accept')"
        >
          确认受理
        </button>
        <button
          v-else-if="
            normalizeStatus(item.status) === CASE_STATUS.ACCEPTED ||
            normalizeStatus(item.status) === CASE_STATUS.REWORK
          "
          class="case-card__btn case-card__btn--primary"
          @click="$emit('appraise')"
        >
          去鉴定
        </button>
        <button v-else class="case-card__btn" @click="$emit('view')">查看卷宗</button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import StatusTag from '@/components/common/StatusTag.vue'
import {
  CASE_STATUS,
  getPatientProgressMiddleLabel,
  isPatientAppraisalActive,
  isPatientInAppraisalFlow,
  isPatientMatching,
  isPatientReportCompleted,
  isPatientRework,
  shouldShowPatientAgencyInfo,
} from '@/constants/status'
import type { CaseItem } from '@/types/case'
import { normalizeCaseStatus } from '@/utils/role'

const props = withDefaults(
  defineProps<{
    item: CaseItem
    mode?: 'agency' | 'patient'
    accidentTypeLabel?: string
    acceptLoading?: boolean
    reportNoPrefix?: string
  }>(),
  {
    mode: 'agency',
    acceptLoading: false,
    reportNoPrefix: '',
  },
)

defineEmits<{
  click: []
  accept: []
  appraise: []
  view: []
  call: [phone: string]
}>()

const normalizeStatus = normalizeCaseStatus

const reportNoLabel = computed(() => {
  const no = props.item.reportNumber
  return props.reportNoPrefix ? `${props.reportNoPrefix}${no}` : no
})

const locationText = computed(
  () => `${props.item.province || ''}${props.item.city || ''}${props.item.district || ''}`,
)

function onPhoneClick() {
  if (props.mode !== 'agency') return
  if (normalizeStatus(props.item.status) === CASE_STATUS.PENDING_CONFIRM) return
  if (!props.item.victimPhone || props.item.victimPhone.includes('*')) return
  uni.makePhoneCall({ phoneNumber: props.item.victimPhone })
}
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';
@import '@/styles/mixins.scss';

.case-card {
  @include card-base;
  margin-bottom: $space-xl;
}

.case-card--hover {
  background-color: #f9fafb;
  border-color: #d1d5db;
}

.case-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: $space-md;
  border-bottom: 2rpx solid $color-border;
  margin-bottom: $space-lg;
}

.case-card__report-no {
  font-size: 32rpx;
  font-weight: 600;
  color: $color-title;
  font-family: consolas, monospace;
}

.case-card__body {
  display: flex;
  flex-direction: column;
  gap: $space-sm;
}

.case-card__row {
  display: flex;
}

.case-card__label {
  width: 160rpx;
  font-size: $font-size-body;
  color: $color-secondary;
  flex-shrink: 0;
}

.case-card__label--danger {
  color: $color-error;
}

.case-card__value {
  flex: 1;
  font-size: $font-size-body;
  color: $color-title;
}

.case-card__value--bold {
  font-weight: 500;
}

.case-card__value--link {
  color: $color-primary;
}

.case-card__value--danger {
  color: $color-error;
  font-weight: 500;
}

.case-card__progress {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $space-xl;
}

.case-card__step {
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 2;
  background: $color-card-bg;
}

.case-card__dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background-color: $color-border;
  margin-bottom: $space-sm;
}

.case-card__step--active .case-card__dot {
  background-color: $color-title;
}

.case-card__dot--current {
  background-color: $color-primary !important;
  box-shadow: 0 0 0 4rpx rgba(37, 99, 235, 0.2);
}

.case-card__step-label {
  font-size: $font-size-caption;
  color: $color-hint;
}

.case-card__step--active .case-card__step-label {
  color: $color-title;
  font-weight: 500;
}

.case-card__line {
  flex: 1;
  height: 2rpx;
  background-color: $color-border;
  margin: 0 10rpx;
  margin-top: -36rpx;
}

.case-card__line--active {
  background-color: $color-title;
}

.case-card__hint {
  background-color: $color-page-bg;
  border: 2rpx solid $color-border;
  border-radius: $radius-sm;
  padding: $space-lg;
}

.case-card__hint-title {
  display: block;
  font-size: $font-size-caption;
  color: $color-secondary;
  margin-bottom: $space-xs;
}

.case-card__hint-content {
  display: block;
  font-size: 30rpx;
  font-weight: 500;
  color: $color-title;
}

.case-card__hint-content--muted {
  color: $color-secondary;
  font-weight: 400;
}

.case-card__hint-content--danger {
  color: $color-error;
}

.case-card__footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: $space-lg;
  padding-top: $space-md;
  border-top: 2rpx dashed $color-border;
}

.case-card__date {
  font-size: $font-size-caption;
  color: $color-hint;
}

.case-card__actions {
  display: flex;
  gap: $space-sm;
}

.case-card__btn {
  font-size: $font-size-caption;
  padding: 0 32rpx;
  height: 60rpx;
  line-height: 60rpx;
  border-radius: $radius-sm;
  background: #f3f4f6;
  color: #4b5563;
  margin: 0;

  &::after {
    display: none;
  }
}

.case-card__btn--primary {
  background: $color-primary;
  color: #ffffff;
}
</style>
