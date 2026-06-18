<template>
  <view class="case-create-page">
    <PageHeader :title="CASE_FORM_COPY.title" :subtitle="CASE_FORM_COPY.subtitle" />

    <view class="case-create-page__body">
      <FormSection
        :title="CASE_FORM_COPY.partySection"
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

      <FormSection
        :title="CASE_FORM_COPY.accidentSection"
        :description="CASE_FORM_COPY.accidentDesc"
      >
        <FormField label="出险日期" required custom :error="fieldErrors.reportDate">
          <picker mode="date" :value="form.reportDate" @change="onDateChange">
            <view class="picker-field">
              <text :class="form.reportDate ? 'picker-field__value' : 'picker-field__placeholder'">
                {{ form.reportDate || '请选择出险日期' }}
              </text>
              <view class="picker-field__arrow" />
            </view>
          </picker>
        </FormField>

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
        :title="CASE_FORM_COPY.insuranceSection"
        :description="CASE_FORM_COPY.insuranceDesc"
      >
        <FormField
          v-model="form.reportNumber"
          label="出险报案号"
          placeholder="请输入保险出险报案号"
          :maxlength="50"
          required
          :error="fieldErrors.reportNumber"
        />
        <FormField
          v-model="form.insuranceCompany"
          label="承保保险公司"
          placeholder="请输入承保保险公司名称"
          :maxlength="100"
          required
          :error="fieldErrors.insuranceCompany"
        />
      </FormSection>
    </view>

    <view class="case-create-page__spacer" />

    <SubmitBar
      fixed
      :text="CASE_FORM_COPY.submit"
      :hint="CASE_FORM_COPY.submitHint"
      :loading="loading"
      @submit="submitForm"
    />
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { createPatientCase } from '@/api/case'
import PageHeader from '@/components/common/PageHeader.vue'
import FormField from '@/components/form/FormField.vue'
import FormSection from '@/components/form/FormSection.vue'
import SubmitBar from '@/components/form/SubmitBar.vue'
import { useCaseDict } from '@/composables/useCaseDict'
import { CASE_FORM_COPY, FEEDBACK_COPY } from '@/constants/copy'
import type { CaseCreateBody } from '@/types/case'
import { showError, showSuccess } from '@/utils/feedback'
import { reportError } from '@/utils/logger'
import { validateCaseForm } from '@/utils/validators'

const loading = ref(false)
const fieldErrors = reactive<Partial<Record<keyof CaseCreateBody, string>>>({})

const form = reactive<CaseCreateBody>({
  victimName: '',
  victimPhone: '',
  reportDate: '',
  province: '',
  city: '',
  district: '',
  accidentType: '',
  injuryType: '',
  reportNumber: '',
  insuranceCompany: '',
})

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

onLoad(() => {
  loadDicts()
})

const onDateChange = (e: { detail: { value: string } }) => {
  form.reportDate = e.detail.value
  fieldErrors.reportDate = ''
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

const clearFieldErrors = () => {
  Object.keys(fieldErrors).forEach((key) => {
    delete fieldErrors[key as keyof CaseCreateBody]
  })
}

const submitForm = async () => {
  clearFieldErrors()
  const result = validateCaseForm(form)
  if (!result.valid) {
    if (result.field) {
      fieldErrors[result.field] = result.message
    }
    showError(result.message || FEEDBACK_COPY.validationRequired)
    return
  }

  loading.value = true
  try {
    await createPatientCase(form)
    showSuccess(FEEDBACK_COPY.caseCreateSuccess)
    setTimeout(() => {
      uni.navigateBack()
      uni.$emit('refreshList')
    }, 1500)
  } catch (error) {
    reportError(error, { scope: 'create_case' })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';
@import '@/styles/mixins.scss';

.case-create-page {
  @include page-background;
  min-height: 100vh;
}

.case-create-page__body {
  padding: 0 $space-xl $space-md;
}

.case-create-page__spacer {
  height: 200rpx;
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
