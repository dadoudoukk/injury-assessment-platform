<template>
  <view class="agency-register-page">
    <PageHeader :title="AGENCY_REGISTER_COPY.title" :subtitle="AGENCY_REGISTER_COPY.subtitle" />

    <view class="agency-register-page__body">
      <FormSection
        :title="AGENCY_REGISTER_COPY.basicSection"
        :description="AGENCY_REGISTER_COPY.basicDesc"
      >
        <FormField
          v-model="form.agencyName"
          label="机构名称"
          placeholder="请输入机构完整名称"
          :maxlength="100"
          required
          :error="fieldErrors.agencyName"
        />
        <FormField
          v-model="form.contactPerson"
          label="联系人"
          placeholder="请输入联系人姓名"
          :maxlength="50"
          required
          :error="fieldErrors.contactPerson"
        />
        <FormField
          v-model="form.contactPhone"
          label="联系电话"
          placeholder="请输入手机号"
          input-type="number"
          :maxlength="20"
          required
          :error="fieldErrors.contactPhone"
        />
      </FormSection>

      <FormSection
        :title="AGENCY_REGISTER_COPY.addressSection"
        :description="AGENCY_REGISTER_COPY.addressDesc"
      >
        <FormField label="所在地区" required custom :error="fieldErrors.province">
          <picker mode="region" @change="onRegionChange">
            <view class="picker-field">
              <text :class="form.province ? 'picker-field__value' : 'picker-field__placeholder'">
                {{ regionText }}
              </text>
              <view class="picker-field__arrow" />
            </view>
          </picker>
        </FormField>

        <view class="agency-register-page__address-field">
          <view class="agency-register-page__address-header">
            <text class="agency-register-page__address-label">
              详细地址 <text class="agency-register-page__required">*</text>
            </text>
            <view class="agency-register-page__map-btn" @click="chooseLocation">
              <text class="agency-register-page__map-icon">📍</text>
              <text>{{ AGENCY_REGISTER_COPY.mapPick }}</text>
            </view>
          </view>
          <textarea
            v-model="form.address"
            class="agency-register-page__textarea"
            :class="{ 'agency-register-page__textarea--error': !!fieldErrors.address }"
            placeholder="请输入详细的办公地址"
            maxlength="255"
            placeholder-class="picker-field__placeholder"
          />
          <text v-if="fieldErrors.address" class="agency-register-page__error">
            {{ fieldErrors.address }}
          </text>
        </view>
      </FormSection>
    </view>

    <view class="agency-register-page__spacer" />

    <SubmitBar
      fixed
      :text="AGENCY_REGISTER_COPY.submit"
      :hint="AGENCY_REGISTER_COPY.submitHint"
      :loading="loading"
      @submit="submitForm"
    />
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { registerAgency } from '@/api/agency'
import PageHeader from '@/components/common/PageHeader.vue'
import FormField from '@/components/form/FormField.vue'
import FormSection from '@/components/form/FormSection.vue'
import SubmitBar from '@/components/form/SubmitBar.vue'
import { AGENCY_REGISTER_COPY, FEEDBACK_COPY } from '@/constants/copy'
import type { AgencyRegisterBody } from '@/types/case'
import { showError } from '@/utils/feedback'
import { reportError } from '@/utils/logger'
import { validateAgencyRegisterForm } from '@/utils/validators'

const loading = ref(false)
const fieldErrors = reactive<Partial<Record<keyof AgencyRegisterBody, string>>>({})

const form = reactive<AgencyRegisterBody>({
  agencyName: '',
  contactPerson: '',
  contactPhone: '',
  province: '',
  city: '',
  district: '',
  address: '',
})

const regionText = computed(() =>
  form.province ? `${form.province} ${form.city} ${form.district}` : '请选择省/市/区',
)

const onRegionChange = (e: { detail: { value: string[] } }) => {
  const [province, city, district] = e.detail.value
  form.province = province
  form.city = city
  form.district = district
  fieldErrors.province = ''
}

const chooseLocation = () => {
  uni.chooseLocation({
    success: (res) => {
      if (res.address || res.name) {
        let fullAddress = res.address || ''
        if (res.name && !fullAddress.includes(res.name)) {
          fullAddress += ` ${res.name}`
        }
        form.address = fullAddress.trim()
        fieldErrors.address = ''
      }
    },
    fail: (err) => {
      const errMsg = err?.errMsg || ''
      if (errMsg.includes('auth deny') || errMsg.includes('authorize')) {
        uni.showModal({
          title: AGENCY_REGISTER_COPY.locationAuthTitle,
          content: AGENCY_REGISTER_COPY.locationAuthContent,
          confirmText: AGENCY_REGISTER_COPY.locationGoSettings,
          success: (res) => {
            if (res.confirm) uni.openSetting({})
          },
        })
      } else if (errMsg.includes('requiredPrivateInfos')) {
        showError(AGENCY_REGISTER_COPY.locationNotConfigured)
      } else if (!errMsg.includes('cancel')) {
        showError(AGENCY_REGISTER_COPY.locationFallback)
      }
    },
  })
}

const clearFieldErrors = () => {
  Object.keys(fieldErrors).forEach((key) => {
    delete fieldErrors[key as keyof AgencyRegisterBody]
  })
}

const submitForm = async () => {
  clearFieldErrors()
  const result = validateAgencyRegisterForm(form)
  if (!result.valid) {
    if (result.field) {
      fieldErrors[result.field] = result.message
    }
    showError(result.message || FEEDBACK_COPY.validationRequired)
    return
  }

  loading.value = true
  try {
    await registerAgency(form)
    uni.showModal({
      title: AGENCY_REGISTER_COPY.submitSuccessTitle,
      content: AGENCY_REGISTER_COPY.submitSuccessContent,
      showCancel: false,
      confirmColor: '#2563EB',
      success: () => {
        uni.navigateBack()
      },
    })
  } catch (error) {
    reportError(error, { scope: 'agency_register' })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';
@import '@/styles/mixins.scss';

.agency-register-page {
  @include page-background;
  min-height: 100vh;
}

.agency-register-page__body {
  padding: 0 $space-xl $space-md;
}

.agency-register-page__spacer {
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

.agency-register-page__address-field {
  margin-bottom: 0;
}

.agency-register-page__address-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: $space-md;
  margin-bottom: $space-sm;
}

.agency-register-page__address-label {
  flex: 1;
  min-width: 0;
  font-size: $font-size-body;
  color: $color-body;
  font-weight: 500;
}

.agency-register-page__required {
  color: $color-error;
}

.agency-register-page__map-btn {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  font-size: $font-size-caption;
  color: $color-primary;
  padding: 4rpx 0;
}

.agency-register-page__map-icon {
  margin-right: 4rpx;
  font-size: $font-size-caption;
}

.agency-register-page__textarea {
  @include input-container;
  width: 100%;
  min-height: 160rpx;
  padding: $space-md $space-sm;
  line-height: 1.6;
  box-sizing: border-box;

  &--error {
    border-color: $color-error;
  }
}

.agency-register-page__error {
  display: block;
  margin-top: $space-xs;
  font-size: $font-size-caption;
  color: $color-error;
}
</style>
