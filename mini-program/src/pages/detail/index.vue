<template>
  <LoadingState v-if="detailLoading && !caseDetail" fullscreen />
  <EmptyState
    v-else-if="loadError"
    variant="error"
    :title="loadError === 'not_found' ? EMPTY_STATE_COPY.detailNotFoundTitle : undefined"
    :description="loadError === 'not_found' ? EMPTY_STATE_COPY.detailNotFoundDesc : undefined"
    :action-text="FEEDBACK_COPY.retry"
    @action="retryLoad"
  />
  <view v-else-if="caseDetail" class="detail-page">
    <view class="detail-page__header">
      <StatusTag :status="caseDetail.status" variant="solid" class="detail-page__status" />
      <text class="detail-page__report-no">报案号：{{ caseDetail.reportNumber }}</text>
    </view>

    <FormSection title="案件基础信息">
      <view class="detail-page__info-list">
        <view
          v-if="caseStatus === CASE_STATUS.REWORK && caseDetail.reworkRemark"
          class="detail-page__info-row"
        >
          <text class="detail-page__label detail-page__label--danger">打回原因</text>
          <text class="detail-page__value detail-page__value--danger">{{ caseDetail.reworkRemark }}</text>
        </view>
        <view class="detail-page__info-row">
          <text class="detail-page__label">伤者姓名</text>
          <text class="detail-page__value">{{ caseDetail.victimName }}</text>
        </view>
        <view class="detail-page__info-row">
          <text class="detail-page__label">联系电话</text>
          <text
            :class="['detail-page__value', canCallPhone ? 'detail-page__value--link' : '']"
            @click="canCallPhone && callPhone(caseDetail.victimPhone)"
          >
            {{ caseDetail.victimPhone }}
          </text>
        </view>
        <view class="detail-page__info-row">
          <text class="detail-page__label">出险地点</text>
          <text class="detail-page__value">
            {{ caseDetail.province }}{{ caseDetail.city }}{{ caseDetail.district }}
          </text>
        </view>
        <view class="detail-page__info-row">
          <text class="detail-page__label">报案日期</text>
          <text class="detail-page__value">{{ caseDetail.reportDate }}</text>
        </view>
        <view class="detail-page__info-row">
          <text class="detail-page__label">保险公司</text>
          <text class="detail-page__value">{{ caseDetail.insuranceCompany }}</text>
        </view>
      </view>
    </FormSection>

    <FormSection v-if="!isPatientMode" title="鉴定流转">
      <template v-if="caseStatus === CASE_STATUS.PENDING_CONFIRM">
        <text class="detail-page__hint">请核实案件概况后确认受理，受理后可查看完整伤者信息并进行视频取证。</text>
        <SubmitBar text="确认受理" :loading="submitLoading" @submit="handleAccept" />
      </template>

      <template v-if="caseStatus === CASE_STATUS.ACCEPTED || caseStatus === CASE_STATUS.REWORK">
        <view class="detail-page__upload-group">
          <text class="detail-page__form-label detail-page__form-label--required">鉴定取证视频</text>
          <text class="detail-page__upload-hint">可多次上传，最多 {{ MAX_VIDEO_COUNT }} 个</text>
          <view class="detail-page__video-list">
            <view
              v-for="(file, index) in form.appraisalVideos"
              :key="file.id"
              class="detail-page__video-cell"
              @click="previewVideo(file)"
            >
              <image
                v-if="file.thumb && !file.thumbBroken"
                class="detail-page__video-thumb"
                :src="file.thumb"
                mode="aspectFill"
                @error="onThumbError(file)"
              />
              <view v-else class="detail-page__video-thumb detail-page__video-thumb--placeholder" />
              <view class="detail-page__play-overlay">
                <text class="detail-page__play-icon">▶</text>
              </view>
              <view class="detail-page__delete-btn" @click.stop="removeVideo(index)">✕</view>
            </view>
            <view
              v-if="form.appraisalVideos.length < MAX_VIDEO_COUNT"
              class="detail-page__upload-btn"
              @click="chooseVideo"
            >
              <text class="detail-page__add-icon">+</text>
              <text class="detail-page__add-text">上传视频</text>
            </view>
          </view>
        </view>
        <SubmitBar text="提交鉴定视频" :loading="submitLoading" @submit="submitVideos" />
      </template>

      <template v-if="caseStatus === CASE_STATUS.APPRAISING">
        <view v-if="caseDetail.appraisalVideos?.length" class="detail-page__upload-group">
          <text class="detail-page__form-label">已提交视频（只读）</text>
          <view class="detail-page__readonly-list">
            <text
              v-for="(v, i) in caseDetail.appraisalVideos"
              :key="i"
              class="detail-page__readonly-item"
            >
              {{ v.name || '视频' + (i + 1) }}
            </text>
          </view>
        </view>
        <FormField
          v-model="form.documentNumber"
          label="鉴定文书编号"
          placeholder="请输入鉴定文书编号"
          :maxlength="50"
          required
        />
        <view class="detail-page__upload-group">
          <text class="detail-page__form-label detail-page__form-label--required">电子证书</text>
          <text class="detail-page__upload-hint">仅支持 PDF 格式，只能上传 1 个</text>
          <view class="detail-page__cert-area">
            <view v-if="form.electronicCertificate" class="detail-page__cert-file">
              <text class="detail-page__cert-name" @click="previewCertificate">
                {{ form.electronicCertificate.name || '电子证书.pdf' }}
              </text>
              <view class="detail-page__delete-btn detail-page__cert-delete" @click="removeCertificate">
                ✕
              </view>
            </view>
            <view v-else class="detail-page__upload-btn detail-page__cert-upload" @click="chooseCertificate">
              <text class="detail-page__add-icon">+</text>
              <text class="detail-page__add-text">上传 PDF</text>
            </view>
          </view>
        </view>
        <SubmitBar text="提交文书编号" :loading="submitLoading" @submit="submitDocumentNumber" />
      </template>

      <template v-if="caseStatus === CASE_STATUS.COMPLETED">
        <view class="detail-page__info-list">
          <view v-if="caseDetail.documentNumber" class="detail-page__info-row">
            <text class="detail-page__label">文书编号</text>
            <text class="detail-page__value detail-page__value--highlight">{{ caseDetail.documentNumber }}</text>
          </view>
          <view v-if="caseDetail.electronicCertificate?.url" class="detail-page__info-row">
            <text class="detail-page__label">电子证书</text>
            <text class="detail-page__value detail-page__value--link" @click="previewServerCertificate">
              {{ caseDetail.electronicCertificate.name || '查看电子证书' }}
            </text>
          </view>
          <view v-if="caseDetail.appraisalVideos?.length" class="detail-page__info-row detail-page__info-row--col">
            <text class="detail-page__label">鉴定视频</text>
            <view class="detail-page__readonly-list">
              <text
                v-for="(v, i) in caseDetail.appraisalVideos"
                :key="i"
                class="detail-page__readonly-item"
              >
                {{ v.name || '视频' + (i + 1) }}
              </text>
            </view>
          </view>
          <view v-if="caseDetail.appraisalAmount" class="detail-page__info-row">
            <text class="detail-page__label">理赔金额（历史）</text>
            <text class="detail-page__value">¥{{ caseDetail.appraisalAmount }}</text>
          </view>
          <view v-if="caseDetail.appraisalConclusion" class="detail-page__info-row detail-page__info-row--col">
            <text class="detail-page__label">鉴定结论（历史）</text>
            <view class="detail-page__readonly-box">{{ caseDetail.appraisalConclusion }}</view>
          </view>
        </view>
      </template>
    </FormSection>
  </view>
</template>

<script setup lang="ts">
import { onLoad, onShow } from '@dcloudio/uni-app'
import StatusTag from '@/components/common/StatusTag.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import FormField from '@/components/form/FormField.vue'
import FormSection from '@/components/form/FormSection.vue'
import SubmitBar from '@/components/form/SubmitBar.vue'
import { useCaseDetail } from '@/composables/useCaseDetail'
import { CASE_STATUS } from '@/constants/status'
import { EMPTY_STATE_COPY, FEEDBACK_COPY } from '@/constants/copy'
import { trackPageView } from '@/utils/logger'

const {
  MAX_VIDEO_COUNT,
  caseDetail,
  form,
  submitLoading,
  detailLoading,
  loadError,
  isPatientMode,
  caseStatus,
  canCallPhone,
  initFromOptions,
  handleShow,
  fetchDetail,
  callPhone,
  onThumbError,
  previewVideo,
  chooseVideo,
  removeVideo,
  chooseCertificate,
  removeCertificate,
  previewCertificate,
  previewServerCertificate,
  handleAccept,
  submitVideos,
  submitDocumentNumber,
} = useCaseDetail()

const retryLoad = () => {
  fetchDetail()
}

onLoad(async (options) => {
  trackPageView('detail/index', { id: options?.id })
  await initFromOptions(options?.id)
})

onShow(() => {
  handleShow()
})
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';
@import '@/styles/mixins.scss';

.detail-page {
  @include page-background;
  min-height: 100vh;
  padding-bottom: $space-3xl;

  :deep(.form-section) {
    padding: 0 $space-xl;
  }
}

.detail-page__header {
  background-color: $color-card-bg;
  padding: $space-2xl $space-xl;
  border-bottom: 2rpx solid $color-border;
}

.detail-page__status :deep(.status-tag__text) {
  font-size: 48rpx;
  font-weight: 600;
}

.detail-page__report-no {
  display: block;
  margin-top: $space-sm;
  font-size: $font-size-body;
  color: $color-secondary;
  font-family: consolas, monospace;
}

.detail-page__info-list {
  display: flex;
  flex-direction: column;
}

.detail-page__info-row {
  display: flex;
  justify-content: space-between;
  padding: $space-md 0;
  border-bottom: 2rpx solid #f3f4f6;

  &:last-child {
    border-bottom: none;
  }

  &--col {
    flex-direction: column;
    align-items: flex-start;
  }
}

.detail-page__label {
  color: $color-secondary;
  font-size: 30rpx;
  min-width: 160rpx;

  &--danger {
    color: $color-error;
  }
}

.detail-page__value {
  color: $color-title;
  font-size: 30rpx;
  text-align: right;
  flex: 1;

  &--link {
    color: $color-primary;
  }

  &--danger {
    color: $color-error;
    font-weight: 500;
  }

  &--highlight {
    font-size: 36rpx;
    font-weight: 600;
  }
}

.detail-page__hint {
  display: block;
  font-size: $font-size-body;
  color: $color-secondary;
  line-height: 1.6;
  margin-bottom: $space-lg;
}

.detail-page__upload-group {
  margin-bottom: $space-lg;
}

.detail-page__form-label {
  display: block;
  font-size: $font-size-body;
  color: $color-body;
  font-weight: 500;
  margin-bottom: $space-sm;

  &--required::after {
    content: ' *';
    color: $color-error;
  }
}

.detail-page__upload-hint {
  display: block;
  font-size: $font-size-caption;
  color: $color-hint;
  margin: -4rpx 0 $space-sm;
}

.detail-page__video-list {
  display: flex;
  flex-wrap: wrap;
  gap: $space-md;
}

.detail-page__video-cell,
.detail-page__upload-btn {
  position: relative;
  width: 160rpx;
  height: 160rpx;
  border-radius: $radius-sm;
  box-sizing: border-box;
  overflow: hidden;
  flex-shrink: 0;
}

.detail-page__video-cell {
  border: 2rpx solid $color-border;
  background: $color-page-bg;
}

.detail-page__video-thumb {
  width: 100%;
  height: 100%;

  &--placeholder {
    background: #d1d5db;
  }
}

.detail-page__play-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(17, 24, 39, 0.18);
  pointer-events: none;
}

.detail-page__play-icon {
  font-size: 44rpx;
  color: #ffffff;
  line-height: 1;
}

.detail-page__delete-btn {
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

.detail-page__upload-btn {
  background-color: $color-page-bg;
  border: 2rpx dashed #d1d5db;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.detail-page__add-icon {
  font-size: 40rpx;
  color: $color-hint;
  margin-bottom: 8rpx;
}

.detail-page__add-text {
  font-size: $font-size-caption;
  color: $color-secondary;
}

.detail-page__cert-area {
  width: 100%;
}

.detail-page__cert-upload {
  width: 100%;
  height: 120rpx;
}

.detail-page__cert-file {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $space-md $space-lg;
  background: $color-page-bg;
  border: 2rpx solid $color-border;
  border-radius: $radius-sm;
}

.detail-page__cert-name {
  flex: 1;
  font-size: $font-size-body;
  color: $color-primary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-page__cert-delete {
  position: static;
  flex-shrink: 0;
  margin-left: $space-sm;
}

.detail-page__readonly-list {
  width: 100%;
}

.detail-page__readonly-item {
  display: block;
  padding: $space-sm 0;
  font-size: $font-size-body;
  color: $color-body;
  border-bottom: 2rpx solid #f3f4f6;
}

.detail-page__readonly-box {
  background-color: $color-page-bg;
  padding: $space-lg;
  border: 2rpx solid $color-border;
  border-radius: $radius-sm;
  width: 100%;
  box-sizing: border-box;
  color: $color-body;
  font-size: $font-size-body;
  line-height: 1.6;
}
</style>
