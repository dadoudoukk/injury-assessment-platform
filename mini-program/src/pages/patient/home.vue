<template>
  <view class="portal-page">
    <PageHeader
      :title="APP_COPY.brandTitle"
      :subtitle="APP_COPY.brandSubtitle"
    />

    <LoadingState v-if="wxLoggingIn" fullscreen text="登录中..." />
    <LoadingState v-else-if="!sessionReady" fullscreen />

    <template v-else>
      <view v-if="showAgencyHub" class="portal-page__welcome">
        <text class="portal-page__welcome-text">
          {{ PORTAL_COPY.agencyWelcome }}，{{ welcomeName }}
        </text>
      </view>

      <view class="portal-page__entries">
        <view
          v-if="showAgencyHub"
          class="entry-card entry-card--agency"
          hover-class="entry-card--hover"
          @click="goToWorkbench"
        >
          <text class="entry-card__icon">📋</text>
          <view class="entry-card__content">
            <text class="entry-card__title">{{ PORTAL_COPY.workbenchTitle }}</text>
            <text class="entry-card__desc">{{ PORTAL_COPY.workbenchDesc }}</text>
          </view>
          <view class="entry-card__arrow" />
        </view>

        <view
          v-if="showAgencyHub"
          class="entry-card entry-card--muted"
          hover-class="entry-card--hover"
          @click="goToMine"
        >
          <text class="entry-card__icon">👤</text>
          <view class="entry-card__content">
            <text class="entry-card__title">{{ PORTAL_COPY.mineTitle }}</text>
            <text class="entry-card__desc">{{ PORTAL_COPY.mineDesc }}</text>
          </view>
          <view class="entry-card__arrow" />
        </view>

        <button
          v-if="!userStore.token"
          class="entry-card entry-card--patient"
          open-type="getPhoneNumber"
          @getphonenumber="onGetPhoneNumber"
        >
          <text class="entry-card__icon">🩹</text>
          <view class="entry-card__content">
            <text class="entry-card__title">{{ PORTAL_COPY.patientEntryTitle }}</text>
            <text class="entry-card__desc">{{ PORTAL_COPY.patientEntryDesc }}</text>
          </view>
          <view class="entry-card__arrow" />
        </button>

        <view
          v-if="!userStore.token"
          class="entry-card entry-card--agency"
          hover-class="entry-card--hover"
          @click="goToAgencyLogin"
        >
          <text class="entry-card__icon">🏥</text>
          <view class="entry-card__content">
            <text class="entry-card__title">{{ PORTAL_COPY.agencyEntryTitle }}</text>
            <text class="entry-card__desc">{{ PORTAL_COPY.agencyEntryDesc }}</text>
          </view>
          <view class="entry-card__arrow" />
        </view>

        <view v-if="!userStore.token" class="portal-page__register" @click="goToRegister">
          <text class="portal-page__register-hint">{{ PORTAL_COPY.registerHint }}</text>
          <text class="portal-page__register-link">{{ PORTAL_COPY.registerLink }}</text>
        </view>
      </view>

      <view v-if="!userStore.token" class="portal-page__flow">
        <text class="portal-page__flow-title">{{ PORTAL_COPY.serviceFlowTitle }}</text>
        <view class="portal-page__flow-steps">
          <view
            v-for="(step, index) in PORTAL_COPY.steps"
            :key="step"
            class="portal-page__flow-step"
          >
            <view class="portal-page__flow-dot">{{ index + 1 }}</view>
            <text class="portal-page__flow-label">{{ step }}</text>
            <view
              v-if="index < PORTAL_COPY.steps.length - 1"
              class="portal-page__flow-line"
            />
          </view>
        </view>
      </view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { wxLoginPatient } from '@/api/auth'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import { APP_COPY, FEEDBACK_COPY, PORTAL_COPY } from '@/constants/copy'
import { ROUTES } from '@/constants/routes'
import { fetchAndSetUserInfo } from '@/services/user-session'
import { ensureAgencySession } from '@/utils/agency-auth'
import { isAgencyUser } from '@/utils/role'
import { showError, showSuccess } from '@/utils/feedback'
import { reportError, trackPageView } from '@/utils/logger'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()
const sessionReady = ref(!userStore.token)
/** 微信授权登录进行中，避免 onShow 与登录流程冲突 */
const wxLoggingIn = ref(false)
/** 已触发患者端跳转，避免重复 reLaunch */
const redirectingToList = ref(false)

const showAgencyHub = computed(
  () => userStore.token && isAgencyUser(userStore.userInfo),
)

const welcomeName = computed(
  () => userStore.userInfo?.nickname || userStore.userInfo?.username || '机构用户',
)

function goToPatientList() {
  if (redirectingToList.value) return
  redirectingToList.value = true
  uni.reLaunch({ url: ROUTES.PATIENT_LIST })
}

const redirectPatientIfLoggedIn = async () => {
  if (wxLoggingIn.value || redirectingToList.value) return

  if (!userStore.token) {
    sessionReady.value = true
    return
  }

  await fetchAndSetUserInfo()
  if (isAgencyUser(userStore.userInfo)) {
    sessionReady.value = true
    await ensureAgencySession(false)
    return
  }

  goToPatientList()
}

onShow(() => {
  trackPageView('patient/home')
  redirectPatientIfLoggedIn()
})

const goToAgencyLogin = () => {
  uni.navigateTo({ url: ROUTES.AGENCY_LOGIN })
}

const goToRegister = () => {
  uni.navigateTo({ url: ROUTES.AGENCY_REGISTER })
}

const goToMine = () => {
  uni.navigateTo({ url: ROUTES.MINE })
}

const goToWorkbench = () => {
  uni.navigateTo({ url: ROUTES.WORKBENCH })
}

const onGetPhoneNumber = async (e: { detail: { errMsg: string; code?: string } }) => {
  if (e.detail.errMsg !== 'getPhoneNumber:ok') {
    showError(PORTAL_COPY.phoneAuthRequired)
    return
  }
  if (wxLoggingIn.value) return

  wxLoggingIn.value = true
  try {
    userStore.clearSession()
    const res = await wxLoginPatient({ code: e.detail.code! })

    if (res?.access_token) {
      userStore.setToken(res.access_token)
      userStore.setLastUserType('patient')
      await fetchAndSetUserInfo()
      if (isAgencyUser(userStore.userInfo)) {
        showError(PORTAL_COPY.agencyAccountHint)
        userStore.logout()
        return
      }
      showSuccess(FEEDBACK_COPY.loginSuccess)
      goToPatientList()
    }
  } catch (error) {
    reportError(error, { scope: 'wx_patient_login' })
  } finally {
    wxLoggingIn.value = false
  }
}
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';
@import '@/styles/mixins.scss';

.portal-page {
  @include page-background;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.portal-page__welcome {
  padding: 0 $space-3xl $space-md;
}

.portal-page__welcome-text {
  font-size: $font-size-body;
  color: $color-secondary;
}

.portal-page__entries {
  padding: 0 $space-3xl;
  flex: 1;
}

.entry-card {
  @include card-base;
  display: flex;
  flex-direction: row;
  align-items: center;
  margin-bottom: $space-xl;
  padding: $space-xl;
  line-height: normal;
  text-align: left;
  transition: border-color 0.2s, background-color 0.2s;

  &::after {
    border: none;
  }
}

.entry-card--hover {
  background-color: #f9fafb;
  border-color: #d1d5db;
}

.entry-card--patient {
  border-left: 8rpx solid $color-primary;
}

.entry-card--agency {
  border-left: 8rpx solid #4b5563;
}

.entry-card--muted {
  border-left: 8rpx solid $color-hint;
}

.entry-card__icon {
  font-size: 48rpx;
  margin-right: $space-lg;
  flex-shrink: 0;
}

.entry-card__content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.entry-card__title {
  font-size: $font-size-card-title;
  font-weight: 600;
  color: $color-title;
  margin-bottom: $space-xs;
}

.entry-card__desc {
  font-size: $font-size-caption;
  color: $color-secondary;
  line-height: 1.5;
}

.entry-card__arrow {
  width: 16rpx;
  height: 16rpx;
  border-top: 4rpx solid $color-hint;
  border-right: 4rpx solid $color-hint;
  transform: rotate(45deg);
  flex-shrink: 0;
  margin-left: $space-sm;
}

.portal-page__register {
  text-align: center;
  margin-top: $space-2xl;
  padding: $space-lg 0;
}

.portal-page__register-hint {
  font-size: $font-size-body;
  color: $color-secondary;
}

.portal-page__register-link {
  font-size: $font-size-body;
  color: $color-primary;
  font-weight: 500;
  margin-left: $space-xs;
}

.portal-page__flow {
  margin: $space-2xl $space-3xl $space-3xl;
  padding: $space-xl;
  background-color: $color-card-bg;
  border: 2rpx solid $color-border;
  border-radius: $radius-md;
}

.portal-page__flow-title {
  display: block;
  font-size: $font-size-body;
  font-weight: 600;
  color: $color-title;
  margin-bottom: $space-lg;
}

.portal-page__flow-steps {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.portal-page__flow-step {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}

.portal-page__flow-dot {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  background-color: $color-primary;
  color: #ffffff;
  font-size: $font-size-caption;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: $space-sm;
  z-index: 1;
}

.portal-page__flow-label {
  font-size: $font-size-caption;
  color: $color-secondary;
  text-align: center;
}

.portal-page__flow-line {
  position: absolute;
  top: 24rpx;
  left: 50%;
  width: 100%;
  height: 2rpx;
  background-color: $color-border;
  z-index: 0;
}
</style>
