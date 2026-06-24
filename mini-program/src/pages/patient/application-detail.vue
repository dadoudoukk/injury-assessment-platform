<template>
  <LoadingState v-if="loading && !detail" fullscreen />
  <EmptyState
    v-else-if="loadError"
    variant="error"
    :title="loadError === 'not_found' ? EMPTY_STATE_COPY.applicationNotFoundTitle : undefined"
    :description="loadError === 'not_found' ? EMPTY_STATE_COPY.applicationNotFoundDesc : undefined"
    :action-text="FEEDBACK_COPY.retry"
    @action="loadDetail"
  />
  <view v-else-if="detail" class="application-detail-page">
    <view class="application-detail-page__header">
      <StatusTag
        :label="getAppStatusLabel(detail.appStatus)"
        :color="getAppStatusColor(detail.appStatus)"
        variant="solid"
      />
      <text class="application-detail-page__report-no">报案号：{{ detail.reportNumber }}</text>
    </view>

    <FormSection title="申请信息">
      <view class="application-detail-page__info-list">
        <view class="application-detail-page__info-row">
          <text class="application-detail-page__label">伤者姓名</text>
          <text class="application-detail-page__value">{{ detail.victimName }}</text>
        </view>
        <view class="application-detail-page__info-row">
          <text class="application-detail-page__label">联系电话</text>
          <text class="application-detail-page__value">{{ detail.victimPhone }}</text>
        </view>
        <view class="application-detail-page__info-row">
          <text class="application-detail-page__label">出险地点</text>
          <text class="application-detail-page__value">
            {{ detail.province }}{{ detail.city }}{{ detail.district }}
          </text>
        </view>
        <view class="application-detail-page__info-row">
          <text class="application-detail-page__label">出险日期</text>
          <text class="application-detail-page__value">{{ detail.reportDate }}</text>
        </view>
        <view class="application-detail-page__info-row">
          <text class="application-detail-page__label">保险公司</text>
          <text class="application-detail-page__value">{{ detail.insuranceCompany }}</text>
        </view>
      </view>
    </FormSection>

    <FormSection
      v-if="detail.appStatus === APP_STATUS.REJECTED && detail.rejectRemark"
      :title="APPLICATION_COPY.rejectReason"
    >
      <text class="application-detail-page__reject-text">{{ detail.rejectRemark }}</text>
    </FormSection>

    <FormSection
      v-if="detail.batchHistory?.length"
      :title="APPLICATION_COPY.attachmentSection"
      :description="APPLICATION_COPY.batchHistoryDesc"
    >
      <ApplicationBatchHistoryList :batches="detail.batchHistory" />
    </FormSection>

    <view class="application-detail-page__hint-box">
      <text class="application-detail-page__hint-text">{{ statusHint }}</text>
    </view>

    <view class="application-detail-page__actions">
      <button
        v-if="detail.appStatus === APP_STATUS.REJECTED"
        class="application-detail-page__btn application-detail-page__btn--primary"
        @click="goResubmit"
      >
        {{ APPLICATION_COPY.goResubmit }}
      </button>
      <button
        v-if="detail.appStatus === APP_STATUS.APPROVED && detail.caseId"
        class="application-detail-page__btn application-detail-page__btn--primary"
        @click="goCaseDetail"
      >
        {{ APPLICATION_COPY.viewCase }}
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { fetchApplicationDetail } from '@/api/case'
import ApplicationBatchHistoryList from '@/components/case/ApplicationBatchHistoryList.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import FormSection from '@/components/form/FormSection.vue'
import { APPLICATION_COPY, EMPTY_STATE_COPY, FEEDBACK_COPY } from '@/constants/copy'
import { ROUTES } from '@/constants/routes'
import { APP_STATUS, getAppStatusColor, getAppStatusLabel } from '@/constants/status'
import type { ApplicationDetail } from '@/types/case'
import { reportError, trackPageView } from '@/utils/logger'

const applicationId = ref('')
const detail = ref<ApplicationDetail | null>(null)
const loading = ref(false)
const loadError = ref('')

const statusHint = computed(() => {
  if (!detail.value) return ''
  if (detail.value.appStatus === APP_STATUS.PENDING_AUDIT) return APPLICATION_COPY.pendingHint
  if (detail.value.appStatus === APP_STATUS.REJECTED) return APPLICATION_COPY.rejectedHint
  return APPLICATION_COPY.approvedHint
})

async function loadDetail() {
  if (!applicationId.value) return
  loading.value = true
  loadError.value = ''
  try {
    const res = await fetchApplicationDetail(applicationId.value)
    if (res) {
      detail.value = res
    } else {
      detail.value = null
      loadError.value = 'not_found'
    }
  } catch (error) {
    loadError.value = 'fetch_failed'
    reportError(error, { scope: 'application_detail', id: applicationId.value })
  } finally {
    loading.value = false
  }
}

function goResubmit() {
  uni.navigateTo({ url: `${ROUTES.PATIENT_RESUBMIT}?id=${applicationId.value}` })
}

function goCaseDetail() {
  if (!detail.value?.caseId) return
  uni.navigateTo({ url: `${ROUTES.DETAIL}?id=${detail.value.caseId}` })
}

onLoad((options) => {
  trackPageView('patient/application-detail', { id: options?.id })
  if (options?.id) {
    applicationId.value = String(options.id)
    loadDetail()
  }
})
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';
@import '@/styles/mixins.scss';

.application-detail-page {
  @include page-background;
  min-height: 100vh;
  padding-bottom: $space-3xl;

  :deep(.form-section) {
    padding: 0 $space-xl;
  }
}

.application-detail-page__header {
  background-color: $color-card-bg;
  padding: $space-2xl $space-xl;
  border-bottom: 2rpx solid $color-border;
  margin-bottom: $space-xl;
}

.application-detail-page__report-no {
  display: block;
  margin-top: $space-md;
  font-size: 36rpx;
  font-weight: 600;
  color: $color-title;
  font-family: consolas, monospace;
}

.application-detail-page__info-list {
  display: flex;
  flex-direction: column;
  gap: $space-md;
}

.application-detail-page__info-row {
  display: flex;
}

.application-detail-page__label {
  width: 160rpx;
  font-size: $font-size-body;
  color: $color-secondary;
  flex-shrink: 0;
}

.application-detail-page__value {
  flex: 1;
  font-size: $font-size-body;
  color: $color-title;
}

.application-detail-page__reject-text {
  display: block;
  font-size: $font-size-body;
  color: $color-error;
  line-height: 1.6;
}

.application-detail-page__hint-box {
  margin: $space-xl;
  padding: $space-lg;
  background-color: $color-page-bg;
  border: 2rpx solid $color-border;
  border-radius: $radius-sm;
}

.application-detail-page__hint-text {
  font-size: $font-size-body;
  color: $color-secondary;
  line-height: 1.6;
}

.application-detail-page__actions {
  padding: 0 $space-xl;
}

.application-detail-page__btn {
  width: 100%;
  height: 88rpx;
  line-height: 88rpx;
  border-radius: $radius-md;
  font-size: $font-size-body;
  font-weight: 500;
  background: #f3f4f6;
  color: #4b5563;

  &::after {
    display: none;
  }
}

.application-detail-page__btn--primary {
  background: $color-primary;
  color: #ffffff;
}
</style>
