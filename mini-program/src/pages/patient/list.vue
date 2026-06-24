<template>
  <view class="patient-list-page">
    <PageHeader title="我的报案" compact :show-brand-line="true" />

    <view class="patient-list-page__body">
      <LoadingState v-if="!initialized" fullscreen />

      <EmptyState
        v-else-if="initialError"
        variant="error"
        :action-text="FEEDBACK_COPY.retry"
        @action="refresh"
      />

      <EmptyState
        v-else-if="mergedList.length === 0 && !loading"
        :title="EMPTY_STATE_COPY.patientListTitle"
        :description="EMPTY_STATE_COPY.patientListDesc"
        :action-text="EMPTY_STATE_COPY.patientListAction"
        @action="goToCreate"
      />

      <template v-else>
        <template v-for="entry in mergedList" :key="entryKey(entry)">
          <ApplicationCard
            v-if="entry.kind === 'application'"
            :item="entry.data"
            @click="goToApplicationDetail(entry.data.id)"
          />
          <CaseCard
            v-else
            :item="entry.data"
            mode="patient"
            report-no-prefix="报案号："
            @click="goToDetail(entry.data.id)"
          />
        </template>

        <LoadMoreFooter
          :loading="loading"
          :has-more="hasMore"
          :error="loadMoreError"
          :no-more-text="LIST_COPY.noMorePatient"
          @retry="retryLoadMore"
        />
      </template>
    </view>

    <BottomNav :items="navItems" @select="onNavSelect" />
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { onLoad, onPullDownRefresh, onReachBottom, onUnload } from '@dcloudio/uni-app'
import ApplicationCard from '@/components/case/ApplicationCard.vue'
import CaseCard from '@/components/case/CaseCard.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import LoadMoreFooter from '@/components/common/LoadMoreFooter.vue'
import BottomNav from '@/components/navigation/BottomNav.vue'
import { usePatientMergedList } from '@/composables/usePatientMergedList'
import { EMPTY_STATE_COPY, FEEDBACK_COPY, LIST_COPY } from '@/constants/copy'
import { ROUTES } from '@/constants/routes'
import type { PatientListEntry } from '@/types/case'
import { showConfirm } from '@/utils/feedback'
import { trackPageView } from '@/utils/logger'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()

const {
  mergedList,
  loading,
  initialized,
  initialError,
  loadMoreError,
  hasMore,
  refresh,
  loadMore,
  retryLoadMore,
} = usePatientMergedList()

const navItems = computed(() => [
  { key: 'create', label: '我要报案', variant: 'primary' as const },
  { key: 'logout', label: '退出登录', variant: 'danger' as const },
])

function entryKey(entry: PatientListEntry): string {
  return entry.kind === 'application' ? `app-${entry.data.id}` : `case-${entry.data.id}`
}

const goToCreate = () => {
  uni.navigateTo({ url: ROUTES.PATIENT_CREATE })
}

const goToDetail = (id: string | number) => {
  uni.navigateTo({ url: `${ROUTES.DETAIL}?id=${id}` })
}

const goToApplicationDetail = (id: string | number) => {
  uni.navigateTo({ url: `${ROUTES.PATIENT_APPLICATION_DETAIL}?id=${id}` })
}

const handleLogout = async () => {
  const confirmed = await showConfirm({ content: FEEDBACK_COPY.logoutConfirm })
  if (confirmed) {
    userStore.logout()
    uni.reLaunch({ url: ROUTES.PATIENT_HOME })
  }
}

const onNavSelect = (key: string) => {
  if (key === 'create') goToCreate()
  else if (key === 'logout') handleLogout()
}

const onRefreshList = () => {
  refresh()
}

onLoad(() => {
  trackPageView('patient/list')
  refresh()
  uni.$on('refreshList', onRefreshList)
})

onUnload(() => {
  uni.$off('refreshList', onRefreshList)
})

onPullDownRefresh(() => {
  refresh()
})

onReachBottom(() => {
  loadMore()
})
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';
@import '@/styles/mixins.scss';

.patient-list-page {
  @include page-background;
  min-height: 100vh;
  padding-bottom: calc(110rpx + env(safe-area-inset-bottom));
}

.patient-list-page__body {
  padding: 0 $space-xl $space-xl;
}
</style>
