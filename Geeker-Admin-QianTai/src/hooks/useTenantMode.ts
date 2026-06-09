import { computed } from "vue";
import { useUserStore } from "@/stores/modules/user";

/**
 * 租户模式：机构账号（userInfo.agencyId 非空）与平台账号的 UI 隔离标识
 */
export const useTenantMode = () => {
  const userStore = useUserStore();

  const isAgencyMode = computed(() => userStore.userInfo.agencyId != null);

  return { isAgencyMode };
};
