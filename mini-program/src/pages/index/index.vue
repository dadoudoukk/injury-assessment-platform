<template>
  <view class="workbench-page">
    <CaseStatBar
      :items="statItems"
      :active-key="activeStatKey"
      @select="onStatSelect"
    />

    <CaseFilterTabs
      :tabs="filterTabs"
      :current-index="currentTab"
      @change="switchTab"
    />

    <view class="workbench-page__body">
      <LoadingState v-if="!initialized" fullscreen />

      <EmptyState
        v-else-if="initialError"
        variant="error"
        :action-text="FEEDBACK_COPY.retry"
        @action="refresh"
      />

      <EmptyState
        v-else-if="caseList.length === 0 && !loading"
        variant="search"
      />

      <template v-else>
        <CaseCard
          v-for="item in caseList"
          :key="item.id"
          :item="item"
          mode="agency"
          :accident-type-label="getAccidentTypeLabel(item.accidentType)"
          :accept-loading="acceptingId === item.id"
          @click="goToDetail(item.id)"
          @accept="handleAccept(item)"
          @appraise="goToDetail(item.id)"
          @view="goToDetail(item.id)"
        />

        <LoadMoreFooter
          :loading="loading"
          :has-more="hasMore"
          :error="loadMoreError"
          :no-more-text="LIST_COPY.noMoreAgency"
          @retry="retryLoadMore"
        />
      </template>
    </view>

    <BottomNav :items="navItems" @select="onNavSelect" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad, onPullDownRefresh, onReachBottom, onShow } from '@dcloudio/uni-app'
import { acceptCase, fetchCaseList, fetchCaseStatsSummary } from '@/api/case'
import CaseCard from '@/components/case/CaseCard.vue'
import CaseFilterTabs from '@/components/case/CaseFilterTabs.vue'
import type { CaseFilterTab } from '@/components/case/CaseFilterTabs.vue'
import CaseStatBar from '@/components/case/CaseStatBar.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import LoadMoreFooter from '@/components/common/LoadMoreFooter.vue'
import BottomNav from '@/components/navigation/BottomNav.vue'
import { useCaseDict } from '@/composables/useCaseDict'
import { usePagination } from '@/composables/usePagination'
import { CASE_STATUS } from '@/constants/status'
import { FEEDBACK_COPY, LIST_COPY } from '@/constants/copy'
import { ROUTES } from '@/constants/routes'
import type { CaseItem, CaseStatsSummary } from '@/types/case'
import type { CaseStatusValue } from '@/constants/status'
import { ensureAgencySession } from '@/utils/agency-auth'
import { showSuccess } from '@/utils/feedback'
import { reportError, trackPageView } from '@/utils/logger'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()
const acceptingId = ref('')
const currentTab = ref(0)
const activeStatKey = ref<string>()
const statsSummary = ref<CaseStatsSummary>({ pending: 0, processing: 0, completed: 0 })

const filterTabs: CaseFilterTab[] = [
  { name: '全部', key: 'all', value: null },
  { name: '待确认', key: 'pending', value: CASE_STATUS.PENDING_CONFIRM as CaseStatusValue },
  { name: '已受理', key: 'accepted', value: CASE_STATUS.ACCEPTED as CaseStatusValue },
  { name: '鉴定中', key: 'appraising', value: CASE_STATUS.APPRAISING as CaseStatusValue },
  { name: '已打回', key: 'rework', value: CASE_STATUS.REWORK as CaseStatusValue },
  { name: '已完成', key: 'completed', value: CASE_STATUS.COMPLETED as CaseStatusValue },
]

const STAT_TO_TAB: Record<string, number> = {
  pending: 1,
  completed: 5,
}

const TAB_TO_STAT: Partial<Record<number, string>> = {
  1: 'pending',
  5: 'completed',
}

const { getAccidentTypeLabel, loadDicts } = useCaseDict()

const {
  list: caseList,
  loading,
  initialized,
  initialError,
  loadMoreError,
  hasMore,
  refresh,
  loadMore,
  retryLoadMore,
} = usePagination<CaseItem>((params) => {
  const tabStatus = filterTabs[currentTab.value].value
  return fetchCaseList({
    ...params,
    ...(tabStatus != null ? { status: tabStatus as CaseStatusValue } : {}),
  })
})

const statItems = computed(() => [
  { key: 'pending', label: '待处理', value: statsSummary.value.pending },
  {
    key: 'processing',
    label: '处理中',
    value: statsSummary.value.processing,
    clickable: false,
  },
  { key: 'completed', label: '已完成', value: statsSummary.value.completed },
])

const navItems = computed(() => [
  { key: 'workbench', label: '工作台', active: true },
  { key: 'mine', label: '个人中心' },
])

const loadStats = async () => {
  try {
    statsSummary.value = await fetchCaseStatsSummary()
  } catch (err) {
    reportError(err, { scope: 'case_stats' })
  }
}

const changeTab = (index: number, options?: { statKey?: string }) => {
  const statKey = options?.statKey ?? TAB_TO_STAT[index]
  const tabUnchanged = currentTab.value === index
  const statUnchanged = activeStatKey.value === statKey
  if (tabUnchanged && statUnchanged) return

  currentTab.value = index
  activeStatKey.value = statKey
  refresh()
}

const switchTab = (index: number) => {
  changeTab(index)
}

const onStatSelect = (key: string) => {
  const tabIndex = STAT_TO_TAB[key]
  if (tabIndex !== undefined) {
    changeTab(tabIndex, { statKey: key })
  }
}

const goToMine = () => {
  uni.navigateTo({ url: ROUTES.MINE })
}

const onNavSelect = (key: string) => {
  if (key === 'mine') goToMine()
}

const goToDetail = (id: string) => {
  uni.navigateTo({ url: `${ROUTES.DETAIL}?id=${id}` })
}

const handleAccept = async (item: CaseItem) => {
  acceptingId.value = item.id
  try {
    await acceptCase(item.id)
    showSuccess(FEEDBACK_COPY.acceptSuccess)
    await Promise.all([refresh(), loadStats()])
  } catch (err) {
    reportError(err, { scope: 'accept_case', caseId: item.id })
  } finally {
    acceptingId.value = ''
  }
}

onLoad(async () => {
  trackPageView('index/index')
  const ok = await ensureAgencySession()
  if (!ok) return
  await loadDicts()
  await Promise.all([refresh(), loadStats()])
})

const isFirstShow = ref(true)

onShow(async () => {
  if (!userStore.token) return
  const ok = await ensureAgencySession()
  if (!ok) return
  if (isFirstShow.value) {
    isFirstShow.value = false
    return
  }
  await Promise.all([refresh(), loadStats()])
})

onPullDownRefresh(() => {
  Promise.all([refresh(), loadStats()])
})

onReachBottom(() => {
  loadMore()
})
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';
@import '@/styles/mixins.scss';

.workbench-page {
  @include page-background;
  min-height: 100vh;
  padding-bottom: calc(110rpx + env(safe-area-inset-bottom));
}

.workbench-page__body {
  padding: $space-lg $space-xl $space-xl;
}
</style>
