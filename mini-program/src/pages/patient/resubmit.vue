<template>
  <view class="resubmit-page">
    <PageHeader
      :title="APPLICATION_COPY.resubmitTitle"
      :subtitle="APPLICATION_COPY.resubmitSubtitle"
    />

    <LoadingState v-if="pageLoading" fullscreen />

    <view v-else-if="detail" class="resubmit-page__body">
      <FormSection
        :title="APPLICATION_COPY.lockedSection"
        :description="APPLICATION_COPY.lockedDesc"
      >
        <view class="resubmit-page__readonly-list">
          <view class="resubmit-page__readonly-row">
            <text class="resubmit-page__readonly-label">出险报案号</text>
            <text class="resubmit-page__readonly-value">{{ detail.reportNumber }}</text>
          </view>
          <view class="resubmit-page__readonly-row">
            <text class="resubmit-page__readonly-label">出险日期</text>
            <text class="resubmit-page__readonly-value">{{ detail.reportDate }}</text>
          </view>
          <view class="resubmit-page__readonly-row">
            <text class="resubmit-page__readonly-label">承保保险公司</text>
            <text class="resubmit-page__readonly-value">{{ detail.insuranceCompany }}</text>
          </view>
        </view>
      </FormSection>

      <FormSection
        v-if="detail.rejectRemark"
        :title="APPLICATION_COPY.rejectReason"
      >
        <text class="resubmit-page__reject-text">{{ detail.rejectRemark }}</text>
      </FormSection>

      <FormSection
        :title="APPLICATION_COPY.editableSection"
        :description="CASE_FORM_COPY.partyDesc"
      >
        <FormField
          v-model="form.victimName"
          label="伤者姓名"
          placeholder="请输入伤者真实姓名"
          required
          :error="fieldErrors.victimName"
        />
        <FormField
          v-model="form.victimPhone"
          label="联系电话"
          placeholder="请输入联系电话"
          input-type="number"
          required
          :error="fieldErrors.victimPhone"
        />
      </FormSection>

      <FormSection :title="CASE_FORM_COPY.accidentSection">
        <FormField label="出险地点" required custom :error="fieldErrors.province">
          <picker mode="region" @change="onRegionChange">
            <view class="picker-field">
              <text :class="form.province ? 'picker-field__value' : 'picker-field__placeholder'">
                {{ regionText }}
              </text>
              <view class="picker-field__arrow" />
            </view>
          </picker>
        </FormField>

        <FormField label="事故类型" required custom :error="fieldErrors.accidentType">
          <picker
            :range="accidentTypeOptions"
            range-key="dictLabel"
            @change="onAccidentChange"
          >
            <view class="picker-field">
              <text :class="form.accidentType ? 'picker-field__value' : 'picker-field__placeholder'">
                {{ getAccidentTypeLabel(form.accidentType) || '请选择事故类型' }}
              </text>
              <view class="picker-field__arrow" />
            </view>
          </picker>
        </FormField>

        <FormField label="伤情类型" required custom :error="fieldErrors.injuryType">
          <picker
            :range="injuryTypeOptions"
            range-key="dictLabel"
            @change="onInjuryChange"
          >
            <view class="picker-field">
              <text :class="form.injuryType ? 'picker-field__value' : 'picker-field__placeholder'">
                {{ getInjuryTypeLabel(form.injuryType) || '请选择伤情类型' }}
              </text>
              <view class="picker-field__arrow" />
            </view>
          </picker>
        </FormField>
      </FormSection>

      <FormSection
        :title="APPLICATION_COPY.attachmentSection"
        :description="APPLICATION_COPY.attachmentDesc"
      >
        <view v-if="detail.batchHistory?.length" class="resubmit-page__attachment-block">
          <text class="resubmit-page__attachment-title">{{ APPLICATION_COPY.attachmentHistory }}</text>
          <ApplicationBatchHistoryList :batches="detail.batchHistory" />
        </view>

        <view v-if="historicalPolicyImages.length" class="resubmit-page__attachment-block">
          <text class="resubmit-page__attachment-title">{{ APPLICATION_COPY.policyHistory }}</text>
          <ImageThumbGrid :files="historicalPolicyImages" readonly />
        </view>

        <view v-if="historicalAccidentImages.length" class="resubmit-page__attachment-block">
          <text class="resubmit-page__attachment-title">{{ APPLICATION_COPY.accidentHistory }}</text>
          <ImageThumbGrid :files="historicalAccidentImages" readonly />
        </view>

        <view class="resubmit-page__attachment-block">
          <text class="resubmit-page__attachment-title">{{ APPLICATION_COPY.policyNew }}</text>
          <ImageThumbGrid
            :files="newPolicyImages"
            :max-count="MAX_MATERIAL_COUNT"
            :add-text="APPLICATION_COPY.addPolicyImage"
            @add="addPolicyImage"
            @remove="removeNewPolicy"
          />
        </view>

        <view class="resubmit-page__attachment-block">
          <text class="resubmit-page__attachment-title">{{ APPLICATION_COPY.accidentNew }}</text>
          <ImageThumbGrid
            :files="newAccidentImages"
            :max-count="MAX_MATERIAL_COUNT"
            :add-text="APPLICATION_COPY.addAccidentImage"
            @add="addAccidentImage"
            @remove="removeNewAccident"
          />
        </view>
      </FormSection>
    </view>

    <view class="resubmit-page__spacer" />

    <SubmitBar
      v-if="detail"
      fixed
      :text="APPLICATION_COPY.resubmit"
      :hint="APPLICATION_COPY.resubmitHint"
      :loading="submitting"
      @submit="submitForm"
    />
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { fetchApplicationDetail, resubmitApplication } from '@/api/case'
import ApplicationBatchHistoryList from '@/components/case/ApplicationBatchHistoryList.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import ImageThumbGrid from '@/components/upload/ImageThumbGrid.vue'
import FormField from '@/components/form/FormField.vue'
import FormSection from '@/components/form/FormSection.vue'
import SubmitBar from '@/components/form/SubmitBar.vue'
import { useCaseDict } from '@/composables/useCaseDict'
import { useFileUpload, type UploadedFileItem } from '@/composables/useFileUpload'
import { APPLICATION_COPY, CASE_FORM_COPY, FEEDBACK_COPY } from '@/constants/copy'
import { APP_STATUS } from '@/constants/status'
import type { ApplicationDetail, ApplicationResubmitBody } from '@/types/case'
import { buildMaterialAttachments } from '@/utils/attachment'
import { showError, showSuccess } from '@/utils/feedback'
import { reportError, trackPageView } from '@/utils/logger'
import { validatePhone } from '@/utils/validators'

const applicationId = ref('')
const detail = ref<ApplicationDetail | null>(null)
const pageLoading = ref(false)
const submitting = ref(false)
const newPolicyImages = ref<UploadedFileItem[]>([])
const newAccidentImages = ref<UploadedFileItem[]>([])
const fieldErrors = reactive<Partial<Record<keyof ApplicationResubmitBody, string>>>({})

const MAX_MATERIAL_COUNT = 9

const form = reactive({
  victimName: '',
  victimPhone: '',
  province: '',
  city: '',
  district: '',
  accidentType: '',
  injuryType: '',
})

const { chooseAndUploadImage } = useFileUpload()
const {
  accidentTypeOptions,
  injuryTypeOptions,
  loadDicts,
  getAccidentTypeLabel,
  getInjuryTypeLabel,
} = useCaseDict()

const regionText = computed(() =>
  form.province ? `${form.province} ${form.city} ${form.district}` : '',
)

const historicalPolicyImages = computed(() => detail.value?.policyImages || [])
const historicalAccidentImages = computed(() => detail.value?.accidentDecisionImages || [])

function fillFormFromDetail(data: ApplicationDetail) {
  form.victimName = data.victimName
  form.victimPhone = data.victimPhone
  form.province = data.province
  form.city = data.city
  form.district = data.district
  form.accidentType = data.accidentType
  form.injuryType = data.injuryType
}

async function loadDetail() {
  if (!applicationId.value) return
  pageLoading.value = true
  try {
    const res = await fetchApplicationDetail(applicationId.value)
    if (!res) {
      showError('申请单不存在')
      setTimeout(() => uni.navigateBack(), 1500)
      return
    }
    if (res.appStatus !== APP_STATUS.REJECTED) {
      showError('当前申请不可补件')
      setTimeout(() => uni.navigateBack(), 1500)
      return
    }
    detail.value = res
    fillFormFromDetail(res)
  } catch (error) {
    reportError(error, { scope: 'resubmit_load', id: applicationId.value })
  } finally {
    pageLoading.value = false
  }
}

const onRegionChange = (e: { detail: { value: string[] } }) => {
  const [province, city, district] = e.detail.value
  form.province = province
  form.city = city
  form.district = district
  fieldErrors.province = ''
}

const onAccidentChange = (e: { detail: { value: number } }) => {
  form.accidentType = accidentTypeOptions.value[e.detail.value].dictValue
  fieldErrors.accidentType = ''
}

const onInjuryChange = (e: { detail: { value: number } }) => {
  form.injuryType = injuryTypeOptions.value[e.detail.value].dictValue
  fieldErrors.injuryType = ''
}

async function addPolicyImage() {
  if (newPolicyImages.value.length >= MAX_MATERIAL_COUNT) {
    showError(`保单图片最多 ${MAX_MATERIAL_COUNT} 张`)
    return
  }
  const item = await chooseAndUploadImage()
  if (item) {
    newPolicyImages.value.push({
      ...item,
      name: item.name || `保单图片${newPolicyImages.value.length + 1}`,
    })
  }
}

function removeNewPolicy(index: number) {
  newPolicyImages.value.splice(index, 1)
}

async function addAccidentImage() {
  if (newAccidentImages.value.length >= MAX_MATERIAL_COUNT) {
    showError(`事故认定书最多 ${MAX_MATERIAL_COUNT} 张`)
    return
  }
  const item = await chooseAndUploadImage()
  if (item) {
    newAccidentImages.value.push({
      ...item,
      name: item.name || `事故认定书${newAccidentImages.value.length + 1}`,
    })
  }
}

function removeNewAccident(index: number) {
  newAccidentImages.value.splice(index, 1)
}

function validateForm(): boolean {
  Object.keys(fieldErrors).forEach((key) => {
    delete fieldErrors[key as keyof ApplicationResubmitBody]
  })

  if (!form.victimName.trim()) {
    fieldErrors.victimName = '请输入伤者姓名'
    showError('请输入伤者姓名')
    return false
  }

  const phoneResult = validatePhone(form.victimPhone)
  if (!phoneResult.valid) {
    fieldErrors.victimPhone = phoneResult.message
    showError(phoneResult.message || FEEDBACK_COPY.validationRequired)
    return false
  }

  if (!form.province || !form.city || !form.district) {
    fieldErrors.province = '请选择出险地点'
    showError('请选择出险地点')
    return false
  }

  if (!form.accidentType) {
    fieldErrors.accidentType = '请选择事故类型'
    showError('请选择事故类型')
    return false
  }

  if (!form.injuryType) {
    fieldErrors.injuryType = '请选择伤情类型'
    showError('请选择伤情类型')
    return false
  }

  return true
}

async function submitForm() {
  if (!applicationId.value || !validateForm()) return

  submitting.value = true
  try {
    const policyImages = newPolicyImages.value.map(({ name, url, kind }) => ({
      name,
      url,
      kind: kind || 'image',
      category: 'policy' as const,
    }))
    const accidentDecisionImages = newAccidentImages.value.map(({ name, url, kind }) => ({
      name,
      url,
      kind: kind || 'image',
      category: 'accident_decision' as const,
    }))
    await resubmitApplication(applicationId.value, {
      victimName: form.victimName.trim(),
      victimPhone: form.victimPhone.trim(),
      province: form.province,
      city: form.city,
      district: form.district,
      accidentType: form.accidentType,
      injuryType: form.injuryType,
      policyImages,
      accidentDecisionImages,
      attachments: buildMaterialAttachments(policyImages, accidentDecisionImages),
    })
    showSuccess(FEEDBACK_COPY.resubmitSuccess)
    setTimeout(() => {
      uni.navigateBack()
      uni.$emit('refreshList')
    }, 1500)
  } catch (error) {
    reportError(error, { scope: 'resubmit_submit', id: applicationId.value })
  } finally {
    submitting.value = false
  }
}

onLoad((options) => {
  trackPageView('patient/resubmit', { id: options?.id })
  loadDicts()
  if (options?.id) {
    applicationId.value = String(options.id)
    loadDetail()
  }
})
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';
@import '@/styles/mixins.scss';

.resubmit-page {
  @include page-background;
  min-height: 100vh;
}

.resubmit-page__body {
  padding: 0 $space-xl $space-md;
}

.resubmit-page__spacer {
  height: 200rpx;
}

.resubmit-page__readonly-list {
  display: flex;
  flex-direction: column;
  gap: $space-md;
}

.resubmit-page__readonly-row {
  display: flex;
}

.resubmit-page__readonly-label {
  width: 200rpx;
  font-size: $font-size-body;
  color: $color-secondary;
  flex-shrink: 0;
}

.resubmit-page__readonly-value {
  flex: 1;
  font-size: $font-size-body;
  color: $color-title;
  font-weight: 500;
}

.resubmit-page__reject-text {
  display: block;
  font-size: $font-size-body;
  color: $color-error;
  line-height: 1.6;
}

.resubmit-page__attachment-block {
  margin-bottom: $space-lg;
}

.resubmit-page__attachment-title {
  display: block;
  font-size: $font-size-caption;
  color: $color-secondary;
  margin-bottom: $space-sm;
}

picker {
  width: 100%;
}

.picker-field {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.picker-field__value {
  color: $color-title;
  font-size: $font-size-body;
}

.picker-field__placeholder {
  color: $color-hint;
  font-size: $font-size-body;
}

.picker-field__arrow {
  width: 16rpx;
  height: 16rpx;
  border-top: 4rpx solid $color-hint;
  border-right: 4rpx solid $color-hint;
  transform: rotate(45deg);
  flex-shrink: 0;
}
</style>
