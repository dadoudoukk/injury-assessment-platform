<template>
  <view class="password-page">
    <PageHeader :title="PASSWORD_COPY.setTitle" :subtitle="PASSWORD_COPY.setSubtitle" />

    <LoadingState v-if="sessionChecking" fullscreen />

    <view v-else class="password-page__body">
      <FormSection title="密码信息">
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

      <view class="password-page__logout" @click="handleLogout">
        <text class="password-page__logout-text">{{ PASSWORD_COPY.logoutLink }}</text>
      </view>
    </view>

    <view v-if="!sessionChecking" class="password-page__spacer" />

    <SubmitBar
      v-if="!sessionChecking"
      fixed
      :text="PASSWORD_COPY.setSubmit"
      :loading="loading"
      @submit="handleSubmit"
    />
  </view>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { setInitialPassword } from '@/api/user'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import FormField from '@/components/form/FormField.vue'
import FormSection from '@/components/form/FormSection.vue'
import SubmitBar from '@/components/form/SubmitBar.vue'
import { FEEDBACK_COPY, PASSWORD_COPY } from '@/constants/copy'
import { ROUTES } from '@/constants/routes'
import { fetchAndSetUserInfo } from '@/services/user-session'
import { useUserStore } from '@/store/modules/user'
import { showConfirm, showError, showSuccess } from '@/utils/feedback'
import { reportError } from '@/utils/logger'
import { isAgencyUser } from '@/utils/role'
import { validateSetPasswordForm, type SetPasswordField } from '@/utils/validators'

const userStore = useUserStore()
const loading = ref(false)
const sessionChecking = ref(true)
const fieldErrors = reactive<Partial<Record<SetPasswordField, string>>>({})

const form = reactive({
  newPassword: '',
  confirmPassword: '',
})

onLoad(() => {
  checkSetPasswordSession()
})

async function checkSetPasswordSession() {
  sessionChecking.value = true
  try {
    if (!userStore.token) {
      uni.reLaunch({ url: ROUTES.AGENCY_LOGIN })
      return
    }
    await fetchAndSetUserInfo()
    if (!isAgencyUser(userStore.userInfo)) {
      uni.reLaunch({ url: ROUTES.PATIENT_HOME })
      return
    }
    if (!userStore.userInfo?.mustChangePassword) {
      uni.reLaunch({ url: ROUTES.WORKBENCH })
    }
  } finally {
    sessionChecking.value = false
  }
}

const clearFieldErrors = () => {
  ;(Object.keys(fieldErrors) as SetPasswordField[]).forEach((key) => {
    delete fieldErrors[key]
  })
}

const handleSubmit = async () => {
  clearFieldErrors()
  const result = validateSetPasswordForm(form)
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
    await setInitialPassword({ newPassword: form.newPassword.trim() })
    await fetchAndSetUserInfo()
    showSuccess(FEEDBACK_COPY.passwordSetSuccess)
    uni.reLaunch({ url: ROUTES.WORKBENCH })
  } catch (e) {
    reportError(e, { scope: 'set_password' })
  } finally {
    loading.value = false
  }
}

const handleLogout = async () => {
  const confirmed = await showConfirm({ content: FEEDBACK_COPY.logoutConfirm })
  if (confirmed) {
    userStore.logout()
    uni.reLaunch({ url: ROUTES.PATIENT_HOME })
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

.password-page__logout {
  margin-top: $space-xl;
  padding: $space-md 0;
  text-align: center;
}

.password-page__logout-text {
  font-size: $font-size-body;
  color: $color-secondary;
}

.password-page__spacer {
  height: calc(160rpx + env(safe-area-inset-bottom));
}
</style>
