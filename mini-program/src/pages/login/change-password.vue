<template>
  <view class="password-page">
    <PageHeader :title="PASSWORD_COPY.changeTitle" :subtitle="PASSWORD_COPY.changeSubtitle" />

    <view class="password-page__body">
      <view class="password-page__form">
      <FormSection title="密码信息">
        <FormField
          v-model="form.oldPassword"
          :label="PASSWORD_COPY.oldPassword"
          :placeholder="PASSWORD_COPY.oldPasswordPlaceholder"
          password
          required
          :error="fieldErrors.oldPassword"
        />
        <FormField
          v-model="form.newPassword"
          :label="PASSWORD_COPY.newPassword"
          :placeholder="PASSWORD_COPY.newPasswordPlaceholder"
          password
          required
          :error="fieldErrors.newPassword"
        />
        <FormField
          v-model="form.confirmPassword"
          :label="PASSWORD_COPY.confirmPassword"
          :placeholder="PASSWORD_COPY.confirmPasswordPlaceholder"
          password
          required
          :error="fieldErrors.confirmPassword"
        />
      </FormSection>
      </view>
    </view>

    <view class="password-page__spacer" />

    <SubmitBar
      fixed
      :text="PASSWORD_COPY.changeSubmit"
      :loading="loading"
      @submit="handleSubmit"
    />
  </view>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { changePassword } from '@/api/user'
import PageHeader from '@/components/common/PageHeader.vue'
import FormField from '@/components/form/FormField.vue'
import FormSection from '@/components/form/FormSection.vue'
import SubmitBar from '@/components/form/SubmitBar.vue'
import { FEEDBACK_COPY, PASSWORD_COPY } from '@/constants/copy'
import { ROUTES } from '@/constants/routes'
import { useUserStore } from '@/store/modules/user'
import { showAlert, showError } from '@/utils/feedback'
import { reportError } from '@/utils/logger'
import { validateChangePasswordForm, type ChangePasswordField } from '@/utils/validators'

const userStore = useUserStore()
const loading = ref(false)
const fieldErrors = reactive<Partial<Record<ChangePasswordField, string>>>({})

const form = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const clearFieldErrors = () => {
  ;(Object.keys(fieldErrors) as ChangePasswordField[]).forEach((key) => {
    delete fieldErrors[key]
  })
}

const handleSubmit = async () => {
  clearFieldErrors()
  const result = validateChangePasswordForm(form)
  if (!result.valid) {
    const field = result.field
    if (field) {
      fieldErrors[field] = result.message ?? ''
    }
    showError(result.message || FEEDBACK_COPY.validationRequired)
    return
  }

  loading.value = true
  try {
    await changePassword({
      oldPassword: form.oldPassword.trim(),
      newPassword: form.newPassword.trim(),
    })
    userStore.logout()
    await showAlert(FEEDBACK_COPY.passwordChangeTitle, FEEDBACK_COPY.passwordChangeSuccess)
    uni.reLaunch({ url: ROUTES.AGENCY_LOGIN })
  } catch (e) {
    reportError(e, { scope: 'change_password' })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';
@import '@/styles/mixins.scss';

.password-page {
  @include page-background;
  min-height: 100vh;
}

.password-page__body {
  padding: 0 $space-xl;
}

.password-page__form {
  position: relative;
  z-index: 10;
}

.password-page__spacer {
  height: calc(160rpx + env(safe-area-inset-bottom));
}
</style>
