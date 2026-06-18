<template>
  <view class="mine-page">
    <PageHeader :title="MINE_COPY.title" compact :show-brand-line="false" />

    <view class="mine-page__identity">
      <view class="mine-page__avatar">
        <text class="mine-page__avatar-text">{{ avatarText }}</text>
      </view>
      <text class="mine-page__name">{{ displayName }}</text>
      <view class="mine-page__role-tag">
        <text class="mine-page__role-text">{{ roleLabel }}</text>
      </view>
    </view>

    <view class="mine-page__sections">
      <FormSection
        v-if="isAgency"
        :title="MINE_COPY.agencySection"
        :description="MINE_COPY.agencySectionDesc"
      >
        <view class="mine-page__info-list">
          <view class="mine-page__info-row">
            <text class="mine-page__label">{{ MINE_COPY.contactPerson }}</text>
            <text class="mine-page__value">{{ userInfo?.contactPerson || MINE_COPY.emptyValue }}</text>
          </view>
          <view class="mine-page__info-row">
            <text class="mine-page__label">{{ MINE_COPY.contactPhone }}</text>
            <text class="mine-page__value">{{ userInfo?.contactPhone || MINE_COPY.emptyValue }}</text>
          </view>
          <view class="mine-page__info-row">
            <text class="mine-page__label">{{ MINE_COPY.region }}</text>
            <text class="mine-page__value">{{ regionText || MINE_COPY.emptyValue }}</text>
          </view>
          <view class="mine-page__info-row mine-page__info-row--col">
            <text class="mine-page__label">{{ MINE_COPY.address }}</text>
            <text class="mine-page__value">{{ userInfo?.address || MINE_COPY.emptyValue }}</text>
          </view>
        </view>
      </FormSection>

      <FormSection v-else :title="MINE_COPY.accountSection">
        <view class="mine-page__info-list">
          <view class="mine-page__info-row">
            <text class="mine-page__label">{{ MINE_COPY.phoneLabel }}</text>
            <text class="mine-page__value mine-page__value--emphasis">
              {{ maskedPhone || MINE_COPY.phoneEmpty }}
            </text>
          </view>
        </view>
      </FormSection>

      <view
        v-if="isAgency && !mustChangePassword"
        class="mine-page__menu"
        hover-class="mine-page__menu--hover"
        @click="goChangePassword"
      >
        <text class="mine-page__menu-text">{{ MINE_COPY.changePassword }}</text>
        <view class="mine-page__menu-arrow" />
      </view>
    </view>

    <view class="mine-page__logout-wrap" :class="{ 'mine-page__logout-wrap--with-nav': isAgency }">
      <button class="mine-page__logout-btn" @click="handleLogout">{{ MINE_COPY.logout }}</button>
    </view>

    <BottomNav v-if="isAgency" :items="navItems" @select="onNavSelect" />
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import PageHeader from '@/components/common/PageHeader.vue'
import FormSection from '@/components/form/FormSection.vue'
import BottomNav from '@/components/navigation/BottomNav.vue'
import { MINE_COPY } from '@/constants/copy'
import { ROUTES } from '@/constants/routes'
import { fetchAndSetUserInfo } from '@/services/user-session'
import { ensureAgencySession } from '@/utils/agency-auth'
import { formatRegion, maskPhone } from '@/utils/format'
import { isAgencyUser } from '@/utils/role'
import { showConfirm } from '@/utils/feedback'
import { trackPageView } from '@/utils/logger'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()

const userInfo = computed(() => userStore.userInfo)
const isAgency = computed(() => isAgencyUser(userInfo.value))
const mustChangePassword = computed(() => userInfo.value?.mustChangePassword === true)

const displayName = computed(() => {
  if (isAgency.value) {
    return userInfo.value?.agencyName || MINE_COPY.emptyValue
  }
  return maskedPhone.value || MINE_COPY.phoneEmpty
})

const roleLabel = computed(() =>
  isAgency.value ? MINE_COPY.agencyRole : MINE_COPY.patientRole,
)

const avatarText = computed(() => {
  const name = displayName.value
  if (!name || name === MINE_COPY.phoneEmpty || name === MINE_COPY.emptyValue) return '用'
  return name.slice(0, 1)
})

const maskedPhone = computed(() => {
  const phone = userInfo.value?.phone || ''
  return phone ? maskPhone(phone) : ''
})

const regionText = computed(() =>
  formatRegion(userInfo.value?.province, userInfo.value?.city, userInfo.value?.district),
)

const navItems = computed(() => [
  { key: 'workbench', label: '工作台' },
  { key: 'mine', label: '个人中心', active: true },
])

onShow(async () => {
  trackPageView('mine/index')
  if (!userStore.token) {
    uni.reLaunch({ url: ROUTES.PATIENT_HOME })
    return
  }
  await fetchAndSetUserInfo()
  if (isAgency.value) {
    await ensureAgencySession(false)
  }
})

const goChangePassword = () => {
  uni.navigateTo({ url: ROUTES.CHANGE_PASSWORD })
}

const onNavSelect = (key: string) => {
  if (key === 'workbench') {
    uni.navigateTo({ url: ROUTES.WORKBENCH })
  }
}

const handleLogout = async () => {
  const confirmed = await showConfirm({ content: MINE_COPY.logoutConfirm })
  if (confirmed) {
    userStore.logout()
    uni.reLaunch({ url: ROUTES.PATIENT_HOME })
  }
}
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';
@import '@/styles/mixins.scss';

.mine-page {
  @include page-background;
  min-height: 100vh;
  padding-bottom: calc(110rpx + env(safe-area-inset-bottom));
}

.mine-page__identity {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: $space-xl $space-3xl $space-2xl;
  margin: 0 $space-xl $space-lg;
  background-color: $color-card-bg;
  border: 2rpx solid $color-border;
  border-radius: $radius-md;
}

.mine-page__avatar {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, $color-primary 0%, #5cadff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: $space-md;
}

.mine-page__avatar-text {
  font-size: 48rpx;
  font-weight: 600;
  color: #ffffff;
}

.mine-page__name {
  font-size: $font-size-card-title;
  font-weight: 600;
  color: $color-title;
  text-align: center;
  line-height: 1.4;
  margin-bottom: $space-sm;
}

.mine-page__role-tag {
  padding: 4rpx 20rpx;
  background-color: rgba(37, 99, 235, 0.08);
  border-radius: 999rpx;
}

.mine-page__role-text {
  font-size: $font-size-caption;
  color: $color-primary;
  font-weight: 500;
}

.mine-page__sections {
  padding: 0 $space-xl;
}

.mine-page__info-list {
  display: flex;
  flex-direction: column;
  gap: $space-md;
}

.mine-page__info-row {
  display: flex;
  align-items: flex-start;
  font-size: $font-size-body;
  line-height: 1.5;

  &--col {
    flex-direction: column;
    gap: $space-xs;
  }
}

.mine-page__label {
  width: 160rpx;
  flex-shrink: 0;
  color: $color-secondary;
}

.mine-page__value {
  flex: 1;
  color: $color-title;
  word-break: break-all;

  &--emphasis {
    font-size: 36rpx;
    font-weight: 600;
    letter-spacing: 1rpx;
  }
}

.mine-page__menu {
  @include card-base;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: $space-lg;
  padding: $space-lg $space-xl;
}

.mine-page__menu--hover {
  background-color: #f9fafb;
  border-color: #d1d5db;
}

.mine-page__menu-text {
  font-size: $font-size-body;
  color: $color-primary;
  font-weight: 500;
}

.mine-page__menu-arrow {
  width: 16rpx;
  height: 16rpx;
  border-top: 4rpx solid $color-hint;
  border-right: 4rpx solid $color-hint;
  transform: rotate(45deg);
}

.mine-page__logout-wrap {
  padding: $space-2xl $space-xl $space-xl;

  &--with-nav {
    padding-bottom: $space-md;
  }
}

.mine-page__logout-btn {
  width: 100%;
  height: 96rpx;
  line-height: 96rpx;
  background-color: $color-card-bg;
  color: #ef4444;
  font-size: 32rpx;
  font-weight: 500;
  border: 2rpx solid #fecaca;
  border-radius: $radius-sm;

  &::after {
    border: none;
  }

  &:active {
    background-color: #fef2f2;
  }
}
</style>
