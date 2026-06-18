import { createSSRApp } from "vue";
import App from "./App.vue";
import pinia from './store'
import { reportError } from '@/utils/logger'

export function createApp() {
  const app = createSSRApp(App);
  app.use(pinia);
  app.config.errorHandler = (err, _instance, info) => {
    reportError(err, { scope: 'vue', info })
  }
  return {
    app,
  };
}
