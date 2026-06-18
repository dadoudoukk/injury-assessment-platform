<template>
  <view class="login-page">
    <PageHeader :title="LOGIN_COPY.title" :subtitle="LOGIN_COPY.subtitle" />

    <LoadingState v-if="wxLoggingIn" fullscreen text="登录中..." />

    <view v-else class="login-page__body">
      <!-- 表单区独立层级，且不使用原生 button，避免与下方微信授权按钮抢触摸 -->
      <view class="login-page__form">
        <FormSection title="账号密码登录">
          <view class="login-field">
            <text class="login-field__label">{{ LOGIN_COPY.username }}</text>
            <input
              v-model="username"
              class="login-field__input"
              type="text"
              :placeholder="LOGIN_COPY.usernamePlaceholder"
              placeholder-class="login-field__placeholder"
              :adjust-position="true"
              :hold-keyboard="true"
              confirm-type="next"
            />
          </view>
          <view class="login-field">
            <text class="login-field__label">{{ LOGIN_COPY.password }}</text>
            <input
              v-model="password"
              class="login-field__input"
              type="text"
              password
              :placeholder="LOGIN_COPY.passwordPlaceholder"
              placeholder-class="login-field__placeholder"
              :adjust-position="true"
              :hold-keyboard="true"
              confirm-type="done"
              @confirm="handleLogin"
            />
          </view>
        </FormSection>

        <view
          class="login-page__submit"
          :class="{ 'login-page__submit--disabled': loading }"
          @tap="handleLogin"
        >
          <text>{{ loading ? '登录中...' : LOGIN_COPY.submit }}</text>
        </view>
      </view>

      <view class="login-page__divider">
        <view class="login-page__divider-line" />
        <text class="login-page__divider-text">{{ LOGIN_COPY.divider }}</text>
        <view class="login-page__divider-line" />
      </view>

      <view class="login-page__wx-wrap">
        <button
          class="login-page__wx-btn"
          hover-class="none"
          open-type="getPhoneNumber"
          @getphonenumber="onWxLogin"
        >
          {{ LOGIN_COPY.wxLogin }}
        </button>
      </view>

      <text class="login-page__footer">{{ LOGIN_COPY.footer }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { loginWithPassword, wxLoginAgency } from '@/api/auth'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import FormSection from '@/components/form/FormSection.vue'
import { LOGIN_COPY } from '@/constants/copy'
import { useUserStore } from '@/store/modules/user'
import { completeAgencyLogin } from '@/utils/agency-auth'
import { showError } from '@/utils/feedback'
import { reportError, trackPageView } from '@/utils/logger'

const userStore = useUserStore()
const loading = ref(false)
const wxLoggingIn = ref(false)
const username = ref('')
const password = ref('')

onLoad(() => {
  trackPageView('login/index')
})

onShow(() => {
  if (wxLoggingIn.value) return
})

const onWxLogin = async (e: { detail: { errMsg: string; code?: string } }) => {
  if (e.detail.errMsg !== 'getPhoneNumber:ok') {
    showError(LOGIN_COPY.phoneAuthRequired)
    return
  }
  if (wxLoggingIn.value) return

  wxLoggingIn.value = true
  let redirected = false
  try {
    userStore.clearSession()
    const res = await wxLoginAgency({ code: e.detail.code! })
    if (res?.access_token) {
      redirected = await completeAgencyLogin(res)
    }
  } catch (error) {
    reportError(error, { scope: 'wx_agency_login' })
  } finally {
    if (!redirected) {
      wxLoggingIn.value = false
    }
  }
}

const handleLogin = async () => {
  if (loading.value) return
  if (!username.value.trim()) {
    return showError('请输入账号')
  }
  if (!password.value.trim()) {
    return showError('请输入密码')
  }

  loading.value = true
  let redirected = false
  try {
    userStore.clearSession()
    const res = await loginWithPassword({
      username: username.value.trim(),
      password: password.value,
    })
    if (res?.access_token) {
      redirected = await completeAgencyLogin(res)
    }
  } catch (error) {
    reportError(error, { scope: 'password_login' })
  } finally {
    if (!redirected) {
      loading.value = false
    }
  }
}
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';
@import '@/styles/mixins.scss';

.login-page {
  @include page-background;
  min-height: 100vh;
}

.login-page__body {
  padding: 0 $space-3xl $space-3xl;
}

.login-page__form {
  position: relative;
  z-index: 10;
}

.login-field {
  margin-bottom: $space-lg;

  &:last-child {
    margin-bottom: 0;
  }
}

.login-field__label {
  display: block;
  font-size: $font-size-body;
  color: $color-body;
  font-weight: 500;
  margin-bottom: $space-sm;
}

.login-field__input {
  @include input-container;
  display: block;
  width: 100%;
  height: 80rpx;
  line-height: 80rpx;
}

.login-field__placeholder {
  color: $color-hint;
}

.login-page__submit {
  @include primary-button;
  margin-top: $space-xl;
  text-align: center;

  &--disabled {
    opacity: 0.6;
    pointer-events: none;
  }
}

.login-page__wx-wrap {
  overflow: hidden;
  position: relative;
  z-index: 1;
}

.login-page__wx-btn {
  background-color: #07c160;
  color: #ffffff;
  font-size: 32rpx;
  font-weight: 500;
  height: 96rpx;
  line-height: 96rpx;
  border-radius: $radius-sm;

  &::after {
    border: none;
  }
}

.login-page__divider {
  display: flex;
  align-items: center;
  margin: $space-2xl 0;
  gap: $space-md;
}

.login-page__divider-line {
  flex: 1;
  height: 2rpx;
  background-color: $color-border;
}

.login-page__divider-text {
  font-size: $font-size-caption;
  color: $color-hint;
  flex-shrink: 0;
}

.login-page__footer {
  display: block;
  margin-top: $space-xl;
  text-align: center;
  font-size: 26rpx;
  color: $color-hint;
  line-height: 1.5;
}
</style>
