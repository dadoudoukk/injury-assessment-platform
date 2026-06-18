<script setup lang="ts">
import { onLaunch, onShow, onHide, onError } from '@dcloudio/uni-app'
import { trackEvent } from '@/utils/logger'

onLaunch(() => {
  trackEvent('app_launch', {
    env: import.meta.env.MODE,
  })
})

onShow(() => {
  trackEvent('app_show')
})

onHide(() => {
  trackEvent('app_hide')
})

onError((error: string) => {
  trackEvent('app_error', { message: error })
})
</script>
<style lang="scss">
@use '@/styles/wot-theme.scss';

page {
  background-color: #f4f6f8;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}
</style>
